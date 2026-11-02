from pathlib import Path

import yaml

from bhtracker.regierung import fetch_kabinett, lade_regierung, parse_kabinett, validate_regierung

FIXTURES = Path(__file__).parent / "fixtures"
MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def ressorts() -> dict:
    return yaml.safe_load((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"))


def test_parse_kabinett_liest_name_amt_und_epl():
    m = parse_kabinett(fixture_text("kabinett_ausschnitt.html"), "2026-11-02", ressorts())
    assert len(m) == 2
    kanzler = next(x for x in m if x.name == "Friedrich Merz")
    assert kanzler.amt.startswith("Bundeskanzler") and kanzler.epl == "04" and kanzler.stand == "2026-11-02"
    aa = next(x for x in m if "Auswärtigen" in x.amt)
    assert aa.name == "Dr. Johann Wadephul" and aa.epl == "05"
    assert aa.quelle == "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/johann-wadephul-2342698"
    assert aa.ressort == "Auswärtiges Amt"


def test_parse_kabinett_ohne_kacheln_liefert_leere_liste():
    assert parse_kabinett(fixture_text("kabinett_leer.html"), "2026-11-02", ressorts()) == []


def test_validate_regierung_pflichtfelder():
    data = {"stand": "2026-11-02", "mitglieder": [{"name": "X Y", "amt": "Staatssekretär", "ressort": "Bundesministerium der Finanzen", "epl": "08", "seit": "2025-05-06", "quelle": "https://x"}]}
    assert validate_regierung(data) == []
    data["mitglieder"][0].pop("quelle")
    assert any("quelle" in e for e in validate_regierung(data))
    data["mitglieder"][0]["quelle"] = "https://x"
    data["mitglieder"][0]["amt"] = "Kaiser"
    assert any("amt" in e for e in validate_regierung(data))
    data["mitglieder"][0]["amt"] = "Staatssekretär"
    data["mitglieder"][0]["seit"] = "Mai 2025"
    assert any("seit" in e for e in validate_regierung(data))


def test_repo_regierung_yaml_ist_gueltig():
    data = yaml.safe_load((MANUAL / "regierung.yaml").read_text(encoding="utf-8"))
    assert validate_regierung(data) == []


def test_lade_regierung_yaml_ueberschreibt_abruf(tmp_path):
    raw = tmp_path / "raw"
    (raw / "regierung").mkdir(parents=True)
    (raw / "regierung" / "kabinett.html").write_text(fixture_text("kabinett_ausschnitt.html"), encoding="utf-8")
    manual = tmp_path / "regierung.yaml"
    manual.write_text(
        "stand: '2026-11-02'\nmitglieder:\n"
        "  - {name: 'Dr. Johann Wadephul', amt: 'Bundesminister des Auswärtigen', ressort: 'Auswärtiges Amt', epl: '05', seit: '2025-05-06', quelle: 'https://www.auswaertiges-amt.de/x', mdb_id: 1043950}\n"
        "  - {name: 'Test Person', amt: 'Parlamentarische Staatssekretärin', ressort: 'Bundesministerium der Finanzen', epl: '08', seit: '2025-05-06', quelle: 'https://x'}\n",
        encoding="utf-8")
    m = lade_regierung(manual, raw, ressorts())
    namen = [x.name for x in m]
    assert namen.count("Dr. Johann Wadephul") == 1 and "Friedrich Merz" in namen and "Test Person" in namen
    w = next(x for x in m if x.name == "Dr. Johann Wadephul")
    assert w.seit == "2025-05-06" and w.mdb_id == 1043950 and w.quelle == "https://www.auswaertiges-amt.de/x"


def test_fetch_kabinett_schreibt_datei(tmp_path):
    p = fetch_kabinett(tmp_path, lambda url: b"<html></html>")
    assert p.exists() and p.name == "kabinett.html"
