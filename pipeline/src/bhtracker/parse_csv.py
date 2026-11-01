"""Parser für die Soll-CSV-Dateien des Download-Portals (2012 bis heute).

Bekannte Varianten der Kopfzeile:
- 2015: ``einnahmen-ausgaben;einnahmen-ausgaben-art;...;soll;...`` ohne Anführungszeichen, UTF-8
- 2025: ``einahmen-ausgaben;einahmen-ausgaben-text;...;soll ;...`` mit Anführungszeichen, UTF-8 mit BOM
- ``*_win*.csv``: Windows-1252 oder UTF-8 mit Ersatzzeichen
Beträge stehen in Tausend Euro.
"""

from __future__ import annotations

import csv
import io
from pathlib import Path

from .model import BudgetRow, parse_amount

_ENCODINGS = ("utf-8-sig", "cp1252")

_HEADER_ALIASES = {
    "einahmen-ausgaben": "art",
    "einnahmen-ausgaben": "art",
    "einahmen-ausgaben-text": "art_text",
    "einnahmen-ausgaben-text": "art_text",
    "einnahmen-ausgaben-art": "art_text",
    "einzelplan": "epl",
    "einzelplan-text": "epl_text",
    "kapitel": "kap",
    "kapitel-text": "kap_text",
    "titel": "titel",
    "titel-text": "titel_text",
    "funktion": "fkt",
    "flex": "flex",
    "seite": "seite",
    "soll": "soll",
    "titelgruppe": "tgr",
    "tgr-text": "tgr_text",
}


def _read_text(path: Path) -> str:
    data = path.read_bytes()
    for enc in _ENCODINGS:
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _normalize_header(fields: list[str]) -> list[str]:
    out = []
    for f in fields:
        key = f.strip().strip('"').lower()
        out.append(_HEADER_ALIASES.get(key, key))
    return out


def _flex(value: str) -> bool | None:
    v = value.strip().lower()
    if v == "ja":
        return True
    if v == "nein":
        return False
    return None


def parse_soll_csv(path: Path, jahr: int) -> list[BudgetRow]:
    text = _read_text(path)
    reader = csv.reader(io.StringIO(text), delimiter=";")
    header = _normalize_header(next(reader))
    idx = {name: i for i, name in enumerate(header)}
    rows: list[BudgetRow] = []
    for raw in reader:
        if not raw or all(not c.strip() for c in raw):
            continue
        cells = [c.strip() for c in raw]

        def get(name: str) -> str:
            i = idx.get(name)
            return cells[i] if i is not None and i < len(cells) else ""

        art = get("art").upper()
        if art not in ("E", "A"):
            continue
        epl = get("epl").zfill(2)
        kap = get("kap")
        # 2023 schreibt das Kapitel zweistellig ("01" statt "0101"): Einzelplan voranstellen
        kap = epl + kap.zfill(2) if len(kap) <= 2 else kap.zfill(4)
        rows.append(BudgetRow(
            jahr=jahr,
            stand="soll",
            art=art,  # type: ignore[arg-type]
            epl=epl,
            kap=kap,
            titel=get("titel").zfill(5),
            epl_text=get("epl_text"),
            kap_text=get("kap_text"),
            titel_text=get("titel_text"),
            fkt=get("fkt").zfill(3),
            flex=_flex(get("flex")),
            tgr=get("tgr") or None,
            tgr_text=get("tgr_text") or None,
            soll=parse_amount(get("soll"), "tsd"),
        ))
    return rows
