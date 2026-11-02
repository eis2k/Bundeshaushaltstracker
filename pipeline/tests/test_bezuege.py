from decimal import Decimal
from pathlib import Path

import yaml

from bhtracker.bezuege import WP_BEGINN, amtszulage_faktor, berechne_bezuege, lade_bezuege, monate, rolle_amt, satz_am, validate_bezuege

MANUAL = Path(__file__).resolve().parents[2] / "data" / "manual"
SAETZE = lade_bezuege(MANUAL / "bezuege.yaml")


def f(art, text, seit=None, bis=None, amt=None, aemter=()):
    return {"art": art, "text": text, "seit": seit, "bis": bis, "stand": "2026-11-02", "amt": amt, "aemter": list(aemter)}


def test_repo_bezuege_yaml_ist_gueltig():
    assert validate_bezuege(yaml.safe_load((MANUAL / "bezuege.yaml").read_text(encoding="utf-8"))) == []
    assert any("quelle" in e for e in validate_bezuege({"saetze": [{"art": "b11", "ab": "2024-03-01", "monat": 1}]}))
    assert any("art" in e for e in validate_bezuege({"saetze": [{"art": "gold", "ab": "2024-03-01", "monat": 1, "quelle": "https://x", "fundstelle": "f", "datum": "2026-01-01"}]}))


def test_monate_und_satz_am():
    assert monate("2025-03-25", "2025-07-02") == ["2025-03", "2025-04", "2025-05", "2025-06", "2025-07"]
    assert satz_am(SAETZE, "abgeordnetenentschaedigung", "2025-06-30").monat == Decimal("11227.20")
    assert satz_am(SAETZE, "abgeordnetenentschaedigung", "2025-07-01").monat == Decimal("11833.47")
    assert satz_am(SAETZE, "kostenpauschale", "2025-12-31") is None


def test_rolle_amt_und_amtszulage():
    assert rolle_amt("Bundeskanzler") == "kanzler" and rolle_amt("Bundesministerin für Wohnen") == "minister"
    assert rolle_amt("Chefin des Bundeskanzleramts") == "minister" and rolle_amt("Staatsministerin") == "parl_sts"
    assert rolle_amt("Parlamentarischer Staatssekretär") == "parl_sts" and rolle_amt("Staatssekretär") == "sts"
    assert amtszulage_faktor(["Vorsitzender: Verkehrsausschuss"]) == Decimal("0.15")
    assert amtszulage_faktor(["Amtierender Vorsitzender: Haushaltsausschuss", "Stellvertretende Vorsitzende: Rechtsausschuss"]) == 0
    assert amtszulage_faktor(["Vorsitzende: Unterausschuss Globale Gesundheit", "Vorsitzender: Parlamentarischer Beirat für nachhaltige Entwicklung"]) == 0
    assert amtszulage_faktor(["Vorsitzende: 1. Untersuchungsausschuss", "Vorsitzender: Enquete-Kommission KI"]) == Decimal("0.15")
    assert amtszulage_faktor(["Präsidentin des Deutschen Bundestages: Präsidium"]) == 1 and amtszulage_faktor(["Vizepräsident: Präsidium"]) == Decimal("0.5")


def test_abgeordnete_seit_wahlperiode():
    b = berechne_bezuege([f("mdb", "Mitglied des Bundestages, SPD")], SAETZE, "2026-11-02")
    z = {x["komponente"]: x for x in b["zeilen"]}
    e = z["Abgeordnetenentschädigung"]
    assert e["zeitraum_von"] == WP_BEGINN and e["zeitraum_bis"] == "2026-11-02" and e["monate"] == 21
    assert e["monatlich"] == 11833.47 and e["summe"] == 246077.79   # 4 × 11.227,20 + 17 × 11.833,47
    assert z["Kostenpauschale"]["summe"] == 60139.97 and z["Kostenpauschale"]["monate"] == 11
    assert any("Kostenpauschale" in h and "2025" in h and "10 Monate" in h for h in b["hinweise"])
    assert z["Mitarbeiterpauschale"]["empfaenger"] == "dritte" and z["Mitarbeiterpauschale"]["summe"] == 191772.0
    assert z["Sachleistungskonto"]["monatlich"] == 1000.0 and z["Sachleistungskonto"]["summe"] == 11000.0
    assert b["summe_person"] == round(246077.79 + 60139.97, 2) and b["summe_aufwand"] == 191772.0 + 11000.0
    assert any("12.330,48" in h for h in b["hinweise"])            # Juli/August 2026
    assert any("Wahlperiode" in h for h in b["hinweise"])         # Eintrittsdatum nicht ausgewertet
    assert any("§ 18" in s for s in b["nicht_bezifferbar"]) and any("§ 27" in s for s in b["nicht_bezifferbar"])


