import pytest

from bhtracker.parse_xml import parse_rechnung_xml
from conftest import raw_file

def test_parse_values_soll_and_ist(fx):
    rows = parse_rechnung_xml(fx / "rechnung_2024_ausschnitt.xml", 2024)
    r = next(r for r in rows if r.id == "01-0101-23201")
    assert r.stand == "ist" and r.art == "E" and r.jahr == 2024
    assert r.soll == 0 and r.ist == 1_088_350
    assert r.epl_text == "Bundespräsident und Bundespräsidialamt"
    assert r.kap_text == ""  # die Rechnungs-XML führt keine Kapiteltexte; der Build ergänzt sie aus den Soll-Daten
    assert r.fkt == "187" and r.flex is False

def test_parse_trailing_minus(fx):
    rows = parse_rechnung_xml(fx / "rechnung_2024_ausschnitt.xml", 2024)
    r = next(r for r in rows if r.id == "01-0113-54709")
    assert r.ist == -16

def test_placeholder_titel_without_nr_is_skipped(fx):
    rows = parse_rechnung_xml(fx / "rechnung_2024_ausschnitt.xml", 2024)
    assert all(r.titel.strip("0") for r in rows), "Titel ohne Nummer dürfen nicht übernommen werden"
    assert all(r.epl == "01" or r.epl == "06" for r in rows)

def test_titel_count_epl_01(fx):
    rows = parse_rechnung_xml(fx / "rechnung_2024_ausschnitt.xml", 2024)
    assert sum(1 for r in rows if r.epl == "01") == 85

EPL01_COUNT = 85

@pytest.mark.skipif(raw_file("rechnung_2024.xml") is None, reason="Rohdatei nicht vorhanden")
def test_full_2024_parses_all_real_titel():
    rows = parse_rechnung_xml(raw_file("rechnung_2024.xml"), 2024)
    assert len(rows) == 6787 - 4
    assert all(r.ist is not None for r in rows)
