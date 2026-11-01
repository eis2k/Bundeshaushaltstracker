"""Summenprüfung der geparsten Titel gegen amtliche Gesamtzahlen (data/manual/gesamtplan_summen.yaml)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from .model import BudgetRow

KREDIT_GRUPPE = "325"


def _fmt(n: int) -> str:
    return f"{n:,.0f}".replace(",", ".")


@dataclass
class CheckResult:
    ok: bool
    ausgaben: int
    einnahmen: int
    kredite: int
    diffs: list[str] = field(default_factory=list)


def load_expected(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["jahre"] = {int(k): v for k, v in (data.get("jahre") or {}).items()}
    return data


def check_totals(rows: list[BudgetRow], jahr: int, expected: dict, *, toleranz: int = 1_000_000) -> CheckResult:
    kern = [r for r in rows if not r.anlage]
    ausgaben = sum(r.soll for r in kern if r.art == "A")
    kredite = sum(r.soll for r in kern if r.art == "E" and r.gruppe == KREDIT_GRUPPE)
    einnahmen = sum(r.soll for r in kern if r.art == "E") - kredite
    diffs: list[str] = []

    exp_a = expected.get("ausgaben_kern")
    if exp_a is not None and abs(ausgaben - exp_a) > toleranz:
        diffs.append(f"{jahr}: Ausgaben Kernhaushalt {_fmt(ausgaben)} € weichen von amtlich {_fmt(exp_a)} € um {_fmt(ausgaben - exp_a)} € ab")

    exp_k = expected.get("nettokreditaufnahme")
    if exp_k is not None and abs(kredite - exp_k) > toleranz:
        diffs.append(f"{jahr}: Kreditaufnahme {_fmt(kredite)} € weicht von amtlich {_fmt(exp_k)} € ab")

    if abs(ausgaben - (einnahmen + kredite)) > toleranz:
        diffs.append(f"{jahr}: Haushaltsausgleich verletzt: Ausgaben {_fmt(ausgaben)} € != Einnahmen {_fmt(einnahmen)} € + Kredite {_fmt(kredite)} €")

    return CheckResult(ok=not diffs, ausgaben=ausgaben, einnahmen=einnahmen, kredite=kredite, diffs=diffs)