def test_nachruecker_und_ausgeschiedene():
    b = berechne_bezuege([f("mdb", "MdB", seit="2026-03-01")], SAETZE, "2026-11-02")
    assert {x["komponente"]: x["monate"] for x in b["zeilen"]}["Abgeordnetenentschädigung"] == 9
    assert not any("Wahlperiode" in h for h in b["hinweise"])
    b2 = berechne_bezuege([f("mdb", "MdB bis 2025-08-31", bis="2025-08-31")], SAETZE, "2026-11-02")
    e = {x["komponente"]: x for x in b2["zeilen"]}["Abgeordnetenentschädigung"]
    assert e["monate"] == 6 and e["summe"] == round(4 * 11227.20 + 2 * 11833.47, 2)


def test_amtszulage_nur_monatsbetrag_ohne_beginn():
    b = berechne_bezuege([f("mdb", "MdB", aemter=["Vorsitzender: Verkehrsausschuss"])], SAETZE, "2026-11-02")
    z = {x["komponente"]: x for x in b["zeilen"]}["Amtszulage Ausschussvorsitz"]
    assert z["monatlich"] == 1775.02 and z["summe"] is None and any("Vorsitz" in h for h in b["hinweise"])


def test_kanzler_mit_mandat():
    fn = [f("mdb", "Mitglied des Bundestages, CDU/CSU"), f("regierung", "Bundeskanzler, Bundeskanzleramt", seit="2025-05-06", amt="Bundeskanzler")]
    b = berechne_bezuege(fn, SAETZE, "2026-11-02")
    z = {x["komponente"]: x for x in b["zeilen"]}
    assert z["Amtsgehalt"]["monatlich"] == 26807.27 and z["Amtsgehalt"]["monate"] == 19 and z["Amtsgehalt"]["summe"] == round(19 * 26807.27, 2)
    assert z["Dienstaufwandsentschädigung"]["monatlich"] == 1022.58
    k = z["Kürzung der Abgeordnetenentschädigung (Amt und Mandat)"]
    assert k["monate"] == 19 and k["summe"] == -111811.78 and k["empfaenger"] == "person"   # 2 × −5.613,60 + 17 × −5.916,74
    assert k["zeitraum_von"] == "2025-05-06" and k["zeitraum_bis"] == "2026-11-02"
    assert any("Ortszuschlag" in s for s in b["nicht_bezifferbar"])


def test_minister_ohne_seit_nur_monatsbetraege():
    fn = [f("mdb", "MdB"), f("regierung", "Bundesminister für Verkehr, BMV", amt="Bundesminister für Verkehr")]
    b = berechne_bezuege(fn, SAETZE, "2026-11-02")
    z = {x["komponente"]: x for x in b["zeilen"]}
    assert z["Amtsgehalt"]["monatlich"] == 21445.81 and z["Amtsgehalt"]["summe"] is None
    assert "Kürzung der Abgeordnetenentschädigung (Amt und Mandat)" not in z and any("§ 29" in h for h in b["hinweise"])
    assert any("Zeitraum nicht belegt" in h for h in b["hinweise"])


def test_parlamentarischer_staatssekretaer_und_beamter():
    b = berechne_bezuege([f("regierung", "Parlamentarische Staatssekretärin, BMAS", seit="2025-05-06", amt="Parlamentarische Staatssekretärin")], SAETZE, "2026-11-02")
    z = {x["komponente"]: x for x in b["zeilen"]}
    assert z["Amtsgehalt"]["monatlich"] == 16084.36 and z["Dienstaufwandsentschädigung"]["monatlich"] == 230.08
    b2 = berechne_bezuege([f("regierung", "Staatssekretär, BMF", seit="2025-05-06", amt="Staatssekretär")], SAETZE, "2026-11-02")
    assert {x["komponente"]: x for x in b2["zeilen"]}["Amtsgehalt"]["monatlich"] == 16084.36
    assert "Dienstaufwandsentschädigung" not in {x["komponente"] for x in b2["zeilen"]}
