from pathlib import Path

from bhtracker.empfaenger import norm_name
from bhtracker.spenden import JAHR_URL, fetch_spenden, ist_natuerliche_person, lade_spenden, parse_spenden, zuordnen

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_spenden_liest_zeilen_und_laesst_monatszeilen_aus():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    assert len(sp) == 3
    csu = next(x for x in sp if x.partei == "CSU")
    assert csu.betrag == 136_000
    assert csu.spender == "Verband der Bayrischen Metall- und Elektro-Industrie e.V. (VBM)"
    assert csu.spender_ort == "München"
    assert csu.eingang == "2025-12-23" and csu.veroeffentlicht == "2025-12-26"
    assert csu.drucksache == "Drs. 21/4050" and csu.drucksache_url == "https://dserver.bundestag.de/btd/21/040/2104050.pdf"
    assert csu.natuerliche_person is False and csu.jahr == 2025


def test_natuerliche_person_erkannt_und_ohne_adresse():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    p = next(x for x in sp if x.partei == "AfD")
    assert p.natuerliche_person is True and p.spender == "Prof. Dr. Erika Musterfrau"
    assert "Musterweg" not in p.spender and "12345" not in p.spender_ort and p.spender_ort == "Musterstadt"
    gmbh = next(x for x in sp if x.partei == "CDU")
    assert gmbh.natuerliche_person is False and gmbh.spender == "ProMinent GmbH" and gmbh.spender_ort == "Heidelberg"


def test_zuordnen_nur_organisationen_exakt():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    normen = {norm_name("Verband der Bayrischen Metall- und Elektro-Industrie e.V. (VBM)"): "vbm"}
    zu, kandidaten = zuordnen(sp, normen)
    assert [s.partei for s in zu["vbm"]] == ["CSU"]
    assert len(kandidaten) == 1 and kandidaten[0]["spender"] == "ProMinent GmbH"
    assert all("Musterfrau" not in str(k) for k in kandidaten)


def test_fetch_spenden_laedt_laufendes_jahr_neu(tmp_path):
    calls = []

    def http(url):
        calls.append(url)
        return fixture_bytes("spenden_2025_ausschnitt.html")

    fetch_spenden(tmp_path, [2024, 2026], http, pause=0, heute_jahr=2026)
    fetch_spenden(tmp_path, [2024, 2026], http, pause=0, heute_jahr=2026)
    assert calls.count(JAHR_URL.format(jahr=2024)) == 1 and calls.count(JAHR_URL.format(jahr=2026)) == 2
    sp = lade_spenden(tmp_path)
    assert {s.jahr for s in sp} == {2024, 2026} and len(sp) == 6


def test_natuerliche_person_mit_anrede_zusatz_und_co():
    # Important 7: Anrede, Namenszusätze, mehr als vier Wörter und „c/o“ sind weiterhin natürliche Personen
    for n in ["Herr Prof. Dr. Hans-Joachim Mustermann", "Wolfgang von Muster", "Kurt von Muster", "Philipp Graf Muster von Musterhausen",
              "Gabriele Muster c/o Muster Verwaltungs GmbH", "Frau Dr. Anna Maria Luise Musterfrau", "Herrn Dr. Max Muster"]:
        assert ist_natuerliche_person(n), n
    for n in ["Verband der Bayrischen Metall- und Elektro-Industrie e.V. (VBM)", "ProMinent GmbH", "Deutsche Bank AG", "Muster Holding SE & Co. KGaA"]:
        assert not ist_natuerliche_person(n), n


def test_organisationsformen_und_firma():
    for n in ["Athos KG", "Muster OHG", "Muster SE & Co. KGaA", "Deutsche Vermögensberatung Aktiengesellschaft DVAG", "Joh. Berenberg, Gossler & Co. KG"]:
        assert not ist_natuerliche_person(n), n
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html").replace("<span>ProMinent GmbH</span>", "<span>Firma</span><br /><span>ProMinent GmbH</span>"), 2025)
    cdu = next(x for x in sp if x.partei == "CDU")
    assert cdu.spender == "ProMinent GmbH" and cdu.natuerliche_person is False
