"""Schreibt die Build-Dateien für die Website: bund/<jahr>.json, zeitreihe.json, index.json."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from .checks import CheckResult
from .model import BudgetRow

_JSON = {"ensure_ascii": False, "separators": (",", ":")}


def _write(path: Path, data) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, **_JSON), encoding="utf-8")
    return path


def _row_dict(r: BudgetRow, ist: int | None) -> dict:
    return {
        "id": r.id, "art": r.art, "epl": r.epl, "kap": r.kap, "titel": r.titel,
        "text": r.titel_text, "fkt": r.fkt, "flex": r.flex, "tgr": r.tgr,
        "soll": r.soll, "ist": ist, "sv": r.sv,
    }


def build_year(rows_soll: list[BudgetRow], rows_ist: list[BudgetRow] | None, jahr: int,
               quelle: dict, out: Path) -> Path:
    ist_by_id = {r.id: r for r in (rows_ist or [])}
    epl = {r.epl: r.epl_text for r in rows_soll if r.epl_text}
    kap = {r.kap: r.kap_text for r in rows_soll if r.kap_text}
    rows = [_row_dict(r, ist_by_id[r.id].ist if r.id in ist_by_id else None) for r in rows_soll]
    soll_ids = {r.id for r in rows_soll}
    for r in (rows_ist or []):
        if r.id not in soll_ids:
            rows.append(_row_dict(r, r.ist))
            epl.setdefault(r.epl, r.epl_text)
    data = {"jahr": jahr, "stand": "soll", "quelle": quelle, "epl": epl, "kap": kap, "rows": rows}
    return _write(out / "bund" / f"{jahr}.json", data)


def _series_entry(jahre: list[int]) -> dict:
    return {"soll": [None] * len(jahre), "ist": [None] * len(jahre)}


def build_zeitreihe(years: dict[int, list[BudgetRow]], ist_years: dict[int, list[BudgetRow]] | None,
                    out: Path) -> Path:
    jahre = sorted(years)
    pos = {j: i for i, j in enumerate(jahre)}
    titel: dict[str, dict] = {}
    kap: dict[str, dict] = {}
    epl: dict[str, dict] = {}

    def bump(store: dict, key: str, kind: str, j: int, value: int, meta: dict | None = None):
        entry = store.setdefault(key, {**(meta or {}), **_series_entry(jahre)})
        cur = entry[kind][pos[j]]
        entry[kind][pos[j]] = value if cur is None else cur + value

    for j, rows in years.items():
        for r in rows:
            meta = {"text": r.titel_text, "epl": r.epl, "kap": r.kap, "art": r.art, "sv": r.sv}
            bump(titel, r.id, "soll", j, r.soll, meta)
            if not r.sv and r.art == "A":  # Kapitel/Einzelplan-Reihen sind reine Ausgabensummen
                bump(kap, f"{r.epl}-{r.kap}", "soll", j, r.soll, {"text": r.kap_text, "epl": r.epl, "art": "A"})
                bump(epl, r.epl, "soll", j, r.soll, {"text": r.epl_text, "art": "A"})
    for j, rows in (ist_years or {}).items():
        if j not in pos:
            continue
        for r in rows:
            if r.ist is None:
                continue
            meta = {"text": r.titel_text, "epl": r.epl, "kap": r.kap, "art": r.art, "sv": r.sv}
            bump(titel, r.id, "ist", j, r.ist, meta)
            if not r.sv and r.art == "A":
                bump(kap, f"{r.epl}-{r.kap}", "ist", j, r.ist, {"text": r.kap_text, "epl": r.epl, "art": "A"})
                bump(epl, r.epl, "ist", j, r.ist, {"text": r.epl_text, "art": "A"})
    data = {"jahre": jahre, "titel": titel, "kap": kap, "epl": epl}
    return _write(out / "zeitreihe.json", data)


MANUAL_FILES = ("presets.yaml", "gesetz_frei.yaml", "vpi.yaml", "konkordanz.yaml")


def build_manual(manual_dir: Path, out: Path) -> list[Path]:
    """Kopiert die handgepflegten YAML-Dateien als JSON in den Build (nur vorhandene)."""
    import yaml

    written: list[Path] = []
    for name in MANUAL_FILES:
        src = manual_dir / name
        if not src.exists():
            continue
        with open(src, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        written.append(_write(out / (src.stem + ".json"), data))
    return written


def build_index(years: list[int], totals: dict[int, CheckResult], *, ist_bis: int | None, out: Path) -> Path:
    data = {
        "jahre": sorted(years),
        "ist_bis": ist_bis,
        "summen": {str(j): {"ausgaben": t.ausgaben, "einnahmen": t.einnahmen, "kredite": t.kredite}
                   for j, t in sorted(totals.items())},
        "erzeugt": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    return _write(out / "index.json", data)
