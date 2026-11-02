# Stufe 3d: Bezüge der Amtsträger – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jede Akte mit Mandat oder Regierungsamt zeigt den Block „Bezüge aus dem Amt“: gesetzlich festgelegte Monatsbeträge je Funktion, Summen je Zeitraum, zwei getrennte Gesamtsummen, Lücken benannt.

**Architecture:** Neues Pipeline-Modul `bezuege.py` rechnet aus den Funktionen einer Akte (mdb, regierung) und der Pflegedatei `data/manual/bezuege.yaml` (amtliche Sätze mit Gültigkeit und Quelle) eine Liste von Zeilen plus Summen; `personen.py` hängt das Ergebnis als `bezuege` an die Akte. `bundestag.py` liefert dafür zwei neue Felder aus der Biografie (Rollen im Block „Mitgliedschaften und Ämter“, Eintrittsdatum). Das Web zeigt den Block in `Akte.svelte` aus dem fertigen JSON, ohne eigene Rechnung.

**Tech Stack:** Python 3.13, pydantic/dataclasses, pyyaml, pytest (Pipeline); Svelte 5, TypeScript, vitest (Web).

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md`, §4.7b (Bezüge der Amtsträger), §4.7a (Akten), §7 Stufe 3d.

## Global Constraints

- Nur amtliche Quellen; jeder Betrag mit `quelle` (URL), `fundstelle` und `datum`. Keine Schätzung fehlender Zeiträume: fehlende Monate werden benannt, nicht gefüllt.
- Beträge aus verschiedenen Quellen werden nicht addiert; die zwei Summen „an die Person ausgezahlt“ und „für die Person aufgewendet“ bleiben getrennt.
- Keine Wertung, keine Adressen, keine Privatpersonen; Texte sind Tatsachensätze mit Paragraf.
- Monatsrechnung: Kalendermonate von `seit` bis `bis` (sonst Stand), beide einschließlich. Jahresbeträge durch zwölf. Rundung je Monatsbetrag auf Cent, `ROUND_HALF_UP`.
- Beginn der 21. Wahlperiode: `2025-03-25`. Faktoren im Code mit Paragraf: Kanzler 5/3 B 11, Minister 4/3 B 11, Parlamentarische Staatssekretäre und Staatsminister 75 % des Ministergehalts (§ 5 Abs. 1 ParlStG), beamtete Staatssekretäre 1 × B 11; Amtszulage 100/50/15 % (§ 11 Abs. 2 AbgG); Kürzung 50 % (§ 29 Abs. 1 AbgG).
- Alle Suiten grün: `cd pipeline && uv run pytest -q`, `cd web && npm run check && npm test -- --run`.

## Review Focus

1. **Nachrücker** („Mitglied des Bundestages seit März 2026“) dürfen keine Summe ab Wahlperiodenbeginn bekommen; Eintritt aus der Biografie zählt. Test in Task 1 und 3.
2. **Fehlendes `seit` bei Regierungsamt** (Bilger, Linnemann, Warken, Kabinettsabruf): Monatsbeträge ja, Summe nein, Kürzung nur als Regel. Test in Task 2.
3. **Amtierende und stellvertretende Vorsitzende, Unterausschüsse, Beiräte** lösen keine Amtszulage aus. Test in Task 1 und 2.
4. **Anpassung 2026** (Juli 12.330,48 €, August 11.336,46 €) darf die Summe nicht verändern: Rechnung mit 11.833,47 € durchgehend, Hinweis im Block. Test in Task 2.
5. **Minister mit Mandat**: Kürzung nur für die Monate, in denen beide Funktionen zusammenfallen; ausgeschiedener Abgeordneter rechnet bis `bis`. Test in Task 2.
6. **Fehlende Sätze** (Kostenpauschale 2025) erscheinen als Hinweis „Betrag für <Jahr> noch nicht belegt (<n> Monate)“, nicht als 0 in der Summe ohne Hinweis. Test in Task 2.

---

### Task 1: Biografie liefert Rollen und Eintrittsdatum

**Files:**
- Modify: `pipeline/src/bhtracker/bundestag.py` (Abgeordneter, parse_bio)
- Test: `pipeline/tests/test_bundestag.py`

**Interfaces:**
- Produces: `Abgeordneter.aemter: list[str]` – Einträge wie `"Vorsitzender: Verkehrsausschuss"`, `"Stellvertretendes Mitglied: Ausschuss für Arbeit und Soziales"`, aus den `h3.m-biography__subHeading`-Überschriften und den Links darunter im Block „Mitgliedschaften und Ämter im Bundestag“ (`ausschuesse` bleibt unverändert die Liste der Gremiennamen).
- Produces: `Abgeordneter.mitglied_seit: str | None` – ISO-Datum aus dem Satz „Mitglied des (Deutschen) Bundestages seit <Monat> <Jahr>“ oder „seit <Jahr>“: Monat bekannt → Erster des Monats, nur Jahr → `<Jahr>-01-01`; fehlt der Satz → `None`.

- [ ] **Step 1: Failing tests**

```python
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
    assert parse_bio(html2, "https://x/-1", "2026-11-01").mitglied_seit == "2005-01-01"
