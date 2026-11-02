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


def test_empfaenger_aus_titeln_zufuehrung_und_baumassnahme():
    rows = [row("07-0705-68601", "Zuführung an die Stiftung Forum Recht"),
            row("04-0452-89401", "Baumaßnahme Stiftung Denkmal für die ermordeten Juden Europas"),
            row("04-0452-68531", "Beitrag an die Stiftung Preußischer Kulturbesitz")]
    e = empfaenger_aus_titeln(rows)
    assert e[norm_name("Stiftung Forum Recht")][1] == ["07-0705-68601"]
    assert e[norm_name("Stiftung Denkmal für die ermordeten Juden Europas")][1] == ["04-0452-89401"]
    assert e[norm_name("Stiftung Preußischer Kulturbesitz")][1] == ["04-0452-68531"]


def test_empfaenger_aus_titeln_verwirft_zwecke_und_satzreste():
    rows = [row("11-1102-63681", "Zuschuss des Bundes an die allgemeine Rentenversicherung"),
            row("60-6002-68301", "Zuschüsse zur Entlastung beim Strompreis"),
            row("60-6002-68302", "Zuschüsse an stromintensive Unternehmen"),
            row("12-1210-89101", "Zuweisungen gemäß LuKIFG"),
            row("60-6002-63401", "Zuweisungen an den Klima- und Transformationsfonds"),
            row("09-0910-68301", "Zuschüsse zu den Übertragungsnetzkosten"),
            row("04-0452-68591", 'Zuschuss an die Rundfunkanstalt Deutsche Welle""'),
            row("06-0601-68501", "Zuschuss an den Bundesnachrichtendienst"),
            row("60-6002-68501", "Zuschuss an die Postbeamtenversorgungskasse")]
    e = empfaenger_aus_titeln(rows)
    namen = {v[0] for v in e.values()}
    assert "Rundfunkanstalt Deutsche Welle" in namen
    assert "Bundesnachrichtendienst" in namen and "Postbeamtenversorgungskasse" in namen
    for falsch in ("Bundes an die allgemeine Rentenversicherung", "zur Entlastung beim Strompreis", "stromintensive Unternehmen",
                   "gemäß LuKIFG", "zu den Übertragungsnetzkosten", "Klima- und Transformationsfonds"):
        assert falsch not in namen, falsch
    assert len(e) == 3


def test_verbindungssatz_je_kategorie_keine_falschen_funktionen():
    # Review Stufe 2, Befund 2: Spenden, entgeltliche Tätigkeiten und beendete Tätigkeiten dürfen nicht als Funktion formuliert werden
    def v(kategorie, funktion):
        return Verbindung("abgeordneter_funktion", "Max Muster", "MdB, SPD", funktion, kategorie, "exakt", [], [{"kurz": "bundestag.de", "url": "https://x", "stand": "2026-11-01"}], "2026-11-01")
    spende = verbindungssatz(v("Spenden und sonstige Zuwendungen", "Übernahme Reisekosten, 2025, 3.507,38 EUR"), "ELNET Deutschland e.V.", [])
    assert spende.startswith("Max Muster (MdB, SPD) hat laut bundestag.de eine Zuwendung von ELNET Deutschland e.V. angezeigt: „Übernahme Reisekosten, 2025, 3.507,38 EUR“.")
    taetig = verbindungssatz(v("Entgeltliche Tätigkeiten neben dem Mandat", "Arbeiter (bis 08.05.2025)"), "Volkswagen AG", [])
    assert taetig.startswith("Max Muster (MdB, SPD) übte laut bundestag.de eine entgeltliche Tätigkeit bei Volkswagen AG aus: „Arbeiter (bis 08.05.2025)“.")
    vereinb = verbindungssatz(v("Vereinbarungen über künftige Tätigkeiten oder Vermögensvorteile", "Vergünstigter Telekomvertrag"), "Deutsche Telekom AG", [])
    assert "hat laut bundestag.de eine Vereinbarung mit Deutsche Telekom AG angezeigt" in vereinb
    beendet = verbindungssatz(v("Funktionen in Unternehmen", "Mitglied des Aufsichtsrates (bis 11.07.2025)"), "DB InfraGO AG", [])
    assert beendet.startswith("Max Muster (MdB, SPD) war laut bundestag.de Mitglied des Aufsichtsrates (bis 11.07.2025) bei DB InfraGO AG.")
    laufend = verbindungssatz(v("Funktionen in Vereinen, Verbänden und Stiftungen", "Mitglied des Beirates (ab 07.04.2025)"), "DEval gGmbH", [])
    assert laufend.startswith("Max Muster (MdB, SPD) ist laut bundestag.de Mitglied des Beirates (ab 07.04.2025) bei DEval gGmbH.")
    sonst = verbindungssatz(v("Beteiligungen an Kapital- oder Personengesellschaften", "Kommanditist"), "X KG", [])
    assert "hält laut bundestag.de eine Beteiligung an X KG: „Kommanditist“" in sonst


