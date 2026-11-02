import json
import shutil
from pathlib import Path

import pytest

from bhtracker.cli import cmd_build
from bhtracker.empfaenger import build_empfaenger
from bhtracker.model import BudgetRow

FIXTURES = Path(__file__).parent / "fixtures"
REPO_MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual"


def row(rid: str, text: str, soll: int, jahr: int, ist: int | None = None) -> BudgetRow:
    epl, kap, titel = rid.split("-")
    return BudgetRow(jahr=jahr, stand="soll", art="A", epl=epl, kap=kap, titel=titel, epl_text="Auswärtiges Amt",
                     kap_text="", titel_text=text, fkt="000", soll=soll, ist=ist)


YEARS = {
    2024: [row("05-0504-68740", "Goethe-Institut e. V., München - Betrieb und operative Mittel", 220_000_000, 2024, 219_000_000),
           row("17-1702-68402", "Zuschuss an die Amadeu-Antonio-Stiftung Berlin", 1_000_000, 2024)],
    2025: [row("05-0504-68740", "Goethe-Institut e. V., München - Betrieb und operative Mittel", 224_700_000, 2025),
           row("17-1702-68402", "Zuschuss an die Amadeu-Antonio-Stiftung Berlin", 1_200_000, 2025)],
}
IST_YEARS = {2024: YEARS[2024]}


def make_raw(tmp_path: Path) -> Path:
    raw = tmp_path / "raw"
    (raw / "lobbyregister").mkdir(parents=True)
    shutil.copy(FIXTURES / "lobby_detail_R004511.json", raw / "lobbyregister" / "R004511_82516.json")
    (raw / "bundestag").mkdir()
    shutil.copy(FIXTURES / "mdb_bio_ausschnitt.html", raw / "bundestag" / "1043330.html")
    (raw / "bundestag" / "1043330.url").write_text("https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", encoding="utf-8")
    (raw / "foerderkatalog").mkdir()
    shutil.copy(FIXTURES / "foekat_humboldt.csv", raw / "foerderkatalog" / "alexander-von-humboldt-stiftung.csv")
    return raw


def make_manual(tmp_path: Path) -> Path:
    manual = tmp_path / "manual"
    manual.mkdir()
    for name in ("empfaenger.yaml", "ressorts.yaml", "verbindungen.yaml"):
        shutil.copy(REPO_MANUAL / name, manual / name)
    (manual / "jahresabschluss.yaml").write_text(
        "eintraege:\n  - {empfaenger: amadeu-antonio-stiftung, geschaeftsjahr: 2024, url: 'https://example.invalid/ja.pdf', seite: 2, pruefer: 'Gem.Audit PartG mbB',"
        " ertraege_gesamt: 12523375, oeffentliche_hand: 7351034, spenden: 3308958, personalaufwand: 6965568, projektfoerderung: 1015267,"
        " weitergeleitete_mittel: 901912, jahresergebnis: 1490418, erfasst: '2026-11-01', hinweis: 'Personalaufwand = alle Beschäftigten'}\n",
        encoding="utf-8")
    return manual


@pytest.fixture
def gebaut(tmp_path):
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    return tmp_path, out


def lade(out: Path, name: str) -> dict:
    return json.loads((out / "empfaenger" / name).read_text(encoding="utf-8"))


def test_build_schreibt_index_und_seiten(gebaut):
    _, out = gebaut
    idx = lade(out, "index.json")
    assert idx["stand"] == "2026-11-01" and idx["mit_personen"] is True
    e = next(x for x in idx["eintraege"] if x["id"] == "amadeu-antonio-stiftung")
    assert e["lobby_untergrenze_bund"] > 0 and e["n_personen"] == 2 and "17" in e["epls"]
    seite = lade(out, "amadeu-antonio-stiftung.json")
    assert seite["lobbyregister"]["nummer"] == "R004511"
    assert seite["lobby_zuwendungen"][0]["epl"] == "17"
    assert seite["pflichtangaben"]["jahresabschluss"]["url"].startswith("https://")
    assert seite["pflichtangaben"]["jahresabschluss"]["kennzahlen"]["ertraege_gesamt"] == 12_523_375
    assert seite["pflichtangaben"]["spenden"] == {"von": 4_190_001, "bis": 4_200_000}
    assert all(("abgerufen" in q) or ("stand" in q) for q in seite["quellen"])
    assert any(q.get("etikett") == "Eigenangabe" for q in seite["quellen"])


