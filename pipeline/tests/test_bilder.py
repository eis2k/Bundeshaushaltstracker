"""Stufe 4b (Spec §4.13): Porträts und Logos aus Wikidata/Commons, nur erlaubte Lizenzen, Zuordnung ohne Verwechslung."""
import json
from pathlib import Path

import pytest

from bhtracker.bilder import (
    build_bilder,
    commons_meta,
    datei_aus_url,
    fetch_bilder,
    lizenz_erlaubt,
    norm_person,
    validate_bilder,
    zuordnen_organisationen,
    zuordnen_organisationen_mit_pruefliste,
    zuordnen_personen,
)

AKTEN = [
    {"id": "anna-muster-mdb-1", "name": "Anna Muster", "sichtbar": True, "arten": ["mdb"]},
    {"id": "dr-bernd-beispiel-mdb-2", "name": "Dr. Bernd Beispiel", "sichtbar": True, "arten": ["mdb", "regierung"]},
    {"id": "carla-doppelt-mdb-3", "name": "Carla Doppelt", "sichtbar": True, "arten": ["mdb"]},
    {"id": "carla-doppelt-mdb-4", "name": "Carla Doppelt", "sichtbar": True, "arten": ["mdb"]},
    {"id": "erika-ohne-mandat", "name": "Erika Ohne Mandat", "sichtbar": True, "arten": ["regierung"]},
    {"id": "frank-vertreter", "name": "Frank Vertreter", "sichtbar": True, "arten": ["gesetzlicher_vertreter"]},
    {"id": "gerd-unsichtbar-mdb-5", "name": "Gerd Unsichtbar", "sichtbar": False, "arten": ["mdb"]},
]
MDB = [
    {"qid": "Q1", "label": "Anna Muster", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Anna%20Muster%202025.jpg"},
    {"qid": "Q2", "label": "Bernd Beispiel", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Bernd.jpg"},
    {"qid": "Q3", "label": "Carla Doppelt", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Carla.jpg"},
    {"qid": "Q5", "label": "Gerd Unsichtbar", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Gerd.jpg"},
    {"qid": "Q6", "label": "Frank Vertreter", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Frank.jpg"},
]
SUCHE = {
    "Erika Ohne Mandat": [{"qid": "Q7", "label": "Erika Ohne Mandat", "beschreibung": "deutsche Politikerin (CDU)", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Erika.jpg"}],
}
LEER = {"stand": "2026-11-02", "zuordnungen": [], "gesperrt": []}


def test_lizenz_erlaubt():
    assert lizenz_erlaubt("CC BY-SA 4.0") and lizenz_erlaubt("CC BY 3.0 de") and lizenz_erlaubt("CC0") and lizenz_erlaubt("Public domain")
    assert not lizenz_erlaubt("CC BY-NC 2.0") and not lizenz_erlaubt("CC BY-NC-SA 4.0") and not lizenz_erlaubt("GFDL") and not lizenz_erlaubt("") and not lizenz_erlaubt("Fair use")


def test_norm_person_entfernt_titel():
    assert norm_person("Dr. Johann David Wadephul") == "johann david wadephul"
    assert norm_person("Prof. Dr. h. c.  Anna  Müller") == "anna müller"
    assert norm_person("Dipl.-Ing. Max Mustermann") == "max mustermann"


def test_datei_aus_url():
    assert datei_aus_url("http://commons.wikimedia.org/wiki/Special:FilePath/Anna%20Muster%202025.jpg") == "Anna Muster 2025.jpg"


def test_zuordnen_personen_nur_eindeutig():
    treffer, pruefliste = zuordnen_personen(AKTEN, MDB, SUCHE, LEER)
    assert treffer["anna-muster-mdb-1"] == {"qid": "Q1", "datei": "Anna Muster 2025.jpg"}
    assert treffer["dr-bernd-beispiel-mdb-2"]["qid"] == "Q2"            # Titel ignoriert
    assert treffer["erika-ohne-mandat"]["qid"] == "Q7"                   # Regierungsmitglied ohne Mandat über die Suche
    assert "carla-doppelt-mdb-3" not in treffer and "carla-doppelt-mdb-4" not in treffer   # gleicher Name zweimal im Index
    assert "frank-vertreter" not in treffer                              # kein Amt, keine Suche
    assert "gerd-unsichtbar-mdb-5" not in treffer                        # nicht sichtbar
    gruende = {p["akte_id"]: p["grund"] for p in pruefliste}
    assert "carla-doppelt-mdb-3" in gruende and "mehrdeutig" in gruende["carla-doppelt-mdb-3"]


def test_zuordnen_personen_wikidata_doppelt_und_suche_mehrdeutig():
    mdb = MDB + [{"qid": "Q11", "label": "Anna Muster", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Andere.jpg"}]
    suche = {"Erika Ohne Mandat": SUCHE["Erika Ohne Mandat"] + [{"qid": "Q8", "label": "Erika Ohne Mandat", "beschreibung": "deutsche Politikerin (SPD)", "bild": None}]}
    treffer, pruefliste = zuordnen_personen(AKTEN, mdb, suche, LEER)
    assert "anna-muster-mdb-1" not in treffer and "erika-ohne-mandat" not in treffer
    kandidaten = {p["akte_id"]: p["kandidaten"] for p in pruefliste}
    assert kandidaten["anna-muster-mdb-1"] == ["Q1", "Q11"]
    assert kandidaten["erika-ohne-mandat"] == ["Q7", "Q8"]


def test_zuordnen_personen_manuell_und_gesperrt():
    manual = {"stand": "2026-11-02", "zuordnungen": [{"akte_id": "carla-doppelt-mdb-3", "qid": "Q3", "quelle": "https://www.wikidata.org/wiki/Q3"}], "gesperrt": [{"id": "anna-muster-mdb-1", "grund": "Bild veraltet"}]}
    treffer, _ = zuordnen_personen(AKTEN, MDB, SUCHE, manual)
    assert treffer["carla-doppelt-mdb-3"]["qid"] == "Q3"
    assert "anna-muster-mdb-1" not in treffer
    suche_ohne_politik = {"Erika Ohne Mandat": [{"qid": "Q9", "label": "Erika Ohne Mandat", "beschreibung": "Schauspielerin", "bild": "x"}]}
    treffer2, _ = zuordnen_personen(AKTEN, MDB, suche_ohne_politik, LEER)
    assert "erika-ohne-mandat" not in treffer2


def test_zuordnen_organisationen_nur_ueber_lobbyregister_id():
    empf = [{"id": "verein-a", "lobbyregister": "R000001"}, {"id": "verein-b", "lobbyregister": "R000002"}, {"id": "ohne", "lobbyregister": None}, {"id": "gesperrt", "lobbyregister": "R000004"}]
    lobby = [{"qid": "Q21", "lr": "R000001", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/A%20Logo.svg"},
             {"qid": "Q22", "lr": "R000002", "logo": None},
             {"qid": "Q24", "lr": "R000004", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/G.svg"}]
    manual = {**LEER, "gesperrt": [{"id": "gesperrt", "grund": "Marke beanstandet"}]}
    t = zuordnen_organisationen(empf, lobby, manual)
    assert t == {"verein-a": {"qid": "Q21", "datei": "A Logo.svg"}}


def _info(lizenz: str, artist: str = '<a href="//commons.wikimedia.org/wiki/User:Foto">Foto Grafin</a>', url: str | None = None) -> dict:
    return {"title": "File:Anna Muster 2025.jpg", "imageinfo": [{"thumburl": "https://upload.wikimedia.org/x/96px-Anna.jpg?utm_source=commons", "url": "https://upload.wikimedia.org/x/Anna.jpg",
            "extmetadata": {"LicenseShortName": {"value": lizenz}, "Artist": {"value": artist}, "AttributionRequired": {"value": "true"}, "LicenseUrl": {"value": url or "https://creativecommons.org/licenses/by-sa/4.0"}}}]}


def test_commons_meta_lizenz_und_urheber():
    m = commons_meta("Anna Muster 2025.jpg", _info("CC BY-SA 4.0"))
    assert m["urheber"] == "Foto Grafin" and m["lizenz"] == "CC BY-SA 4.0"
    assert m["url"] == "https://upload.wikimedia.org/x/96px-Anna.jpg"
    assert m["url_gross"] == "https://commons.wikimedia.org/wiki/Special:FilePath/Anna%20Muster%202025.jpg?width=256"
    assert m["seite"] == "https://commons.wikimedia.org/wiki/File:Anna_Muster_2025.jpg"
    assert commons_meta("Anna Muster 2025.jpg", _info("CC BY-NC 2.0")) is None
    assert commons_meta("Anna Muster 2025.jpg", _info("CC BY-SA 4.0", artist="")) is None       # Namensnennung nötig, Urheber fehlt
    assert commons_meta("Anna Muster 2025.jpg", _info("CC0", artist=""))["urheber"] == "unbekannt"


def test_validate_bilder():
    assert validate_bilder(LEER) == []
    assert validate_bilder({"zuordnungen": [{"akte_id": "x"}], "gesperrt": [{"grund": "y"}]})


def _raw(tmp_path: Path) -> Path:
    raw = tmp_path / "raw" / "bilder"
    raw.mkdir(parents=True)
    (raw / "mdb.json").write_text(json.dumps(MDB), encoding="utf-8")
    (raw / "lobby.json").write_text(json.dumps([{"qid": "Q21", "lr": "R000001", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/A%20Logo.svg"}]), encoding="utf-8")
    (raw / "suche.json").write_text(json.dumps(SUCHE), encoding="utf-8")
    (raw / "commons.json").write_text(json.dumps({
        "Anna Muster 2025.jpg": _info("CC BY-SA 4.0"), "Bernd.jpg": _info("CC BY-NC 2.0"), "Erika.jpg": _info("CC BY 4.0"),
        "A Logo.svg": _info("Public domain", artist="Verein A"),
    }), encoding="utf-8")
    (raw / "stand.json").write_text(json.dumps({"stand": "2026-11-02"}), encoding="utf-8")
    return tmp_path / "raw"


def test_build_bilder_schreibt_verweise_pruefliste_und_verworfen(tmp_path):
    raw = _raw(tmp_path)
    manual = tmp_path / "manual"; manual.mkdir()
    (manual / "bilder.yaml").write_text('stand: "2026-11-02"\nzuordnungen: []\ngesperrt: []\n', encoding="utf-8")
    out = tmp_path / "build"; out.mkdir()
    erg = build_bilder(manual, raw, out, AKTEN, [{"id": "verein-a", "lobbyregister": "R000001"}], "2026-11-02")
    b = json.loads((out / "bilder.json").read_text(encoding="utf-8"))
    assert b["personen"]["anna-muster-mdb-1"]["lizenz"] == "CC BY-SA 4.0" and b["personen"]["anna-muster-mdb-1"]["art"] == "person"
    assert b["personen"]["anna-muster-mdb-1"]["qid"] == "Q1"
    assert "dr-bernd-beispiel-mdb-2" not in b["personen"]                      # CC BY-NC verworfen
    assert any(v["id"] == "dr-bernd-beispiel-mdb-2" and v["lizenz"] == "CC BY-NC 2.0" for v in b["verworfen"])
    assert b["organisationen"]["verein-a"]["art"] == "organisation" and b["organisationen"]["verein-a"]["urheber"] == "Verein A"
    assert any(p["akte_id"] == "carla-doppelt-mdb-3" for p in b["pruefliste"])
    assert erg == {"personen": 2, "organisationen": 1, "pruefliste": 2, "verworfen": 1, "ohne_bild": 3}   # Bernd (verworfen), Carla ×2 (mehrdeutig)


def test_build_bilder_ohne_rohdaten_schreibt_nichts(tmp_path):
    out = tmp_path / "build"; out.mkdir()
    assert build_bilder(tmp_path / "manual", tmp_path / "raw", out, AKTEN, [], "2026-11-02") is None
    assert not (out / "bilder.json").exists()   # ohne Rohdaten entsteht keine Datei; eine vorhandene bleibt (siehe unten)


def test_fetch_bilder_schreibt_rohdateien_und_fragt_commons_in_bloecken(tmp_path):
    aufrufe: list[str] = []

    def http(url: str) -> bytes:
        aufrufe.append(url)
        if "query.wikidata.org" in url and "P10301" in url:
            return json.dumps({"results": {"bindings": [{"item": {"value": "http://www.wikidata.org/entity/Q21"}, "lr": {"value": "R000001"}, "logo": {"value": "http://commons.wikimedia.org/wiki/Special:FilePath/A%20Logo.svg"}}]}}).encode()
        if "query.wikidata.org" in url:
            return json.dumps({"results": {"bindings": [{"item": {"value": f"http://www.wikidata.org/entity/Q{i}"}, "itemLabel": {"value": f"Person {i}"}, "bild": {"value": f"http://commons.wikimedia.org/wiki/Special:FilePath/P{i}.jpg"}} for i in range(1, 61)]}}).encode()
        if "wbsearchentities" in url:
            return json.dumps({"search": [{"id": "Q7", "label": "Erika Ohne Mandat", "description": "deutsche Politikerin"}]}).encode()
        if "wbgetentities" in url:
            return json.dumps({"entities": {"Q7": {"claims": {"P18": [{"mainsnak": {"datavalue": {"value": "Erika.jpg"}}}]}}}}).encode()
        if "commons.wikimedia.org" in url:
            n = url.count("File%3A")
            return json.dumps({"query": {"pages": {str(i): {"title": f"File:X{i}.jpg", "imageinfo": [{"thumburl": "t", "extmetadata": {}}]} for i in range(n)}}}).encode()
        raise AssertionError(url)

    akten = [{"id": "p1", "name": "Person 1", "sichtbar": True, "arten": ["mdb"]}, {"id": "erika-ohne-mandat", "name": "Erika Ohne Mandat", "sichtbar": True, "arten": ["regierung"]}]
    erg = fetch_bilder(tmp_path / "raw", akten, [{"id": "verein-a", "lobbyregister": "R000001"}], http=http, pause=0)
    raw = tmp_path / "raw" / "bilder"
    assert {p.name for p in raw.iterdir()} >= {"mdb.json", "lobby.json", "suche.json", "commons.json", "stand.json"}
    assert erg["mdb"] == 60 and erg["lobby"] == 1 and erg["suche"] == 1
    commons = [u for u in aufrufe if "commons.wikimedia.org" in u]
    assert len(commons) == 2 and all(u.count("File%3A") <= 50 for u in commons)    # 60 Porträts + 1 Logo + Erika = 62 Dateien → 2 Blöcke
    suche = json.loads((raw / "suche.json").read_text(encoding="utf-8"))
    assert suche["Erika Ohne Mandat"][0]["bild"] == "Erika.jpg"


def test_zuordnen_personen_mehrere_bilder_je_item_sind_kein_konflikt():
    # SPARQL liefert je P18-Wert eine Zeile; dasselbe Item zweimal darf nicht als „mehrdeutig“ gelten
    mdb = MDB + [{"qid": "Q1", "label": "Anna Muster", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/Anna%20Muster%202023.jpg"}]
    treffer, pruefliste = zuordnen_personen(AKTEN, mdb, SUCHE, LEER)
    assert treffer["anna-muster-mdb-1"]["qid"] == "Q1"
    assert not any(p["akte_id"] == "anna-muster-mdb-1" for p in pruefliste)


# ---------------------------------------------------------------- Fix-Pass nach Review
def test_norm_person_laesst_vornamen_mit_titelkuerzel_in_ruhe():
    assert norm_person("Ingrid Pahlmann") == "ingrid pahlmann"
    assert norm_person("Philipp Amthor") == "philipp amthor"
    assert norm_person("Falko Droßmann") == "falko droßmann"
    assert norm_person("Dr. Ingrid Pahlmann-Drossmann") == "ingrid pahlmann-drossmann"


def test_suche_nur_mit_gleichem_label_und_auch_englischer_beschreibung():
    suche = {"Erika Ohne Mandat": [
        {"qid": "Q7", "label": "Erika Ohne Mandat", "beschreibung": "German politician (CDU)", "bild": "Erika.jpg"},
        {"qid": "Q8", "label": "Erika Ohne Mandat-Meier", "beschreibung": "deutsche Politikerin", "bild": "Andere.jpg"},   # Alias/Namensanfang: anderes Label
    ]}
    treffer, pruefliste = zuordnen_personen(AKTEN, MDB, suche, LEER)
    assert treffer["erika-ohne-mandat"] == {"qid": "Q7", "datei": "Erika.jpg"}
    assert not any(p["akte_id"] == "erika-ohne-mandat" for p in pruefliste)


def test_regierungsmitglied_ohne_mandat_nimmt_kein_abgeordnetenbild_gleichen_namens():
    akten = [{"id": "x-y-breg", "name": "X Y", "sichtbar": True, "arten": ["regierung"]}]
    mdb = [{"qid": "Q99", "label": "X Y", "bild": "http://commons.wikimedia.org/wiki/Special:FilePath/X.jpg"}]
    treffer, _ = zuordnen_personen(akten, mdb, {}, LEER)
    assert treffer == {}


def test_commons_meta_unbekannter_urheber_und_attribution():
    versteckt = 'Unknown author<span style="display: none;">Unknown author</span>'
    assert commons_meta("A.jpg", _info("CC BY 4.0", artist=versteckt)) is None
    assert commons_meta("A.jpg", _info("Public domain", artist=versteckt))["urheber"] == "unbekannt"
    info = _info("CC BY-SA 4.0", artist='<a href="x">Foto Grafin</a>')
    info["imageinfo"][0]["extmetadata"]["Attribution"] = {"value": "Foto Grafin / Agentur, CC BY-SA 4.0"}
    assert commons_meta("A.jpg", info)["urheber"] == "Foto Grafin / Agentur, CC BY-SA 4.0"
    lang = _info("CC BY-SA 4.0", artist="A" * 130)
    assert commons_meta("A.jpg", lang)["urheber"].endswith("…") and len(commons_meta("A.jpg", lang)["urheber"]) == 120
    info2 = _info("CC BY 4.0"); info2["imageinfo"][0]["extmetadata"]["Restrictions"] = {"value": "trademarked"}
    assert commons_meta("A.jpg", info2)["restriktionen"] == "trademarked"
    ohne_thumb = _info("CC0", artist=""); del ohne_thumb["imageinfo"][0]["thumburl"]
    assert commons_meta("A.jpg", ohne_thumb)["url"] == "https://commons.wikimedia.org/wiki/Special:FilePath/A.jpg?width=120"


def test_build_bilder_ohne_rohdaten_behaelt_alte_datei(tmp_path, capsys):
    out = tmp_path / "build"; out.mkdir()
    (out / "bilder.json").write_text('{"personen": {}}', encoding="utf-8")
    assert build_bilder(tmp_path / "manual", tmp_path / "raw", out, AKTEN, [], "2026-11-02") is None
    assert (out / "bilder.json").exists()
    assert "fetch-bilder" in capsys.readouterr().err


def test_organisation_item_mit_mehreren_nummern_kommt_in_pruefliste():
    empf = [{"id": "mutter", "lobbyregister": "R000001"}, {"id": "tochter", "lobbyregister": "R000002"}, {"id": "andere", "lobbyregister": "R000003"}]
    lobby = [{"qid": "Q1", "lr": "R000001", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/K.svg"},
             {"qid": "Q1", "lr": "R000002", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/K.svg"},
             {"qid": "Q3", "lr": "R000003", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/B.svg"},
             {"qid": "Q3", "lr": "R000003", "logo": "http://commons.wikimedia.org/wiki/Special:FilePath/A.svg"}]
    treffer, pruefliste = zuordnen_organisationen_mit_pruefliste(empf, lobby, LEER)
    assert "mutter" not in treffer and "tochter" not in treffer
    assert treffer["andere"]["datei"] == "A.svg"          # mehrere Logos: deterministisch das alphabetisch erste
    assert {p["id"] for p in pruefliste} == {"mutter", "tochter"}


def test_validate_bilder_verlangt_fundstelle():
    assert validate_bilder({"zuordnungen": [{"akte_id": "x", "qid": "Q1"}]})
    assert validate_bilder({"zuordnungen": [{"akte_id": "x", "qid": "Q1", "quelle": "https://www.wikidata.org/wiki/Q1"}]}) == []


def test_build_bilder_zaehlt_ohne_bild(tmp_path):
    raw = _raw(tmp_path)
    out = tmp_path / "build"; out.mkdir()
    erg = build_bilder(tmp_path / "manual", raw, out, AKTEN, [{"id": "verein-a", "lobbyregister": "R000001"}], "2026-11-02")
    b = json.loads((out / "bilder.json").read_text(encoding="utf-8"))
    assert erg["ohne_bild"] == b["ohne_bild"]["anzahl"] and b["ohne_bild"]["anzahl"] >= 1
    assert "carla-doppelt-mdb-3" in b["ohne_bild"]["ids"]
