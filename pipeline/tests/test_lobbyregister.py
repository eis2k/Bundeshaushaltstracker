import copy
import json
from pathlib import Path

from bhtracker.lobbyregister import (
    auswahl,
    bundeszuwendungen,
    detail_url,
    extract_profil,
    fetch_details,
    lade_profile,
    untergrenze_bund,
)

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    with open(FIXTURES / name, encoding="utf-8") as f:
        return json.load(f)


def test_extract_profil_liest_personen_zuwendungen_und_pflichtangaben():
    p = extract_profil(load_fixture("lobby_detail_R004511.json"))
    assert p.nummer == "R004511" and p.eintrag_id == 82516 and p.version == 12
    assert p.name == "Amadeu Antonio Stiftung"
    assert p.rechtsform == "Rechtsfähige Stiftung bürgerlichen Rechts" and p.sitz == "Berlin"
    assert p.stand == "2026-09-02"
    assert [x.rolle for x in p.personen].count("gesetzlicher_vertreter") == 2
    assert all(x.regierungsfunktion is None for x in p.personen)
    zb = bundeszuwendungen(p)
    assert len(p.zuwendungen) == 16  # Bund, Länder und EU zusammen
    assert len(zb) == 7 and zb[0].geber == "Bundesministerium für Familie, Senioren, Frauen und Jugend"
    assert zb[0].spanne.von == 1_040_001 and zb[0].spanne.bis == 1_050_000 and zb[0].geschaeftsjahr == "2025"
    assert untergrenze_bund(p) == sum(z.spanne.von for z in zb)
    assert p.spenden.von == 4_190_001 and p.lobbyausgaben.bis == 10_000
    assert p.jahresabschluss_url.startswith("https://www.lobbyregister.bundestag.de/media/")
    assert p.jahresabschluss_jahr == "2024"
    assert "Öffentliche Zuwendungen" in p.finanzierungsquellen
    assert p.url == "https://www.lobbyregister.bundestag.de/suche/R004511/82516"


def test_person_in_beiden_listen_wird_einmal_gefuehrt():
    d = load_fixture("lobby_detail_R004511.json")  # Reinfrank steht als Vertreter und als Interessenvertreter
    p = extract_profil(d)
    assert [x.nachname for x in p.personen].count("Reinfrank") == 1
    assert next(x for x in p.personen if x.nachname == "Reinfrank").rolle == "gesetzlicher_vertreter"


def test_regierungsfunktion_wird_uebernommen():
    d = copy.deepcopy(load_fixture("lobby_detail_R004511.json"))
    rep = d["lobbyistIdentity"]["legalRepresentatives"][0]
    rep["recentGovernmentFunctionPresent"] = True
    rep["recentGovernmentFunction"] = {
        "ended": True, "endDate": "2025-04",
        "type": {"code": "HOUSE_OF_REPRESENTATIVES", "de": "Bundestag"},
        "houseOfRepresentatives": {"function": {"code": "MEMBER", "de": "Mitglied des Deutschen Bundestages"}},
    }
    p = extract_profil(d)
    rf = p.personen[0].regierungsfunktion
    assert rf is not None
    assert rf.art == "HOUSE_OF_REPRESENTATIVES" and rf.funktion == "Mitglied des Deutschen Bundestages"
    assert rf.beendet and rf.ende == "2025-04" and rf.stelle == "Bundestag"


def test_auswahl_nur_aktive_organisationen():
    liste = load_fixture("lobby_liste_ausschnitt.json")
    paare = auswahl(liste, set())
    assert all(isinstance(nr, str) and isinstance(i, int) for nr, i in paare)
    assert len(paare) == 2  # natürliche Person fehlt
    assert ("R004511", 82516) in paare


def test_fetch_details_ueberspringt_vorhandene(tmp_path):
    calls = []

    def http(url):
        calls.append(url)
        return json.dumps(load_fixture("lobby_detail_R004511.json")).encode("utf-8")

    fetch_details(tmp_path, [("R004511", 82516)], http, pause=0)
    fetch_details(tmp_path, [("R004511", 82516)], http, pause=0)
    assert calls == [detail_url("R004511", 82516)]
    assert lade_profile(tmp_path)[0].name == "Amadeu Antonio Stiftung"