def test_titel_empfaenger_bekommt_zeitreihe(gebaut):
    _, out = gebaut
    idx = lade(out, "index.json")
    assert idx["titel"]["05-0504-68740"]["id"] == "goethe-institut"
    seite = lade(out, "goethe-institut.json")
    t = seite["haushalt"]["titel"][0]
    assert t["id"] == "05-0504-68740" and t["epl"] == "05" and t["epl_text"] == "Auswärtiges Amt"
    assert t["werte"]["2025"]["soll"] == 224_700_000 and t["werte"]["2024"]["ist"] == 219_000_000 and t["werte"]["2025"]["ist"] is None
    e = next(x for x in idx["eintraege"] if x["id"] == "goethe-institut")
    assert e["haushalt_soll_letztes_jahr"] == 224_700_000 and e["lobby_untergrenze_bund"] == 0


def test_foerderkatalog_projekte_am_empfaenger(gebaut):
    _, out = gebaut
    seite = lade(out, "alexander-von-humboldt-stiftung.json")
    assert len(seite["foerderkatalog"]) == 9 and seite["foerderkatalog"][0]["epl"] == "30"
    e = next(x for x in lade(out, "index.json")["eintraege"] if x["id"] == "alexander-von-humboldt-stiftung")
    assert e["foerderkatalog_summe"] == pytest.approx(sum(p["summe"] for p in seite["foerderkatalog"]))


def test_betraege_bleiben_getrennt(gebaut):
    _, out = gebaut
    text = (out / "empfaenger" / "amadeu-antonio-stiftung.json").read_text(encoding="utf-8")
    assert '"gesamt"' not in text


def test_verbindung_aus_regierungsfunktion_und_angaben(tmp_path):
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    # Lobbyregister-Profil mit jüngster Regierungsfunktion
    p = raw / "lobbyregister" / "R004511_82516.json"
    d = json.loads(p.read_text(encoding="utf-8"))
    rep = d["lobbyistIdentity"]["legalRepresentatives"][0]
    rep["recentGovernmentFunctionPresent"] = True
    rep["recentGovernmentFunction"] = {"ended": True, "endDate": "2025-04", "type": {"code": "HOUSE_OF_REPRESENTATIVES", "de": "Bundestag"},
                                       "houseOfRepresentatives": {"function": {"code": "MEMBER", "de": "Mitglied des Deutschen Bundestages"}}}
    p.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
    # Stamm-Eintrag, der zur Angabe der Abgeordneten exakt passt
    (manual / "empfaenger.yaml").write_text(
        "empfaenger:\n  - {id: dsw, name: 'Deutsche Stiftung Weltbevölkerung (DSW)', aliasse: [], lobbyregister: null, titel: [], foerderkatalog: null, art: verein_stiftung, geprueft: true, quelle: 'https://x'}\n",
        encoding="utf-8")
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    aas = lade(out, "amadeu-antonio-stiftung.json")
    assert [v["typ"] for v in aas["verbindungen"]] == ["regierungsfunktion"]
    assert "Mitglied des Deutschen Bundestages" in aas["verbindungen"][0]["satz"] and aas["verbindungen"][0]["abgleich"] == "eigenangabe"
    dsw = lade(out, "dsw.json")
    assert dsw["verbindungen"][0]["person"] == "Sanae Abdi" and dsw["verbindungen"][0]["abgleich"] == "exakt"
    assert dsw["verbindungen"][0]["quellen"][0]["url"].endswith("abdi_sanae-1043330")
    assert next(x for x in lade(out, "index.json")["eintraege"] if x["id"] == "dsw")["n_verbindungen"] == 1


def test_ohne_personen_entfernt_alle_namen(tmp_path):
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, mit_personen=False, stand="2026-11-01")
    text = (out / "empfaenger" / "amadeu-antonio-stiftung.json").read_text(encoding="utf-8")
    assert "Reinfrank" not in text and json.loads(text)["verbindungen"] == [] and json.loads(text)["personen"] == []
    idx = lade(out, "index.json")
    assert idx["mit_personen"] is False
    assert all(e["n_personen"] == 0 and e["n_verbindungen"] == 0 for e in idx["eintraege"])


