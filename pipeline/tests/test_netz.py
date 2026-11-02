import json
from pathlib import Path

from bhtracker.netz import baue_graph, build_netz, umfeld
from bhtracker.personen import Akte, Funktion
from bhtracker.spenden import Spende

RESSORTS = {"ressorts": [{"epl": "17", "kurz": "BMBFSFJ", "namen": ["Bundesministerium für Bildung, Familie, Senioren, Frauen und Jugend"]},
                         {"epl": "30", "kurz": "BMFTR", "namen": ["Bundesministerium für Forschung, Technologie und Raumfahrt"]}]}


def seite(id: str, name: str, epls: list[str], von: int = 1_000_000) -> dict:
    return {"id": id, "name": name, "lobby_untergrenze_bund": von * len(epls),
            "lobby_zuwendungen": [{"geber": f"Ministerium {e}", "epl": e, "von": von, "bis": von + 9_999, "zweck": "", "geschaeftsjahr": "2025"} for e in epls],
            "haushalt": {"titel": []}, "foerderkatalog": [], "personen": [], "verbindungen": []}


def person(id: str, name: str, orgs: list[tuple[str, str]], sichtbar: bool = True, epl: str | None = None) -> Akte:
    funktionen = [Funktion("gesetzlicher_vertreter", "Vorstand", oid, oname, None, None, None, "2026-09-02", {"kurz": "Lobbyregister", "url": "https://l", "stand": "2026-09-02"}) for oid, oname in orgs]
    if epl:
        funktionen.append(Funktion("regierung", "Bundesminister", None, f"Ministerium {epl}", epl, "2025-05-06", None, "2026-11-02", {"kurz": "bundesregierung.de", "url": "https://b"}))
    return Akte(id=id, name=name, quellen_ids=[id], funktionen=funktionen, amt=bool(epl), verbindung=False, freigabe=False, sichtbar=sichtbar, gleichnamig=[],
                angaben=[], organisationen=[{"id": oid, "name": oname, "funktion": "Vorstand", "rolle": "gesetzlicher_vertreter", "stand": "2026-09-02"} for oid, oname in orgs],
                spenden=[], zeitlinie=[], quellen=[], stand="2026-11-02")


def mini():
    seiten = {"aas": seite("aas", "Amadeu Antonio Stiftung", ["17"]), "zweite": seite("zweite", "Zweite Stiftung", ["30"]), "vbm": seite("vbm", "VBM e.V.", [])}
    akten = [person("timo-reinfrank", "Timo Reinfrank", [("aas", "Amadeu Antonio Stiftung"), ("zweite", "Zweite Stiftung")]),
             person("friedrich-merz", "Friedrich Merz", [], epl="17")]
    spenden = {"vbm": [Spende(2025, "CSU", 136_000, "VBM e.V.", "München", "2025-12-23", "2025-12-26", "Drs. 21/4050", "https://d", False)]}
    return seiten, akten, spenden


def test_graph_hat_drei_kantenarten():
    seiten, akten, spenden = mini()
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    arten = {(k.von, k.nach, k.art) for k in kanten}
    assert ("m:17", "e:aas", "geld") in arten
    assert ("p:timo-reinfrank", "e:aas", "posten") in arten
    assert ("p:friedrich-merz", "m:17", "posten") in arten
    assert ("e:vbm", "partei:csu", "spende") in arten
    assert knoten["m:17"].art == "ministerium" and knoten["m:17"].label == "BMBFSFJ"
    assert knoten["p:timo-reinfrank"].seite == "v1;a=personen;pe=timo-reinfrank"
    assert knoten["e:aas"].seite == "v1;a=empfaenger;e=aas"
    geld = next(k for k in kanten if k.art == "geld" and k.nach == "e:aas")
    assert geld.wert == 1_000_000 and geld.quelle["kurz"] == "Lobbyregister"


def test_unsichtbare_person_ist_knoten_ohne_seite():
    seiten, akten, spenden = mini()
    akten[0].sichtbar = False
    knoten, _ = baue_graph(seiten, akten, spenden, RESSORTS)
    assert knoten["p:timo-reinfrank"].sichtbar is False and knoten["p:timo-reinfrank"].seite is None


def test_umfeld_zwei_schritte_ueber_person():
    seiten, akten, spenden = mini()
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    u = umfeld("e:aas", knoten, kanten)
    ids = {k["id"] for k in u["knoten"]}
    assert {"e:aas", "p:timo-reinfrank", "e:zweite", "m:17"} <= ids
    assert u["start"] == "e:aas" and u["weitere"] == 0


