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


def test_interpolate_fades_one_sided_posten_towards_zero():
    stuetz = {2015: {"einnahmen": [], "ausgaben": [{"id": "alg", "text": "Alg", "betrag": 100}], "quelle": "Q"},
              2020: {"einnahmen": [], "ausgaben": [{"id": "alg", "text": "Alg", "betrag": 200}, {"id": "kug", "text": "Kug", "betrag": 1000}], "quelle": "Q"}}
    out = interpolate(stuetz, [2015, 2016, 2019, 2020])
    kug_2016 = next(e for e in out[2016]["ausgaben"] if e["id"] == "kug")
    kug_2019 = next(e for e in out[2019]["ausgaben"] if e["id"] == "kug")
    assert kug_2016["betrag"] == 200    # 1000 × 1/5
    assert kug_2019["betrag"] == 800    # 1000 × 4/5
    only_a = interpolate({2020: {"einnahmen": [], "ausgaben": [{"id": "kug", "text": "Kug", "betrag": 1000}], "quelle": "Q"},
                          2024: {"einnahmen": [], "ausgaben": [{"id": "alg", "text": "Alg", "betrag": 10}], "quelle": "Q"}}, [2022])
    assert next(e for e in only_a[2022]["ausgaben"] if e["id"] == "kug")["betrag"] == 500


def test_bundesmittel_must_exist_in_the_bund_build_of_that_year():
    from bhtracker.sozialkassen import check_bundesmittel
    manual = {"toepfe": {"gkv": {"name": "G", "kurz": "G", "jahre": {}, "bundesmittel": [
        {"titel": "15-1502-63606", "text": "alt", "bis": 2015}, {"titel": "15-1501-63606", "text": "neu", "ab": 2016}]}}}
    ids_by_year = {2015: {"15-1502-63606"}, 2016: {"15-1501-63606"}, 2017: set()}
    assert check_bundesmittel(manual, ids_by_year) == ["gkv 2017: Titel 15-1501-63606 fehlt im Bundeshaushalt 2017"]


def test_build_passes_quellen_with_urls(tmp_path: Path):
    written = build_sozialkassen(load(), [2025], tmp_path)
    d = json.loads(written[0].read_text(encoding="utf-8"))
    grv = d["toepfe"]["grv"]
    assert grv["quelle"]["url"].startswith("https://")
    assert grv["quelle"]["dokument"]
    assert d["querfluesse"][0]["quelle"]["url"].startswith("https://")
