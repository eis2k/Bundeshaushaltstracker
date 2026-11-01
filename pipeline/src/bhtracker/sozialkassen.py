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
    quellen = manual.get("quellen") or {}
    for tid, t in toepfe.items():
        for key in ("name", "kurz", "jahre"):
            if key not in t:
                errors.append(f"{tid}: Feld '{key}' fehlt")
        for jahr, y in (t.get("jahre") or {}).items():
            if "quelle" not in y:
                errors.append(f"{tid} {jahr}: quelle fehlt")
            elif quellen and y["quelle"] not in quellen:
                errors.append(f"{tid} {jahr}: quelle '{y['quelle']}' nicht unter 'quellen' definiert")
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
    for kurz, q in quellen.items():
        if not (isinstance(q, dict) and str(q.get("url", "")).startswith("http") and q.get("dokument")):
            errors.append(f"quellen {kurz}: dokument und url (https) nötig")
    return errors


def check_bundesmittel(manual: dict, ids_by_year: dict[int, set[str]]) -> list[str]:
    """Jede verknüpfte Bund-Titel-ID muss in jedem Jahr, für das sie gilt, im Bundeshaushalt vorkommen."""
    errors: list[str] = []
    for tid, t in (manual.get("toepfe") or {}).items():
        for b in t.get("bundesmittel") or []:
            for jahr, ids in sorted(ids_by_year.items()):
                if b.get("ab") and jahr < int(b["ab"]):
                    continue
                if b.get("bis") and jahr > int(b["bis"]):
                    continue
                if b["titel"] not in ids:
                    errors.append(f"{tid} {jahr}: Titel {b['titel']} fehlt im Bundeshaushalt {jahr}")
    return errors


def _blend(a: list[dict], b: list[dict], w: float) -> list[dict]:
    """Lineare Mischung zweier Positionslisten nach id (w = Anteil von b); einseitige Posten laufen gegen 0."""
    by_a = {e["id"]: e for e in a}
    by_b = {e["id"]: e for e in b}
    out: list[dict] = []
    for pid in list(by_a) + [k for k in by_b if k not in by_a]:
        ea, eb = by_a.get(pid), by_b.get(pid)
        va = ea["betrag"] if ea else 0
        vb = eb["betrag"] if eb else 0
        betrag = int(round(va * (1 - w) + vb * w))
        if betrag <= 0:
            continue
        out.append({"id": pid, "text": (ea or eb)["text"], "betrag": betrag})
    return out


def interpolate(stuetz: dict[int, dict], jahre: list[int]) -> dict[int, dict]:
    """Füllt die Jahre zwischen Stützjahren linear, außerhalb flach; markiert geschaetzt."""
    stuetz = {int(k): v for k, v in stuetz.items()}
    keys = sorted(stuetz)
    out: dict[int, dict] = {}
    for jahr in jahre:
        if jahr in stuetz:
            y = copy.deepcopy(stuetz[jahr])
            y["geschaetzt"] = False
            out[jahr] = y
            continue
        prev = max((k for k in keys if k < jahr), default=None)
        nxt = min((k for k in keys if k > jahr), default=None)
        if prev is None and nxt is None:
            continue
        if prev is None or nxt is None:
            ref = prev if prev is not None else nxt
            src = copy.deepcopy(stuetz[ref])
            src["geschaetzt"] = True
            src["hinweis"] = f"außerhalb der Stützjahre, Wert von {ref} übernommen"
            out[jahr] = src
            continue
        w = (jahr - prev) / (nxt - prev)
        a, b = stuetz[prev], stuetz[nxt]
        out[jahr] = {
            "quelle": a.get("quelle") if a.get("quelle") == b.get("quelle") else f"{a.get('quelle')} / {b.get('quelle')}",
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


def _resolve_quelle(kurz: str | None, quellen: dict) -> dict:
    if not kurz:
        return {"kurz": None, "dokument": None, "url": None}
    first = kurz.split("/")[0].strip()
    q = quellen.get(first) or {}
    return {"kurz": kurz, "dokument": q.get("dokument"), "url": q.get("url")}


def build_sozialkassen(manual: dict, jahre: list[int], out: Path, ids_by_year: dict[int, set[str]] | None = None) -> list[Path]:
    errors = validate(manual)
    if ids_by_year:
        errors += check_bundesmittel(manual, {j: ids for j, ids in ids_by_year.items() if j in jahre})
    if errors:
        raise ValueError("sozialkassen.yaml ungültig: " + "; ".join(errors))
    quellen = manual.get("quellen") or {}
    written: list[Path] = []
    per_topf = {tid: interpolate(t["jahre"], jahre) for tid, t in manual["toepfe"].items()}
    for jahr in jahre:
        toepfe: dict[str, dict] = {}
        for tid, t in manual["toepfe"].items():
            y = per_topf[tid].get(jahr)
            if not y:
                continue
            toepfe[tid] = {
                "name": t["name"], "kurz": t["kurz"], "farbe": t.get("farbe", "beitraege"),
                "geschaetzt": bool(y.get("geschaetzt")), "quelle": _resolve_quelle(y.get("quelle"), quellen), "hinweis": y.get("hinweis"),
                "geprueft": y.get("geprueft", True),
                "bundesmittel": _bundesmittel_for(t.get("bundesmittel") or [], jahr),
                "einnahmen": [{"id": e["id"], "text": e["text"], "betrag": int(e["betrag"]), "geprueft": e.get("geprueft", True)} for e in y.get("einnahmen") or []],
                "ausgaben": [{"id": e["id"], "text": e["text"], "betrag": int(e["betrag"]), "geprueft": e.get("geprueft", True)} for e in y.get("ausgaben") or []],
            }
        data = {"jahr": jahr, "toepfe": toepfe,
                "querfluesse": [{"von": q["von"], "nach": q["nach"], "id": q["id"], "text": q["text"], "quelle": _resolve_quelle(q.get("quelle"), quellen)}
                                for q in manual.get("querfluesse") or []]}
        p = out / "sozialkassen" / f"{jahr}.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
        written.append(p)
    return written
