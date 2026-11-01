import json
from pathlib import Path

from bhtracker.build import build_index, build_year, build_zeitreihe
from bhtracker.checks import CheckResult
from bhtracker.model import BudgetRow


def soll(epl, kap, titel, betrag, art="A", jahr=2025, sv=False, text="T"):
    return BudgetRow(jahr=jahr, stand="soll", art=art, epl=epl, kap=kap, titel=titel, epl_text=f"Epl {epl}",
                     kap_text=f"Kap {kap}", titel_text=text, fkt="221", flex=False, soll=betrag, sv=sv)


def ist(epl, kap, titel, betrag_soll, betrag_ist, art="A", jahr=2025):
    return BudgetRow(jahr=jahr, stand="ist", art=art, epl=epl, kap=kap, titel=titel, epl_text=f"Epl {epl}",
                     kap_text="", titel_text="T", fkt="221", flex=False, soll=betrag_soll, ist=betrag_ist)


QUELLE = {"soll": {"dokument": "Bundeshaushaltsplan 2025", "url": "https://x/HH_2025_ALL.csv", "abgerufen": "2026-11-01"},
          "ist": None}


def test_build_year_writes_rows_with_ist_joined(tmp_path: Path):
    rows_soll = [soll("11", "1102", "63681", 1000), soll("11", "1101", "68101", 500), soll("60", "6092", "89310", 50, sv=True)]
    rows_ist = [ist("11", "1102", "63681", 1000, 990), ist("11", "1102", "63699", 0, 7)]  # 63699 nur in Rechnung
    out = build_year(rows_soll, rows_ist, 2025, QUELLE, tmp_path)
    assert out == tmp_path / "bund" / "2025.json"
    data = json.loads(out.read_text(encoding="utf-8"))
    assert data["jahr"] == 2025 and data["quelle"]["soll"]["url"].endswith(".csv")
    assert data["epl"]["11"] == "Epl 11" and data["kap"]["1102"] == "Kap 1102"
    by_id = {r["id"]: r for r in data["rows"]}
    assert by_id["11-1102-63681"]["soll"] == 1000 and by_id["11-1102-63681"]["ist"] == 990
    assert by_id["11-1101-68101"]["ist"] is None
    assert by_id["60-6092-89310"]["sv"] is True
    assert by_id["11-1102-63699"]["soll"] == 0 and by_id["11-1102-63699"]["ist"] == 7
    assert set(by_id["11-1102-63681"]) == {"id", "art", "epl", "kap", "titel", "text", "fkt", "flex", "tgr", "soll", "ist", "sv"}


def test_build_year_is_compact_utf8(tmp_path: Path):
    out = build_year([soll("01", "0101", "68401", 1, text="Künstlerhilfe")], None, 2025, QUELLE, tmp_path)
    txt = out.read_text(encoding="utf-8")
    assert "Künstlerhilfe" in txt and ": " not in txt.split('"rows"')[1][:200]


def test_build_zeitreihe_has_null_for_missing_years(tmp_path: Path):
    years = {
        2015: [soll("11", "1102", "63681", 800, jahr=2015)],
        2016: [soll("11", "1102", "63681", 900, jahr=2016), soll("11", "1102", "63682", 10, jahr=2016)],
    }
    ist_years = {2015: [ist("11", "1102", "63681", 800, 790, jahr=2015)]}
    out = build_zeitreihe(years, ist_years, tmp_path)
    z = json.loads(out.read_text(encoding="utf-8"))
    assert z["jahre"] == [2015, 2016]
    assert z["titel"]["11-1102-63681"]["soll"] == [800, 900]
    assert z["titel"]["11-1102-63681"]["ist"] == [790, None]
    assert z["titel"]["11-1102-63682"]["soll"] == [None, 10]
    assert z["titel"]["11-1102-63682"]["epl"] == "11" and z["titel"]["11-1102-63682"]["art"] == "A"
    assert z["kap"]["11-1102"]["soll"] == [800, 910]
    assert z["epl"]["11"]["soll"] == [800, 910]


def test_build_index(tmp_path: Path):
    totals = {2025: CheckResult(ok=True, ausgaben=500, einnahmen=300, kredite=200)}
    out = build_index([2025], totals, ist_bis=2025, out=tmp_path)
    idx = json.loads(out.read_text(encoding="utf-8"))
    assert idx["jahre"] == [2025] and idx["ist_bis"] == 2025
    assert idx["summen"]["2025"] == {"ausgaben": 500, "einnahmen": 300, "kredite": 200}
    assert "erzeugt" in idx


def test_build_manual_copies_yaml_as_json(tmp_path: Path):
    from bhtracker.build import build_manual
    manual = Path(__file__).resolve().parents[2] / "data" / "manual"
    written = build_manual(manual, tmp_path)
    names = {p.name for p in written}
    assert {"presets.json", "gesetz_frei.json"} <= names
    presets = json.loads((tmp_path / "presets.json").read_text(encoding="utf-8"))
    assert any(p["id"] == "schwarze_null" for p in presets["presets"])
    gf = json.loads((tmp_path / "gesetz_frei.json").read_text(encoding="utf-8"))
    assert all(e["quelle"].startswith("http") and e["status"] in ("gesetz", "frei") for e in gf["eintraege"])
