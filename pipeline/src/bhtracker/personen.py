"""Personen-Akten (Spec §4.7a): Identitäten aus Lobbyregister, Bundestag und Bundesregierung, Zusammenführung nur mit Beleg,
Sichtbarkeitsregel, Akten in Shard-Dateien plus Index.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path

import yaml

from .bezuege import WP_BEGINN, berechne_bezuege, lade_bezuege, lade_vorsitz_ab, tag_danach
from .bundestag import KATEGORIE_VORHER, Abgeordneter, lade_abgeordnete
from .empfaenger import norm_name, slug
from .lobbyregister import Profil, lade_profile
from .regierung import Amtstraeger, lade_regierung
from .spenden import Spende, lade_spenden, zuordnen

_TITEL = re.compile(r"^(?:Prof\.|Dr\.|Dipl\.-?\w*\.?|Ing\.|h\. ?c\.|mult\.|med\.|rer\.|nat\.|jur\.|phil\.|PD|Frhr\.|Freifrau|Freiherr)\s+", re.I)


def shard(id: str) -> str:
    return hashlib.sha1(id.encode("utf-8")).hexdigest()[:2]


def name_key(name: str) -> str:
    """Name ohne akademische Titel, normalisiert; Grundlage für „gleicher Name“."""
    rest = name.strip()
    for _ in range(6):
        neu = _TITEL.sub("", rest)
        if neu == rest:
            break
        rest = neu
    return norm_name(rest)


@dataclass
class Funktion:
    art: str
    text: str
    organisation_id: str | None
    organisation: str
    epl: str | None
    seit: str | None
    bis: str | None
    stand: str
    quelle: dict
    ausschuesse: list[str] = field(default_factory=list)
    amt: str | None = None                       # regierung: Amtsbezeichnung (Bundeskanzler, Bundesminister …, Staatssekretär)
    aemter: list[str] = field(default_factory=list)   # mdb: „Rolle: Gremium“ aus der Biografie (Amtszulage, § 11 Abs. 2 AbgG)
    seit_hinweis: str | None = None              # mdb: woher `seit` stammt (Biografie, Biografie des Vorgängers) oder warum es fehlt
    seit_quelle: str | None = None               # mdb: URL der Biografie, die den Eintritt belegt (bei Nachrückern die des Vorgängers)


@dataclass
class Akte:
    id: str
    name: str
    quellen_ids: list[str]
    funktionen: list[Funktion]
    amt: bool
    verbindung: bool
    freigabe: bool
    sichtbar: bool
    gleichnamig: list[str]
    angaben: list[dict]
    organisationen: list[dict]
    spenden: list[dict]
    zeitlinie: list[dict]
    quellen: list[dict]
    stand: str
    grund_sichtbar: str | None = None
    quelle_art: str = "lr"          # lr | mdb | breg (stärkste Quelle)
    mdb_id: int | None = None
    lr_nummern: list[str] = field(default_factory=list)
    org_normen: list[str] = field(default_factory=list)      # normalisierte Namen der Organisationen (Lobbyregister)
    angaben_org_normen: list[str] = field(default_factory=list)  # normalisierte Organisationsnamen aus den Bundestags-Angaben
    frueheres_mandat: bool = False
    bezuege: dict | None = None                  # Stufe 3d: Bezüge aus dem Amt (bezuege.berechne_bezuege), nur bei Mandat oder Regierungsamt


# ---------------------------------------------------------------- Roh-Identitäten je Quelle

def _person_name(vorname: str, nachname: str) -> str:
    return f"{vorname} {nachname}".strip()


def roh_identitaeten(profile: list[Profil], abgeordnete: list[Abgeordneter], regierung: list[Amtstraeger]) -> list[Akte]:
    akten: list[Akte] = []
    for p in sorted(profile, key=lambda x: x.nummer):
        org_id = slug(p.name)
        quelle = {"kurz": "Lobbyregister", "url": p.url, "stand": p.stand, "etikett": "Eigenangabe"}
        for person in p.personen:
            name = _person_name(person.vorname, person.nachname)
            if not name:
                continue
            funktionen = [Funktion(art=person.rolle, text=person.funktion or ("Interessenvertretung" if person.rolle == "interessenvertreter" else "gesetzliche Vertretung"),
                                   organisation_id=org_id, organisation=p.name, epl=None, seit=None, bis=None, stand=p.stand, quelle=quelle)]
            verbindung = False
            frueheres_mandat = False
            if person.regierungsfunktion:
                rf = person.regierungsfunktion
                # Lobbyregister: „recentGovernmentFunction“ kann laufen (ended False) oder beendet sein; nur Beendetes heißt „früher“
                funktionen.append(Funktion(art="fruehere_regierungsfunktion" if rf.beendet else "regierungsfunktion",
                                           text=", ".join(t for t in (rf.funktion or rf.art, rf.stelle) if t),
                                           organisation_id=None, organisation=rf.stelle, epl=None, seit=None, bis=rf.ende if rf.beendet else None, stand=p.stand, quelle=quelle))
                verbindung = True
                frueheres_mandat = rf.art == "HOUSE_OF_REPRESENTATIVES"
            akten.append(Akte(id=f"{slug(name)}-lr-{p.nummer.lower()}", name=name, quellen_ids=[f"{slug(name)}-lr-{p.nummer.lower()}"],
                              funktionen=funktionen, amt=False, verbindung=verbindung, freigabe=False, sichtbar=False, gleichnamig=[],
                              angaben=[], organisationen=[], spenden=[], zeitlinie=[], quellen=[quelle], stand=p.stand,
                              quelle_art="lr", lr_nummern=[p.nummer], org_normen=[norm_name(p.name)], frueheres_mandat=frueheres_mandat))
    # Nachrücker: Eintritt = Tag nach dem Ausscheiden des Vorgängers, belegt durch dessen Biografie (nach Kennung, sonst nach Name)
    _MON = ("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember")
    nachfolge_by_id: dict[int, tuple[str, str, str]] = {}
    nachfolge_by_name: dict[str, tuple[str, str, str]] = {}
    for v in abgeordnete:
        aus = getattr(v, "ausgeschieden", None)
        if not aus:
            continue
        eintrag = (tag_danach(aus), v.name, v.url)
        if getattr(v, "nachfolger_mdb_id", None):
            nachfolge_by_id[v.nachfolger_mdb_id] = eintrag
        if getattr(v, "nachfolger_name", None):
            nachfolge_by_name[name_key(v.nachfolger_name)] = eintrag
    for a in sorted(abgeordnete, key=lambda x: x.mdb_id):
        quelle = {"kurz": "bundestag.de", "url": a.url, "stand": a.stand, "etikett": "Eigenangabe"}
        bis = getattr(a, "ausgeschieden", None)
        kopf = f"Mitglied des Bundestages bis {bis}" if bis else "Mitglied des Bundestages"
        text = f"{kopf}, {a.fraktion}" if a.fraktion else kopf
        eintritt = getattr(a, "mitglied_seit", None)
        seit: str | None = None
        seit_hinweis: str | None = None
        seit_quelle: str | None = None
        vorgaenger = nachfolge_by_id.get(a.mdb_id) or nachfolge_by_name.get(name_key(a.name))
        if vorgaenger:
            seit, v_name, seit_quelle = vorgaenger
            seit_hinweis = f"Eintritt am {seit}, dem Tag nach dem Ausscheiden von {v_name} (Biografie des Vorgängers)."
        elif eintritt and len(eintritt) == 10 and eintritt > WP_BEGINN:
            seit = eintritt
            seit_quelle = a.url
            seit_hinweis = f"Eintritt laut Biografie: {_MON[int(eintritt[5:7]) - 1]} {eintritt[:4]}, gerechnet ab dem Monatsersten."
        elif eintritt and eintritt[:4] > WP_BEGINN[:4]:
            seit_hinweis = f"Eintritt laut Biografie im Jahr {eintritt[:4]} ohne Monat; gerechnet ab Beginn der 21. Wahlperiode ({WP_BEGINN}), Summe deshalb möglicherweise zu hoch."
        elif eintritt:
            seit_hinweis = f"Mitglied seit {eintritt[:4] if len(eintritt) == 4 else eintritt} laut Biografie; gerechnet ab Beginn der 21. Wahlperiode ({WP_BEGINN})."
        funktionen = [Funktion(art="mdb", text=text, organisation_id=None, organisation="Deutscher Bundestag", epl=None, seit=seit, bis=bis,
                               stand=a.stand, quelle={**quelle, "etikett": "amtlich"}, ausschuesse=list(a.ausschuesse), aemter=list(getattr(a, "aemter", [])),
                               seit_hinweis=seit_hinweis, seit_quelle=seit_quelle)]
        angaben = [{"kategorie": x.kategorie, "organisation": x.organisation, "ort": x.ort, "funktion": x.funktion, "stand": a.stand, "quelle": quelle} for x in a.angaben]
        akten.append(Akte(id=f"{slug(a.name)}-mdb-{a.mdb_id}", name=a.name, quellen_ids=[f"{slug(a.name)}-mdb-{a.mdb_id}"], funktionen=funktionen,
                          amt=True, verbindung=False, freigabe=False, sichtbar=False, gleichnamig=[], angaben=angaben, organisationen=[], spenden=[],
                          zeitlinie=[], quellen=[quelle], stand=a.stand, quelle_art="mdb", mdb_id=a.mdb_id,
                          angaben_org_normen=[norm_name(x.organisation) for x in a.angaben if x.kategorie != KATEGORIE_VORHER]))
    for m in regierung:
        quelle = {"kurz": "bundesregierung.de" if "bundesregierung.de" in m.quelle else "Ressortseite", "url": m.quelle, "stand": m.stand, "etikett": "amtlich"}
        funktionen = [Funktion(art="regierung", text=f"{m.amt}, {m.ressort}", organisation_id=None, organisation=m.ressort, epl=m.epl, seit=m.seit, bis=m.bis,
                               stand=m.stand, quelle=quelle, amt=m.amt)]
        akten.append(Akte(id=f"{slug(m.name)}-breg", name=m.name, quellen_ids=[f"{slug(m.name)}-breg"], funktionen=funktionen, amt=True, verbindung=False,
                          freigabe=False, sichtbar=False, gleichnamig=[], angaben=[], organisationen=[], spenden=[], zeitlinie=[], quellen=[quelle],
                          stand=m.stand, quelle_art="breg", mdb_id=m.mdb_id))
    return akten


# ---------------------------------------------------------------- Zusammenführung

_STAERKE = {"mdb": 3, "breg": 2, "lr": 1}


def _belegt(a: Akte, b: Akte, profile_by_nr: dict[str, Profil]) -> bool:
    """Regeln §4.7a (a) bis (c)."""
    arten = {a.quelle_art, b.quelle_art}
    if arten == {"mdb", "lr"}:
        mdb, lr = (a, b) if a.quelle_art == "mdb" else (b, a)
        if any(n in mdb.angaben_org_normen for n in lr.org_normen):
            return True   # (a) die Bundestags-Angabe nennt genau die Organisation
        if lr.frueheres_mandat:
            return True   # (b) das Register meldet ein früheres Mandat
        return False
    if arten == {"mdb", "breg"}:
        mdb, breg = (a, b) if a.quelle_art == "mdb" else (b, a)
        return breg.mdb_id is not None and breg.mdb_id == mdb.mdb_id
    if arten == {"lr"}:
        pa = [profile_by_nr.get(n) for n in a.lr_nummern]
        pb = [profile_by_nr.get(n) for n in b.lr_nummern]
        for x in pa:
            for y in pb:
                if not x or not y:
                    continue
                mx = {norm_name(m) for m in x.mitgliedschaften}
                my = {norm_name(m) for m in y.mitgliedschaften}
                if norm_name(y.name) in mx or norm_name(x.name) in my:
                    return True   # (c) gegenseitige Nennung
                namen_x = {_person_name(p.vorname, p.nachname) for p in x.personen}
                namen_y = {_person_name(p.vorname, p.nachname) for p in y.personen}
                if len(namen_x & namen_y) >= 2:
                    return True   # (c) mindestens zwei gemeinsame Vertreternamen
        return False
    return False


def _merge(gruppe: list[Akte]) -> Akte:
    gruppe = sorted(gruppe, key=lambda a: (-_STAERKE[a.quelle_art], a.id))
    kopf = gruppe[0]
    out = Akte(id=kopf.id, name=kopf.name, quellen_ids=[], funktionen=[], amt=any(a.amt for a in gruppe), verbindung=any(a.verbindung for a in gruppe),
               freigabe=False, sichtbar=False, gleichnamig=[], angaben=[], organisationen=[], spenden=[], zeitlinie=[], quellen=[],
               stand=max(a.stand for a in gruppe), grund_sichtbar=None, quelle_art=kopf.quelle_art,
               mdb_id=next((a.mdb_id for a in gruppe if a.mdb_id), None), lr_nummern=[], org_normen=[], angaben_org_normen=[],
               frueheres_mandat=any(a.frueheres_mandat for a in gruppe))
    for a in gruppe:
        out.quellen_ids += a.quellen_ids
        out.funktionen += a.funktionen
        out.angaben += a.angaben
        out.quellen += [q for q in a.quellen if q not in out.quellen]
        out.lr_nummern += a.lr_nummern
        out.org_normen += a.org_normen
        out.angaben_org_normen += a.angaben_org_normen
    return out


def zusammenfuehren(roh: list[Akte], profile_by_nr: dict[str, Profil], manual: dict) -> tuple[list[Akte], list[dict]]:
    manual = manual or {}
    trennen: set[frozenset[str]] = set()
    for t in manual.get("trennen") or []:
        ids = [str(x) for x in t.get("ids") or []]
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                trennen.add(frozenset((ids[i], ids[j])))
    manuell: dict[str, int] = {}
    for n, z in enumerate(manual.get("zusammenfuehren") or []):
        for i in z.get("ids") or []:
            manuell[str(i)] = n

    by_id = {a.id: a for a in roh}
    parent: dict[str, str] = {a.id: a.id for a in roh}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: str, y: str) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    gruppen_nach_name: dict[str, list[Akte]] = defaultdict(list)
    for a in roh:
        gruppen_nach_name[name_key(a.name)].append(a)
    for gruppe in gruppen_nach_name.values():
        for i in range(len(gruppe)):
            for j in range(i + 1, len(gruppe)):
                a, b = gruppe[i], gruppe[j]
                if frozenset((a.id, b.id)) in trennen:
                    continue
                if _belegt(a, b, profile_by_nr):
                    union(a.id, b.id)
    # Manuelle Zusammenführung und mdb_id (Kabinett ↔ Bundestag) gelten auch bei Namensvarianten (zweiter Vorname, Geburtsname)
    manuell_gruppen: dict[int, list[str]] = defaultdict(list)
    for i, n in manuell.items():
        if i in by_id:
            manuell_gruppen[n].append(i)
    nach_mdb_id: dict[int, list[str]] = defaultdict(list)
    for a in roh:
        if a.mdb_id and a.quelle_art in ("mdb", "breg"):
            nach_mdb_id[a.mdb_id].append(a.id)
    for ids in list(manuell_gruppen.values()) + list(nach_mdb_id.values()):
        for i in range(len(ids)):
            for j in range(i + 1, len(ids)):
                if frozenset((ids[i], ids[j])) not in trennen:
                    union(ids[i], ids[j])

    cluster: dict[str, list[Akte]] = defaultdict(list)
    for a in roh:
        cluster[find(a.id)].append(a)
    akten = [_merge(g) for g in cluster.values()]

    # Ids: slug(name) wenn eindeutig, sonst Quellensuffix behalten; Gleichnamige verweisen aufeinander
    nach_name: dict[str, list[Akte]] = defaultdict(list)
    for a in akten:
        nach_name[name_key(a.name)].append(a)
    kandidaten: list[dict] = []
    vergeben: set[str] = set()
    for key, gruppe in nach_name.items():
        gruppe.sort(key=lambda a: (-_STAERKE[a.quelle_art], a.id))
        if len(gruppe) == 1:
            wunsch = slug(gruppe[0].name)
            gruppe[0].id = wunsch if wunsch not in vergeben else gruppe[0].id
        else:
            kandidaten.append({"name": gruppe[0].name, "ids": [a.id for a in gruppe],
                               "quellen": [q.get("url") for a in gruppe for q in a.quellen], "hinweis": "gleicher Name ohne Beleg für dieselbe Person"})
            for a in gruppe:
                a.gleichnamig = [b.id for b in gruppe if b is not a]
        for a in gruppe:
            vergeben.add(a.id)
    return akten, kandidaten


# ---------------------------------------------------------------- Pflegedatei

def validate_personen(data: dict) -> list[str]:
    """personen.yaml: zusammenfuehren/trennen brauchen mindestens zwei ids und eine Quelle (URL); freigabe braucht id, Quelle und geprueft_von."""
    errors: list[str] = []
    data = data or {}
    for key in ("zusammenfuehren", "trennen"):
        for i, e in enumerate(data.get(key) or []):
            wer = f"{key} Eintrag {i + 1}"
            ids = e.get("ids") or []
            if not isinstance(ids, list) or len(ids) < 2:
                errors.append(f"{wer}: ids braucht mindestens zwei Einträge")
            if not str(e.get("quelle") or "").startswith("http"):
                errors.append(f"{wer}: quelle (URL) fehlt")
    for i, e in enumerate(data.get("freigabe") or []):
        wer = f"freigabe Eintrag {i + 1}"
        if not e.get("id"):
            errors.append(f"{wer}: id fehlt")
        if not str(e.get("quelle") or "").startswith("http"):
            errors.append(f"{wer}: quelle (URL) fehlt")
        if not e.get("geprueft_von"):
            errors.append(f"{wer}: geprueft_von fehlt")
    return errors


# ---------------------------------------------------------------- Sichtbarkeit

def sichtbarkeit(a: Akte, verbindungen_by_person: set[str], manual: dict, modus: str) -> bool:
    if modus == "alle":
        a.grund_sichtbar = "alle"
        return True
    if a.amt:
        a.grund_sichtbar = "amt"
        return True
    if a.verbindung or a.id in verbindungen_by_person or any(q in verbindungen_by_person for q in a.quellen_ids):
        a.grund_sichtbar = "verbindung"
        return True
    frei = {str(f.get("id")) for f in (manual or {}).get("freigabe") or [] if f.get("quelle")}
    if a.id in frei or any(q in frei for q in a.quellen_ids):
        a.freigabe = True
        a.grund_sichtbar = "freigabe"
        return True
    a.grund_sichtbar = None
    return False


# ---------------------------------------------------------------- Build

def _lade_yaml(path: Path) -> dict:
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def profile_mit_seite(profile: list[Profil], seiten: dict[str, dict]) -> list[Profil]:
    """Nur Lobbyregister-Organisationen, die eine Empfänger-Seite haben (Bundesmittel), liefern Personen (Spec §4.7a)."""
    nummern = {(s.get("lobbyregister") or {}).get("nummer") for s in seiten.values() if s.get("lobbyregister")}
    normen = {norm_name(s["name"]) for s in seiten.values()}
    return [p for p in profile if p.nummer in nummern or norm_name(p.name) in normen]


def _geld_der_seite(seite: dict, letztes_jahr: int | None = None) -> dict:
    """Geldkennzahlen einer Empfänger-Seite für die Organisationsliste der Akte (Quellen nebeneinander, nicht addiert).
    `letztes_jahr`: das jüngste Haushaltsjahr des ganzen Builds (wie in der Empfängerliste); ohne Angabe das jüngste Jahr der Seite."""
    geld_aus: list[str] = []
    for z in sorted(seite.get("lobby_zuwendungen") or [], key=lambda x: -x.get("von", 0)):
        if z["geber"] not in geld_aus:
            geld_aus.append(z["geber"])
    # Soll des jüngsten Jahres über alle Titel (ausgelaufene Titel mischen sich nicht mit aktuellen Werten)
    titel = (seite.get("haushalt") or {}).get("titel") or []
    jahre_alle = sorted({j for t in titel for j in (t.get("werte") or {})})
    jahr = str(letztes_jahr) if letztes_jahr is not None else (jahre_alle[-1] if jahre_alle else None)
    letztes = sum(int((t.get("werte") or {}).get(jahr, {}).get("soll") or 0) for t in titel) if jahr else 0
    return {"lobby_untergrenze_bund": seite.get("lobby_untergrenze_bund", 0), "haushalt_soll_letztes_jahr": letztes,
            "foerderkatalog_summe": round(sum(p.get("summe", 0) for p in seite.get("foerderkatalog") or []), 2), "geld_aus": geld_aus}


def _jahr(datum: str | None) -> int | None:
    if not datum:
        return None
    m = re.match(r"(\d{4})", str(datum))
    return int(m.group(1)) if m else None


def build_personen(manual_dir: Path, raw_dir: Path, out: Path, empfaenger_seiten: dict[str, dict], spenden: list[Spende], stand: str, *,
                   modus: str = "relevant", mit_personen: bool = True) -> Path | None:
    erg = build_personen_akten(manual_dir, raw_dir, out, empfaenger_seiten, spenden, stand, modus=modus, mit_personen=mit_personen)
    return erg[0] if erg else None


def build_personen_akten(manual_dir: Path, raw_dir: Path, out: Path, empfaenger_seiten: dict[str, dict], spenden: list[Spende], stand: str, *,
                         modus: str = "relevant", mit_personen: bool = True) -> tuple[Path, list[Akte], dict[str, list[Spende]]] | None:
    """Schreibt Akten-Shards und Index; gibt (Index-Pfad, Akten, Spenden je Empfänger-Id) zurück. Ohne Personen wird ein altes personen/ gelöscht."""
    if not mit_personen:
        if (out / "personen").exists():
            shutil.rmtree(out / "personen")
        return None
    manual = _lade_yaml(manual_dir / "personen.yaml")
    fehler = validate_personen(manual)
    if fehler:
        raise ValueError("personen.yaml: " + "; ".join(fehler))
    saetze = lade_bezuege(manual_dir / "bezuege.yaml")
    vorsitz_ab = lade_vorsitz_ab(manual_dir / "bezuege.yaml")
    jahre_global = {j for s in empfaenger_seiten.values() for t in (s.get("haushalt") or {}).get("titel") or [] for j in (t.get("werte") or {})}
    letztes_jahr = int(max(jahre_global)) if jahre_global else None
    ressorts = _lade_yaml(manual_dir / "ressorts.yaml")
    profile = profile_mit_seite(lade_profile(raw_dir), empfaenger_seiten)
    profile_by_nr = {p.nummer: p for p in profile}
    abgeordnete = lade_abgeordnete(raw_dir)
    regierung = lade_regierung(manual_dir / "regierung.yaml", raw_dir, ressorts) if (manual_dir / "regierung.yaml").exists() or (raw_dir / "regierung").exists() else []

    # Organisationen: Lobbyregister-Nummer bzw. normalisierter Name → Empfänger-Seite
    seite_by_nr: dict[str, dict] = {}
    seite_by_norm: dict[str, dict] = {}
    for sid, s in empfaenger_seiten.items():
        if s.get("lobbyregister") and s["lobbyregister"].get("nummer"):
            seite_by_nr[s["lobbyregister"]["nummer"]] = s
        seite_by_norm[norm_name(s["name"])] = s
    verbindungs_namen: set[str] = set()
    mdb_posten: dict[str, list[tuple[dict, dict]]] = defaultdict(list)   # name_key → (Seite, Verbindung abgeordneter_funktion, exakt)
    for s in empfaenger_seiten.values():
        for v in s.get("verbindungen") or []:
            if v.get("person"):
                verbindungs_namen.add(name_key(v["person"]))
                if v.get("typ") == "abgeordneter_funktion" and v.get("abgleich", "exakt") == "exakt":
                    mdb_posten[name_key(v["person"])].append((s, v))

    roh = roh_identitaeten(profile, abgeordnete, regierung)
    akten, kandidaten = zusammenfuehren(roh, profile_by_nr, manual)

    zu_spenden, spenden_kandidaten = zuordnen(spenden, {n: s["id"] for n, s in seite_by_norm.items()})

    out_dir = out / "personen"
    out_dir.mkdir(parents=True, exist_ok=True)
    for alt in out_dir.glob("*.json"):
        alt.unlink()
    shards: dict[str, dict[str, dict]] = defaultdict(dict)
    eintraege: list[dict] = []
    for a in akten:
        # Organisationen der Person mit ihrem Geld vom Bund
        orgs: list[dict] = []
        gesehen: set[str] = set()
        for f in a.funktionen:
            if f.art not in ("gesetzlicher_vertreter", "interessenvertreter"):
                continue
            seite = None
            for nr in a.lr_nummern:
                if nr in seite_by_nr and norm_name(seite_by_nr[nr]["name"]) == norm_name(f.organisation):
                    seite = seite_by_nr[nr]
            seite = seite or seite_by_norm.get(norm_name(f.organisation))
            if not seite or seite["id"] in gesehen:
                if seite is None:
                    f.organisation_id = None
                continue
            gesehen.add(seite["id"])
            f.organisation_id = seite["id"]
            orgs.append({"id": seite["id"], "name": seite["name"], "funktion": f.text, "rolle": f.art, "stand": f.stand,
                         "quelle": {"kurz": "Lobbyregister", "url": (seite.get("lobbyregister") or {}).get("url") or f.quelle.get("url"), "etikett": "Eigenangabe"},
                         **_geld_der_seite(seite, letztes_jahr)})
            if name_key(a.name) in verbindungs_namen and any(name_key(v.get("person", "")) == name_key(a.name) for v in seite.get("verbindungen") or []):
                a.verbindung = True
        # Posten laut veröffentlichungspflichtigen Angaben (Bundestag) bei Empfängern mit Seite: nur für Akten mit Bundestags-Identität
        if a.mdb_id:
            for seite, v in mdb_posten.get(name_key(a.name), []):
                if seite["id"] in gesehen:
                    continue
                gesehen.add(seite["id"])
                q = (v.get("quellen") or [{}])[0]
                orgs.append({"id": seite["id"], "name": seite["name"], "funktion": v.get("funktion_beim_empfaenger") or "Funktion laut Bundestagsangabe",
                             "rolle": "abgeordneter_funktion", "stand": q.get("stand") or stand,
                             "quelle": {"kurz": "bundestag.de", "url": q.get("url"), "etikett": "Eigenangabe"}, **_geld_der_seite(seite, letztes_jahr)})
                a.verbindung = True
        a.organisationen = orgs
        # Spenden der verbundenen Organisationen
        for o in orgs:
            for s in zu_spenden.get(o["id"], []):
                a.spenden.append({"organisation_id": o["id"], "organisation": o["name"], "partei": s.partei, "betrag": s.betrag, "eingang": s.eingang,
                                  "veroeffentlicht": s.veroeffentlicht, "drucksache": s.drucksache, "drucksache_url": s.drucksache_url,
                                  "quelle": {"kurz": "bundestag.de", "url": s.drucksache_url or "https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000", "etikett": "amtlich"}})
        # Zeitlinie
        zl: list[dict] = []
        for o in orgs:
            seite = empfaenger_seiten[o["id"]]
            for z in seite.get("lobby_zuwendungen") or []:
                j = _jahr(z.get("geschaeftsjahr"))
                if j:
                    zl.append({"jahr": j, "art": "geld", "quelle": "lobbyregister", "organisation_id": o["id"], "text": f"{o['name']} erhielt laut Lobbyregister ab {z['von']:,} € von {z['geber']}".replace(",", "."), "wert": z["von"]})
            for t in (seite.get("haushalt") or {}).get("titel") or []:
                for jahr, w in (t.get("werte") or {}).items():
                    if w.get("soll"):
                        zl.append({"jahr": int(jahr), "art": "geld", "quelle": "haushalt", "organisation_id": o["id"], "text": f"{o['name']}: Titel {t['id']} Soll {w['soll']:,} €".replace(",", "."), "wert": w["soll"]})
        for f in a.funktionen:
            j = _jahr(f.seit) or _jahr(f.bis) or _jahr(f.stand)
            if j:
                bei = f" bei {f.organisation}" if f.organisation and f.art not in ("mdb", "regierung") and f.organisation.lower() not in f.text.lower() else ""
                wann = f", seit {f.seit}" if f.seit else (f", bis {f.bis}" if f.bis else f", Stand {f.stand}")
                zl.append({"jahr": j, "art": "posten", "organisation_id": f.organisation_id, "text": f"{f.text}{bei}{wann}"})
        for s in a.spenden:
            j = _jahr(s.get("eingang"))
            if j:
                zl.append({"jahr": j, "art": "spende", "organisation_id": s["organisation_id"], "text": f"{s['organisation']} spendete {s['betrag']:,} € an {s['partei']}".replace(",", "."), "wert": s["betrag"]})
        a.zeitlinie = sorted(zl, key=lambda e: (e["jahr"], e["art"]))
        if saetze and any(f.art in ("mdb", "regierung") for f in a.funktionen):
            a.bezuege = berechne_bezuege([asdict(f) for f in a.funktionen], saetze, stand, vorsitz_ab.get(a.id))
        a.sichtbar = sichtbarkeit(a, set(), manual, modus)
        a.stand = stand
        arten: list[str] = []
        for f in a.funktionen:
            if f.art not in arten:
                arten.append(f.art)
        eintraege.append({"id": a.id, "name": a.name, "funktion_kurz": a.funktionen[0].text if a.funktionen else "", "amt": a.amt, "sichtbar": a.sichtbar,
                          "arten": arten, "n_organisationen": len(orgs), "shard": shard(a.id)})
        if a.sichtbar:
            d = asdict(a)
            for k in ("quelle_art", "lr_nummern", "org_normen", "angaben_org_normen", "frueheres_mandat"):
                d.pop(k, None)
            shards[shard(a.id)][a.id] = d
    for sh, inhalt in shards.items():
        (out_dir / f"{sh}.json").write_text(json.dumps(inhalt, ensure_ascii=False), encoding="utf-8", newline="\n")
    eintraege.sort(key=lambda e: (not e["sichtbar"], e["name"]))
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps({"stand": stand, "modus": modus, "eintraege": eintraege}, ensure_ascii=False), encoding="utf-8", newline="\n")

    review = manual_dir.parent / "review"
    review.mkdir(parents=True, exist_ok=True)
    with open(review / "personen_kandidaten.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# Automatisch erzeugt von `bht build`. Gleiche Namen ohne Beleg für dieselbe Person. Zusammenführen: data/manual/personen.yaml.\n")
        yaml.safe_dump({"stand": stand, "kandidaten": kandidaten}, f, allow_unicode=True, sort_keys=False)
    with open(review / "spenden_kandidaten.yaml", "w", encoding="utf-8", newline="\n") as f:
        f.write("# Automatisch erzeugt von `bht build`. Spenden von Organisationen ohne exakten Treffer im Empfänger-Stamm (keine natürlichen Personen).\n")
        yaml.safe_dump({"stand": stand, "kandidaten": spenden_kandidaten}, f, allow_unicode=True, sort_keys=False)
    return index_path, akten, zu_spenden


# ---------------------------------------------------------------- Orchestrierung (Task 5)

def lade_seiten(out: Path) -> dict[str, dict]:
    """Alle Empfänger-Seiten des Builds (ohne Index)."""
    d = out / "empfaenger"
    seiten: dict[str, dict] = {}
    if not d.exists():
        return seiten
    for p in d.glob("*.json"):
        if p.name == "index.json":
            continue
        s = json.loads(p.read_text(encoding="utf-8"))
        seiten[s["id"]] = s
    return seiten


def ergaenze_akten(out: Path, seiten: dict[str, dict], akten: list[Akte], zu_spenden: dict[str, list[Spende]] | None = None) -> int:
    """Schreibt akte_id und akte_sichtbar an die Personen der Empfänger-Seiten (Name und Organisation müssen passen)
    und die veröffentlichungspflichtigen Parteispenden der Organisation (parteispenden)."""
    nach_name: dict[str, list[Akte]] = defaultdict(list)
    for a in akten:
        nach_name[name_key(a.name)].append(a)
    n = 0
    for sid, s in seiten.items():
        geaendert = False
        if zu_spenden is not None:
            s["parteispenden"] = [{"partei": sp.partei, "betrag": sp.betrag, "eingang": sp.eingang, "veroeffentlicht": sp.veroeffentlicht, "drucksache": sp.drucksache,
                                   "drucksache_url": sp.drucksache_url,
                                   "quelle": {"kurz": "bundestag.de", "url": sp.drucksache_url or "https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000", "etikett": "amtlich"}}
                                  for sp in sorted(zu_spenden.get(sid, []), key=lambda x: (x.eingang, x.partei))]
            geaendert = True
        for p in s.get("personen") or []:
            treffer = [a for a in nach_name.get(name_key(p.get("name", "")), []) if any(o["id"] == sid for o in a.organisationen)]
            if len(treffer) == 1:
                p["akte_id"], p["akte_sichtbar"] = treffer[0].id, treffer[0].sichtbar
            else:
                p["akte_id"], p["akte_sichtbar"] = None, False
            geaendert = True
            n += 1
        if geaendert:
            (out / "empfaenger" / f"{sid}.json").write_text(json.dumps(s, ensure_ascii=False, indent=0), encoding="utf-8", newline="\n")
    return n


def build_akten_und_netz(manual_dir: Path, raw_dir: Path, out: Path, stand: str, *, modus: str = "relevant", mit_personen: bool = True) -> dict:
    """Akten (sofern Personen gebaut werden) und Netz aus den fertigen Empfänger-Seiten; gibt Kennzahlen zurück."""
    from .netz import baue_graph, build_netz  # lokaler Import, netz importiert personen

    seiten = lade_seiten(out)
    spenden = lade_spenden(raw_dir)
    ressorts = _lade_yaml(manual_dir / "ressorts.yaml")
    akten: list[Akte] = []
    sichtbar = 0
    zu_spenden: dict[str, list[Spende]]
    if mit_personen:
        erg = build_personen_akten(manual_dir, raw_dir, out, seiten, spenden, stand, modus=modus, mit_personen=True)
        assert erg is not None
        _, akten, zu_spenden = erg
        sichtbar = sum(1 for a in akten if a.sichtbar)
    else:
        build_personen_akten(manual_dir, raw_dir, out, seiten, spenden, stand, modus=modus, mit_personen=False)
        zu_spenden, _ = zuordnen(spenden, {norm_name(s["name"]): s["id"] for s in seiten.values()})
    ergaenze_akten(out, seiten, akten, zu_spenden)
    knoten, kanten = baue_graph(seiten, akten, zu_spenden, ressorts)
    build_netz(out, knoten, kanten, mit_personen=mit_personen)
    return {"akten": len(akten), "sichtbar": sichtbar, "knoten": len(knoten), "kanten": len(kanten)}