def test_aehnliche_namen_landen_in_prueflisten(gebaut):
    tmp_path, out = gebaut
    import yaml
    kand = yaml.safe_load((tmp_path / "review" / "empfaenger_kandidaten.yaml").read_text(encoding="utf-8"))
    assert any("Amadeu" in k["name_a"] and "Amadeu" in k["name_b"] for k in kand["kandidaten"])
    seite = lade(out, "amadeu-antonio-stiftung.json")
    assert seite["haushalt"]["titel"] == []  # nicht exakt → keine Zuordnung
    vk = yaml.safe_load((tmp_path / "review" / "verbindungen_kandidaten.yaml").read_text(encoding="utf-8"))
    assert "kandidaten" in vk


def test_cli_build_ohne_rohdaten_ueberspringt(tmp_path, capsys):
    import argparse
    out = tmp_path / "build"
    raw = tmp_path / "raw"
    raw.mkdir()
    manual = make_manual(tmp_path)
    shutil.copy(REPO_MANUAL / "sondervermoegen.yaml", manual / "sondervermoegen.yaml")
    args = argparse.Namespace(raw=str(raw), out=str(out), manual=str(manual), summen=str(REPO_MANUAL / "gesamtplan_summen.yaml"),
                              von=2025, bis=2025, ohne_personen=False)
    cmd_build(args)
    assert "empfaenger: keine Rohdaten" in capsys.readouterr().out or not (out / "empfaenger").exists()


def test_titel_empfaenger_ohne_stamm_wird_nur_kandidat(tmp_path):
    # Review Stufe 2, Befund 1: Namen aus Titeltexten ohne Stamm- oder Lobbyregister-Treffer bekommen keine Seite
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    years = {2025: YEARS[2025] + [row("04-0452-68530", "Zuschuss an das Deutsche Historische Museum", 50_000_000, 2025)]}
    build_empfaenger(manual, raw, out, years, {}, stand="2026-11-01")
    idx = lade(out, "index.json")
    assert not any("Historische" in e["name"] for e in idx["eintraege"])
    assert "04-0452-68530" not in idx["titel"]
    import yaml
    kand = yaml.safe_load((tmp_path / "review" / "empfaenger_kandidaten.yaml").read_text(encoding="utf-8"))
    assert any(k["name_a"] == "Deutsche Historische Museum" and k["quelle_a"].startswith("Haushaltstitel") and k.get("art") == "titel_ohne_stamm" for k in kand["kandidaten"])


def test_ohne_personen_leert_verbindungs_prueflisten(tmp_path):
    # Review Stufe 2, Befund 4
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, mit_personen=False, stand="2026-11-01")
    import yaml
    vk = yaml.safe_load((tmp_path / "review" / "verbindungen_kandidaten.yaml").read_text(encoding="utf-8"))
    assert vk["kandidaten"] == []


def test_foerderkatalog_auszug_wird_markiert(tmp_path):
    # Review Stufe 2, Befund 5: Der CSV-Export des Förderkatalogs liefert höchstens 100 Zeilen
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    text = (FIXTURES / "foekat_humboldt.csv").read_text(encoding="latin-1")
    kopf, *zeilen = text.splitlines()
    datenzeile = next(z for z in zeilen if z.strip())
    viele = "\n".join([kopf] + [datenzeile.replace("M538100", f"M{i:06d}") for i in range(100)])
    (raw / "foerderkatalog" / "alexander-von-humboldt-stiftung.csv").write_text(viele, encoding="latin-1", newline="")
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    seite = lade(out, "alexander-von-humboldt-stiftung.json")
    assert len(seite["foerderkatalog"]) == 100 and seite["foerderkatalog_auszug"] is True
    assert lade(out, "goethe-institut.json")["foerderkatalog_auszug"] is False


def test_werte_nur_aus_jahren_mit_passendem_titeltext(tmp_path):
    # Review Stufe 2, Befund 7: Eine Titelnummer kann in anderen Jahren einen anderen Empfänger bezeichnen
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    years = {2015: [row("05-0504-68740", "Zuschuss an das Institut für Auslandsbeziehungen", 100, 2015)],
             2025: YEARS[2025]}
    build_empfaenger(manual, raw, out, years, {}, stand="2026-11-01")
    t = lade(out, "goethe-institut.json")["haushalt"]["titel"][0]
    assert "2025" in t["werte"] and "2015" not in t["werte"]


