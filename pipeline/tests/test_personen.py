import dataclasses
import json
from pathlib import Path

import pytest
import yaml

from bhtracker.bundestag import parse_bio
from bhtracker.lobbyregister import Person, Profil, Regierungsfunktion, extract_profil
from bhtracker.personen import (
    Akte,
    build_personen,
    ergaenze_akten,
    validate_personen,
    roh_identitaeten,
    shard,
    sichtbarkeit,
    zusammenfuehren,
)
from bhtracker.regierung import Amtstraeger
from bhtracker.spenden import Spende

FIXTURES = Path(__file__).parent / "fixtures"
MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual"


def profil_aas() -> Profil:
    return extract_profil(json.loads((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8")))


def profil_mit(name: str, nummer: str, personen: list[Person], mitgliedschaften: list[str] | None = None) -> Profil:
    p = profil_aas()
    return dataclasses.replace(p, name=name, nummer=nummer, eintrag_id=1, url=f"https://www.lobbyregister.bundestag.de/suche/{nummer}/1",
                               personen=personen, mitgliedschaften=mitgliedschaften or [])


def mdb_abdi():
    return parse_bio((FIXTURES / "mdb_bio_ausschnitt.html").read_text(encoding="utf-8"),
                     "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "2026-11-01")


def kanzler() -> Amtstraeger:
    return Amtstraeger("Friedrich Merz", "Bundeskanzler", "Bundeskanzleramt", "04", "2025-05-06", None,
                       "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/friedrich-merz-2342660", "2026-11-02", None)


def akte(id: str = "x", amt: bool = False) -> Akte:
    return Akte(id=id, name="X Y", quellen_ids=[id], funktionen=[], amt=amt, verbindung=False, freigabe=False, sichtbar=False,
                gleichnamig=[], angaben=[], organisationen=[], spenden=[], zeitlinie=[], quellen=[], stand="2026-11-02")


def test_shard_ist_stabil_und_zweistellig():
    assert shard("sanae-abdi") == shard("sanae-abdi") and len(shard("sanae-abdi")) == 2
    assert shard("a") != shard("b")


def test_roh_identitaeten_je_quelle():
    akten = roh_identitaeten([profil_aas()], [mdb_abdi()], [kanzler()])
    ids = {a.id for a in akten}
    assert {"timo-reinfrank-lr-r004511", "tahera-ameer-lr-r004511", "sanae-abdi-mdb-1043330", "friedrich-merz-breg"} <= ids
    abdi = next(a for a in akten if a.id == "sanae-abdi-mdb-1043330")
    assert abdi.amt is True and abdi.funktionen[0].art == "mdb" and "SPD" in abdi.funktionen[0].text
    assert len(abdi.angaben) >= 3 and abdi.funktionen[0].ausschuesse
    merz = next(a for a in akten if a.id == "friedrich-merz-breg")
    assert merz.amt is True and merz.funktionen[0].art == "regierung" and merz.funktionen[0].epl == "04"
    reinfrank = next(a for a in akten if a.id == "timo-reinfrank-lr-r004511")
    assert reinfrank.amt is False and reinfrank.funktionen[0].art == "gesetzlicher_vertreter" and reinfrank.funktionen[0].organisation_id == "amadeu-antonio-stiftung"


def test_gleicher_name_ohne_beleg_bleibt_getrennt():
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Reinfrank", "Timo", "Vorstand", "gesetzlicher_vertreter", None)])
    profile = [profil_aas(), p2]
    akten, kandidaten = zusammenfuehren(roh_identitaeten(profile, [], []), {p.nummer: p for p in profile}, {})
    reinfrank = [a for a in akten if a.name == "Timo Reinfrank"]
    assert len(reinfrank) == 2
    assert all(len(a.gleichnamig) == 1 for a in reinfrank)
    assert any(k["name"] == "Timo Reinfrank" for k in kandidaten)


def test_gegenseitige_nennung_fuehrt_zusammen():
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Reinfrank", "Timo", "Vorstand", "gesetzlicher_vertreter", None)],
                    mitgliedschaften=["Amadeu Antonio Stiftung"])
    profile = [profil_aas(), p2]
    akten, _ = zusammenfuehren(roh_identitaeten(profile, [], []), {p.nummer: p for p in profile}, {})
    reinfrank = [a for a in akten if a.name == "Timo Reinfrank"]
    assert len(reinfrank) == 1
    assert sorted(reinfrank[0].quellen_ids) == ["timo-reinfrank-lr-r004511", "timo-reinfrank-lr-r009999"]
    assert reinfrank[0].id == "timo-reinfrank"


def test_mdb_angabe_fuehrt_mit_lobbyregister_zusammen():
    deval = profil_mit("DEval - Deutsches Evaluierungsinstitut der Entwicklungszusammenarbeit gemeinnützige GmbH", "R007777",
                       [Person("Abdi", "Sanae", "Mitglied des Beirates", "gesetzlicher_vertreter", None)])
    akten, _ = zusammenfuehren(roh_identitaeten([deval], [mdb_abdi()], []), {deval.nummer: deval}, {})
    abdi = [a for a in akten if a.name == "Sanae Abdi"]
    assert len(abdi) == 1 and abdi[0].id == "sanae-abdi" and {f.art for f in abdi[0].funktionen} == {"mdb", "gesetzlicher_vertreter"}


def test_manuell_trennen_schlaegt_regel():
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Reinfrank", "Timo", "Vorstand", "gesetzlicher_vertreter", None)],
                    mitgliedschaften=["Amadeu Antonio Stiftung"])
    profile = [profil_aas(), p2]
    manual = {"trennen": [{"ids": ["timo-reinfrank-lr-r004511", "timo-reinfrank-lr-r009999"], "quelle": "https://x"}]}
    akten, _ = zusammenfuehren(roh_identitaeten(profile, [], []), {p.nummer: p for p in profile}, manual)
    assert len([a for a in akten if a.name == "Timo Reinfrank"]) == 2


def test_sichtbarkeit_regeln():
    assert sichtbarkeit(akte(amt=True), set(), {}, "relevant") is True
    assert sichtbarkeit(akte("x"), {"x"}, {}, "relevant") is True
    assert sichtbarkeit(akte("y"), set(), {}, "relevant") is False
    assert sichtbarkeit(akte("y"), set(), {"freigabe": [{"id": "y", "quelle": "https://x"}]}, "relevant") is True
    assert sichtbarkeit(akte("y"), set(), {}, "alle") is True


def _seiten() -> dict[str, dict]:
    return {"amadeu-antonio-stiftung": {"id": "amadeu-antonio-stiftung", "name": "Amadeu Antonio Stiftung", "lobby_untergrenze_bund": 3_700_000,
                                        "haushalt": {"titel": []}, "lobby_zuwendungen": [{"geber": "BMBFSFJ", "epl": "17", "von": 1_040_001, "bis": 1_050_000, "zweck": "", "geschaeftsjahr": "2025"}],
                                        "foerderkatalog": [], "personen": [{"name": "Timo Reinfrank"}, {"name": "Tahera Ameer"}],
                                        "verbindungen": [{"typ": "regierungsfunktion", "person": "Tahera Ameer"}]}}


def test_build_personen_schreibt_shards_und_index(tmp_path):
    raw = tmp_path / "raw"
    (raw / "lobbyregister").mkdir(parents=True)
    (raw / "lobbyregister" / "R004511_82516.json").write_text((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8"), encoding="utf-8")
    (raw / "bundestag").mkdir()
    (raw / "bundestag" / "1043330.html").write_text((FIXTURES / "mdb_bio_ausschnitt.html").read_text(encoding="utf-8"), encoding="utf-8")
    (raw / "bundestag" / "1043330.url").write_text("https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", encoding="utf-8")
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "personen.yaml").write_text("zusammenfuehren: []\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    (manual / "regierung.yaml").write_text("stand: '2026-11-02'\nmitglieder: []\n", encoding="utf-8")
    (manual / "ressorts.yaml").write_text((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    spenden = [Spende(2025, "CSU", 136_000, "Amadeu Antonio Stiftung", "Berlin", "2025-12-23", "2025-12-26", "Drs. 21/4050", "https://d/x.pdf", False)]
    out = tmp_path / "build"
    idx_path = build_personen(manual, raw, out, _seiten(), spenden, "2026-11-02")
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    assert idx["modus"] == "relevant"
    assert by_id["sanae-abdi"]["sichtbar"] is True and by_id["sanae-abdi"]["amt"] is True
    assert by_id["sanae-abdi"]["arten"] == ["mdb"] and by_id["tahera-ameer"]["arten"] == ["gesetzlicher_vertreter"]
    assert by_id["timo-reinfrank"]["sichtbar"] is False
    assert by_id["tahera-ameer"]["sichtbar"] is True   # Verbindung (Regierungsfunktion) auf der Empfänger-Seite
    sh = json.loads((out / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))
    abdi = sh["sanae-abdi"]
    assert abdi["funktionen"][0]["art"] == "mdb" and abdi["angaben"]
    p2 = out / "personen" / f"{by_id['timo-reinfrank']['shard']}.json"
    assert not p2.exists() or "timo-reinfrank" not in json.loads(p2.read_text(encoding="utf-8"))   # nicht sichtbar → keine Akte in der Shard-Datei
    sh3 = json.loads((out / "personen" / f"{by_id['tahera-ameer']['shard']}.json").read_text(encoding="utf-8"))
    ameer = sh3["tahera-ameer"]
    assert ameer["organisationen"][0]["id"] == "amadeu-antonio-stiftung" and ameer["organisationen"][0]["lobby_untergrenze_bund"] == 3_700_000
    assert ameer["spenden"][0]["partei"] == "CSU" and ameer["spenden"][0]["betrag"] == 136_000
    assert any(z["art"] == "geld" and z["jahr"] == 2025 for z in ameer["zeitlinie"]) and any(z["art"] == "posten" for z in ameer["zeitlinie"])
    assert all(z["quelle"] == "lobbyregister" for z in ameer["zeitlinie"] if z["art"] == "geld")
    kand = yaml.safe_load((tmp_path / "review" / "personen_kandidaten.yaml").read_text(encoding="utf-8"))
    assert "kandidaten" in kand


def test_build_personen_modus_alle(tmp_path):
    raw = tmp_path / "raw"
    (raw / "lobbyregister").mkdir(parents=True)
    (raw / "lobbyregister" / "R004511_82516.json").write_text((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8"), encoding="utf-8")
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "personen.yaml").write_text("zusammenfuehren: []\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    (manual / "ressorts.yaml").write_text((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    out = tmp_path / "build"
    idx = json.loads(build_personen(manual, raw, out, _seiten(), [], "2026-11-02", modus="alle").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    assert idx["modus"] == "alle" and by_id["timo-reinfrank"]["sichtbar"] is True
    sh = json.loads((out / "personen" / f"{by_id['timo-reinfrank']['shard']}.json").read_text(encoding="utf-8"))
    assert sh["timo-reinfrank"]["grund_sichtbar"] == "alle"


def test_ohne_personen_baut_nichts(tmp_path):
    out = tmp_path / "build"
    assert build_personen(tmp_path, tmp_path, out, {}, [], "2026-11-02", mit_personen=False) is None
    assert not (out / "personen").exists()


def test_nur_personen_von_empfaengern_mit_seite(tmp_path):
    # Spec §4.7a: Akten für Vertreter von Empfängern mit Bundesmitteln; Organisationen ohne Empfänger-Seite liefern keine Akten
    raw = tmp_path / "raw"
    (raw / "lobbyregister").mkdir(parents=True)
    (raw / "lobbyregister" / "R004511_82516.json").write_text((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8"), encoding="utf-8")
    fremd = json.loads((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8"))
    fremd["registerNumber"] = "R000001"; fremd["registerEntryDetails"]["registerEntryId"] = 1; fremd["lobbyistIdentity"]["name"] = "Fremder Verband e.V."
    fremd["lobbyistIdentity"]["legalRepresentatives"] = [{"lastName": "Fremd", "firstName": "Frieda", "function": "Vorstand", "recentGovernmentFunctionPresent": False}]
    (raw / "lobbyregister" / "R000001_1.json").write_text(json.dumps(fremd, ensure_ascii=False), encoding="utf-8")
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "personen.yaml").write_text("zusammenfuehren: []\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    (manual / "ressorts.yaml").write_text((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    seiten = _seiten()
    seiten["amadeu-antonio-stiftung"]["lobbyregister"] = {"nummer": "R004511"}
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", seiten, [], "2026-11-02", modus="alle").read_text(encoding="utf-8"))
    namen = {e["name"] for e in idx["eintraege"]}
    assert "Timo Reinfrank" in namen and "Frieda Fremd" not in namen


# ---------------------------------------------------------------- Fix-Pass nach Review (2.11.2026)

def _raw_mit_abdi(tmp_path):
    raw = tmp_path / "raw"
    (raw / "lobbyregister").mkdir(parents=True)
    (raw / "lobbyregister" / "R004511_82516.json").write_text((FIXTURES / "lobby_detail_R004511.json").read_text(encoding="utf-8"), encoding="utf-8")
    (raw / "bundestag").mkdir()
    (raw / "bundestag" / "1043330.html").write_text((FIXTURES / "mdb_bio_ausschnitt.html").read_text(encoding="utf-8"), encoding="utf-8")
    (raw / "bundestag" / "1043330.url").write_text("https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", encoding="utf-8")
    manual = tmp_path / "manual"
    manual.mkdir()
    (manual / "personen.yaml").write_text("zusammenfuehren: []\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    (manual / "regierung.yaml").write_text("stand: '2026-11-02'\nmitglieder: []\n", encoding="utf-8")
    (manual / "ressorts.yaml").write_text((MANUAL / "ressorts.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    return raw, manual


def test_ausgeschiedene_abgeordnete_tragen_ende():
    # Critical 1: „ist mit Ablauf des 31. August 2025 aus dem Deutschen Bundestag ausgeschieden“ → bis-Datum, keine Gegenwartsaussage
    html = (FIXTURES / "mdb_bio_ausschnitt.html").read_text(encoding="utf-8").replace(
        '<h1 class="m-biography__introName">Sanae Abdi</h1>',
        '<h1 class="m-biography__introName">Sanae Abdi</h1><p>Sanae Abdi hat auf ihre Mitgliedschaft im 21. Deutschen Bundestag verzichtet '
        'und ist mit Ablauf des 31. August 2025 aus dem Deutschen Bundestag ausgeschieden. <span>Nachfolgerin ist die Abgeordnete X.</span></p>')
    a = parse_bio(html, "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "2026-11-01")
    assert a.ausgeschieden == "2025-08-31" and a.hinweis and "ausgeschieden" in a.hinweis
    f = roh_identitaeten([], [a], [])[0].funktionen[0]
    assert f.bis == "2025-08-31" and f.text.startswith("Mitglied des Bundestages bis 2025-08-31")
    assert mdb_abdi().ausgeschieden is None and roh_identitaeten([], [mdb_abdi()], [])[0].funktionen[0].bis is None


def test_mdb_posten_bei_empfaenger_steht_in_akte(tmp_path):
    # Important 1: Verbindung abgeordneter_funktion (exakt) der Empfänger-Seite → Organisation der Akte, Quelle bundestag.de
    raw, manual = _raw_mit_abdi(tmp_path)
    seiten = _seiten()
    seiten["amadeu-antonio-stiftung"]["verbindungen"].append({
        "typ": "abgeordneter_funktion", "person": "Sanae Abdi", "funktion_person": "MdB, SPD", "funktion_beim_empfaenger": "Mitglied des Kuratoriums",
        "kategorie": "Funktionen in Vereinen, Verbänden und Stiftungen", "abgleich": "exakt",
        "quellen": [{"kurz": "bundestag.de", "url": "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "stand": "2026-11-01"}]})
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", seiten, [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    assert by_id["sanae-abdi"]["n_organisationen"] == 1
    sh = json.loads((tmp_path / "build" / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))
    o = sh["sanae-abdi"]["organisationen"][0]
    assert o["id"] == "amadeu-antonio-stiftung" and o["rolle"] == "abgeordneter_funktion" and o["funktion"] == "Mitglied des Kuratoriums"
    assert o["quelle"]["kurz"] == "bundestag.de" and o["lobby_untergrenze_bund"] == 3_700_000
    assert sh["sanae-abdi"]["verbindung"] is True


def test_mdb_id_fuehrt_auch_bei_namensvariante_zusammen():
    # Important 4: „Dr. Johann D. Wadephul“ (Bundestag) und „Dr. Johann Wadephul“ (Kabinett) sind mit mdb_id eine Akte
    a = dataclasses.replace(mdb_abdi(), name="Dr. Johann D. Wadephul", mdb_id=1047914)
    breg = Amtstraeger("Dr. Johann Wadephul", "Bundesminister des Auswärtigen", "Auswärtiges Amt", "05", "2025-05-06", None,
                       "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/johann-wadephul-2342698", "2026-11-02", 1047914)
    akten, kandidaten = zusammenfuehren(roh_identitaeten([], [a], [breg]), {}, {})
    assert len(akten) == 1 and akten[0].mdb_id == 1047914 and {f.art for f in akten[0].funktionen} == {"mdb", "regierung"}
    assert kandidaten == []


def test_manuelles_zusammenfuehren_ueber_namensgrenzen():
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Reinfrank-Schmidt", "Timo", "Vorstand", "gesetzlicher_vertreter", None)])
    profile = [profil_aas(), p2]
    roh = roh_identitaeten(profile, [], [])
    ids = [a.id for a in roh if a.name in ("Timo Reinfrank", "Timo Reinfrank-Schmidt")]
    assert len(ids) == 2
    manual = {"zusammenfuehren": [{"ids": ids, "quelle": "https://www.lobbyregister.bundestag.de/suche/R009999/1", "datum": "2026-11-02"}]}
    akten, _ = zusammenfuehren(roh, {p.nummer: p for p in profile}, manual)
    treffer = [a for a in akten if a.name.startswith("Timo Reinfrank")]
    assert len(treffer) == 1 and sorted(treffer[0].lr_nummern) == ["R004511", "R009999"]


def test_validate_personen_pflichtfelder():
    # Important 10
    assert validate_personen({"zusammenfuehren": [], "trennen": [], "freigabe": []}) == []
    err = validate_personen({"zusammenfuehren": [{"ids": ["a", "b"]}], "trennen": [{"ids": ["a"], "quelle": "https://x"}],
                             "freigabe": [{"id": "c", "quelle": "https://q"}]})
    assert any("quelle" in e for e in err) and any("ids" in e for e in err) and any("geprueft_von" in e for e in err)
    assert validate_personen(yaml.safe_load((MANUAL / "personen.yaml").read_text(encoding="utf-8"))) == []


def test_build_personen_bricht_bei_ungueltiger_pflegedatei_ab(tmp_path):
    raw, manual = _raw_mit_abdi(tmp_path)
    (manual / "personen.yaml").write_text("zusammenfuehren:\n  - {ids: [a, b]}\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    with pytest.raises(ValueError, match="personen.yaml"):
        build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02")


def test_ohne_personen_loescht_alte_akten(tmp_path):
    # Important 6a: ein Lauf mit --ohne-personen lässt keine Akten aus einem früheren Lauf liegen
    raw, manual = _raw_mit_abdi(tmp_path)
    out = tmp_path / "build"
    build_personen(manual, raw, out, _seiten(), [], "2026-11-02")
    assert (out / "personen" / "index.json").exists()
    assert build_personen(manual, raw, out, _seiten(), [], "2026-11-02", mit_personen=False) is None
    assert not (out / "personen").exists()


def test_committed_personen_index_ist_relevant():
    # Important 6b: das committete Verzeichnis trägt nie den Modus „alle“
    idx = MANUAL.parent / "build" / "personen" / "index.json"
    if idx.exists():
        assert json.loads(idx.read_text(encoding="utf-8"))["modus"] == "relevant"


def test_ergaenze_akten_schreibt_parteispenden_auf_die_seite(tmp_path):
    # Important 9: Spenden erscheinen auch bei der Organisation
    out = tmp_path / "build"
    (out / "empfaenger").mkdir(parents=True)
    s = _seiten()["amadeu-antonio-stiftung"]
    (out / "empfaenger" / "amadeu-antonio-stiftung.json").write_text(json.dumps(s), encoding="utf-8")
    sp = Spende(2025, "CSU", 136_000, "Amadeu Antonio Stiftung", "Berlin", "2025-12-23", "2025-12-26", "Drs. 21/4050", "https://d/x.pdf", False)
    ergaenze_akten(out, {"amadeu-antonio-stiftung": s}, [], {"amadeu-antonio-stiftung": [sp]})
    neu = json.loads((out / "empfaenger" / "amadeu-antonio-stiftung.json").read_text(encoding="utf-8"))
    assert neu["parteispenden"][0] == {"partei": "CSU", "betrag": 136_000, "eingang": "2025-12-23", "veroeffentlicht": "2025-12-26", "drucksache": "Drs. 21/4050",
                                      "drucksache_url": "https://d/x.pdf", "quelle": {"kurz": "bundestag.de", "url": "https://d/x.pdf", "etikett": "amtlich"}}
    assert "spender_ort" not in json.dumps(neu)


def test_akte_traegt_bezuege(tmp_path):
    # Stufe 3d: Akten mit Mandat oder Amt tragen den Block „Bezüge aus dem Amt“
    raw, manual = _raw_mit_abdi(tmp_path)
    (manual / "bezuege.yaml").write_text((MANUAL / "bezuege.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (manual / "regierung.yaml").write_text(
        'stand: "2026-11-02"\nmitglieder:\n  - {name: "Sanae Abdi", amt: "Parlamentarische Staatssekretärin", ressort: "Bundesministerium für Arbeit und Soziales", epl: "11", seit: "2025-05-06", quelle: "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", mdb_id: 1043330}\n', encoding="utf-8")
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    sh = json.loads((tmp_path / "build" / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))
    b = sh["sanae-abdi"]["bezuege"]
    k = {x["komponente"]: x for x in b["zeilen"]}
    assert k["Abgeordnetenentschädigung"]["summe"] == 237470.27 and k["Amtsgehalt"]["monatlich"] == 16084.36   # März 2025 tageweise (§ 32 Abs. 8 AbgG)
    assert k["Kürzung der Abgeordnetenentschädigung (Amt und Mandat)"]["monate"] == 19
    assert by_id["sanae-abdi"]["epl_leitung"] == [{"epl": "11", "amt": "Parlamentarische Staatssekretärin", "seit": "2025-05-06", "bis": None}]   # Stufe 4a
    assert by_id["timo-reinfrank"]["epl_leitung"] == []
    assert b["summe_person"] < b["summe_person"] + b["summe_aufwand"]
    reinfrank = next(a for a in idx["eintraege"] if a["id"] == "timo-reinfrank")
    assert reinfrank["sichtbar"] is False    # Vertreter ohne Amt haben keine Bezüge und bleiben wie bisher
    assert all(f.get("amt") is None or f["art"] == "regierung" for f in sh["sanae-abdi"]["funktionen"])


def test_nachruecker_erbt_eintritt_vom_vorgaenger(tmp_path):
    # C2: Eintritt des Nachrückers = Tag nach dem Ausscheiden des Vorgängers (Biografie des Vorgängers als Quelle)
    raw, manual = _raw_mit_abdi(tmp_path)
    (manual / "bezuege.yaml").write_text((MANUAL / "bezuege.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    vor = (FIXTURES / "mdb_bio_ausschnitt.html").read_text(encoding="utf-8")
    vor = vor.replace('<h1 class="m-biography__introName">Sanae Abdi</h1>',
                      '<h1 class="m-biography__introName">Vera Vorgaenger</h1><p>Vera Vorgaenger ist mit Ablauf des 31. Mai 2026 aus dem Deutschen Bundestag ausgeschieden. '
                      'Nachfolgerin ist die Abgeordnete <a href="/abgeordnete/biografien/A/abdi_sanae-1043330" class="a-link --inline"><span class="a-link__label">Sanae Abdi, SPD</span></a>.</p>', 1)
    (raw / "bundestag" / "1099999.html").write_text(vor, encoding="utf-8")
    (raw / "bundestag" / "1099999.url").write_text("https://www.bundestag.de/abgeordnete/biografien/V/vorgaenger_vera-1099999", encoding="utf-8")
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    sh = json.loads((tmp_path / "build" / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))
    f = sh["sanae-abdi"]["funktionen"][0]
    assert f["seit"] == "2026-06-01" and "Vorgänger" in f["seit_hinweis"] and "1099999" in f["seit_quelle"]
    e = {z["komponente"]: z for z in sh["sanae-abdi"]["bezuege"]["zeilen"]}["Abgeordnetenentschädigung"]
    assert e["zeitraum_von"] == "2026-06-01" and e["monate"] == 6
    assert not any("Beginn der 21. Wahlperiode" in h for h in sh["sanae-abdi"]["bezuege"]["hinweise"])
    assert any("Vorgänger" in h for h in sh["sanae-abdi"]["bezuege"]["hinweise"])


# ---------------------------------------------------------------- Nacharbeiten Stufe 3

def test_laufende_regierungsfunktion_heisst_nicht_frueher():
    p = profil_mit("Zweite Stiftung", "R009999", [Person("Amt", "Anna", "Vorstand", "gesetzlicher_vertreter",
                   Regierungsfunktion("STATE_SECRETARY", "Staatssekretärin", "Bundesministerium X", False, None))])
    f = next(a for a in roh_identitaeten([p], [], []) if a.name == "Anna Amt").funktionen[1]
    assert f.art == "regierungsfunktion" and f.bis is None
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Alt", "Bert", "Vorstand", "gesetzlicher_vertreter",
                    Regierungsfunktion("STATE_SECRETARY", "Staatssekretär", "Bundesministerium X", True, "2021-12-08"))])
    f2 = next(a for a in roh_identitaeten([p2], [], []) if a.name == "Bert Alt").funktionen[1]
    assert f2.art == "fruehere_regierungsfunktion" and f2.bis == "2021-12-08"


def test_zeitlinie_ohne_dopplung_und_mit_endjahr(tmp_path):
    raw, manual = _raw_mit_abdi(tmp_path)
    d = json.loads((raw / "lobbyregister" / "R004511_82516.json").read_text(encoding="utf-8"))
    d["lobbyistIdentity"]["legalRepresentatives"][0].update({"recentGovernmentFunctionPresent": True, "recentGovernmentFunction": {
        "type": {"code": "STATE_SECRETARY", "de": "Staatssekretär"}, "federalAdministration": {"function": "Staatssekretär", "supremeFederalAuthority": "Bundesministerium X"},
        "ended": True, "endDate": "2021-12-08"}})
    (raw / "lobbyregister" / "R004511_82516.json").write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    wer = next(e for e in idx["eintraege"] if e["sichtbar"] and "fruehere_regierungsfunktion" in e["arten"])
    a = json.loads((tmp_path / "build" / "personen" / f"{wer['shard']}.json").read_text(encoding="utf-8"))[wer["id"]]
    posten = [z for z in a["zeitlinie"] if z["art"] == "posten"]
    assert any(z["jahr"] == 2021 and "Bundesministerium X" in z["text"] and z["text"].count("Bundesministerium X") == 1 for z in posten)
    abdi = json.loads((tmp_path / "build" / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))["sanae-abdi"]
    assert not any("bei Deutscher Bundestag" in z["text"] for z in abdi["zeitlinie"])


def test_haushalt_soll_nur_juengstes_jahr():
    from bhtracker.personen import _geld_der_seite
    seite = {"lobby_zuwendungen": [], "foerderkatalog": [], "haushalt": {"titel": [
        {"id": "a", "werte": {"2024": {"soll": 100}, "2026": {"soll": 300}}}, {"id": "b", "werte": {"2024": {"soll": 50}}}]}}
    assert _geld_der_seite(seite)["haushalt_soll_letztes_jahr"] == 300


def test_haushalt_soll_mit_globalem_jahr():
    from bhtracker.personen import _geld_der_seite
    seite = {"lobby_zuwendungen": [], "foerderkatalog": [], "haushalt": {"titel": [
        {"id": "a", "werte": {"2024": {"soll": 100}, "2025": {"soll": 300}}}, {"id": "b", "werte": {"2024": {"soll": 50}}}]}}
    assert _geld_der_seite(seite, letztes_jahr=2026)["haushalt_soll_letztes_jahr"] == 0     # wie die Empfängerliste: kein Wert im globalen letzten Jahr
    assert _geld_der_seite(seite, letztes_jahr=2024)["haushalt_soll_letztes_jahr"] == 150


def test_index_traegt_partei_aus_fraktion_oder_regierungsdatei(tmp_path):
    # Stufe 4c: Partei im Index – Fraktion der Bundestags-Funktion, sonst `partei` aus regierung.yaml (Kabinettsseite)
    raw, manual = _raw_mit_abdi(tmp_path)
    (manual / "regierung.yaml").write_text(
        'stand: "2026-11-02"\nmitglieder:\n'
        '  - {name: "Sanae Abdi", amt: "Parlamentarische Staatssekretärin", ressort: "Bundesministerium für Arbeit und Soziales", epl: "11", seit: "2025-05-06", quelle: "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", mdb_id: 1043330}\n'
        '  - {name: "Katherina Reiche", amt: "Bundesministerin für Wirtschaft und Energie", ressort: "Bundesministerium für Wirtschaft und Energie", epl: "09", seit: "2025-05-06", partei: "CDU", quelle: "https://dserver.bundestag.de/btp/21/21002.pdf"}\n',
        encoding="utf-8")
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    assert by_id["sanae-abdi"]["partei"] == "SPD"
    assert by_id["katherina-reiche"]["partei"] == "CDU"
    assert by_id["timo-reinfrank"]["partei"] is None