```

Prüfe vorher, ob die Fixture `mdb_bio_ausschnitt.html` die Überschrift `Ordentliches Mitglied` enthält; wenn nicht, die erste vorhandene `h3.m-biography__subHeading` im Replace verwenden.

- [ ] **Step 2: Run** `cd pipeline && uv run pytest -q tests/test_bundestag.py` → Expected: FAIL (`aemter`/`mitglied_seit` unbekannt).

- [ ] **Step 3: Implement** in `bundestag.py`: Felder `aemter: list[str] = field(default_factory=list)`, `mitglied_seit: str | None = None` an `Abgeordneter`; in `parse_bio` den Block „Mitgliedschaften und Ämter im Bundestag“ mit `re.finditer(r'<h3 class="m-biography__subHeading">(.*?)</h3>\s*<ul[^>]*>(.*?)</ul>', block, re.S)` in Rolle + Links zerlegen und `f"{rolle}: {gremium}"` sammeln; `_MITGLIED_SEIT = re.compile(r"Mitglied des (?:Deutschen )?Bundestages seit (?:(Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) )?(\d{4})")` auf `_text(page_html)` anwenden (`_MONATE` aus dem Austritts-Fix wiederverwenden).

- [ ] **Step 4: Run** → Expected: PASS; ganze Datei grün.

- [ ] **Step 5: Commit** `git add pipeline/src/bhtracker/bundestag.py pipeline/tests/test_bundestag.py && git commit -m "Bundestag: Rollen im Ämter-Block und Eintrittsdatum aus der Biografie"`

---

### Task 2: Modul `bezuege` und Pflegedatei

**Files:**
- Create: `pipeline/src/bhtracker/bezuege.py`
- Create: `data/manual/bezuege.yaml`
- Test: `pipeline/tests/test_bezuege.py`

**Interfaces:**
- Consumes: `Funktion` aus `personen.py` (Felder `art`, `text`, `seit`, `bis`, `stand`, neu `amt: str | None` und `aemter: list[str]`, siehe Task 3; hier als einfache Dicts getestet, deshalb nimmt die Rechenfunktion eine Liste von Dicts).
- Produces:
  - `WP_BEGINN = "2025-03-25"`
  - `@dataclass Satz(art: str, ab: str, monat: Decimal | None, jahr: Decimal | None, quelle: str, fundstelle: str, datum: str)`
  - `lade_bezuege(path: Path) -> list[Satz]`; `validate_bezuege(data: dict) -> list[str]` (jede Zeile braucht `art` aus `ARTEN`, `ab` ISO, genau eins von `monat`/`jahr`, `quelle` http, `fundstelle`, `datum` ISO).
  - `satz_am(saetze: list[Satz], art: str, datum: str) -> Satz | None` (jüngster Satz mit `ab <= datum`).
  - `monate(von: str, bis: str) -> list[str]` → `["2025-03", "2025-04", …]` einschließlich beider Monate.
  - `rolle_amt(amt: str) -> str` → `"kanzler" | "minister" | "parl_sts" | "sts"` (Präfixe: „Bundeskanzler“ → kanzler; „Bundesminister“, „Chef“ → minister; „Parlamentarische“, „Staatsminister“ → parl_sts; „Staatssekretär“ → sts).
  - `amtszulage_faktor(aemter: list[str]) -> Decimal` → `1` Präsident, `0.5` Vizepräsident, `0.15` Vorsitz eines Ausschusses/Untersuchungsausschusses/Enquete-Kommission/Parlamentarischen Kontrollgremiums, sonst `0`; „Amtierende“, „Stellvertretende“, „Unterausschuss“, „Kommission“ außer Enquete, „Beirat“, „Gremium“ zählen nicht.
  - `berechne_bezuege(funktionen: list[dict], saetze: list[Satz], stand: str) -> dict` mit Schlüsseln `zeilen` (Liste), `summe_person`, `summe_aufwand` (float, auf Cent), `hinweise` (Liste Sätze), `nicht_bezifferbar` (Liste Sätze), `wp_beginn`. Jede Zeile: `{posten, komponente, rechtsgrundlage, monatlich, zeitraum_von, zeitraum_bis, monate, summe, empfaenger: "person"|"dritte", quelle: {kurz, url, fundstelle}}`; `summe` ist `None`, wenn der Zeitraum nicht belegt ist.

- [ ] **Step 1: Pflegedatei `data/manual/bezuege.yaml` anlegen**

```yaml
# Gesetzlich festgelegte Bezüge (Spec §4.7b). Jeder Satz: art, ab (gültig ab), monat ODER jahr in Euro, quelle (URL), fundstelle, datum.
# Neue Werte nur mit amtlicher Fundstelle per Pull Request. Faktoren (5/3, 4/3, 75 %, 100/50/15 %, 50 %) stehen im Code mit Paragraf.
stand: "2026-11-02"
saetze:
  - {art: abgeordnetenentschaedigung, ab: "2022-07-01", monat: 10323.29, quelle: "https://dserver.bundestag.de/btd/20/015/2001516.pdf", fundstelle: "Drucksache 20/1516, Anpassung zum 1. Juli 2022 (+3,1 %)", datum: "2022-04-25"}
  - {art: abgeordnetenentschaedigung, ab: "2023-07-01", monat: 10591.70, quelle: "https://dserver.bundestag.de/btd/20/068/2006815.pdf", fundstelle: "Drucksache 20/6815, Anpassung zum 1. Juli 2023 (+2,6 %)", datum: "2023-05-10"}
  - {art: abgeordnetenentschaedigung, ab: "2024-07-01", monat: 11227.20, quelle: "https://dserver.bundestag.de/btd/20/112/2011298.pdf", fundstelle: "Drucksache 20/11298, Anpassung zum 1. Juli 2024 (+6,0 %)", datum: "2024-05-07"}
  - {art: abgeordnetenentschaedigung, ab: "2025-07-01", monat: 11833.47, quelle: "https://www.bundestag.de/abgeordnete/mdb_diaeten/mdb_diaeten-214848", fundstelle: "bundestag.de „Entschädigung“; Drucksache 21/5200 Spalte „Betrag seit dem 1. Juli 2025“", datum: "2026-11-02"}
  - {art: abgeordnetenentschaedigung, ab: "2026-07-01", monat: 11833.47, quelle: "https://dserver.bundestag.de/btd/21/063/2106330.pdf", fundstelle: "Anpassungsverfahrensabweichungsgesetz 2026, Drucksache 21/6330 § 1 (Juli 12.330,48 €, August 11.336,46 €, ab September 11.833,47 €)", datum: "2026-07-10"}
  - {art: kostenpauschale, ab: "2026-01-01", monat: 5467.27, quelle: "https://www.bundestag.de/abgeordnete/mdb_diaeten/1334e-260800", fundstelle: "bundestag.de „Kostenpauschale“, Stand Januar 2026; WD 3 - 3000 - 099/25", datum: "2026-11-02"}
  - {art: mitarbeiterpauschale, ab: "2026-05-01", monat: 27396.00, quelle: "https://www.bundestag.de/abgeordnete/mdb_diaeten/1334d-260806", fundstelle: "bundestag.de „Mitarbeiter“, Stand 1. Mai 2026", datum: "2026-11-02"}
  - {art: sachleistungskonto, ab: "2026-01-01", jahr: 12000.00, quelle: "https://www.bundestag.de/abgeordnete/mdb_diaeten/1334f-260802", fundstelle: "bundestag.de „Büroausstattung“: jährlich höchstens 12.000 Euro", datum: "2026-11-02"}
  - {art: amtsaufwand_praesident, ab: "2022-01-01", monat: 1023.00, quelle: "https://www.gesetze-im-internet.de/abgg/__12.html", fundstelle: "§ 12 Abs. 5 AbgG", datum: "2026-11-02"}
  - {art: amtsaufwand_vize, ab: "2022-01-01", monat: 307.00, quelle: "https://www.gesetze-im-internet.de/abgg/__12.html", fundstelle: "§ 12 Abs. 5 AbgG", datum: "2026-11-02"}
  - {art: b11, ab: "2024-03-01", monat: 16084.36, quelle: "https://www.gesetze-im-internet.de/bbesg/anlage_iv.html", fundstelle: "Anlage IV BBesG, Bundesbesoldungsordnung B, gültig ab 1. März 2024 (BGBl. 2023 I Nr. 414)", datum: "2026-11-02"}
  - {art: dienstaufwand_kanzler, ab: "2002-01-01", jahr: 12271.01, quelle: "https://www.gesetze-im-internet.de/bming/__11.html", fundstelle: "§ 11 Abs. 1 Buchst. c BMinG: jährlich 24.000 DM, Umrechnung 1,95583", datum: "2026-11-02"}
  - {art: dienstaufwand_minister, ab: "2002-01-01", jahr: 3681.30, quelle: "https://www.gesetze-im-internet.de/bming/__11.html", fundstelle: "§ 11 Abs. 1 Buchst. c BMinG: jährlich 7.200 DM, Umrechnung 1,95583", datum: "2026-11-02"}