def test_automatische_verbindung_traegt_beide_belege(tmp_path):
    # §4.6a: automatische Verbindung mit beiden Belegen verlinkt (bundestag.de und die Quelle des Empfängers)
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    (manual / "empfaenger.yaml").write_text(
        "empfaenger:\n  - {id: amadeu-antonio-stiftung, name: 'Amadeu Antonio Stiftung', aliasse: ['Deutsche Stiftung Weltbevölkerung (DSW)'], lobbyregister: R004511, titel: [], foerderkatalog: null, art: verein_stiftung, geprueft: true, quelle: 'https://x'}\n",
        encoding="utf-8")
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    v = [x for x in lade(out, "amadeu-antonio-stiftung.json")["verbindungen"] if x["typ"] == "abgeordneter_funktion"][0]
    assert [q["kurz"] for q in v["quellen"]] == ["bundestag.de", "Lobbyregister"]
    assert all(q.get("etikett") == "Eigenangabe" for q in v["quellen"])


def test_build_entfernt_veraltete_seiten(tmp_path):
    # Seiten aus früheren Läufen, deren Empfänger es nicht mehr gibt, dürfen nicht liegen bleiben (sonst bleiben sie per Link erreichbar)
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    (out / "empfaenger").mkdir(parents=True)
    alt = out / "empfaenger" / "zur-entlastung-beim-strompreis.json"
    alt.write_text("{}", encoding="utf-8")
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    assert not alt.exists()
    assert (out / "empfaenger" / "index.json").exists() and (out / "empfaenger" / "goethe-institut.json").exists()


def _personen_manual(manual: Path) -> None:
    (manual / "personen.yaml").write_text("zusammenfuehren: []\ntrennen: []\nfreigabe: []\n", encoding="utf-8")
    (manual / "regierung.yaml").write_text("stand: '2026-11-02'\nmitglieder: []\n", encoding="utf-8")


def test_akten_und_netz_nach_empfaenger_build(tmp_path):
    from bhtracker.personen import build_akten_und_netz
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    _personen_manual(manual)
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    ergebnis = build_akten_und_netz(manual, raw, out, "2026-11-02", modus="relevant")
    assert (out / "personen" / "index.json").exists() and (out / "netz" / "index.json").exists()
    idx = json.loads((out / "personen" / "index.json").read_text(encoding="utf-8"))
    sichtbar = {e["id"] for e in idx["eintraege"] if e["sichtbar"]}
    assert "sanae-abdi" in sichtbar and "timo-reinfrank" not in sichtbar
    # Empfänger-Seite kennt die Akten ihrer Personen
    seite = lade(out, "amadeu-antonio-stiftung.json")
    p = next(x for x in seite["personen"] if x["name"] == "Timo Reinfrank")
    assert p["akte_id"] == "timo-reinfrank" and p["akte_sichtbar"] is False
    assert ergebnis["akten"] >= 3 and ergebnis["sichtbar"] >= 1
    netz_idx = json.loads((out / "netz" / "index.json").read_text(encoding="utf-8"))
    assert "e:amadeu-antonio-stiftung" in netz_idx and "p:timo-reinfrank" in netz_idx


def test_akten_modus_alle_zeigt_mehr(tmp_path):
    from bhtracker.personen import build_akten_und_netz
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    _personen_manual(manual)
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, stand="2026-11-01")
    relevant = build_akten_und_netz(manual, raw, out, "2026-11-02", modus="relevant")["sichtbar"]
    alle = build_akten_und_netz(manual, raw, out, "2026-11-02", modus="alle")["sichtbar"]
    assert alle > relevant
    seite = lade(out, "amadeu-antonio-stiftung.json")
    assert next(x for x in seite["personen"] if x["name"] == "Timo Reinfrank")["akte_sichtbar"] is True


def test_ohne_personen_baut_weder_akten_noch_netz(tmp_path):
    from bhtracker.personen import build_akten_und_netz
    raw, manual, out = make_raw(tmp_path), make_manual(tmp_path), tmp_path / "build"
    _personen_manual(manual)
    build_empfaenger(manual, raw, out, YEARS, IST_YEARS, mit_personen=False, stand="2026-11-01")
    ergebnis = build_akten_und_netz(manual, raw, out, "2026-11-02", mit_personen=False)
    assert ergebnis["akten"] == 0 and not (out / "personen").exists()
    netz_idx = json.loads((out / "netz" / "index.json").read_text(encoding="utf-8"))
    assert not any(k.startswith("p:") for k in netz_idx)
