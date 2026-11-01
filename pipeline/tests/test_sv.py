from pathlib import Path

import pytest
import yaml

from bhtracker.model import BudgetRow
from bhtracker.parse_csv import parse_soll_csv
from bhtracker.sv import load_manual, mark_sv
from conftest import raw_file

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual" / "sondervermoegen.yaml"


def row(epl, kap, titel, soll=1):
    return BudgetRow(jahr=2025, stand="soll", art="A", epl=epl, kap=kap, titel=titel, epl_text="",
                     kap_text="", titel_text="", fkt="000", soll=soll)


def test_mark_sv_by_difference_to_kern_file():
    all_rows = [row("11", "1102", "63681"), row("60", "6092", "89310"), row("14", "1491", "55401")]
    kern_rows = [row("11", "1102", "63681")]
    out = mark_sv(all_rows, kern_rows, load_manual(MANUAL))
    assert [r.sv for r in out] == [False, True, True]


def test_mark_sv_without_kern_file_uses_manual_list_and_9x_pattern():
    all_rows = [row("11", "1102", "63681"), row("60", "6092", "89310"), row("17", "1790", "88201"), row("05", "0590", "12345")]
    out = mark_sv(all_rows, None, load_manual(MANUAL))
    assert [r.sv for r in out] == [False, True, True, True]


def test_manual_list_has_required_fields():
    manual = load_manual(MANUAL)
    assert {"6092", "1491", "6093"} <= {k["kap"] for k in manual["kapitel"]}
    for k in manual["kapitel"]:
        assert k["kap"][2] == "9" and k["art"] in {"sondervermoegen", "eu", "behoerde", "nato"} and k["quelle"].startswith("http")


@pytest.mark.skipif(raw_file("HH_2025_ALL.csv") is None or raw_file("HH_2025.csv") is None, reason="Rohdateien fehlen")
def test_full_2025_sv_share():
    all_rows = parse_soll_csv(raw_file("HH_2025_ALL.csv"), 2025)
    kern_rows = parse_soll_csv(raw_file("HH_2025.csv"), 2025)
    out = mark_sv(all_rows, kern_rows, load_manual(MANUAL))
    sv_ausgaben = sum(r.soll for r in out if r.sv and r.art == "A")
    kern_ausgaben = sum(r.soll for r in out if not r.sv and r.art == "A")
    assert kern_ausgaben == 502_500_000_000
    assert sv_ausgaben == 642_092_020_000 - 502_500_000_000
    assert all(r.kap[2] == "9" for r in out if r.sv)
