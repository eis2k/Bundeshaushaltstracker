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
    anlage_ausgaben = sum(r.soll for r in out if r.anlage and r.art == "A")
    kern_ausgaben = sum(r.soll for r in out if not r.anlage and r.art == "A")
    sv_ausgaben = sum(r.soll for r in out if r.sv and r.art == "A")
    assert kern_ausgaben == 502_546_135_000  # amtlich gerundet 502,5 Mrd
    assert anlage_ausgaben == 642_092_020_000 - 502_546_135_000
    assert 0 < sv_ausgaben < anlage_ausgaben  # EU-Anlagen und Behördenpläne zählen nicht als Nebenhaushalt
    assert all(r.kap[2] == "9" for r in out if r.anlage)


def test_only_sondervermoegen_and_nato_count_as_nebenhaushalt_when_marking_by_manual_list():
    all_rows = [row("60", "6090", "02201"), row("10", "1091", "42201"), row("60", "6092", "89310"), row("14", "1490", "55101")]
    out = mark_sv(all_rows, None, load_manual(MANUAL))
    assert [r.sv for r in out] == [False, False, True, True]


def test_difference_marking_also_excludes_eu_and_behoerden_anlagen():
    all_rows = [row("11", "1102", "63681"), row("60", "6090", "02201"), row("60", "6092", "89310")]
    kern_rows = [row("11", "1102", "63681")]
    out = mark_sv(all_rows, kern_rows, load_manual(MANUAL))
    assert [r.sv for r in out] == [False, False, True]
    assert [r.anlage for r in out] == [False, True, True]


def test_transfers_between_kern_and_sondervermoegen_are_flagged():
    from bhtracker.sv import mark_transfers
    rows = [
        row("60", "6002", "63401", soll=5).model_copy(update={"titel_text": "Zuweisung an das Sondervermögen Aufbauhilfe 2021"}),
        row("60", "6093", "88401", soll=10, ).model_copy(update={"titel_text": "Zuweisung an den Klima- und Transformationsfonds", "sv": True}),
        row("60", "6092", "33401", soll=10).model_copy(update={"titel_text": "Zuweisungen aus dem Sondervermögen Infrastruktur und Klimaneutralität", "art": "E", "sv": True}),
        row("60", "6092", "23101", soll=3).model_copy(update={"titel_text": "Zuweisungen aus dem Bundeshaushalt", "art": "E", "sv": True}),
        row("11", "1102", "63681", soll=100),
    ]
    out = mark_transfers(rows)
    assert [r.transfer for r in out] == [True, True, True, True, False]
