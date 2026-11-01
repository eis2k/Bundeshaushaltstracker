"""Parser für die Haushaltsrechnungs-XML (rechnung_<jahr>.xml) mit Soll und Ist je Titel.

Struktur: haushalt/einzelplan[@nr]/text, kapitel[@nr]/(einnahmen|ausgaben)/
einnahmen-ausgaben-art/titel[@nr @fkt @flexibilisiert @ein-aus-art]/(text, soll[@wert], ist[@wert]).
Beträge in Euro mit Tausenderpunkt und Dezimalkomma, Minus ggf. nachgestellt.
Leere Platzhalter-Titel (nr="") kommen in den Dateien vor und werden übersprungen.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from .model import BudgetRow, parse_amount


def _text(el: ET.Element | None) -> str:
    if el is None:
        return ""
    t = el.find("text")
    return (t.text or "").strip() if t is not None else ""


def _flex(value: str | None) -> bool | None:
    if value == "ja":
        return True
    if value == "nein":
        return False
    return None


def parse_rechnung_xml(path: Path, jahr: int) -> list[BudgetRow]:
    root = ET.parse(path).getroot()
    rows: list[BudgetRow] = []
    for epl in root.iter("einzelplan"):
        epl_nr = (epl.get("nr") or "").zfill(2)
        epl_text = _text(epl)
        for kap in epl.iter("kapitel"):
            kap_nr = (kap.get("nr") or "").zfill(4)
            kap_text = _text(kap)
            for block in kap:
                if block.tag not in ("einnahmen", "ausgaben"):
                    continue
                art = "E" if block.tag == "einnahmen" else "A"
                for titel in block.iter("titel"):
                    nr = (titel.get("nr") or "").strip()
                    if not nr:
                        continue
                    soll_el = titel.find("soll")
                    ist_el = titel.find("ist")
                    rows.append(BudgetRow(
                        jahr=jahr,
                        stand="ist",
                        art=art,  # type: ignore[arg-type]
                        epl=epl_nr,
                        kap=kap_nr,
                        titel=nr.zfill(5),
                        epl_text=epl_text,
                        kap_text=kap_text,
                        titel_text=_text(titel),
                        fkt=(titel.get("fkt") or "").zfill(3),
                        flex=_flex(titel.get("flexibilisiert")),
                        soll=parse_amount(soll_el.get("wert") if soll_el is not None else "", "eur"),
                        ist=parse_amount(ist_el.get("wert") if ist_el is not None else "", "eur"),
                    ))
    return rows