vorsitz_ab: []   # optional: {akte_id, ab, quelle, datum} für den Beginn eines Ausschussvorsitzes
```

- [ ] **Step 2: Failing tests** `tests/test_bezuege.py`

```python
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
```

- [ ] **Step 3: Run** `uv run pytest -q tests/test_bezuege.py` → Expected: FAIL (`bhtracker.bezuege` fehlt).

- [ ] **Step 4: Implement `bezuege.py`** mit den Interfaces oben. Rechenweg in `berechne_bezuege`:
  1. Zeitraum je Funktion: `von = seit or (WP_BEGINN if art == "mdb" else None)`, `bis = bis or stand`; `None` → Zeilen mit `summe=None`, `monate=None`, Hinweis „<Posten>: Zeitraum nicht belegt, keine Summe“. Für mdb ohne `seit` Hinweis „Zeitraum ab Beginn der 21. Wahlperiode (25.3.2025); Eintrittsdatum nicht ausgewertet“. Wenn `seit` vor `WP_BEGINN` liegt, gilt `WP_BEGINN`.
  2. Je Monat `m` in `monate(von, bis)` den Satz per `satz_am(saetze, art, f"{m}-01")` holen; fehlender Satz → Monat zählt nicht, Lückenmonate je Jahr sammeln → Hinweis „<Komponente>: Betrag für <Jahr> noch nicht belegt (<n> Monate)“. `monatlich` ist der Satz des letzten Monats.
  3. mdb: Abgeordnetenentschädigung (§ 11 Abs. 1 AbgG, person), Amtszulage (§ 11 Abs. 2; Komponente „Amtszulage Ausschussvorsitz“ / „Amtszulage Präsidium“; `monatlich = Entschädigung × Faktor`; `summe=None`, es sei denn `vorsitz_ab` gepflegt), Amtsaufwandsentschädigung Präsidium (§ 12 Abs. 5, nur bei Faktor 1 oder 0.5), Kostenpauschale (§ 12 Abs. 2, person), Mitarbeiterpauschale (§ 12 Abs. 3, dritte, Hinweis „fließt an die Mitarbeiter, nicht an den Abgeordneten“), Sachleistungskonto (§ 12 Abs. 4, dritte, `jahr/12`).
  4. regierung: Rolle über `rolle_amt(amt or text)`; Amtsgehalt = B 11 × {kanzler: 5/3, minister: 4/3, parl_sts: 4/3 × 0.75, sts: 1} (§ 11 Abs. 1 Buchst. a BMinG, § 5 Abs. 1 ParlStG, Anlage I BBesG), Dienstaufwandsentschädigung `jahr/12` aus `dienstaufwand_kanzler` bzw. `dienstaufwand_minister` (× 0.75 für parl_sts; keine für sts) (§ 11 Abs. 1 Buchst. c BMinG).
  5. Kürzung § 29 Abs. 1 AbgG: Monate, in denen ein mdb-Zeitraum und ein regierung-Zeitraum (kanzler, minister, parl_sts) zusammenfallen, je Monat `−Entschädigung/2`; nur wenn beide Zeiträume belegt sind, sonst Hinweis „§ 29 Abs. 1 AbgG: Kürzung um 50 % bei Amt und Mandat, Zeitraum nicht belegt“.
  6. Summen: `summe_person` = Summe aller `summe` mit `empfaenger == "person"` (Kürzung negativ), `summe_aufwand` analog für „dritte“; `None`-Zeilen zählen nicht.
  7. Hinweise immer: Juli/August-2026-Technik (wenn 2026-07 im Zeitraum), „Monatsbeträge sind gesetzlich festgelegt; Summen sind daraus gerechnet, keine Einzelabrechnung“, bei regierung „B 11 nach Anlage IV BBesG, Tabellenstand 1. März 2024; spätere Anpassungen noch nicht verkündet“.
  8. `nicht_bezifferbar`: mdb → Dienstreisen/Netzkarte/Büro/IT (§ 12 Abs. 4 AbgG), Zuschuss Kranken- und Pflegeversicherung (§ 27 AbgG), Übergangsgeld (§ 18 AbgG), Altersentschädigung (§§ 19, 20 AbgG), Kürzungen § 14 und § 12 Abs. 6 AbgG, Fraktionszulagen; regierung → Ortszuschlag (§ 11 Abs. 1 Buchst. b BMinG, entfällt bei Amtswohnung § 12 Abs. 1), Übergangsgeld (§ 14 BMinG), Ruhegehalt (§ 15 BMinG), Amtswohnung, Dienstwagen, Beihilfe.
  Rundung mit `Decimal` und `ROUND_HALF_UP` je Monat; Ausgabe als `float`.

- [ ] **Step 5: Run** → Expected: PASS (alle Tests der Datei).

- [ ] **Step 6: Commit** `git add pipeline/src/bhtracker/bezuege.py pipeline/tests/test_bezuege.py data/manual/bezuege.yaml && git commit -m "Bezüge: Modul und Pflegedatei mit amtlichen Sätzen"`

---

### Task 3: Bezüge in die Akten

**Files:**
- Modify: `pipeline/src/bhtracker/personen.py` (Funktion, Akte, roh_identitaeten, build_personen_akten)
- Test: `pipeline/tests/test_personen.py`

**Interfaces:**
- Consumes: `Abgeordneter.aemter`, `Abgeordneter.mitglied_seit` (Task 1); `lade_bezuege`, `berechne_bezuege` (Task 2).
- Produces: `Funktion.amt: str | None` (regierung: `m.amt`), `Funktion.aemter: list[str]` (mdb), `Funktion.seit` für mdb = `mitglied_seit`, wenn es nach `WP_BEGINN` liegt, sonst `None`; `Akte.bezuege: dict | None` in den Shard-Dateien; `index.json`-Eintrag unverändert.

- [ ] **Step 1: Failing tests** (in `test_personen.py`, Setup wie `_raw_mit_abdi`)

```python
def test_akte_traegt_bezuege(tmp_path):
    raw, manual = _raw_mit_abdi(tmp_path)
    (manual / "bezuege.yaml").write_text((MANUAL / "bezuege.yaml").read_text(encoding="utf-8"), encoding="utf-8")
    (manual / "regierung.yaml").write_text(
        'stand: "2026-11-02"\nmitglieder:\n  - {name: "Sanae Abdi", amt: "Parlamentarische Staatssekretärin", ressort: "Bundesministerium für Arbeit und Soziales", epl: "11", seit: "2025-05-06", quelle: "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", mdb_id: 1043330}\n', encoding="utf-8")
    idx = json.loads(build_personen(manual, raw, tmp_path / "build", _seiten(), [], "2026-11-02").read_text(encoding="utf-8"))
    by_id = {e["id"]: e for e in idx["eintraege"]}
    sh = json.loads((tmp_path / "build" / "personen" / f"{by_id['sanae-abdi']['shard']}.json").read_text(encoding="utf-8"))
    b = sh["sanae-abdi"]["bezuege"]
    k = {x["komponente"]: x for x in b["zeilen"]}
    assert k["Abgeordnetenentschädigung"]["summe"] == 246077.79 and k["Amtsgehalt"]["monatlich"] == 16084.36
    assert k["Kürzung der Abgeordnetenentschädigung (Amt und Mandat)"]["monate"] == 19
    assert b["summe_person"] < b["summe_person"] + b["summe_aufwand"]
    reinfrank = next(a for a in idx["eintraege"] if a["id"] == "timo-reinfrank")
    assert reinfrank["sichtbar"] is False    # Vertreter ohne Amt haben keine Bezüge und bleiben wie bisher
    assert all(f.get("amt") is None or f["art"] == "regierung" for f in sh["sanae-abdi"]["funktionen"])
