"""Erklärtexte zu Titeln (data/texts/titel/*.md): Frontmatter mit id, quelle (Pflicht), stand; Body höchstens zwei Sätze."""

from __future__ import annotations

import json
import re
from pathlib import Path

import yaml

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-ZÄÖÜ„\"(])")


def parse_text_file(path: Path) -> dict:
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    if not m:
        raise ValueError(f"{path.name}: Frontmatter fehlt")
    meta = yaml.safe_load(m.group(1)) or {}
    text = " ".join(m.group(2).split())
    quelle = meta.get("quelle")
    if isinstance(quelle, str):
        quelle = [quelle]
    return {"id": str(meta.get("id", path.stem)), "quelle": quelle or [], "stand": str(meta.get("stand", "")), "text": text}


def count_sentences(text: str) -> int:
    text = text.strip()
    if not text:
        return 0
    return len(_SENTENCE_SPLIT.split(text))


def build_texts(texts_dir: Path, out: Path) -> Path:
    data: dict[str, dict] = {}
    errors: list[str] = []
    for p in sorted(texts_dir.glob("*.md")):
        if p.name.lower() == "readme.md":
            continue
        t = parse_text_file(p)
        if not t["quelle"]:
            errors.append(f"{p.name}: quelle fehlt")
        if not all(str(q).startswith("http") for q in t["quelle"]):
            errors.append(f"{p.name}: quelle muss eine URL sein")
        n = count_sentences(t["text"])
        if n > 2:
            errors.append(f"{p.name}: {n} Sätze, erlaubt sind höchstens zwei")
        if not t["text"]:
            errors.append(f"{p.name}: Text fehlt")
        data[t["id"]] = {"text": t["text"], "quelle": t["quelle"], "stand": t["stand"]}
    if errors:
        raise ValueError("Erklärtexte ungültig: " + "; ".join(errors))
    out_file = out / "texte.json" if out.suffix != ".json" else out
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    return out_file
