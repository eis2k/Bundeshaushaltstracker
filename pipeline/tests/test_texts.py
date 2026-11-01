import json
from pathlib import Path

import pytest

from bhtracker.texts import build_texts, parse_text_file

REPO = Path(__file__).resolve().parents[2]


def write(tmp: Path, name: str, body: str) -> Path:
    p = tmp / name
    p.write_text(body, encoding="utf-8")
    return p


def test_parse_text_file_reads_frontmatter_and_body(tmp_path: Path):
    p = write(tmp_path, "11-1102-63681.md", "---\nid: 11-1102-63681\nquelle:\n  - https://www.gesetze-im-internet.de/sgb_6/__213.html\nstand: 2026-11-01\n---\nDer Bund zahlt der Rentenkasse jedes Jahr einen Zuschuss. Grundlage ist § 213 SGB VI.\n")
    t = parse_text_file(p)
    assert t["id"] == "11-1102-63681"
    assert t["quelle"] == ["https://www.gesetze-im-internet.de/sgb_6/__213.html"]
    assert t["stand"] == "2026-11-01"
    assert t["text"].startswith("Der Bund zahlt")


def test_text_without_quelle_fails_the_build(tmp_path: Path):
    write(tmp_path, "11-1102-63681.md", "---\nid: 11-1102-63681\nstand: 2026-11-01\n---\nText ohne Quelle.\n")
    with pytest.raises(ValueError, match="quelle"):
        build_texts(tmp_path, tmp_path / "out")


def test_text_with_more_than_two_sentences_fails(tmp_path: Path):
    write(tmp_path, "11-1102-63681.md", "---\nid: 11-1102-63681\nquelle: [https://x]\nstand: 2026-11-01\n---\nEins. Zwei. Drei.\n")
    with pytest.raises(ValueError, match="Sätze"):
        build_texts(tmp_path, tmp_path / "out")


def test_build_texts_writes_json_keyed_by_id(tmp_path: Path):
    write(tmp_path, "a.md", "---\nid: 11-1102-63681\nquelle: [https://x]\nstand: 2026-11-01\n---\nSatz eins. Satz zwei.\n")
    write(tmp_path, "b.md", "---\nid: 14\nquelle: [https://y]\nstand: 2026-11-01\n---\nEinzelplan 14.\n")
    out = build_texts(tmp_path, tmp_path / "out")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert set(data) == {"11-1102-63681", "14"}
    assert data["14"]["quelle"] == ["https://y"]


def test_repo_texts_are_valid_and_cover_the_largest_titles():
    texts_dir = REPO / "data" / "texts" / "titel"
    out = build_texts(texts_dir, REPO / "data" / "build" / "_texts_check")
    data = json.loads(out.read_text(encoding="utf-8"))
    assert len(data) >= 50
    for must in ("11-1102-63681", "11-1101-68112", "32-3205-57501", "15-1501-63606", "17-1701-68102"):
        assert must in data
    build = json.loads((REPO / "data" / "build" / "bund" / "2025.json").read_text(encoding="utf-8"))
    ids = {r["id"] for r in build["rows"]} | set(build["epl"])
    unknown = [k for k in data if k not in ids]
    assert unknown == [], f"Texte ohne passenden Titel 2025: {unknown}"
