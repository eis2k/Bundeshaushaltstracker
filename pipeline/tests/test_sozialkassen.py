import json
from pathlib import Path

import pytest
import yaml

from bhtracker.sozialkassen import build_sozialkassen, interpolate, validate

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual" / "sozialkassen.yaml"


def load():
    with open(MANUAL, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_manual_file_is_valid():
    assert validate(load()) == []


def test_validate_reports_missing_fields_and_unbalanced_years():
    bad = {"toepfe": {"x": {"name": "X", "kurz": "X", "jahre": {2020: {
        "einnahmen": [{"id": "beitraege", "text": "B", "betrag": 100}],
        "ausgaben": [{"id": "a", "text": "A", "betrag": 300}],
    }}}}}
    errors = validate(bad)
    assert any("quelle" in e for e in errors)
    assert any("2020" in e and "Differenz" in e for e in errors)


def test_interpolate_fills_years_between_support_points():
    jahre = [2015, 2016, 2020]
    stuetz = {2015: {"einnahmen": [{"id": "b", "text": "B", "betrag": 100}], "ausgaben": [{"id": "a", "text": "A", "betrag": 110}], "quelle": "Q"},
              2020: {"einnahmen": [{"id": "b", "text": "B", "betrag": 200}], "ausgaben": [{"id": "a", "text": "A", "betrag": 210}], "quelle": "Q"}}
    out = interpolate(stuetz, jahre)
    assert out[2016]["einnahmen"][0]["betrag"] == 120
    assert out[2016]["ausgaben"][0]["betrag"] == 130
    assert out[2016]["geschaetzt"] is True
    assert out[2015]["geschaetzt"] is False
    assert out[2020]["einnahmen"][0]["betrag"] == 200


def test_interpolate_extrapolates_flat_outside_range():
    out = interpolate({2020: {"einnahmen": [{"id": "b", "text": "B", "betrag": 5}], "ausgaben": [], "quelle": "Q"}}, [2019, 2020, 2021])
    assert out[2019]["einnahmen"][0]["betrag"] == 5 and out[2019]["geschaetzt"] is True
    assert out[2021]["einnahmen"][0]["betrag"] == 5 and out[2021]["geschaetzt"] is True


def test_build_sozialkassen_writes_one_file_per_year(tmp_path: Path):
    written = build_sozialkassen(load(), [2015, 2016, 2025], tmp_path)
    assert {p.name for p in written} == {"2015.json", "2016.json", "2025.json"}
    d = json.loads((tmp_path / "sozialkassen" / "2016.json").read_text(encoding="utf-8"))
    assert d["jahr"] == 2016
    assert set(d["toepfe"]) == {"grv", "gkv", "spv", "ba"}
    grv = d["toepfe"]["grv"]
    assert grv["geschaetzt"] is True
    assert grv["bundesmittel"][0]["titel"] == "11-1102-63681"
    assert d["querfluesse"][0]["von"] == "grv"
    d25 = json.loads((tmp_path / "sozialkassen" / "2025.json").read_text(encoding="utf-8"))
    assert d25["toepfe"]["spv"]["geschaetzt"] is False
    assert sum(e["betrag"] for e in d25["toepfe"]["grv"]["einnahmen"]) == 417_422_000_000