def test_ressort_zu_epl_ohne_rueckwaerts_praefix_und_exakte_aliasse():
    # Review Stufe 2, Befund 3: „Bund“ und „Bundesrepublik Deutschland“ dürfen nur exakt greifen
    r = {"ressorts": [{"epl": "60", "kurz": "AFV", "exakt": True, "namen": ["Allgemeine Finanzverwaltung", "Bundesrepublik Deutschland", "Bund"]},
                      {"epl": "12", "kurz": "BMV", "namen": ["Bundesministerium für Verkehr", "BMV"]}]}
    assert ressort_zu_epl("Bund", r) == "60"
    assert ressort_zu_epl("Bundesrepublik Deutschland - BMV", r) is None
    assert ressort_zu_epl("Bund/BMBF", r) is None
    assert ressort_zu_epl("Bundesministerium für Verkehr (BMV)", r) == "12"
    assert ressort_zu_epl("Bundesministerium", r) is None   # Name kürzer als Alias: kein Rückwärts-Präfix


def test_laufende_regierungsfunktion_auf_der_empfaenger_seite():
    # Fix-Pass Nacharbeiten: laufende Funktion (ended False) heißt nicht „früher“ und der Satz behauptet kein „zuvor“
    from bhtracker.empfaenger import verbindungen_aus_profil, verbindungssatz
    from bhtracker.lobbyregister import Person, Regierungsfunktion, extract_profil
    import dataclasses, json
    p = extract_profil(json.loads((Path(__file__).parent / "fixtures" / "lobby_detail_R004511.json").read_text(encoding="utf-8")))
    lauf = Person("Kappert", "Kirsten", "Vorstand", "gesetzlicher_vertreter", Regierungsfunktion("HOUSE_OF_REPRESENTATIVES", "Mitglied des Deutschen Bundestages", "Deutscher Bundestag", False, None))
    alt = Person("Alt", "Bert", "Vorstand", "gesetzlicher_vertreter", Regierungsfunktion("STATE_SECRETARY", "Staatssekretär", "Bundesministerium X", True, "2021-12-08"))
    p2 = dataclasses.replace(p, personen=[lauf, alt])
    v = {x.person: x for x in verbindungen_aus_profil(p2)}
    assert v["Kirsten Kappert"].kategorie.startswith("Laufende") and v["Bert Alt"].kategorie.startswith("Frühere")
    s1 = verbindungssatz(v["Kirsten Kappert"], "Verein X", [])
    s2 = verbindungssatz(v["Bert Alt"], "Verein X", [])
    assert "hat zugleich eine öffentliche Funktion" in s1 and "zuvor" not in s1
    assert "hatte zuvor eine öffentliche Funktion" in s2 and "bis 2021-12-08" in s2


def test_aufteilung_je_epl_trennt_quellen_und_einzelplaene():
    # Review C2 (Stufe 4c): Beträge je Einzelplan und Quelle; Förderkatalog-Ressorts sind keine Geldquelle
    from bhtracker.empfaenger import aufteilung_je_epl
    titel = [{"id": "04-0401-68501", "epl": "04", "werte": {"2025": {"soll": 300.0, "ist": None}, "2026": {"soll": 395.4, "ist": None}}},
             {"id": "05-0502-68701", "epl": "05", "werte": {"2026": {"soll": 10.0, "ist": None}}},
             {"id": "04-0401-68502", "epl": "04", "werte": {"2025": {"soll": 1.0, "ist": None}}}]
    lobby = [{"geber": "BMWE", "epl": "09", "von": 1_880_000, "bis": 1_890_000}, {"geber": "BMV", "epl": "12", "von": 470_000, "bis": 480_000},
             {"geber": "BMWE", "epl": "09", "von": 10, "bis": 20}, {"geber": "Unbekannt", "epl": None, "von": 5, "bis": 5}]
    haushalt, lob = aufteilung_je_epl(titel, lobby, 2026)
    assert haushalt == {"04": 395.4, "05": 10.0}
    assert lob == {"09": 1_880_010, "12": 470_000}
    assert aufteilung_je_epl(titel, [], None) == ({}, {})
