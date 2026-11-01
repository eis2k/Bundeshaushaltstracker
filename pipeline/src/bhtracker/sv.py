"""Markierung der Anlagen zum Bundeshaushalt (Sondervermögen, EU-Anlagen, Behörden-Wirtschaftspläne).

Die *_ALL-Dateien des Portals enthalten zusätzlich zum Kernhaushalt die Anlagen;
ihre Kapitelnummern enden auf 9x (0690, 1491, 6092 …). Liegt die Kern-Datei vor,
gilt die Differenzmenge; sonst die manuelle Liste plus das 9x-Muster.
"""

from __future__ import annotations

from pathlib import Path

import yaml

from .model import BudgetRow


def load_manual(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def _is_anlage_kapitel(kap: str, manual_kaps: set[str]) -> bool:
    return kap in manual_kaps or (len(kap) == 4 and kap[2] == "9")


def mark_sv(rows_all: list[BudgetRow], rows_kern: list[BudgetRow] | None, manual: dict) -> list[BudgetRow]:
    manual_kaps = {k["kap"] for k in manual.get("kapitel", [])}
    if rows_kern is not None:
        kern_keys = {(r.epl, r.kap, r.titel) for r in rows_kern}
        return [r.model_copy(update={"sv": (r.epl, r.kap, r.titel) not in kern_keys}) for r in rows_all]
    return [r.model_copy(update={"sv": _is_anlage_kapitel(r.kap, manual_kaps)}) for r in rows_all]
