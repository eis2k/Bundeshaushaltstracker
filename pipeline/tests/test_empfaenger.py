from pathlib import Path

import yaml

from bhtracker.bundestag import Abgeordneter, Angabe
from bhtracker.empfaenger import (
    Stamm,
    Verbindung,
    empfaenger_aus_titeln,
    norm_name,
    ressort_zu_epl,
    slug,
    verbindungen_aus_angaben,
    verbindungssatz,
)
from bhtracker.model import BudgetRow

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual"


def row(rid: str, text: str, soll: int = 1_000_000) -> BudgetRow:
    epl, kap, titel = rid.split("-")
    return BudgetRow(jahr=2025, stand="soll", art="A", epl=epl, kap=kap, titel=titel, epl_text="", kap_text="",
                     titel_text=text, fkt="000", soll=soll)


def test_norm_name_entfernt_rechtsform_und_umlaute():
    assert norm_name("Deutsche Stiftung Weltbevölkerung (DSW)") == "deutsche stiftung weltbevoelkerung"
    assert norm_name("Goethe-Institut e. V.") == norm_name("Goethe Institut e.V.") == "goethe institut"
    assert norm_name("Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e. V.") == "fraunhofer gesellschaft zur foerderung der angewandten forschung"
    assert norm_name("meet2respect gUG (haftungsbeschränkt)") == "meet2respect"


def test_slug():
    assert slug("Goethe-Institut e. V.") == "goethe-institut"
    assert slug("Deutsche Stiftung Weltbevölkerung (DSW)") == "deutsche-stiftung-weltbevoelkerung"


def test_empfaenger_aus_titeln_erkennt_namen():
    rows = [row("04-0452-68591", 'Zuschuss an die Rundfunkanstalt Deutsche Welle""'),
            row("05-0504-68740", "Goethe-Institut e. V., München - Betrieb und operative Mittel"),
            row("11-1101-68101", "Bürgergeld"),
            row("17-1702-68604", "Zuschuss an das Deutsche Jugendinstitut e. V., München"),
            row("23-2302-68501", "Institutionelle Förderung der Engagement Global gGmbH - Betrieb")]
    e = empfaenger_aus_titeln(rows)
    assert e[norm_name("Rundfunkanstalt Deutsche Welle")][1] == ["04-0452-68591"]
    assert e[norm_name("Goethe-Institut e. V.")][0] == "Goethe-Institut e. V."
    # Titeltexte stehen im Akkusativ („an das Deutsche Jugendinstitut“); die Nominativform kommt per Alias aus empfaenger.yaml
    assert e[norm_name("Deutsche Jugendinstitut e. V.")][1] == ["17-1702-68604"]
    assert e[norm_name("Engagement Global gGmbH")][1] == ["23-2302-68501"]
    assert norm_name("Bürgergeld") not in e


def test_ressort_zu_epl_unbekannt_bleibt_none():
    r = {"ressorts": [{"epl": "30", "kurz": "BMFTR", "namen": ["Bundesministerium für Bildung und Forschung", "BMBF", "Bundesministerium für Forschung, Technologie und Raumfahrt"]}]}
    assert ressort_zu_epl("BMBF", r) == "30"
    assert ressort_zu_epl("Bundesministerium für Forschung, Technologie und Raumfahrt (BMFTR)", r) == "30"
    assert ressort_zu_epl("Stadt Köln", r) is None


def test_ressorts_yaml_deckt_alle_ministerien():
    r = yaml.safe_load((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"))
    epls = {x["epl"] for x in r["ressorts"]}
    assert {"04", "05", "06", "07", "08", "09", "10", "11", "12", "14", "15", "16", "17", "23", "25", "30"} <= epls
    assert ressort_zu_epl("Bundesministerium für Familie, Senioren, Frauen und Jugend", r) == "17"
    assert ressort_zu_epl("Bundesamt für Wirtschaft und Ausfuhrkontrolle", r) == "09"


def test_verbindung_nur_bei_exaktem_namen():
    stamm = {"deutsche-bank": Stamm("deutsche-bank", "Deutsche Bank AG", []),
             "dsw": Stamm("dsw", "Deutsche Stiftung Weltbevölkerung (DSW)", [])}
    mdb = Abgeordneter("Sanae Abdi", "SPD", "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", 1043330,
                       ["Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung"],
                       [Angabe("Funktionen in Vereinen, Verbänden und Stiftungen", "Deutsche Stiftung Weltbevölkerung (DSW)", "Hannover", "Mitglied des Parlamentarischen Beirates (ab 07.07.2025)"),
                        Angabe("Funktionen in Unternehmen", "Deutsche Bank Stiftung", "Frankfurt", "Kuratorium")], "2026-11-01", None)
    verb, kandidaten = verbindungen_aus_angaben([mdb], stamm)
    assert [v.abgleich for v in verb["dsw"]] == ["exakt"]
    assert verb["dsw"][0].funktion_beim_empfaenger.startswith("Mitglied des Parlamentarischen Beirates")
    assert verb["dsw"][0].funktion_person == "MdB, SPD" and verb["dsw"][0].quellen[0]["url"].endswith("-1043330")
    assert "deutsche-bank" not in verb
    assert any(k.empfaenger_id == "deutsche-bank" and k.organisation_text == "Deutsche Bank Stiftung" for k in kandidaten)


def test_alias_zaehlt_als_exakt():
    stamm = {"goethe-institut": Stamm("goethe-institut", "Goethe-Institut e. V.", ["Goethe-Institut"])}
    mdb = Abgeordneter("X Y", "CDU/CSU", "https://x-1", 1, [], [Angabe("Funktionen in Vereinen, Verbänden und Stiftungen", "Goethe-Institut", "München", "Mitglied des Präsidiums")], "2026-11-01", None)
    verb, _ = verbindungen_aus_angaben([mdb], stamm)
    assert verb["goethe-institut"][0].abgleich == "exakt"


def test_berufliche_taetigkeit_vorher_erzeugt_keine_verbindung():
    stamm = {"giz": Stamm("giz", "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH", [])}
    mdb = Abgeordneter("Sanae Abdi", "SPD", "https://x-1", 1, [],
                       [Angabe("Berufliche Tätigkeit vor der Mitgliedschaft im Deutschen Bundestag", "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH", "Bonn", "Projekt- und Finanzmanagerin, Rückkehrrecht")], "2026-11-01", None)
    verb, kandidaten = verbindungen_aus_angaben([mdb], stamm)
    assert verb == {} and kandidaten[0].empfaenger_id == "giz" and "vor der Mitgliedschaft" in kandidaten[0].hinweis


def test_verbindungssatz_ist_tatsachensatz():
    v = Verbindung("abgeordneter_funktion", "Sanae Abdi", "MdB, SPD", "Mitglied des Beirates (ab 07.04.2025)", "Funktionen in Unternehmen", "exakt",
                   ["Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung"], [{"kurz": "bundestag.de", "url": "https://x", "stand": "2026-11-01"}], "2026-11-01")
    s = verbindungssatz(v, "DEval gGmbH", ["Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung"])
    assert s.startswith("Sanae Abdi (MdB, SPD) ist laut bundestag.de Mitglied des Beirates (ab 07.04.2025) bei DEval gGmbH.")
    assert "Verdacht" not in s
    assert "DEval gGmbH erhielt laut Lobbyregister Mittel von: Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung" in s
    assert "Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung" in s
