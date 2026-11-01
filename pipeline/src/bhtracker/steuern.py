"""Steuer-Szenarien (data/manual/steuern.yaml): prüfen und als steuern.json in den Build schreiben."""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path

import yaml

MODELLARTEN = {"satz_mal_basis", "satzaenderung", "basis_mal_faktor"}
STATUS = {"erhoben", "ausgesetzt", "nie_eingefuehrt"}
EMPFAENGER = {"bund", "laender", "gemeinsam"}


def _url(v) -> bool:
    return isinstance(v, str) and v.startswith("http")


def validate_steuern(data: dict) -> list[str]:
    errors: list[str] = []
    szenarien = data.get("szenarien") or []
    if not szenarien:
        errors.append("keine Szenarien")
    seen: set[str] = set()
    for s in szenarien:
        sid = s.get("id", "?")
        if sid in seen:
            errors.append(f"{sid}: doppelte id")
        seen.add(sid)
        for key in ("id", "name", "kurz", "status", "empfaenger", "bund_anteil", "beschreibung", "modell", "geschichte"):
            if key not in s:
                errors.append(f"{sid}: Feld '{key}' fehlt")
        if s.get("status") not in STATUS:
            errors.append(f"{sid}: status muss einer von {sorted(STATUS)} sein")
        if s.get("empfaenger") not in EMPFAENGER:
            errors.append(f"{sid}: empfaenger muss einer von {sorted(EMPFAENGER)} sein")
        ba = s.get("bund_anteil")
        if not isinstance(ba, (int, float)) or not 0 <= ba <= 1:
            errors.append(f"{sid}: bund_anteil muss zwischen 0 und 1 liegen")
        if not _url(s.get("bund_anteil_quelle")):
            errors.append(f"{sid}: bund_anteil_quelle fehlt")
        m = s.get("modell") or {}
        if m.get("art") not in MODELLARTEN:
            errors.append(f"{sid}: modell.art muss eine von {sorted(MODELLARTEN)} sein")
        basis = m.get("basis") or {}
        if not isinstance(basis.get("wert"), (int, float)) or basis.get("wert", -1) < 0:
            errors.append(f"{sid}: modell.basis.wert fehlt oder negativ")
        for key in ("text", "jahr"):
            if key not in basis:
                errors.append(f"{sid}: modell.basis.{key} fehlt")
        if not _url(basis.get("quelle")):
            errors.append(f"{sid}: modell.basis.quelle fehlt")
        if m.get("art") == "satzaenderung" and not isinstance(m.get("satz_alt"), (int, float)):
            errors.append(f"{sid}: modell.satz_alt fehlt")
        annahmen = m.get("annahmen") or []
        if not annahmen:
            errors.append(f"{sid}: modell.annahmen fehlt")
        for a in annahmen:
            for key in ("id", "text", "wert", "min", "max", "schritt", "einheit"):
                if key not in a:
                    errors.append(f"{sid} annahme {a.get('id', '?')}: Feld '{key}' fehlt")
            if not _url(a.get("quelle")):
                errors.append(f"{sid} annahme {a.get('id', '?')}: quelle fehlt")
            if all(k in a for k in ("min", "max", "wert")) and not (a["min"] <= a["wert"] <= a["max"]):
                errors.append(f"{sid} annahme {a.get('id')}: wert außerhalb von min/max")
        geschichte = s.get("geschichte") or []
        if not geschichte:
            errors.append(f"{sid}: geschichte fehlt")
        for g in geschichte:
            for key in ("datum", "titel", "text", "akteure"):
                if key not in g:
                    errors.append(f"{sid} geschichte '{g.get('titel', '?')}': Feld '{key}' fehlt")
            if "datum" in g and not isinstance(g["datum"], (dt.date, dt.datetime)):
                errors.append(f"{sid} geschichte '{g.get('titel', '?')}': datum muss ein Datum sein")
            if not _url(g.get("quelle")):
                errors.append(f"{sid} geschichte '{g.get('titel', '?')}': quelle fehlt")
    return errors


def _norm(obj):
    if isinstance(obj, (dt.date, dt.datetime)):
        return obj.isoformat()[:10]
    if isinstance(obj, dict):
        return {k: _norm(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_norm(v) for v in obj]
    return obj


def build_steuern(manual_file: Path, out: Path) -> Path:
    with open(manual_file, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    errors = validate_steuern(data)
    if errors:
        raise ValueError("steuern.yaml ungültig: " + "; ".join(errors))
    for s in data["szenarien"]:
        s["geschichte"] = sorted(s["geschichte"], key=lambda g: g["datum"])
    out_file = out / "steuern.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(_norm(data), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out_file
