from pathlib import Path

from bhtracker.checks import CheckResult, check_totals, load_expected
from bhtracker.model import BudgetRow

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual" / "gesamtplan_summen.yaml"


def row(art, titel, soll, kap="1102", epl="11", sv=False):
    return BudgetRow(jahr=2025, stand="soll", art=art, epl=epl, kap=kap, titel=titel, epl_text="",
                     kap_text="", titel_text="", fkt="000", soll=soll, sv=sv)


ROWS = [
    row("A", "63681", 600), row("A", "97201", -100), row("A", "89310", 50, kap="6092", epl="60", sv=True),
    row("E", "01101", 300, kap="6001", epl="60"), row("E", "32511", 200, kap="3201", epl="32"),
    row("E", "33401", 50, kap="6092", epl="60", sv=True),
]


def test_check_totals_ok_and_separates_kredite():
    res = check_totals(ROWS, 2025, {"ausgaben_kern": 500, "nettokreditaufnahme": 200}, toleranz=0)
    assert isinstance(res, CheckResult)
    assert res.ok and res.diffs == []
    assert res.ausgaben == 500          # Kern: 600 - 100, Anlagen nicht mitgezählt
    assert res.einnahmen == 300         # ohne Kredite
    assert res.kredite == 200
    assert res.ausgaben == res.einnahmen + res.kredite


def test_check_totals_reports_difference_with_text():
    res = check_totals(ROWS, 2025, {"ausgaben_kern": 2_500}, toleranz=1)
    assert not res.ok
    assert any("Ausgaben" in d and "2.000" in d for d in res.diffs)


def test_check_totals_reports_unbalanced_budget():
    rows = ROWS + [row("E", "11101", 7, kap="6001", epl="60")]
    res = check_totals(rows, 2025, {"ausgaben_kern": 500}, toleranz=0)
    assert not res.ok and any("Ausgleich" in d for d in res.diffs)


def test_load_expected_reads_yaml():
    exp = load_expected(MANUAL)
    assert exp["toleranz"] == 1_000_000
    assert exp["jahre"][2025]["ausgaben_kern"] == 502_546_135_000
    assert exp["jahre"][2025]["quelle"]["url"].startswith("https://")
