"""Nebenhaushalte (Sondervermögen) und Transfers zwischen Kernhaushalt und Nebenhaushalten.

Die *_ALL-Dateien des Portals enthalten zusätzlich zum Kernhaushalt die Anlagen (Kapitel ??9?).
Als Nebenhaushalt zählen nur Sondervermögen und das NATO-Programm (art sondervermoegen/nato in
data/manual/sondervermoegen.yaml). EU-Anlagen (Eigenmittel, Marktordnung) sind Durchlaufposten, die der
Kern bereits als Weiterleitung enthält; Behörden-Wirtschaftspläne (BfR, BLE) werden aus Kern-Zuschüssen
finanziert. Beide bleiben außen vor, sonst würden sie doppelt gezählt.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from .model import BudgetRow

NEBENHAUSHALT_ARTEN = {"sondervermoegen", "nato"}

_TRANSFER_WORDS = re.compile(
    r"Sondervermögen|Klima- und Transformationsfonds|Energie- und Klimafonds|aus dem Bundeshaushalt|an den Bundeshaushalt|Bundeswehr\s*\(Sondervermögen",
    re.I,
)


def load_manual(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _kap_arten(manual: dict) -> dict[str, str]:
    return {k["kap"]: k.get("art", "sondervermoegen") for k in manual.get("kapitel", [])}


def _is_nebenhaushalt(kap: str, arten: dict[str, str]) -> bool:
    art = arten.get(kap)
    if art is not None:
        return art in NEBENHAUSHALT_ARTEN
    return len(kap) == 4 and kap[2] == "9"


def _is_anlage(kap: str, arten: dict[str, str]) -> bool:
    return kap in arten or (len(kap) == 4 and kap[2] == "9")


def mark_sv(rows_all: list[BudgetRow], rows_kern: list[BudgetRow] | None, manual: dict) -> list[BudgetRow]:
    """Setzt `anlage` für alle Anlagen (nicht Kernhaushalt) und `sv` nur für Nebenhaushalte, die zuschaltbar sind."""
    arten = _kap_arten(manual)
    out = []
    kern_keys = {(r.epl, r.kap, r.titel) for r in rows_kern} if rows_kern is not None else None
    for r in rows_all:
        anlage = (r.epl, r.kap, r.titel) not in kern_keys if kern_keys is not None else _is_anlage(r.kap, arten)
        out.append(r.model_copy(update={"anlage": anlage, "sv": anlage and _is_nebenhaushalt(r.kap, arten)}))
    return out


def mark_transfers(rows: list[BudgetRow]) -> list[BudgetRow]:
    """Markiert Zahlungen zwischen Kern und Nebenhaushalten (und zwischen Nebenhaushalten), damit sie bei
    zugeschalteten Nebenhaushalten nur einmal zählen: Kern-Ausgaben der Gruppen 6xx/8xx/9xx an ein
    Sondervermögen, Einnahmen eines Nebenhaushalts aus dem Bundeshaushalt oder einem anderen Sondervermögen
    (Gruppen 2xx/3xx) und Zuweisungen eines Nebenhaushalts an ein anderes."""
    out = []
    for r in rows:
        transfer = False
        if _TRANSFER_WORDS.search(r.titel_text or ""):
            if not r.sv and r.art == "A" and r.hg in ("6", "8", "9"):
                transfer = True
            elif r.sv and r.art == "E" and r.hg in ("2", "3"):
                transfer = True
            elif r.sv and r.art == "A" and r.hg in ("6", "8", "9"):
                transfer = True
        out.append(r.model_copy(update={"transfer": transfer}) if transfer != r.transfer else r)
    return out
