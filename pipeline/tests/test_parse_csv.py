import pytest

from bhtracker.parse_csv import parse_soll_csv
from conftest import raw_file


def test_parse_2025_all_header_variants(fx):
    rows = parse_soll_csv(fx / "soll_2025_kopf.csv", 2025)
    r = next(r for r in rows if r.titel == "68401" and r.kap == "0101")
    assert r.art == "A" and r.soll == 2_000_000 and r.flex is False and r.fkt == "187"
    assert r.epl_text == "Bundespräsident und Bundespräsidialamt"
    assert r.kap_text == "Bundespräsident"
    assert r.jahr == 2025 and r.stand == "soll" and r.ist is None
    assert r.tgr is None


def test_parse_2015_unquoted_header(fx):
    rows = parse_soll_csv(fx / "soll_2015_kopf.csv", 2015)
    assert rows[0].id == "01-0101-23201" and rows[0].art == "E" and rows[0].flex is None
    assert rows[1].soll == 780_000 and rows[1].flex is False


def test_parse_cp1252(fx):
    rows = parse_soll_csv(fx / "soll_2016_win.csv", 2016)
    assert rows[0].epl_text == "Bundespräsident und Bundespräsidialamt"


def test_titelgruppe_is_kept(fx):
    rows = parse_soll_csv(fx / "soll_2025_kopf.csv", 2025)
    with_tgr = [r for r in rows if r.tgr]
    assert with_tgr, "Fixture sollte mindestens einen Titel mit Titelgruppe enthalten"
    assert with_tgr[0].tgr_text


@pytest.mark.skipif(raw_file("HH_2025_ALL.csv") is None, reason="Rohdatei nicht vorhanden")
def test_full_2025_totals():
    rows = parse_soll_csv(raw_file("HH_2025_ALL.csv"), 2025)
    assert len(rows) == 7411
    assert sum(r.soll for r in rows if r.art == "A") == 642_092_020_000
    assert sum(r.soll for r in rows if r.art == "E") == 642_092_020_000


@pytest.mark.skipif(raw_file("Haushalt_2015_utf8.csv") is None, reason="Rohdatei nicht vorhanden")
def test_full_2015_totals():
    rows = parse_soll_csv(raw_file("Haushalt_2015_utf8.csv"), 2015)
    assert len(rows) == 5818
    assert sum(r.soll for r in rows if r.art == "A") == 299_100_000_000


def test_parse_2023_two_digit_kapitel_and_lowercase_art(fx):
    rows = parse_soll_csv(fx / "soll_2023_kopf.csv", 2023)
    assert rows[0].id == "01-0101-23201" and rows[0].art == "E"
    assert all(len(r.kap) == 4 and r.kap.startswith(r.epl) for r in rows)
    assert any(r.art == "A" for r in rows)
