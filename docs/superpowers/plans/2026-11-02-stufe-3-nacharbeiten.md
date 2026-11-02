# Stufe 3 Nacharbeiten – Implementierungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die auf den Akten und im Netz sichtbaren Review-Reste aus Stufe 3 und 3d beseitigen: falsche Etiketten, doppelte Namen, irreführende Zeiträume, helle Partei-Knoten, fehlende Quellen je Bezugszeile, Präsidiumszulage ohne Summe, Lücken in Prüf- und Parserlogik.

**Architecture:** Kleine, getestete Änderungen in `personen.py`, `bezuege.py`, `spenden.py`, `regierung.py` und in den Svelte-Ansichten; Pflegedatei `bezuege.yaml` bekommt `vorsitz_ab` für das Präsidium (Plenarprotokoll 21/1). Kein neues Modul.

**Tech Stack:** wie bisher (Python/pytest, Svelte 5/vitest).

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md` §4.7a, §4.7b; Quelle der Funde: `docs/superpowers/plans/2026-11-02-stufe-3-personen.ledger.md` und `…stufe-3d-bezuege.ledger.md` („minor (deferred)“).

## Global Constraints

- Quellenregel: Tatsachen mit Paragraf oder Fundstelle, keine Wertung; Beträge aus verschiedenen Quellen nie addiert.
- Kein Schätzen; fehlende Daten werden benannt.
- Suiten grün: `cd pipeline && uv run pytest -q`; `cd web && npm run check && npm test -- --run`.

## Review Focus

1. Eine laufende Regierungsfunktion aus dem Lobbyregister (`beendet: false`) darf nicht „Frühere öffentliche Funktion“ heißen. Test Task 1.
2. Die Präsidiumszulage summiert ab 25.3.2025 nur für die fünf gewählten Mitglieder, andere Akten unverändert. Test Task 1.
3. Partei- und Ministeriumsknoten im Netz sind nie „hell“ und tragen keinen Akten-Hinweis. Test Task 2.
4. `#…;a=netz` ohne Knoten zeigt eine Erklärung statt „Lade Umfeld …“. Test Task 2.

---

### Task 1: Pipeline – Sätze, Zeitlinie, Bezugsquellen, Klassifikator, Kabinett

**Files:**
- Modify: `pipeline/src/bhtracker/personen.py`, `bezuege.py`, `spenden.py`, `regierung.py`; `data/manual/bezuege.yaml`
- Test: `pipeline/tests/test_personen.py`, `test_bezuege.py`, `test_spenden.py`, `test_regierung.py`

**Interfaces:**
- Produces: `Funktion.art == "regierungsfunktion"` für laufende Lobbyregister-Regierungsfunktionen (`beendet False`), `"fruehere_regierungsfunktion"` nur bei `beendet True`; Zeitlinien-Text ohne „bei X“, wenn `organisation` schon im Text steht oder `art` in (`mdb`, `regierung`); Zeitlinien-Jahr aus `bis`, wenn `seit` fehlt und `bis` gesetzt ist.
- Produces: `_geld_der_seite`: `haushalt_soll_letztes_jahr` = Summe `soll` nur des jüngsten Jahres über alle Titel.
- Produces: Bezugszeile `quellen: list[{kurz,url,fundstelle}]` (alle verwendeten Sätze, Reihenfolge nach `ab`), `quelle` bleibt der letzte; `validate_bezuege` meldet doppelte `(art, ab)` und Beträge `<= 0`; `vorsitz_ab` wirkt auf Amtszulage und Amtsaufwandsentschädigung Präsidium; Hinweis „Beginn des Vorsitzes nicht belegt“ entfällt dann.
- Produces: `ist_natuerliche_person` erkennt `KG`, `OHG`, `KGaA`, `Aktiengesellschaft`, `& Co.`, `Firma` als Organisation; `parse_spenden` streicht ein führendes „Firma“ aus dem Namen (Zeile wird zur Organisation).
- Produces: `parse_kabinett` übernimmt nur Kacheln, deren Amt mit einem Eintrag aus `AEMTER` beginnt.

- [ ] **Step 1: Failing tests**

