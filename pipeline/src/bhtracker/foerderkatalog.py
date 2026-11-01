"""Förderkatalog des Bundes (foerderportal.bund.de/foekat): Projektförderung von BMFTR, BMWE, BMUV, BMLEH, BMV, BMJV.

Es gibt keinen Gesamtexport. Je Empfänger: Suchmaske laden (Sitzung), Detailsuche nach dem Empfängernamen,
dann den CSV-Export des Suchergebnisses holen (actionMode=print&presentationType=csv). Die CSV ist Latin-1,
Felder stehen als ="…" (Excel-Schutz), Beträge mit Tausenderpunkt und Dezimalkomma.
"""

from __future__ import annotations

import csv
import http.cookiejar
import io
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .portal import TIMEOUT, USER_AGENT

BASE = "https://foerderportal.bund.de/foekat/jsp/SucheAction.do"
KEINE_TREFFER = "Die Suche liefert keine Ergebnisse"
_TREFFER = re.compile(r"\((\d+) Treffer\)")


@dataclass(frozen=True)
class Projekt:
    fkz: str
    ressort: str
    stelle: str
    empfaenger: str
    empfaenger_ort: str
    ausfuehrende: str
    thema: str
    lps: str
    lps_text: str
    von: str
    bis: str
    summe: float
    foerderart: str


def _datum(s: str) -> str:
    m = re.match(r"(\d{2})\.(\d{2})\.(\d{4})", s.strip())
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else s.strip()


def _betrag(s: str) -> float:
    t = s.strip().replace(".", "").replace(",", ".")
    try:
        return float(t) if t else 0.0
    except ValueError:
        return 0.0


def parse_csv(text: str) -> list[Projekt]:
    cleaned = text.replace('="', '"')
    rows = list(csv.reader(io.StringIO(cleaned), delimiter=";"))
    if not rows:
        return []
    hdr = [h.strip() for h in rows[0]]

    def col(name_start: str) -> int | None:
        for i, h in enumerate(hdr):
            if h.startswith(name_start):
                return i
        return None

    i_fkz, i_res, i_stelle = col("FKZ"), col("Ressort"), col("Administrierende Stelle")
    i_emp = col("Förderempfänger")
    i_thema, i_lps, i_lpst = col("Thema"), col("Leistungsplansystematik"), col("Klartext Leistungsplansystematik")
    i_von, i_bis, i_sum, i_art = col("Laufzeit von"), col("Laufzeit bis"), col("Förder- / Auftragssumme"), col("Förderart")
    if i_fkz is None or i_emp is None:
        return []
    # Die Spalten "Stadt/Gemeinde", "Ort", … kommen zweimal (Empfänger, Ausführende Stelle); Positionen relativ zu den Namensspalten.
    i_emp_ort = i_emp + 3 if i_emp is not None else None
    i_ausf = col("Ausführende Stelle")

    def g(r: list[str], i: int | None) -> str:
        return r[i].strip() if i is not None and i < len(r) else ""

    out: list[Projekt] = []
    for r in rows[1:]:
        if not any(x.strip() for x in r) or not g(r, i_fkz):
            continue
        out.append(Projekt(
            fkz=g(r, i_fkz), ressort=g(r, i_res), stelle=g(r, i_stelle), empfaenger=g(r, i_emp), empfaenger_ort=g(r, i_emp_ort),
            ausfuehrende=g(r, i_ausf), thema=g(r, i_thema), lps=g(r, i_lps), lps_text=g(r, i_lpst),
            von=_datum(g(r, i_von)), bis=_datum(g(r, i_bis)), summe=_betrag(g(r, i_sum)), foerderart=g(r, i_art),
        ))
    return out


class Sitzung:
    """Eine Browser-Sitzung mit Cookies; `opener` ist injizierbar (Objekt mit .open(request, timeout))."""

    def __init__(self, opener=None, pause: float = 1.5):
        self.opener = opener or urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.pause = pause

    def _get(self, url: str) -> bytes:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        with self.opener.open(req, timeout=TIMEOUT) as resp:
            return resp.read()

    def _post(self, url: str, form: dict[str, str]) -> bytes:
        data = urllib.parse.urlencode(form).encode("latin-1", errors="replace")
        req = urllib.request.Request(url, data=data, headers={"User-Agent": USER_AGENT, "Content-Type": "application/x-www-form-urlencoded"})
        with self.opener.open(req, timeout=TIMEOUT) as resp:
            return resp.read()

    def suche_csv(self, name: str) -> str | None:
        self._get(f"{BASE}?actionMode=searchmask")
        if self.pause:
            time.sleep(self.pause)
        seite = self._post(BASE, {"actionMode": "searchlist", "suche.detailSuche": "true", "suche.nameZeStSuche": name,
                                  "submitAction": "Suchen"}).decode("latin-1", errors="replace")
        if KEINE_TREFFER in seite:
            return None
        if self.pause:
            time.sleep(self.pause)
        return self._get(f"{BASE}?actionMode=print&presentationType=csv").decode("latin-1", errors="replace")

    @staticmethod
    def treffer(seite: str) -> int | None:
        m = _TREFFER.search(seite)
        return int(m.group(1)) if m else None


def _dir(raw_dir: Path) -> Path:
    d = raw_dir / "foerderkatalog"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_projekte(raw_dir: Path, empfaenger: list[tuple[str, str]], sitzung: Sitzung,
                   log: Callable[[str], None] = print) -> list[Path]:
    d = _dir(raw_dir)
    written: list[Path] = []
    for i, (eid, suchname) in enumerate(empfaenger, 1):
        target = d / f"{eid}.csv"
        if target.exists():
            continue
        text = sitzung.suche_csv(suchname)
        target.write_text(text or "", encoding="latin-1", errors="replace", newline="")
        written.append(target)
        if i % 50 == 0:
            log(f"foerderkatalog: {i}/{len(empfaenger)} Empfänger")
    return written


def lade_projekte(raw_dir: Path) -> dict[str, list[Projekt]]:
    d = raw_dir / "foerderkatalog"
    if not d.exists():
        return {}
    out: dict[str, list[Projekt]] = {}
    for p in sorted(d.glob("*.csv")):
        text = p.read_text(encoding="latin-1")
        out[p.stem] = parse_csv(text) if text else []
    return out