```

- [ ] **Step 2: Run** `uv run pytest -q tests/test_personen.py::test_akte_traegt_bezuege` → Expected: FAIL (`bezuege` fehlt in der Akte).

- [ ] **Step 3: Implement**: `Funktion` um `amt: str | None = None`, `aemter: list[str] = field(default_factory=list)`; `Akte` um `bezuege: dict | None = None`. In `roh_identitaeten`: mdb-Funktion mit `aemter=list(a.aemter)`, `seit=a.mitglied_seit if a.mitglied_seit and a.mitglied_seit > WP_BEGINN else None`; regierung-Funktion mit `amt=m.amt`. In `build_personen_akten`: `saetze = lade_bezuege(manual_dir / "bezuege.yaml")` (fehlende Datei → `[]`), je Akte mit Funktion `mdb` oder `regierung`: `a.bezuege = berechne_bezuege([asdict(f) for f in a.funktionen], saetze, stand)`; `_merge` übernimmt `bezuege=None`. Shard-Ausgabe enthält `bezuege`.

- [ ] **Step 4: Run** `uv run pytest -q` → Expected: alle grün (bisherige Tests prüfen `funktionen[0]` per Index, nicht per Länge; bei Bruch anpassen und im Ledger vermerken).

- [ ] **Step 5: Commit** `git add pipeline && git commit -m "Personen: Bezüge aus dem Amt in den Akten"`

---

### Task 4: Web-Block „Bezüge aus dem Amt“

**Files:**
- Modify: `web/src/lib/model/personen.ts` (Typen, Hilfsfunktion), `web/src/lib/views/Akte.svelte` (Block), `web/src/App.svelte` (Hinweis-Aside Personen um einen Satz), `web/src/lib/model/empfaenger.ts` nur falls `Quelle` erweitert werden muss (nein: `fundstelle` kommt in `quelle.fundstelle`, Typ erweitern in personen.ts lokal).
- Test: `web/tests/personen.test.ts`

**Interfaces:**
- Consumes: `Akte.bezuege` aus Task 3.
- Produces: `interface BezugZeile { posten: string; komponente: string; rechtsgrundlage: string; monatlich: number; zeitraum_von: string | null; zeitraum_bis: string | null; monate: number | null; summe: number | null; empfaenger: "person" | "dritte"; quelle: { kurz: string; url: string | null; fundstelle?: string } }`, `interface Bezuege { zeilen: BezugZeile[]; summe_person: number; summe_aufwand: number; hinweise: string[]; nicht_bezifferbar: string[]; wp_beginn: string }`, `Akte.bezuege?: Bezuege | null`; `export function bezuegeNachPosten(b: Bezuege): { posten: string; zeilen: BezugZeile[] }[]` (Reihenfolge des ersten Auftretens).

- [ ] **Step 1: Failing test**

```ts
describe("bezuegeNachPosten", () => {
  test("gruppiert Zeilen je Posten in Reihenfolge", () => {
    const b: Bezuege = { summe_person: 1, summe_aufwand: 2, hinweise: [], nicht_bezifferbar: [], wp_beginn: "2025-03-25",
      zeilen: [z("Mitglied des Bundestages", "Abgeordnetenentschädigung"), z("Bundeskanzler", "Amtsgehalt"), z("Mitglied des Bundestages", "Kostenpauschale")] };
    expect(bezuegeNachPosten(b).map((g) => [g.posten, g.zeilen.length])).toEqual([["Mitglied des Bundestages", 2], ["Bundeskanzler", 1]]);
  });
});
```
mit `z(posten, komponente): BezugZeile` als Hilfsfunktion im Test.

- [ ] **Step 2: Run** `cd web && npm test -- --run tests/personen.test.ts` → Expected: FAIL.

- [ ] **Step 3: Implement** Typen und `bezuegeNachPosten` in `personen.ts`. In `Akte.svelte` nach dem Block „Organisationen und ihr Geld vom Bund“ einen Block `{#if akte.bezuege}` „Bezüge aus dem Amt“: je Posten eine Überschrift, Tabelle Komponente (mit `rechtsgrundlage` als `<small>`) · monatlich · Zeitraum (`von – bis`, `monate` Monate; bei `summe === null` „Zeitraum nicht belegt“) · Summe · Quelle (Link, `fundstelle` als `title`); Zeilen `empfaenger === "dritte"` mit Tag „an Dritte“. Zwei Summenzeilen: „An die Person ausgezahlt (gerechnet aus den Monatsbeträgen): …“ und „Für die Person aufgewendet (Mitarbeiter, Sachleistungen): …“. Danach `hinweise` als `<ul class="muted small">`, „Nicht bezifferbar“ als Liste. Schlusssatz aus der Spec („Gesetzlich festgelegte Beträge, keine Einzelabrechnung …“). Negative Summen (Kürzung) mit Minuszeichen über `fmtEuro`. Keine Farben außer den vorhandenen.
  In `App.svelte` im Hinweis-Aside „Personen und Netz“ einen Satz: „Bezüge aus dem Amt sind die gesetzlich festgelegten Monatsbeträge mit Fundstelle; was nicht je Person veröffentlicht wird, steht als Lücke dabei.“

- [ ] **Step 4: Run** `npm run check && npm test -- --run` → Expected: 0 Fehler, alle Tests grün.

- [ ] **Step 5: Commit** `git add web && git commit -m "Akte: Block Bezüge aus dem Amt"`

---

### Task 5: Daten, Doku, Prüfung

**Files:**
- Modify: `CONTRIBUTING.md` (Tabellenzeile `data/manual/bezuege.yaml`), `pipeline/README.md` (Absatz Bezüge), `docs/superpowers/specs/…design.md` §7 (3d ✅), `web/public/impressum.html` nur falls dort Akteninhalte aufgezählt sind (dann „Bezüge aus dem Amt“ ergänzen).
- Data: `data/build/personen/*` (Rebuild), `data/build/netz/*` unverändert erwartet.

- [ ] **Step 1: Rebuild** mit dem Scratch-Skript `rebuild_stufe3.py` (Empfänger → Akten → Netz). Expected: `akten` unverändert 12.107, `sichtbar` 949; Shard von `friedrich-merz` enthält `bezuege` mit `Amtsgehalt` 26.807,27 und Kürzungszeile; `sanae-abdi` ohne Amtsgehalt; eine Akte mit „Vorsitzender: …“ (z. B. Verkehrsausschuss) hat Zeile „Amtszulage Ausschussvorsitz“ ohne Summe.

- [ ] **Step 2: Browser**: `#v1;j=2025;a=personen;pe=friedrich-merz` → Block sichtbar mit zwei Summen; `pe=annalena-baerbock` → Zeitraum endet 2025-06-30, 4 Monate. Seite nach dem Rebuild hart neu laden.

- [ ] **Step 3: Doku** anpassen, Spec §7 Stufe 3d abhaken mit Datum, Issue 7 im Commit-Text nennen.

- [ ] **Step 4: Suiten** `cd pipeline && uv run pytest -q`; `cd web && npm run check && npm test -- --run && npm run build` → Expected: grün, Build ohne Fehler.

- [ ] **Step 5: Commit** `git add -A data/build/personen data/build/netz data/build/empfaenger CONTRIBUTING.md pipeline/README.md docs web/public && git commit -m "Stufe 3d: Daten-Build mit Bezügen, Doku (Issue 7)"`

Danach: Review (Opus-Subagent, ganzer Branch, Fokus auf Review Focus 1–6 und Rundung), Fix-Pass, ff-Merge nach `main`, Push.
