"""Lobbyregister des Deutschen Bundestags: amtliches JSON der Registereinträge.

Liste:   https://www.lobbyregister.bundestag.de/sucheJson           (alle Einträge, Kurzform)
Detail:  https://www.lobbyregister.bundestag.de/sucheJson/<R-Nr>/<Eintrag-Id>
Doku:    https://www.lobbyregister.bundestag.de/informationen-und-hilfe/open-data-1049716

Alle Angaben sind Eigenangaben der Registrierten (Lobbyregistergesetz); die Pipeline übernimmt sie
unverändert mit Versionsnummer und Gültigkeitsdatum.
"""

from __future__ import annotations

import json
import time
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .portal import TIMEOUT, USER_AGENT

LISTE_URL = "https://www.lobbyregister.bundestag.de/sucheJson"
GESAMT_URL = "https://www.lobbyregister.bundestag.de/sucheDetailJson"
FEDERAL = "GERMAN_PUBLIC_SECTOR_FEDERAL"


def detail_url(register_nummer: str, eintrag_id: int) -> str:
    return f"{LISTE_URL}/{register_nummer}/{eintrag_id}"


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


# ---------------------------------------------------------------- Datenmodell

@dataclass(frozen=True)
class Spanne:
    von: int
    bis: int


@dataclass(frozen=True)
class Zuwendung:
    geber: str
    ort: str
    spanne: Spanne
    zweck: str
    typ: str
    geschaeftsjahr: str


@dataclass(frozen=True)
class Regierungsfunktion:
    art: str
    funktion: str
    stelle: str
    beendet: bool
    ende: str | None


@dataclass(frozen=True)
class Person:
    nachname: str
    vorname: str
    funktion: str
    rolle: str  # gesetzlicher_vertreter | interessenvertreter
    regierungsfunktion: Regierungsfunktion | None


@dataclass
class Profil:
    nummer: str
    eintrag_id: int
    version: int
    stand: str
    url: str
    pdf_url: str | None
    name: str
    rechtsform: str
    rechtsform_code: str
    sitz: str
    land: str
    website: str | None
    taetigkeit: str
    personen: list[Person] = field(default_factory=list)
    zuwendungen: list[Zuwendung] = field(default_factory=list)
    finanzierungsquellen: list[str] = field(default_factory=list)
    spenden: Spanne | None = None
    mitgliedsbeitraege: Spanne | None = None
    lobbyausgaben: Spanne | None = None
    geschaeftsjahr: str | None = None
    jahresabschluss_url: str | None = None
    jahresabschluss_jahr: str | None = None
    mitgliedschaften: list[str] = field(default_factory=list)


# ---------------------------------------------------------------- Extraktion

def _spanne(d: dict | None) -> Spanne | None:
    if not isinstance(d, dict):
        return None
    von, bis = d.get("from"), d.get("to")
    if von is None and bis is None:
        return None
    return Spanne(int(von or 0), int(bis or von or 0))


def _regierungsfunktion(p: dict) -> Regierungsfunktion | None:
    if not p.get("recentGovernmentFunctionPresent"):
        return None
    rf = p.get("recentGovernmentFunction") or {}
    typ = rf.get("type") or {}
    art = str(typ.get("code") or "")
    funktion, stelle = "", str(typ.get("de") or "")
    if "houseOfRepresentatives" in rf:
        funktion = str(((rf["houseOfRepresentatives"] or {}).get("function") or {}).get("de") or "")
    elif "federalAdministration" in rf:
        fa = rf["federalAdministration"] or {}
        funktion = str(fa.get("function") or "").strip()
        stelle = str(fa.get("supremeFederalAuthority") or stelle)
    elif "federalGovernment" in rf:
        fg = rf["federalGovernment"] or {}
        funktion = str((fg.get("function") or {}).get("de") if isinstance(fg.get("function"), dict) else fg.get("function") or "")
        stelle = str(fg.get("ministry") or stelle)
    return Regierungsfunktion(art=art, funktion=funktion, stelle=stelle, beendet=bool(rf.get("ended")), ende=rf.get("endDate"))


