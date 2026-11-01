"""Sozialkassen (GRV, GKV, SPV, BA) aus data/manual/sozialkassen.yaml: prüfen, Jahre interpolieren, Build schreiben."""

from __future__ import annotations

import copy
import json
from pathlib import Path

TOLERANZ_SALDO = 0.30  # Einnahmen und Ausgaben eines Jahres dürfen um höchstens 30 % der Ausgaben auseinanderliegen


def _sum(entries: list[dict]) -> int:
    return sum(int(e.get("betrag", 0)) for e in entries)


def validate(manual: dict) -> list[str]:
    errors: list[str] = []
    toepfe = manual.get("toepfe") or {}
    if not toepfe:
        errors.append("keine Töpfe definiert")
    for tid, t in toepfe.items():
        for key in ("name", "kurz", "jahre"):
            if key not in t:
                errors.append(f"{tid}: Feld '{key}' fehlt")
        for jahr, y in (t.get("jahre") or {}).items():
            if "quelle" not in y:
                errors.append(f"{tid} {jahr}: quelle fehlt")
            for side in ("einnahmen", "ausgaben"):
                for e in y.get(side) or []:
                    for key in ("id", "text", "betrag"):
                        if key not in e:
                            errors.append(f"{tid} {jahr} {side}: Feld '{key}' fehlt in {e}")
                    if not isinstance(e.get("betrag"), int) or e.get("betrag", -1) < 0:
                        errors.append(f"{tid} {jahr} {side} {e.get('id')}: betrag muss ganze Euro ≥ 0 sein")
            ein, aus = _sum(y.get("einnahmen") or []), _sum(y.get("ausgaben") or [])
            if aus and abs(ein - aus) > TOLERANZ_SALDO * aus:
                errors.append(f"{tid} {jahr}: Differenz Einnahmen {ein:,} zu Ausgaben {aus:,} über {int(TOLERANZ_SALDO * 100)} %")
    for q in manual.get("querfluesse") or []:
        for key in ("von", "nach", "id", "text"):
            if key not in q:
                errors.append(f"querfluesse: Feld '{key}' fehlt in {q}")
        if q.get("von") not in toepfe or q.get("nach") not in toepfe:
            errors.append(f"querfluesse: unbekannter Topf in {q}")
    return errors


def _blend(a: list[dict], b: list[dict], w: float) -> list[dict]:
    """Lineare Mischung zweier Positionslisten nach id (w = Anteil von b)."""
    by_b = {e["id"]: e for e in b}
    out: list[dict] = []
    seen: set[str] = set()
    for e in a:
        seen.add(e["id"])
        eb = by_b.get(e["id"])
        betrag = round(e["betrag"] * (1 - w) + eb["betrag"] * w) if eb else e["betrag"]
        out.append({"id": e["id"], "text": e["text"], "betrag": int(betrag)})
    for e in b:
        if e["id"] not in seen:
            out.append({"id": e["id"], "text": e["text"], "betrag": int(e["betrag"])})
    return out


def interpolate(stuetz: dict[int, dict], jahre: list[int]) -> dict[int, dict]:
    """Füllt die Jahre zwischen Stützjahren linear, außerhalb flach; markiert geschaetzt."""
    keys = sorted(int(k) for k in stuetz)
    out: dict[int, dict] = {}
    for jahr in jahre:
        if jahr in stuetz or jahr in {int(k) for k in stuetz}:
            y = copy.deepcopy(stuetz.get(jahr) or stuetz.get(str(jahr)))
            y["geschaetzt"] = False
            out[jahr] = y
            continue
        prev = max((k for k in keys if k < jahr), default=None)
        nxt = min((k for k in keys if k > jahr), default=None)
        if prev is None and nxt is None:
            continue
        if prev is None or nxt is None:
            src = copy.deepcopy(stuetz[prev if prev is not None else nxt])
            src["geschaetzt"] = True
            src["hinweis"] = f"außerhalb der Stützjahre, Wert von {prev if prev is not None else nxt} übernommen"
            out[jahr] = src
            continue
        w = (jahr - prev) / (nxt - prev)
        a, b = stuetz[prev], stuetz[nxt]
        out[jahr] = {
            "quelle": f"{a.get('quelle')} / {b.get('quelle')}",
            "geschaetzt": True,
            "hinweis": f"linear zwischen {prev} und {nxt} interpoliert",
            "einnahmen": _blend(a.get("einnahmen") or [], b.get("einnahmen") or [], w),
            "ausgaben": _blend(a.get("ausgaben") or [], b.get("ausgaben") or [], w),
        }
    return out


def _bundesmittel_for(entries: list[dict], jahr: int) -> list[dict]:
    out = []
    for b in entries:
        if b.get("ab") and jahr < int(b["ab"]):
            continue
        if b.get("bis") and jahr > int(b["bis"]):
            continue
        out.append({"titel": b["titel"], "text": b.get("text", "")})
    return out


def build_sozialkassen(manual: dict, jahre: list[int], out: Path) -> list[Path]:
    errors = validate(manual)
    if errors:
        raise ValueError("sozialkassen.yaml ungültig: " + "; ".join(errors))
    written: list[Path] = []
    per_topf = {tid: interpolate({int(k): v for k, v in t["jahre"].items()}, jahre) for tid, t in manual["toepfe"].items()}
    for jahr in jahre:
        toepfe: dict[str, dict] = {}
        for tid, t in manual["toepfe"].items():
            y = per_topf[tid].get(jahr)
            if not y:
                continue
            toepfe[tid] = {
                "name": t["name"], "kurz": t["kurz"], "farbe": t.get("farbe", "beitraege"),
                "geschaetzt": bool(y.get("geschaetzt")), "quelle": y.get("quelle"), "hinweis": y.get("hinweis"),
                "bundesmittel": _bundesmittel_for(t.get("bundesmittel") or [], jahr),
                "einnahmen": [{"id": e["id"], "text": e["text"], "betrag": int(e["betrag"])} for e in y.get("einnahmen") or []],
                "ausgaben": [{"id": e["id"], "text": e["text"], "betrag": int(e["betrag"])} for e in y.get("ausgaben") or []],
            }
        data = {"jahr": jahr, "toepfe": toepfe,
                "querfluesse": [{k: q.get(k) for k in ("von", "nach", "id", "text", "quelle")} for q in manual.get("querfluesse") or []]}
        p = out / "sozialkassen" / f"{jahr}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written.append(p)
    return written
