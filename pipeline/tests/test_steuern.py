import copy
import json
from pathlib import Path

import pytest
import yaml

from bhtracker.steuern import build_steuern, validate_steuern

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual" / "steuern.yaml"


def load():
    with open(MANUAL, encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_repo_file_is_valid_and_covers_the_requested_taxes():
    data = load()
    assert validate_steuern(data) == []
    ids = {s["id"] for s in data["szenarien"]}
    assert {"vermoegensteuer", "erbschaftsteuer", "spitzensteuersatz", "abgeltungsteuer"} <= ids


def test_annahme_without_quelle_fails():
    data = load()
    data["szenarien"][0]["modell"]["annahmen"][0].pop("quelle")
    errors = validate_steuern(data)
    assert any("quelle" in e for e in errors)


def test_geschichte_needs_datum_and_quelle():
    data = load()
    data["szenarien"][0]["geschichte"][0].pop("datum")
    data["szenarien"][0]["geschichte"][1].pop("quelle")
    errors = validate_steuern(data)
    assert any("datum" in e for e in errors) and any("quelle" in e for e in errors)


def test_bund_anteil_must_be_between_0_and_1():
    data = load()
    data["szenarien"][0]["bund_anteil"] = 1.5
    assert any("bund_anteil" in e for e in validate_steuern(data))


def test_unknown_modell_art_fails():
    data = load()
    data["szenarien"][0]["modell"]["art"] = "zauberei"
    assert any("art" in e for e in validate_steuern(data))


def test_build_writes_json(tmp_path: Path):
    out = build_steuern(MANUAL, tmp_path)
    data = json.loads(out.read_text(encoding="utf-8"))
    assert out.name == "steuern.json"
    assert [s["id"] for s in data["szenarien"]][:1] == ["vermoegensteuer"]
    v = data["szenarien"][0]
    assert v["empfaenger"] == "laender" and v["bund_anteil"] == 0
    assert all(a["quelle"].startswith("http") for a in v["modell"]["annahmen"])
    assert all(g["quelle"].startswith("http") for g in v["geschichte"])


def test_satzaenderung_slider_must_not_go_below_satz_alt():
    # Unter satz_alt ergäbe das Modell Mindereinnahmen, die der Rechenkern auf 0 kappt (Review Stufe 1b, Befund 2)
    data = load()
    s = next(x for x in data["szenarien"] if x["id"] == "abgeltungsteuer")
    s["modell"]["annahmen"][0]["min"] = 0.20
    errors = validate_steuern(data)
    assert any("satz_alt" in e and "min" in e for e in errors)
