"""Nachtragshaushalte: die Portal-CSVs der Nachträge enthalten nur geänderte Titel (Spalten soll/bisher)."""

from __future__ import annotations

from .model import BudgetRow


def apply_nachtrag(base: list[BudgetRow], nachtrag: list[BudgetRow]) -> list[BudgetRow]:
    """Überschreibt die Soll-Werte der im Nachtrag gelisteten Titel; neue Titel werden angehängt."""
    by_id = {r.id: r for r in nachtrag}
    out: list[BudgetRow] = []
    seen: set[str] = set()
    for r in base:
        if r.id in by_id:
            out.append(r.model_copy(update={"soll": by_id[r.id].soll}))
        else:
            out.append(r)
        seen.add(r.id)
    out.extend(r for r in nachtrag if r.id not in seen)
    return out