```python
# test_personen.py
def test_laufende_regierungsfunktion_heisst_nicht_frueher():
    p = profil_mit("Zweite Stiftung", "R009999", [Person("Amt", "Anna", "Vorstand", "gesetzlicher_vertreter",
                   Regierungsfunktion("STATE_SECRETARY", "Staatssekretärin", "Bundesministerium X", False, None))])
    akten = roh_identitaeten([p], [], [])
    f = next(a for a in akten if a.name == "Anna Amt").funktionen[1]
    assert f.art == "regierungsfunktion" and f.bis is None
    p2 = profil_mit("Zweite Stiftung", "R009999", [Person("Alt", "Bert", "Vorstand", "gesetzlicher_vertreter",
                    Regierungsfunktion("STATE_SECRETARY", "Staatssekretär", "Bundesministerium X", True, "2021-12-08"))])
    f2 = next(a for a in roh_identitaeten([p2], [], []) if a.name == "Bert Alt").funktionen[1]
    assert f2.art == "fruehere_regierungsfunktion" and f2.bis == "2021-12-08"

def test_zeitlinie_ohne_dopplung_und_mit_endjahr(tmp_path):
    # Aufbau wie test_akte_traegt_bezuege (Abdi als Parl. Staatssekretärin); Erwartungen:
    # kein Eintrag endet auf „bei Deutscher Bundestag“, kein Text enthält denselben Organisationsnamen zweimal,
    # und für Tahera Ameer (frühere Regierungsfunktion mit bis) liegt der Posten-Eintrag im Jahr von bis.
```
Konkret für Ameer: Fixture R004511 nennt für sie eine beendete Regierungsfunktion mit `endDate`; der Test liest `bis` aus der Funktion und prüft `any(z["art"] == "posten" and z["jahr"] == int(bis[:4]) and "Ameer" not in z["text"] for z in zeitlinie)`.

```python
def test_haushalt_soll_nur_juengstes_jahr():
    from bhtracker.personen import _geld_der_seite
    seite = {"lobby_zuwendungen": [], "foerderkatalog": [], "haushalt": {"titel": [
        {"id": "a", "werte": {"2024": {"soll": 100}, "2026": {"soll": 300}}}, {"id": "b", "werte": {"2024": {"soll": 50}}}]}}
    assert _geld_der_seite(seite)["haushalt_soll_letztes_jahr"] == 300

# test_bezuege.py
def test_zeile_nennt_alle_verwendeten_saetze():
    b = berechne_bezuege([f("mdb", "MdB")], SAETZE, "2026-11-02")
    e = {x["komponente"]: x for x in b["zeilen"]}["Abgeordnetenentschädigung"]
    assert [q["fundstelle"][:18] for q in e["quellen"]] == ["Drucksache 20/1129", "bundestag.de „Ents", "Anpassungsverfahre"]
    assert e["quelle"] == e["quellen"][-1]

def test_validate_bezuege_dubletten_und_betraege():
    s = {"art": "b11", "ab": "2024-03-01", "monat": 1, "quelle": "https://x", "fundstelle": "f", "datum": "2026-01-01"}
    assert any("doppelt" in e for e in validate_bezuege({"saetze": [s, dict(s)]}))
    assert any("größer als 0" in e for e in validate_bezuege({"saetze": [{**s, "monat": 0}]}))

def test_praesidium_mit_vorsitz_ab_hat_summe():
    b = berechne_bezuege([f("mdb", "MdB", aemter=["Präsidentin: Der Ältestenrat"])], SAETZE, "2026-11-02", vorsitz_ab="2025-03-25")
    z = {x["komponente"]: x for x in b["zeilen"]}
    assert z["Amtszulage Präsidium"]["monate"] == 21 and z["Amtszulage Präsidium"]["summe"] == 237470.27   # 100 % der Entschädigung, tageweise wie diese
    assert z["Amtsaufwandsentschädigung Präsidium"]["summe"] == round(21 * 1023.0, 2)
    assert not any("Beginn des Vorsitzes nicht belegt" in h for h in b["hinweise"])

def test_repo_vorsitz_ab_praesidium():
    data = yaml.safe_load((MANUAL / "bezuege.yaml").read_text(encoding="utf-8"))
    ids = {v["akte_id"] for v in data["vorsitz_ab"]}
    assert {"julia-kloeckner", "andrea-lindholz", "josephine-ortleb", "omid-nouripour", "bodo-ramelow"} <= ids
    assert all(v["ab"] == "2025-03-25" and "21001" in v["quelle"] for v in data["vorsitz_ab"])

# test_spenden.py
def test_organisationsformen_und_firma():
    for n in ["Athos KG", "Muster OHG", "Muster SE & Co. KGaA", "Deutsche Vermögensberatung Aktiengesellschaft DVAG", "Joh. Berenberg, Gossler & Co. KG"]:
        assert not ist_natuerliche_person(n), n
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html").replace("<span>ProMinent GmbH</span>", "<span>Firma</span><br /><span>ProMinent GmbH</span>"), 2025)
    cdu = next(x for x in sp if x.partei == "CDU")
    assert cdu.spender == "ProMinent GmbH" and cdu.natuerliche_person is False

# test_regierung.py
def test_parse_kabinett_verwirft_unbekannte_aemter():
    html = fixture_text("kabinett_ausschnitt.html").replace("Lebenslauf", "Vita", 1)
    assert all(any(m.amt.startswith(a) for a in AEMTER) for m in parse_kabinett(html, "2026-11-02", ressorts()))
```