def _personen(li: dict) -> list[Person]:
    out: list[Person] = []
    seen: set[tuple[str, str]] = set()
    for p in li.get("legalRepresentatives") or []:
        key = (str(p.get("lastName") or ""), str(p.get("firstName") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(Person(key[0], key[1], str(p.get("function") or ""), "gesetzlicher_vertreter", _regierungsfunktion(p)))
    for p in li.get("entrustedPersons") or []:
        key = (str(p.get("lastName") or ""), str(p.get("firstName") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(Person(key[0], key[1], str(p.get("function") or "Interessenvertretung"), "interessenvertreter", _regierungsfunktion(p)))
    return out


def extract_profil(detail: dict) -> Profil:
    red = detail.get("registerEntryDetails") or {}
    li = detail.get("lobbyistIdentity") or {}
    adr = li.get("address") or {}
    kontakt = li.get("contactDetails") or {}
    websites = kontakt.get("websites") or []
    pa = detail.get("publicAllowances") or {}
    zuwendungen = []
    gj = str(pa.get("relatedFiscalYearStart") or "")[:4] or None
    for z in pa.get("publicAllowances") or []:
        sp = _spanne(z.get("publicAllowanceEuro")) or Spanne(0, 0)
        zuwendungen.append(Zuwendung(
            geber=str(z.get("name") or "").strip(), ort=str(z.get("location") or "").strip(), spanne=sp,
            zweck=" ".join(str(z.get("description") or "").split()), typ=str((z.get("type") or {}).get("code") or ""),
            geschaeftsjahr=gj or "",
        ))
    mfs = detail.get("mainFundingSources") or {}
    quellen = [str(q.get("de") or q.get("code") or "") for q in mfs.get("mainFundingSources") or []]
    don = detail.get("donators") or {}
    mf = detail.get("membershipFees") or {}
    fe = detail.get("financialExpenses") or {}
    ar = detail.get("annualReports") or {}
    nummer = str(detail.get("registerNumber") or "")
    eintrag_id = int(red.get("registerEntryId") or 0)
    return Profil(
        nummer=nummer, eintrag_id=eintrag_id, version=int(red.get("version") or 0),
        stand=str(red.get("validFromDate") or "")[:10],
        url=str(red.get("detailsPageUrl") or f"https://www.lobbyregister.bundestag.de/suche/{nummer}/{eintrag_id}"),
        pdf_url=red.get("pdfUrl"),
        name=str(li.get("name") or f"{li.get('lastName', '')}, {li.get('firstName', '')}".strip(", ")),
        rechtsform=str((li.get("legalForm") or {}).get("de") or ""), rechtsform_code=str((li.get("legalForm") or {}).get("code") or ""),
        sitz=str(adr.get("city") or ""), land=str((adr.get("country") or {}).get("de") or ""),
        website=str(websites[0].get("website")) if websites and websites[0].get("website") else None,
        taetigkeit=str((detail.get("activitiesAndInterests") or {}).get("activity", {}).get("de") or ""),
        personen=_personen(li), zuwendungen=zuwendungen, finanzierungsquellen=quellen,
        spenden=_spanne(don.get("totalDonationsEuro")), mitgliedsbeitraege=_spanne(mf.get("totalMembershipFees")),
        lobbyausgaben=_spanne(fe.get("financialExpensesEuro")), geschaeftsjahr=gj,
        jahresabschluss_url=ar.get("annualReportPdfUrl"),
        jahresabschluss_jahr=str(ar.get("previousLastFiscalYearStart") or "")[:4] or None,
        mitgliedschaften=[str(m.get("membership") or "") for m in li.get("memberships") or []],
    )


def bundeszuwendungen(p: Profil) -> list[Zuwendung]:
    return [z for z in p.zuwendungen if z.typ == FEDERAL]


def untergrenze_bund(p: Profil) -> int:
    return sum(z.spanne.von for z in bundeszuwendungen(p))


def hat_bundesmittel(eintrag: dict) -> bool:
    """Für Detailprofile: mindestens eine Zuwendung der öffentlichen Hand des Bundes."""
    pa = (eintrag.get("publicAllowances") or {}).get("publicAllowances") or []
    return any((z.get("type") or {}).get("code") == FEDERAL for z in pa)


def auswahl(liste: dict, zusaetzlich: set[str]) -> list[tuple[str, int]]:
    """Alle aktiven Organisationen der Liste (natürliche Personen nicht) plus explizit genannte Nummern."""
    out: list[tuple[str, int]] = []
    for r in liste.get("results") or []:
        nr = str(r.get("registerNumber") or "")
        li = r.get("lobbyistIdentity") or {}
        aktiv = (r.get("accountDetails") or {}).get("activeLobbyist", True)
        eid = (r.get("registerEntryDetails") or {}).get("registerEntryId")
        if not nr or eid is None:
            continue
        if nr in zusaetzlich or (li.get("identity") != "NATURAL" and aktiv):
            out.append((nr, int(eid)))
    return out


# ---------------------------------------------------------------- Abruf und Ablage

def _dir(raw_dir: Path) -> Path:
    d = raw_dir / "lobbyregister"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_liste(raw_dir: Path, http: Callable[[str], bytes] = _urlopen_bytes) -> dict:
    data = http(LISTE_URL)
    (_dir(raw_dir) / "liste.json").write_bytes(data)
    return json.loads(data.decode("utf-8"))


def fetch_details(raw_dir: Path, paare: list[tuple[str, int]], http: Callable[[str], bytes] = _urlopen_bytes,
                  pause: float = 1.5, log: Callable[[str], None] = print) -> list[Path]:
    d = _dir(raw_dir)
    written: list[Path] = []
    for i, (nr, eid) in enumerate(paare, 1):
        target = d / f"{nr}_{eid}.json"
        if target.exists():
            continue
        target.write_bytes(http(detail_url(nr, eid)))
        written.append(target)
        if i % 100 == 0:
            log(f"lobbyregister: {i}/{len(paare)} Profile")
        if pause:
            time.sleep(pause)
    return written


def lade_profile(raw_dir: Path) -> list[Profil]:
    d = raw_dir / "lobbyregister"
    if not d.exists():
        return []
    out: list[Profil] = []
    for p in sorted(d.glob("R*_*.json")):
        with open(p, encoding="utf-8") as f:
            out.append(extract_profil(json.load(f)))
    return out


def split_gesamtexport(text: str, raw_dir: Path) -> int:
    """Zerlegt den Gesamtexport aller Detailprofile (eine Anfrage statt tausender) in Einzeldateien; natürliche Personen bleiben weg."""
    d = _dir(raw_dir)
    start = text.find('"results"')
    if start < 0:
        return 0
    pos = text.index("[", start) + 1
    dec = json.JSONDecoder()
    n = 0
    while True:
        while pos < len(text) and text[pos] in " \r\n\t,":
            pos += 1
        if pos >= len(text) or text[pos] == "]":
            break
        obj, end = dec.raw_decode(text, pos)
        pos = end
        li = obj.get("lobbyistIdentity") or {}
        nr = obj.get("registerNumber")
        eid = (obj.get("registerEntryDetails") or {}).get("registerEntryId")
        if nr and eid is not None and li.get("identity") != "NATURAL":
            (d / f"{nr}_{eid}.json").write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8", newline="\n")
            n += 1
    return n


def fetch_gesamtexport(raw_dir: Path, http: Callable[[str], bytes] = _urlopen_bytes, datei: Path | None = None) -> int:
    """Lädt den Gesamtexport (oder nutzt eine bereits geladene Datei) und zerlegt ihn in Profile."""
    if datei is not None:
        data = Path(datei).read_bytes()
    else:
        data = http(GESAMT_URL)
        (_dir(raw_dir) / "gesamtexport.json").write_bytes(data)
    return split_gesamtexport(data.decode("utf-8"), raw_dir)
