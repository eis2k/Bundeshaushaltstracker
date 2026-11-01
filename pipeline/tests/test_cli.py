import json
from pathlib import Path

from bhtracker import cli
from bhtracker.model import BudgetRow
from bhtracker.nachtrag import apply_nachtrag


def soll(titel, betrag, kap="1102", epl="11", jahr=2020):
    return BudgetRow(jahr=jahr, stand="soll", art="A", epl=epl, kap=kap, titel=titel, epl_text="E", kap_text="K",
                     titel_text="T", fkt="221", flex=False, soll=betrag)


def test_apply_nachtrag_overrides_listed_titel_and_appends_new():
    base = [soll("63681", 100), soll("63682", 50)]
    n1 = [soll("63681", 120), soll("99999", 7)]
    out = apply_nachtrag(base, n1)
    assert [(r.titel, r.soll) for r in out] == [("63681", 120), ("63682", 50), ("99999", 7)]
    assert base[0].soll == 100  # Eingabe bleibt unverändert


def test_cli_build_smoke(tmp_path: Path, monkeypatch, fx):
    raw = tmp_path / "raw"
    (raw / "2025" / "soll").mkdir(parents=True)
    (raw / "2025" / "soll" / "HH_2025_ALL.csv").write_bytes((fx / "soll_2025_kopf.csv").read_bytes())
    (raw / "2024" / "ist").mkdir(parents=True)
    (raw / "2024" / "ist" / "rechnung_2024.xml").write_bytes((fx / "rechnung_2024_ausschnitt.xml").read_bytes())
    (raw / "2024" / "soll").mkdir(parents=True)
    (raw / "2024" / "soll" / "HH_2024_ALL.csv").write_bytes((fx / "soll_2025_kopf.csv").read_bytes())
    expected = tmp_path / "summen.yaml"
    expected.write_text("toleranz: 1000000000000000\njahre: {}\n", encoding="utf-8")
    out = tmp_path / "build"
    rc = cli.main(["build", "--from", "2024", "--to", "2025", "--raw", str(raw), "--out", str(out),
                   "--summen", str(expected), "--manual", str(Path(__file__).resolve().parents[2] / "data" / "manual")])
    assert rc == 0
    idx = json.loads((out / "index.json").read_text(encoding="utf-8"))
    assert idx["jahre"] == [2024, 2025] and idx["ist_bis"] == 2024
    assert (out / "bund" / "2025.json").exists() and (out / "zeitreihe.json").exists()
    y2024 = json.loads((out / "bund" / "2024.json").read_text(encoding="utf-8"))
    assert any(r["ist"] is not None for r in y2024["rows"])
    assert y2024["quelle"]["soll"]["dokument"] and y2024["quelle"]["ist"]["dokument"]
    # Liegt eine Haushaltsrechnung vor, gilt deren Soll (Endstand inkl. Nachträge): CSV 2.000 Tsd, XML 2.300.000 €
    by_id = {r["id"]: r for r in y2024["rows"]}
    assert by_id["01-0101-68401"]["soll"] == 2_300_000 and by_id["01-0101-68401"]["ist"] == 2_713_016
    assert by_id["01-0101-68401"]["tgr"] is None and y2024["kap"]["0101"] == "Bundespräsident"


def test_cli_build_fails_on_total_mismatch(tmp_path: Path, fx):
    raw = tmp_path / "raw"
    (raw / "2025" / "soll").mkdir(parents=True)
    (raw / "2025" / "soll" / "HH_2025_ALL.csv").write_bytes((fx / "soll_2025_kopf.csv").read_bytes())
    expected = tmp_path / "summen.yaml"
    expected.write_text("toleranz: 1\njahre:\n  2025:\n    ausgaben_kern: 999999999999\n", encoding="utf-8")
    rc = cli.main(["build", "--from", "2025", "--to", "2025", "--raw", str(raw), "--out", str(tmp_path / "build"),
                   "--summen", str(expected), "--manual", str(Path(__file__).resolve().parents[2] / "data" / "manual")])
    assert rc == 1