- [ ] **Step 2: Run** die vier Testdateien → Expected: FAIL (neue Tests), Rest grün.
- [ ] **Step 3: Implement** gemäß Interfaces; `bezuege.yaml` bekommt fünf `vorsitz_ab`-Einträge `{akte_id, ab: "2025-03-25", quelle: "https://dserver.bundestag.de/btp/21/21001.pdf", fundstelle: "Plenarprotokoll 21/1, Wahl der Präsidentin (TOP 5) und der Vizepräsidenten (TOP 6)", datum: "2025-03-25"}`; `validate_bezuege` prüft `fundstelle` auch dort. In `berechne_bezuege` zählt `vorsitz_ab` als `von` für Amtszulage und Amtsaufwand mit `tageweise=True` wie die Entschädigung.
- [ ] **Step 4: Run** `uv run pytest -q` → Expected: alle grün.
- [ ] **Step 5: Commit** `git add pipeline data/manual/bezuege.yaml && git commit -m "Nacharbeiten Stufe 3: Satzvorlagen, Zeitlinie, Bezugsquellen, Präsidium, Klassifikator, Kabinett"`

---

### Task 2: Web – Etiketten, Netz, Zeiträume, leere Netzansicht

**Files:**
- Modify: `web/src/lib/model/personen.ts`, `web/src/lib/model/format.ts`, `web/src/lib/views/Akte.svelte`, `web/src/lib/views/Netz.svelte`, `web/src/App.svelte`, `web/src/lib/state.svelte.ts`
- Test: `web/tests/personen.test.ts`, `web/tests/state.test.ts`, `web/tests/format.test.ts` (anlegen, falls nicht vorhanden)

**Interfaces:**
- Produces: `FUNKTION_LABELS.regierungsfunktion = "Öffentliche Funktion laut Lobbyregister"`; `fmtDatum("2025-03-25") === "25.3.2025"` (ungültig → Eingabe unverändert); `AppState.netzLeer: boolean` ist `true`, wenn `view === "netz"` und kein `netzStart` (init mit `a=netz` ohne `n=`).
- Akte: „bei X“ nur, wenn `organisation` nicht schon in `text` enthalten ist; Zeiträume im Bezüge-Block mit `fmtDatum`; Zeile mit `summe === null` zeigt „Zeitraum nicht belegt“ (auch bei `monate === 0`); Kostenpauschale-Zeitraum zeigt gedecktes Intervall (`zeitraum_von`/`zeitraum_bis` kommen aus der Pipeline unverändert, die UI ergänzt „(n Monate mit Satz)“).
- Netz: `hell` und Hinweis „(keine freigeschaltete Akte)“ nur für `art === "person" && !seite`; `role="button"`/`tabindex` nur bei `seite`; Legende „hell: Person ohne freigeschaltete Akte“.
- App: `a=netz` ohne Knoten → „Kein Knoten gewählt. Ein Umfeld öffnet sich von einer Akte oder Empfänger-Seite aus.“ plus Knopf.

- [ ] **Step 1: Failing tests** – `fmtDatum`, Label `regierungsfunktion`, `state.init("#v1;j=2025;a=netz")` → `netzLeer === true`, `netzFehlt === null`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4:** `npm run check && npm test -- --run` → grün.
- [ ] **Step 5: Commit** `git add web && git commit -m "Nacharbeiten Stufe 3: Etiketten, Netzknoten, Zeiträume, leere Netzansicht"`

---

### Task 3: Daten, Prüfung, Abschluss

- [ ] Rebuild (`rebuild_stufe3.py`), Stichproben: Akte `tahera-ameer` ohne „Frühere“ bei laufender Funktion (falls zutreffend), `julia-kloeckner` mit Summe der Amtszulage, Netz `e:evonik-industries` mit nicht hellem Partei-Knoten.
- [ ] Browser: Docker neu bauen (`docker compose up -d --build`) und `http://localhost:8080/#v1;j=2025;a=personen;pe=julia-kloeckner` prüfen.
- [ ] Suiten, Commit `Nacharbeiten Stufe 3: Daten-Build`, Review (Opus, Fokus Review Focus 1–4), Fix-Pass, ff-Merge, Push.
