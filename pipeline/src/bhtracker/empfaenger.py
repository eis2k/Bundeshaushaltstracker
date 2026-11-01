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
        return {norm_name(self.name), *(norm_name(a) for a in self.aliasse)} - {""}


# ---------------------------------------------------------------- Empfänger aus Titeltexten

_ZUSCHUSS = re.compile(
    r"^(?:Zuschuss|Zuschüsse|Zuwendung|Zuwendungen|Beitrag|Beiträge|Einlage|Zuweisung|Zuweisungen|Institutionelle Förderung|Förderung)"
    r"\s+(?:an|in|der|des)\s+(?:die\s+|den\s+|das\s+|der\s+)?(?P<name>.+?)(?:\s+-\s+.*|,\s+[A-ZÄÖÜ][\wäöüß.\- ]+(?:\s+\(Main\))?|\s+für\s+.*|\s+zur\s+.*|\s+zum\s+.*)?$"
)
_NAME_ORT_ZWECK = re.compile(
    r"^(?P<name>.+?(?:e\. ?V\.|gGmbH|GmbH|Stiftung[^,]*|Institut[^,]*|Gesellschaft[^,]*|Akademie[^,]*|Verband[^,]*|Zentrum[^,]*)),?\s+[A-ZÄÖÜ][\wäöüß\-]+(?:\s+\(Main\))?\s+-\s+.*$"
)
_EIGENNAME = re.compile(r"\b(e\. ?V\.|gGmbH|GmbH|Stiftung|Anstalt|Institut|Kasse|Verband)\b")
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
        # Generische Formulierungen ohne Eigennamen aussortieren
        low = name.lower()
        if any(w in low for w in ("einrichtungen", "maßnahmen", "vorhaben", "projekte", "träger", "verbände ", "länder", "gemeinden", "sonstige")) and not _EIGENNAME.search(name):
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
    n = norm_name(name)
    if not n:
        return None
    best: tuple[int, str] | None = None
    for r in ressorts.get("ressorts") or []:
        for alias in r.get("namen") or []:
            a = norm_name(alias)
            if not a:
                continue
            if n == a or n.startswith(a + " ") or (len(a) >= 8 and a.startswith(n + " ")):
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
    index: dict[str, str] = {}
    for sid, s in stamm.items():
        for n in s.normen():
            index.setdefault(n, sid)
    verb: dict[str, list[Verbindung]] = {}
    kandidaten: list[Kandidat] = []
    for mdb in abgeordnete:
        funktion_person = f"MdB, {mdb.fraktion}" if mdb.fraktion else "MdB"
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
            for sid, s in stamm.items():
                score = max(_aehnlich(n, sn) for sn in s.normen()) if s.normen() else 0.0
                if score >= 0.85:
                    kandidaten.append(Kandidat(mdb.name, funktion_person, a.organisation, sid, s.name, round(score, 3), mdb.url,
                                               "vor der Mitgliedschaft" if vorher else ""))
    return verb, kandidaten


def verbindungen_aus_profil(p: Profil) -> list[Verbindung]:
    out: list[Verbindung] = []
    for person in p.personen:
        rf = person.regierungsfunktion
        if not rf:
            continue
        teile = [rf.funktion or rf.art, rf.stelle]
        if rf.ende:
            teile.append(f"bis {rf.ende}")
        out.append(Verbindung(
            typ="regierungsfunktion", person=f"{person.vorname} {person.nachname}".strip(),
            funktion_person=", ".join(t for t in teile if t), funktion_beim_empfaenger=person.funktion,
            kategorie="Frühere Regierungs- oder Bundestagsfunktion laut Lobbyregister", abgleich="eigenangabe",
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


def verbindungssatz(v: Verbindung, empfaenger_name: str, geld_aus: list[str]) -> str:
    q = v.quellen[0]["kurz"] if v.quellen else "Quelle"
    if v.typ == "regierungsfunktion":
        satz = f"{v.person} ist laut {q} {v.funktion_beim_empfaenger or 'in leitender Funktion'} bei {empfaenger_name} und hatte zuvor eine öffentliche Funktion: {v.funktion_person}."
    else:
        satz = f"{v.person} ({v.funktion_person}) ist laut {q} {v.funktion_beim_empfaenger} bei {empfaenger_name}."
    if v.ausschuesse:
        satz += f" Ausschüsse und Gremien im Bundestag laut bundestag.de: {'; '.join(v.ausschuesse)}."
    if geld_aus:
        satz += f" {empfaenger_name} erhielt laut Lobbyregister Mittel von: {'; '.join(geld_aus)}."
    return satz
