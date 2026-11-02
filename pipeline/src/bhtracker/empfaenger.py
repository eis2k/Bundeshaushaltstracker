"""Empfänger von Bundesmitteln: Stamm, Namensabgleich, Verbindungen und Build der Empfänger-Seiten (Spec §4.6a).

Grundregel: Veröffentlicht wird nur, was aus einer amtlichen Quelle exakt hervorgeht oder von Hand bestätigt ist.
Ähnliche, aber nicht gleiche Namen landen als Kandidaten in data/review/.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field

from .bundestag import KATEGORIE_VORHER, Abgeordneter
from .lobbyregister import Profil
from .model import BudgetRow

# ---------------------------------------------------------------- Namen

RECHTSFORM_TOKENS = (
    "e v", "ev", "ggmbh", "gmbh und co kg", "gmbh", "mbh", "ag", "se", "kg", "gug", "ug", "gbr", "ohg", "kgaa", "aoer", "eg",
)
_UMLAUTE = str.maketrans({"ä": "ae", "ö": "oe", "ü": "ue", "ß": "ss"})
_KLAMMER = re.compile(r"\s*\([^)]*\)")
_NICHT_WORT = re.compile(r"[^a-z0-9]+")
AEHNLICH_SCHWELLE = 0.85


def norm_name(s: str) -> str:
    t = s.strip().lower().translate(_UMLAUTE)
    t = _KLAMMER.sub("", t)
    t = t.replace("&", " und ")
    t = _NICHT_WORT.sub(" ", t)          # Punkte, Kommas, Bindestriche → Leerzeichen ("e. v." → "e v")
    t = re.sub(r"\s+", " ", t).strip()
    changed = True
    while changed:
        changed = False
        for tk in RECHTSFORM_TOKENS:
            if t.endswith(" " + tk):
                t = t[: len(t) - len(tk)].rstrip()
                changed = True
    return t


def slug(s: str) -> str:
    base = norm_name(s).replace(" ", "-")
    base = re.sub(r"-+", "-", base).strip("-")
    return base[:60].rstrip("-") or "empfaenger"


# ---------------------------------------------------------------- Stamm

@dataclass
class Stamm:
    id: str
    name: str
    aliasse: list[str] = field(default_factory=list)
    lobbyregister: str | None = None
    titel: list[str] = field(default_factory=list)
    foerderkatalog: str | None = None
    art: str = "sonstige"
    geprueft: bool = False
    quelle: str | None = None

    def normen(self) -> set[str]:
        key = (self.name, tuple(self.aliasse))
        cache = self.__dict__.get("_normen_cache")
        if cache is None or cache[0] != key:
            cache = (key, {norm_name(self.name), *(norm_name(a) for a in self.aliasse)} - {""})
            self.__dict__["_normen_cache"] = cache
        return cache[1]


STOPP_TOKENS = {"fuer", "und", "der", "die", "das", "des", "den", "dem", "von", "vom", "zur", "zum", "mit", "bei", "deutsche", "deutscher",
                "deutsches", "deutschland", "deutschen", "bundes", "bund", "gesellschaft", "verband", "verein", "stiftung", "institut", "zentrum",
                "foerderung", "forschung", "international", "internationale", "berlin", "ev", "gmbh", "ggmbh", "landesverband", "bundesverband", "hilfe"}


class StammIndex:
    """Exakte Normen und Token-Index über den Stamm, damit Ähnlichkeitsvergleiche nur plausible Paare prüfen."""

    def __init__(self, stamm: dict[str, Stamm]):
        self.stamm = stamm
        self.exakt: dict[str, str] = {}
        self.tokens: dict[str, set[str]] = {}
        for sid, s in stamm.items():
            self.add(sid, s)

    @staticmethod
    def token(n: str) -> set[str]:
        return {t for t in n.split() if len(t) >= 4 and t not in STOPP_TOKENS}

    def add(self, sid: str, s: Stamm) -> None:
        for n in s.normen():
            self.exakt.setdefault(n, sid)
            for t in self.token(n):
                self.tokens.setdefault(t, set()).add(sid)

    def aehnliche(self, n: str) -> list[tuple[float, str]]:
        ids: set[str] = set()
        for t in self.token(n):
            ids |= self.tokens.get(t, set())
        hits = []
        for sid in ids:
            normen = self.stamm[sid].normen()
            sc = max(_aehnlich(n, sn) for sn in normen) if normen else 0.0
            if sc >= AEHNLICH_SCHWELLE:
                hits.append((sc, sid))
        return sorted(hits, reverse=True)


# ---------------------------------------------------------------- Empfänger aus Titeltexten

_ZUSCHUSS = re.compile(
    r"^(?:Zuschuss|Zuschüsse|Zuwendung|Zuwendungen|Beitrag|Beiträge|Einlage|Einlagen|Zuführung|Zuführungen|Zuweisung|Zuweisungen|Darlehen|Institutionelle Förderung|Förderung|Baumaßnahme|Baumaßnahmen|Zuschüsse für Baumaßnahmen)"
    r"(?:\s+des\s+Bundes)?"
    r"(?:\s+(?:an|in|für|der|des))?"
    r"\s+(?:die\s+|den\s+|das\s+|der\s+)?(?P<name>[A-ZÄÖÜ].+?)"
    r"(?:\s+-\s+.*|,\s+[A-ZÄÖÜ][\wäöüß.\- ]+(?:\s+\(Main\))?|\s+zur\s+.*|\s+zum\s+.*)?$"
)
_NAME_ORT_ZWECK = re.compile(
    r"^(?P<name>[A-ZÄÖÜ].+?(?:e\. ?V\.|gGmbH|GmbH|Stiftung[^,]*|Institut[^,]*|Gesellschaft[^,]*|Akademie[^,]*|Verband[^,]*|Zentrum[^,]*)),?\s+[A-ZÄÖÜ][\wäöüß\-]+(?:\s+\(Main\))?\s+-\s+.*$"
)
# Ein Empfängername braucht ein Organisationsmerkmal; Zweckbestimmungen („zur Entlastung beim Strompreis“) sind keine Empfänger.
_EIGENNAME = re.compile(
    r"(e\. ?V\.|gGmbH|GmbH|\bAG\b|\bSE\b|mbH|gUG|\bStiftung|\bInstitut|\bGesellschaft|\bAkademie|\bVerband|\bVerein\b|\bWerk\b|\bZentrum|\bUniversität|\bHochschule"
    r"|\b(?!(?:ins)?gesamt\b)[\wäöüß]*(?:anstalt|amt|dienst|kasse|werk)\b|\bAgentur|\bOrganisation|\bMuseum|\bTheater|\bOrchester|\bBibliothek|\bArchiv|\bKolleg|\bRat\b|\bKommission|\bUnion\b|\bBank\b|\bBüro\b|\bKammer\b)"
)
_SATZREST = re.compile(r"^(Bundes|Landes|Länder|zur|zum|zu|zum|gemäß|nach|bzw\.|von|für|aufgrund|im|in|auf|aus|bei|mit|über|wegen|sonstige|andere|weitere)\b", re.I)
_GRUPPEN_ZUWENDUNG = ("684", "685", "686", "687", "893", "894")


def _clean(name: str) -> str:
    return name.strip().strip('"').strip(" ,-")


def empfaenger_aus_titeln(rows: list[BudgetRow]) -> dict[str, tuple[str, list[str]]]:
    out: dict[str, tuple[str, list[str]]] = {}
    for r in rows:
        if r.art != "A":
            continue
        text = _clean(r.titel_text)
        name: str | None = None
        m = _ZUSCHUSS.match(text)
        if m:
            name = _clean(m.group("name"))
        else:
            m = _NAME_ORT_ZWECK.match(text)
            if m:
                name = _clean(m.group("name"))
            elif r.titel[:3] in _GRUPPEN_ZUWENDUNG and _EIGENNAME.search(text) and " - " not in text and len(text) < 90:
                name = text
        if not name or len(name) < 4:
            continue
        if _SATZREST.match(name) or not name[0].isupper():
            continue
        if not _EIGENNAME.search(name):
            continue
        low = name.lower()
        if any(w in low for w in ("einrichtungen", "maßnahmen", "vorhaben", "projekte", "träger ", "verbände ", "länder", "gemeinden", "sonstige")) and not re.search(r"(e\. ?V\.|gGmbH|GmbH|Stiftung)", name):
            continue
        key = norm_name(name)
        if not key:
            continue
        anzeige, ids = out.get(key, (name, []))
        if r.id not in ids:
            ids.append(r.id)
        out[key] = (anzeige, ids)
    return out


# ---------------------------------------------------------------- Ressorts

def ressort_zu_epl(name: str, ressorts: dict) -> str | None:
    """Geldgeber-Name → Einzelplan. Exakter Treffer oder Alias als Wortpräfix des Namens; Einträge mit `exakt: true` nur exakt.
    Mehrdeutiges („Bundesrepublik Deutschland - BMV“, „Bund/BMBF“) bleibt None, nie geraten."""
    n = norm_name(name)
    if not n:
        return None
    best: tuple[int, str] | None = None
    for r in ressorts.get("ressorts") or []:
        nur_exakt = bool(r.get("exakt"))
        for alias in r.get("namen") or []:
            a = norm_name(alias)
            if not a:
                continue
            if n == a or (not nur_exakt and n.startswith(a + " ")):
                if best is None or len(a) > best[0]:
                    best = (len(a), str(r["epl"]))
    return best[1] if best else None


# ---------------------------------------------------------------- Verbindungen

@dataclass
class Kandidat:
    person: str
    funktion_person: str
    organisation_text: str
    empfaenger_id: str
    empfaenger_name: str
    aehnlichkeit: float
    quelle: str
    hinweis: str = ""


@dataclass
class Verbindung:
    typ: str
    person: str
    funktion_person: str
    funktion_beim_empfaenger: str
    kategorie: str
    abgleich: str
    ausschuesse: list[str]
    quellen: list[dict]
    stand: str


def _aehnlich(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if (len(a) >= 8 and a in b) or (len(b) >= 8 and b in a):
        return 1.0
    return difflib.SequenceMatcher(None, a, b).ratio()


def verbindungen_aus_angaben(abgeordnete: list[Abgeordneter], stamm: dict[str, Stamm]) -> tuple[dict[str, list[Verbindung]], list[Kandidat]]:
    sidx = StammIndex(stamm)
    index = sidx.exakt
    verb: dict[str, list[Verbindung]] = {}
    kandidaten: list[Kandidat] = []
    for mdb in abgeordnete:
        mdb_kurz = f"MdB bis {mdb.ausgeschieden}" if getattr(mdb, "ausgeschieden", None) else "MdB"
        funktion_person = f"{mdb_kurz}, {mdb.fraktion}" if mdb.fraktion else mdb_kurz
        quelle = {"kurz": "bundestag.de", "url": mdb.url, "stand": mdb.stand}
        for a in mdb.angaben:
            n = norm_name(a.organisation)
            if not n:
                continue
            vorher = a.kategorie == KATEGORIE_VORHER
            exakt = index.get(n)
            if exakt and not vorher:
                verb.setdefault(exakt, []).append(Verbindung(
                    typ="abgeordneter_funktion", person=mdb.name, funktion_person=funktion_person,
                    funktion_beim_empfaenger=a.funktion or a.kategorie, kategorie=a.kategorie, abgleich="exakt",
                    ausschuesse=list(mdb.ausschuesse), quellen=[quelle], stand=mdb.stand,
                ))
                continue
            if exakt and vorher:
                kandidaten.append(Kandidat(mdb.name, funktion_person, a.organisation, exakt, stamm[exakt].name, 1.0, mdb.url,
                                           "Berufliche Tätigkeit vor der Mitgliedschaft im Bundestag; keine laufende Funktion"))
                continue
            for score, sid in sidx.aehnliche(n):
                kandidaten.append(Kandidat(mdb.name, funktion_person, a.organisation, sid, stamm[sid].name, round(score, 3), mdb.url,
                                           "vor der Mitgliedschaft" if vorher else ""))
    return verb, kandidaten


def verbindungen_aus_profil(p: Profil) -> list[Verbindung]:
    out: list[Verbindung] = []
    for person in p.personen:
        rf = person.regierungsfunktion
        if not rf:
            continue
        teile = [rf.funktion or rf.art, rf.stelle]
        if rf.beendet and rf.ende:
            teile.append(f"bis {rf.ende}")
        out.append(Verbindung(
            typ="regierungsfunktion", person=f"{person.vorname} {person.nachname}".strip(),
            funktion_person=", ".join(t for t in teile if t), funktion_beim_empfaenger=person.funktion,
            kategorie=("Frühere" if rf.beendet else "Laufende") + " Regierungs- oder Bundestagsfunktion laut Lobbyregister", abgleich="eigenangabe",
            ausschuesse=[], quellen=[{"kurz": "Lobbyregister", "url": p.url, "stand": p.stand}], stand=p.stand,
        ))
    return out


def manuelle_verbindungen(yaml_data: dict, empfaenger_id: str) -> list[Verbindung]:
    out: list[Verbindung] = []
    for v in (yaml_data or {}).get("verbindungen") or []:
        if v.get("empfaenger") != empfaenger_id or not v.get("geprueft"):
            continue
        out.append(Verbindung(
            typ=str(v.get("typ") or "manuell"), person=str(v.get("person") or ""), funktion_person=str(v.get("funktion_person") or ""),
            funktion_beim_empfaenger=str(v.get("funktion_beim_empfaenger") or ""), kategorie=str(v.get("kategorie") or "von Hand belegt"),
            abgleich="geprueft", ausschuesse=[], quellen=[{"kurz": str(v.get("quelle_kurz") or "Beleg"), "url": str(v.get("quelle") or ""), "stand": str(v.get("stand") or "")}],
            stand=str(v.get("stand") or ""),
        ))
    return out


def _satz_angabe(v: Verbindung, q: str, name: str) -> str:
    """Tatsachensatz je Kategorie der veröffentlichungspflichtigen Angaben; nichts wird zur Funktion umgedeutet."""
    k = v.kategorie.lower()
    f = v.funktion_beim_empfaenger.strip()
    vorbei = "(bis " in f or f.lower().startswith("bis ")
    wer = f"{v.person} ({v.funktion_person})"
    if k.startswith("funktionen"):
        return f"{wer} {'war' if vorbei else 'ist'} laut {q} {f or 'in einer Funktion'} bei {name}."
    if k.startswith("entgeltliche"):
        return f"{wer} {'übte' if vorbei else 'übt'} laut {q} eine entgeltliche Tätigkeit bei {name} aus: „{f}“."
    if k.startswith("spenden") or "zuwendungen" in k:
        return f"{wer} hat laut {q} eine Zuwendung von {name} angezeigt: „{f}“."
    if k.startswith("vereinbarungen"):
        return f"{wer} hat laut {q} eine Vereinbarung mit {name} angezeigt: „{f}“."
    if k.startswith("beteiligungen"):
        return f"{wer} hält laut {q} eine Beteiligung an {name}: „{f}“."
    return f"{wer} nennt {name} laut {q} in den veröffentlichungspflichtigen Angaben ({v.kategorie}): „{f}“."


def verbindungssatz(v: Verbindung, empfaenger_name: str, geld_aus: list[str]) -> str:
    q = v.quellen[0]["kurz"] if v.quellen else "Quelle"
    if v.typ == "regierungsfunktion":
        verb = "hat zugleich eine öffentliche Funktion" if v.kategorie.startswith("Laufende") else "hatte zuvor eine öffentliche Funktion"
        satz = f"{v.person} ist laut {q} {v.funktion_beim_empfaenger or 'in leitender Funktion'} bei {empfaenger_name} und {verb}: {v.funktion_person}."
    elif v.typ == "abgeordneter_funktion":
        satz = _satz_angabe(v, q, empfaenger_name)
    else:
        satz = f"{v.person} ({v.funktion_person}) ist laut {q} {v.funktion_beim_empfaenger} bei {empfaenger_name}."
    if v.ausschuesse:
        satz += f" Ausschüsse und Gremien im Bundestag laut bundestag.de: {'; '.join(v.ausschuesse)}."
    if geld_aus:
        satz += f" {empfaenger_name} erhielt laut Lobbyregister Mittel von: {'; '.join(geld_aus)}."
    return satz


# ---------------------------------------------------------------- Build (Spec §4.6a)

import json  # noqa: E402
from pathlib import Path  # noqa: E402

import yaml  # noqa: E402

from .bundestag import lade_abgeordnete  # noqa: E402
from .foerderkatalog import Projekt, lade_projekte  # noqa: E402
from .lobbyregister import bundeszuwendungen, lade_profile, untergrenze_bund  # noqa: E402



def _lade_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _stamm_aus_manual(manual: dict) -> dict[str, Stamm]:
    out: dict[str, Stamm] = {}
    for e in manual.get("empfaenger") or []:
        s = Stamm(id=str(e["id"]), name=str(e["name"]), aliasse=[str(a) for a in e.get("aliasse") or []],
                  lobbyregister=e.get("lobbyregister") or None, titel=[str(t) for t in e.get("titel") or []],
                  foerderkatalog=e.get("foerderkatalog") or None, art=str(e.get("art") or "sonstige"),
                  geprueft=bool(e.get("geprueft")), quelle=e.get("quelle"))
        out[s.id] = s
    return out


def _art_aus_profil(p: Profil) -> str:
    t = (p.taetigkeit + " " + p.rechtsform).lower()
    n = p.name.lower()
    if any(w in n for w in ("caritas", "diakonie", "kirche", "kirchlich", "evangelisch", "katholisch", "awo", "arbeiterwohlfahrt", "paritätisch", "rotes kreuz", "wohlfahrt", "brot für die welt", "misereor")):
        return "kirche_wohlfahrt"
    if "wissenschaft" in t or "forschungseinrichtung" in t or "hochschule" in t:
        return "forschung"
    if "unternehmen" in t and "gemeinnützig" not in t:
        return "unternehmen"
    if "öffentlichen rechts" in t or "anstalt" in t or "körperschaft" in t:
        return "oeffentlich"
    if any(w in t for w in ("gemeinnützig", "nichtregierungsorganisation", "verein", "stiftung", "verband", "netzwerk", "initiative")):
        return "verein_stiftung"
    return "sonstige"


def _art_aus_name(name: str) -> str:
    n = name.lower()
    if any(w in n for w in ("bundesanstalt", "anstalt", "kasse", "bundesamt", "bundesinstitut", "aör", "a.ö.r.")):
        return "oeffentlich"
    if any(w in n for w in ("gmbh", " ag", "aktiengesellschaft")) and "ggmbh" not in n and "gemeinnützig" not in n:
        return "unternehmen"
    if any(w in n for w in ("institut", "forschung", "universität", "akademie")):
        return "forschung"
    if any(w in n for w in ("e. v.", "e.v.", "stiftung", "verband", "verein", "ggmbh")):
        return "verein_stiftung"
    return "sonstige"


def _unique_id(wunsch: str, vergeben: set[str]) -> str:
    sid, i = wunsch, 2
    while sid in vergeben:
        sid = f"{wunsch}-{i}"
        i += 1
    vergeben.add(sid)
    return sid


def _kandidat(name_a: str, quelle_a: str, name_b: str, quelle_b: str, score: float) -> dict:
    return {"name_a": name_a, "quelle_a": quelle_a, "name_b": name_b, "quelle_b": quelle_b, "aehnlichkeit": round(score, 3)}


def baue_stamm(manual: dict, profile: list[Profil], years: dict[int, list[BudgetRow]]) -> tuple[dict[str, Stamm], list[dict]]:
    """Stamm = manuelle Einträge + Lobbyregister-Organisationen mit Bundesmitteln. Namentlich genannte Titel-Empfänger
    werden nur zugeordnet, wenn sie exakt zu einem Stamm-Eintrag passen; sonst landen sie als Kandidaten in der Prüfliste
    (Spec §4.6a: nur Empfänger, die aus amtlichen Listen eindeutig hervorgehen)."""
    stamm = _stamm_aus_manual(manual)
    vergeben = set(stamm)
    by_lobby: dict[str, str] = {s.lobbyregister: sid for sid, s in stamm.items() if s.lobbyregister}
    sidx = StammIndex(stamm)
    kandidaten: list[dict] = []

    for p in sorted(profile, key=lambda x: x.nummer):
        if not bundeszuwendungen(p) and p.nummer not in by_lobby:
            continue
        n = norm_name(p.name)
        sid = by_lobby.get(p.nummer) or sidx.exakt.get(n)
        if sid:
            if not stamm[sid].lobbyregister:
                stamm[sid].lobbyregister = p.nummer
            by_lobby[p.nummer] = sid
            continue
        for sc, other in sidx.aehnliche(n):
            kandidaten.append({**_kandidat(p.name, f"Lobbyregister {p.nummer}", stamm[other].name, "Stamm", sc), "art": "aehnlich"})
        sid = _unique_id(slug(p.name), vergeben)
        s = Stamm(id=sid, name=p.name, lobbyregister=p.nummer, art=_art_aus_profil(p), quelle=p.url)
        stamm[sid] = s
        sidx.add(sid, s)
        by_lobby[p.nummer] = sid

    rows: list[BudgetRow] = [r for rs in years.values() for r in rs]
    for n, (anzeige, ids) in empfaenger_aus_titeln(rows).items():
        sid = sidx.exakt.get(n)
        if sid:
            for t in ids:
                if t not in stamm[sid].titel:
                    stamm[sid].titel.append(t)
            continue
        treffer = sidx.aehnliche(n)
        if treffer:
            for sc, other in treffer:
                kandidaten.append({**_kandidat(anzeige, f"Haushaltstitel {', '.join(ids)}", stamm[other].name, "Stamm", sc), "art": "aehnlich"})
        else:
            kandidaten.append({**_kandidat(anzeige, f"Haushaltstitel {', '.join(ids)}", "", "", 0.0), "art": "titel_ohne_stamm"})
    return stamm, kandidaten


def _text_nennt(text: str, s: Stamm) -> bool:
    """Nennt die Zweckbestimmung den Empfänger (Name oder Alias, normalisiert als Teilzeichenkette)?"""
    t = " " + norm_name(text) + " "
    return any((" " + n + " ") in t for n in s.normen() if len(n) >= 4)


def _werte(titel_id: str, years: dict[int, list[BudgetRow]], ist_years: dict[int, list[BudgetRow]], s: Stamm | None = None) -> tuple[dict, BudgetRow | None]:
    werte: dict[str, dict] = {}
    beispiel: BudgetRow | None = None
    for j in sorted(years):
        row = next((r for r in years[j] if r.id == titel_id), None)
        if row is None:
            continue
        if s is not None and not _text_nennt(row.titel_text, s):
            continue   # dieselbe Titelnummer bezeichnet in diesem Jahr etwas anderes
        beispiel = row
        ist_row = next((r for r in (ist_years.get(j) or []) if r.id == titel_id), None)
        ist = ist_row.ist if ist_row is not None and ist_row.ist is not None else (row.ist if row.ist is not None else None)
        werte[str(j)] = {"soll": row.soll, "ist": ist}
    return werte, beispiel


def _spanne_dict(sp) -> dict | None:
    return {"von": sp.von, "bis": sp.bis} if sp else None


def _verbindung_dict(v: Verbindung, satz: str, geld_aus: list[str]) -> dict:
    return {"typ": v.typ, "person": v.person, "funktion_person": v.funktion_person, "funktion_beim_empfaenger": v.funktion_beim_empfaenger,
            "kategorie": v.kategorie, "abgleich": v.abgleich, "satz": satz, "ausschuesse": v.ausschuesse, "geld_aus": geld_aus,
            "quellen": v.quellen, "stand": v.stand}


def build_empfaenger(manual_dir: Path, raw_dir: Path, out: Path, years: dict[int, list[BudgetRow]],
                     ist_years: dict[int, list[BudgetRow]], *, mit_personen: bool = True, stand: str) -> Path:
    manual = _lade_yaml(manual_dir / "empfaenger.yaml")
    ressorts = _lade_yaml(manual_dir / "ressorts.yaml")
    verb_manual = _lade_yaml(manual_dir / "verbindungen.yaml")
    ja_manual = _lade_yaml(manual_dir / "jahresabschluss.yaml")
    ja_by_id = {str(e.get("empfaenger")): e for e in ja_manual.get("eintraege") or []}
    profile = lade_profile(raw_dir)
    profil_by_nr = {p.nummer: p for p in profile}
    abgeordnete = lade_abgeordnete(raw_dir)
    projekte = lade_projekte(raw_dir)
    stamm, stamm_kandidaten = baue_stamm(manual, profile, years)
    verb_auto, verb_kandidaten = verbindungen_aus_angaben(abgeordnete, stamm)

    out_dir = out / "empfaenger"
    out_dir.mkdir(parents=True, exist_ok=True)
    eintraege: list[dict] = []
    titel_map: dict[str, dict] = {}
    geschrieben: set[str] = {"index.json"}
    letztes_jahr = max(years) if years else None
    for sid, s in stamm.items():
        p = profil_by_nr.get(s.lobbyregister) if s.lobbyregister else None
        titel_eintraege = []
        epls: set[str] = set()
        haushalt_letztes = 0
        for tid in s.titel:
            werte, bsp = _werte(tid, years, ist_years, s)
            if bsp is None:
                continue
            titel_eintraege.append({"id": tid, "text": bsp.titel_text, "epl": bsp.epl, "epl_text": bsp.epl_text, "werte": werte})
            epls.add(bsp.epl)
            titel_map[tid] = {"id": sid, "name": s.name}
            if letztes_jahr is not None and str(letztes_jahr) in werte:
                haushalt_letztes += werte[str(letztes_jahr)]["soll"]
        lobby_z = []
        if p:
            for z in bundeszuwendungen(p):
                epl = ressort_zu_epl(z.geber, ressorts)
                if epl:
                    epls.add(epl)
                lobby_z.append({"geber": z.geber, "epl": epl, "von": z.spanne.von, "bis": z.spanne.bis, "zweck": z.zweck, "geschaeftsjahr": z.geschaeftsjahr})
        fk = []
        for pr in projekte.get(sid, []):
            epl = ressort_zu_epl(pr.ressort, ressorts)
            if epl:
                epls.add(epl)
            fk.append({"fkz": pr.fkz, "ressort": pr.ressort, "epl": epl, "thema": pr.thema, "von": pr.von, "bis": pr.bis, "summe": pr.summe, "foerderart": pr.foerderart})
        geld_aus = []
        for z in sorted(lobby_z, key=lambda x: -x["von"]):
            if z["geber"] not in geld_aus:
                geld_aus.append(z["geber"])
        personen = []
        verbindungen = []
        if mit_personen:
            if p:
                for person in p.personen:
                    rf = person.regierungsfunktion
                    personen.append({"name": f"{person.vorname} {person.nachname}".strip(), "funktion": person.funktion, "rolle": person.rolle,
                                     "regierungsfunktion": {"art": rf.art, "funktion": rf.funktion, "stelle": rf.stelle, "beendet": rf.beendet, "ende": rf.ende} if rf else None,
                                     "quelle": {"kurz": "Lobbyregister", "url": p.url, "stand": p.stand}})
                verbindungen += [_verbindung_dict(v, verbindungssatz(v, s.name, geld_aus), geld_aus) for v in verbindungen_aus_profil(p)]
            zweiter_beleg = ({"kurz": "Lobbyregister", "url": p.url, "stand": p.stand, "etikett": "Eigenangabe"} if p
                             else {"kurz": "bundeshaushalt.de", "url": "https://www.bundeshaushalt.de/", "stand": stand, "etikett": "amtlich"} if titel_eintraege else None)
            for v in verb_auto.get(sid, []):
                quellen = [{**q, "etikett": "Eigenangabe"} for q in v.quellen]
                if zweiter_beleg:
                    quellen.append(zweiter_beleg)
                v2 = Verbindung(v.typ, v.person, v.funktion_person, v.funktion_beim_empfaenger, v.kategorie, v.abgleich, v.ausschuesse, quellen, v.stand)
                verbindungen.append(_verbindung_dict(v2, verbindungssatz(v2, s.name, geld_aus), geld_aus))
            verbindungen += [_verbindung_dict(v, verbindungssatz(v, s.name, geld_aus), geld_aus) for v in manuelle_verbindungen(verb_manual, sid)]
        ja = ja_by_id.get(sid)
        jahresabschluss = None
        if p and p.jahresabschluss_url or ja:
            kennzahlen = None
            if ja:
                kennzahlen = {k: ja.get(k) for k in ("ertraege_gesamt", "oeffentliche_hand", "spenden", "personalaufwand", "projektfoerderung", "weitergeleitete_mittel", "jahresergebnis")}
            jahresabschluss = {"url": (ja or {}).get("url") or (p.jahresabschluss_url if p else None),
                               "geschaeftsjahr": str((ja or {}).get("geschaeftsjahr") or (p.jahresabschluss_jahr if p else "") or ""),
                               "kennzahlen": kennzahlen, "seite": (ja or {}).get("seite"), "pruefer": (ja or {}).get("pruefer"),
                               "hinweis": (ja or {}).get("hinweis"), "erfasst": (ja or {}).get("erfasst")}
        pflicht = None
        if p or ja:
            pflicht = {"finanzierungsquellen": p.finanzierungsquellen if p else [], "spenden": _spanne_dict(p.spenden) if p else None,
                       "mitgliedsbeitraege": _spanne_dict(p.mitgliedsbeitraege) if p else None, "lobbyausgaben": _spanne_dict(p.lobbyausgaben) if p else None,
                       "geschaeftsjahr": p.geschaeftsjahr if p else None, "jahresabschluss": jahresabschluss}
        quellen = []
        if p:
            quellen.append({"kurz": "Lobbyregister", "url": p.url, "abgerufen": stand, "stand": p.stand, "etikett": "Eigenangabe", "version": p.version})
        if titel_eintraege:
            quellen.append({"kurz": "bundeshaushalt.de", "url": "https://www.bundeshaushalt.de/", "abgerufen": stand})
        if fk:
            quellen.append({"kurz": "Förderkatalog des Bundes", "url": "https://foerderportal.bund.de/foekat/", "abgerufen": stand})
        for v in verbindungen:
            for q in v["quellen"]:
                if q.get("kurz") == "bundestag.de" and not any(x.get("url") == q.get("url") for x in quellen):
                    quellen.append({"kurz": "bundestag.de", "url": q.get("url"), "abgerufen": q.get("stand") or stand, "etikett": "Eigenangabe"})
        if ja:
            quellen.append({"kurz": "Jahresabschluss des Empfängers", "url": ja.get("url"), "abgerufen": ja.get("erfasst") or stand, "etikett": "Eigenangabe"})
        seite = {
            "id": sid, "name": s.name, "art": s.art, "rechtsform": p.rechtsform if p else "", "sitz": p.sitz if p else "",
            "website": p.website if p else None, "stand": stand, "geprueft": s.geprueft,
            "lobbyregister": {"nummer": p.nummer, "eintrag_id": p.eintrag_id, "version": p.version, "stand": p.stand, "url": p.url, "pdf_url": p.pdf_url} if p else None,
            "haushalt": {"titel": titel_eintraege},
            "lobby_zuwendungen": lobby_z, "lobby_untergrenze_bund": untergrenze_bund(p) if p else 0,
            "foerderkatalog": fk, "foerderkatalog_auszug": len(fk) >= 100, "personen": personen, "verbindungen": verbindungen, "pflichtangaben": pflicht, "quellen": quellen,
        }
        (out_dir / f"{sid}.json").write_text(json.dumps(seite, ensure_ascii=False, indent=0), encoding="utf-8", newline="\n")
        geschrieben.add(f"{sid}.json")
        eintraege.append({"id": sid, "name": s.name, "art": s.art, "rechtsform": seite["rechtsform"], "sitz": seite["sitz"],
                          "lobby_untergrenze_bund": seite["lobby_untergrenze_bund"], "haushalt_soll_letztes_jahr": haushalt_letztes,
                          "foerderkatalog_summe": round(sum(x["summe"] for x in fk), 2), "n_personen": len(personen),
                          "n_verbindungen": len(verbindungen), "lobbyregister": p.nummer if p else None, "epls": sorted(epls)})
    eintraege.sort(key=lambda e: (-e["lobby_untergrenze_bund"], -e["haushalt_soll_letztes_jahr"], e["name"]))
    # Seiten früherer Läufe, deren Empfänger es nicht mehr gibt, entfernen (sonst bleiben sie per Link erreichbar)
    for alt in out_dir.glob("*.json"):
        if alt.name not in geschrieben:
            alt.unlink()
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps({"stand": stand, "mit_personen": mit_personen, "eintraege": eintraege, "titel": titel_map}, ensure_ascii=False), encoding="utf-8", newline="\n")

    review = manual_dir.parent / "review"
    review.mkdir(parents=True, exist_ok=True)
    with open(review / "empfaenger_kandidaten.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# Automatisch erzeugt von `bht build`. Ähnliche, nicht exakt gleiche Namen. Bestätigen: Alias in data/manual/empfaenger.yaml.\n")
        yaml.safe_dump({"stand": stand, "kandidaten": stamm_kandidaten}, f, allow_unicode=True, sort_keys=False)
    with open(review / "verbindungen_kandidaten.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# Automatisch erzeugt von `bht build`. Angaben von Abgeordneten, die einem Empfänger ähneln. Bestätigen: data/manual/verbindungen.yaml.\n")
        yaml.safe_dump({"stand": stand, "kandidaten": [k.__dict__ for k in verb_kandidaten] if mit_personen else []}, f, allow_unicode=True, sort_keys=False)
    return index_path
