import dataclasses
import json
from pathlib import Path

import yaml

from bhtracker.bundestag import parse_bio
from bhtracker.lobbyregister import Person, Profil, extract_profil
from bhtracker.personen import (
    Akte,
    build_personen,
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