def test_umfeld_expandiert_ministerien_nicht():
    seiten, akten, spenden = mini()
    for i in range(200):
        seiten[f"b{i}"] = seite(f"b{i}", f"Organisation {i}", ["30"], von=10_000 + i)
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    u = umfeld("e:zweite", knoten, kanten)
    ids = {k["id"] for k in u["knoten"]}
    assert "m:30" in ids and "e:b150" not in ids and len(u["knoten"]) <= 60
    # Umfeld eines Ministeriums zeigt direkte Nachbarn (gekappt), expandiert aber nicht weiter
    um = umfeld("m:30", knoten, kanten)
    assert len(um["knoten"]) == 60 and um["weitere"] == 142   # 201 Organisationen + Start = 202 Knoten, 60 gezeigt


def test_kappung_sortiert_nach_wert():
    seiten, akten, spenden = mini()
    for i in range(80):
        seiten[f"o{i}"] = seite(f"o{i}", f"Org {i}", ["30"], von=1_000 * (i + 1))
    akten.append(person("viel-vernetzt", "Viel Vernetzt", [(f"o{i}", f"Org {i}") for i in range(80)]))
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    u = umfeld("p:viel-vernetzt", knoten, kanten)
    assert len(u["knoten"]) == 60 and u["weitere"] == 22   # Start + 80 Organisationen + Ministerium 30 (Randknoten im zweiten Schritt) = 82
    ids = {k["id"] for k in u["knoten"]}
    assert "e:o79" in ids and "e:o0" not in ids   # größte zuerst


def test_build_netz_shards(tmp_path):
    seiten, akten, spenden = mini()
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    idx_path = build_netz(tmp_path / "build", knoten, kanten)
    idx = json.loads(idx_path.read_text(encoding="utf-8"))
    assert "p:timo-reinfrank" in idx and "e:aas" in idx and "m:17" in idx
    sh = json.loads((tmp_path / "build" / "netz" / f"{idx['e:aas']}.json").read_text(encoding="utf-8"))
    assert sh["e:aas"]["start"] == "e:aas"
    idx2 = json.loads(build_netz(tmp_path / "build2", knoten, kanten, mit_personen=False).read_text(encoding="utf-8"))
    assert not any(k.startswith("p:") for k in idx2) and "e:aas" in idx2
    sh2 = json.loads((tmp_path / "build2" / "netz" / f"{idx2['e:aas']}.json").read_text(encoding="utf-8"))
    assert not any(k["id"].startswith("p:") for k in sh2["e:aas"]["knoten"])


def test_build_netz_nur_fuer_knoten_mit_seite(tmp_path):
    # Umfelder werden nur für Knoten vorberechnet, von denen aus man das Netz öffnen kann: Seiten, Ministerien, Parteien (130 MB → handhabbar)
    seiten, akten, spenden = mini()
    akten[0].sichtbar = False
    knoten, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    idx = json.loads(build_netz(tmp_path / "build", knoten, kanten).read_text(encoding="utf-8"))
    assert "p:timo-reinfrank" not in idx and "p:friedrich-merz" in idx and "e:aas" in idx and "m:17" in idx and "partei:csu" in idx
    # der unsichtbare Knoten bleibt aber als Nachbar im Umfeld der Organisation
    sh = json.loads((tmp_path / "build" / "netz" / f"{idx['e:aas']}.json").read_text(encoding="utf-8"))
    assert any(k["id"] == "p:timo-reinfrank" for k in sh["e:aas"]["knoten"])


def test_posten_kante_aus_bundestagsangabe():
    # Important 1: Posten eines Abgeordneten bei einem Empfänger (Quelle bundestag.de) ist eine Kante
    seiten, akten, spenden = mini()
    q = {"kurz": "bundestag.de", "url": "https://www.bundestag.de/abgeordnete/biografien/A/x-1", "stand": "2026-11-01", "etikett": "Eigenangabe"}
    akten[1].organisationen = [{"id": "aas", "name": "Amadeu Antonio Stiftung", "funktion": "Mitglied des Kuratoriums", "rolle": "abgeordneter_funktion", "stand": "2026-11-01", "quelle": q}]
    _, kanten = baue_graph(seiten, akten, spenden, RESSORTS)
    k = next(k for k in kanten if k.von == "p:friedrich-merz" and k.nach == "e:aas")
    assert k.art == "posten" and k.quelle["kurz"] == "bundestag.de" and "Kuratoriums" in k.text
