from pathlib import Path

from bhtracker.bundestag import alle_bio_urls, bio_urls_aus_seite, parse_bio

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_text(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_bio_urls_aus_seite():
    urls = bio_urls_aus_seite(fixture_text("mdb_liste_seite.html"))
    assert len(urls) == 12
    assert urls[0] == "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330"


def test_parse_bio_liest_angaben_und_ausschuesse():
    a = parse_bio(fixture_text("mdb_bio_ausschnitt.html"),
                  "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "2026-11-01")
    assert a.name == "Sanae Abdi" and a.fraktion == "SPD" and a.mdb_id == 1043330 and a.stand == "2026-11-01"
    assert "Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung" in a.ausschuesse
    k = [x for x in a.angaben if x.kategorie == "Funktionen in Unternehmen"][0]
    assert k.organisation == "DEval - Deutsches Evaluierungsinstitut der Entwicklungszusammenarbeit gemeinnützige GmbH"
    assert k.ort == "Berlin" and k.funktion == "Mitglied des Beirates (ab 07.04.2025)"
    v = [x for x in a.angaben if x.kategorie == "Funktionen in Vereinen, Verbänden und Stiftungen"][0]
    assert v.organisation == "Deutsche Stiftung Weltbevölkerung (DSW)" and v.ort == "Hannover"
    b = [x for x in a.angaben if x.kategorie.startswith("Berufliche Tätigkeit")][0]
    assert b.organisation == "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH" and b.ort == "Bonn"
    assert a.hinweis is None


def test_parse_bio_ohne_angaben_bricht_nicht_ab():
    a = parse_bio(fixture_text("mdb_bio_ohne_angaben.html"), "https://www.bundestag.de/abgeordnete/biografien/X/x-1", "2026-11-01")
    assert a.angaben == [] and a.hinweis == "keine veröffentlichungspflichtigen Angaben"
    assert a.mdb_id == 1 and a.ausschuesse


def test_alle_bio_urls_stoppt_ohne_neue_links():
    seite = fixture_text("mdb_liste_seite.html")
    calls = []

    def http(url):
        calls.append(url)
        return seite.encode("utf-8")

    urls = alle_bio_urls(http, pause=0)
    assert len(urls) == 12  # zweite Seite liefert nur Bekanntes → Ende
    assert len(calls) == 2 and "offset=0" in calls[0] and "offset=12" in calls[1]


def test_parse_bio_liest_rollen_und_eintritt():
    html = fixture_text("mdb_bio_ausschnitt.html")
    html = html.replace('<h3 class="m-biography__subHeading">Ordentliches Mitglied</h3>',
                        '<h3 class="m-biography__subHeading">Vorsitzende</h3><ul class="e-linkList"><li class="e-linkList__item"><a title="Verkehrsausschuss" href="/ausschuesse/verkehr" class="a-link --inList"><span class="a-link__label">Verkehrsausschuss</span></a></li></ul>'
                        '<h3 class="m-biography__subHeading">Ordentliches Mitglied</h3>', 1)
    html = html.replace("</h1>", "</h1><p>Mitglied des Bundestages seit März 2026; vorher Landtag.</p>", 1)
    a = parse_bio(html, "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "2026-11-01")
    assert "Vorsitzende: Verkehrsausschuss" in a.aemter
    assert any(x.startswith("Ordentliches Mitglied: ") for x in a.aemter)
    assert a.mitglied_seit == "2026-03-01"
    assert "Verkehrsausschuss" in a.ausschuesse


def test_parse_bio_eintritt_nur_jahr_und_ohne_satz():
    html = fixture_text("mdb_bio_ausschnitt.html")
    assert parse_bio(html, "https://x/-1", "2026-11-01").mitglied_seit is None
    html2 = html.replace("</h1>", "</h1><p>Mitglied des Deutschen Bundestages seit 2005; von 2013 bis 2017 Vorsitzender des X.</p>", 1)
    assert parse_bio(html2, "https://x/-1", "2026-11-01").mitglied_seit == "2005"   # nur Jahr bekannt → kein Tag erfunden


def test_parse_bio_liest_nachfolger():
    # C2: die Biografie des Ausgeschiedenen nennt Austritt und Nachfolger (Link mit mdb_id oder nur Name)
    html = fixture_text("mdb_bio_ausschnitt.html").replace("</h1>",
        '</h1><p>Sanae Abdi hat auf ihre Mitgliedschaft im 21. Deutschen Bundestag verzichtet und ist mit Ablauf des 31. Mai 2026 aus dem Deutschen Bundestag ausgeschieden. '
        'Nachfolger ist der Abgeordnete <a href="/abgeordnete/biografien/B/breilmann_michael-1183252" class="a-link --inline --icon --icon-richtextInternal"><span class="a-link__label">Michael Breilmann, CDU/CSU</span><span class="a-link__label --hidden">(Interner Link)</span></a>.</p>', 1)
    a = parse_bio(html, "https://x/-1", "2026-11-01")
    assert a.ausgeschieden == "2026-05-31" and a.nachfolger_mdb_id == 1183252 and a.nachfolger_name == "Michael Breilmann"
    html2 = fixture_text("mdb_bio_ausschnitt.html").replace("</h1>",
        "</h1><p>Sanae Abdi ist mit Ablauf des 30. Juni 2025 aus dem Deutschen Bundestag ausgeschieden. Nachfolgerin ist die Abgeordnete Mayra Vriesema, Bündnis 90/Die Grünen.</p>", 1)
    b = parse_bio(html2, "https://x/-1", "2026-11-01")
    assert b.nachfolger_mdb_id is None and b.nachfolger_name == "Mayra Vriesema"
    assert parse_bio(fixture_text("mdb_bio_ausschnitt.html"), "https://x/-1", "2026-11-01").nachfolger_name is None
