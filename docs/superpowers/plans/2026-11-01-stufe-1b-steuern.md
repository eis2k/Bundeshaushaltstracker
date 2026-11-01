# Stufe 1b: Steuer-Presets mit Herkunft – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Nutzer können auf der Einnahmenseite Steuer-Szenarien zuschalten (Vermögensteuer, Erbschaftsteuer-Varianten, Spitzensteuersatz, Abgeltungsteuer), deren Annahmen verstellen, die Wirkung auf den Bund in der Bilanz sehen und zu jeder Steuer eine belegte Zeitlinie „Wer hat das beschlossen“ lesen.

**Architecture:** Eine handgepflegte Datei `data/manual/steuern.yaml` beschreibt je Steuer-Szenario Status, Empfänger (Bund/Länder), Aufkommensbasis mit Quelle, ein lineares Modell mit sichtbaren Annahmen und die Geschichte als Liste belegter Ereignisse. Die Pipeline prüft Pflichtfelder und Quellen und kopiert sie als `steuern.json`. Im Rechenkern bekommt das Szenario ein Feld `steuern` (aktive Szenarien mit Annahmewerten); `balance` zählt den Bund-Anteil des Modellaufkommens zu den Einnahmen. Die Fluss-Ansicht zeigt Modellaufkommen als gestricheltes Band „Modell“, die Presets-Leiste eine eigene Gruppe „Steuer-Modelle“, das Panel die Annahmen-Regler, die Wirkung mit Bund-Anteil und den Kasten „Wer hat das beschlossen“.

**Tech Stack:** wie Stufe 1 (Python/uv, Svelte 5, Vite, vitest).

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md`, §4.8a und §2 (Quellenregel).

## Global Constraints

- Jede Annahme und jedes Ereignis trägt eine URL als Quelle; der Build bricht ohne Quelle ab (wie bei Erklärtexten).
- Modelle sind als Modell gekennzeichnet („Rechnung aus den Annahmen, keine Prognose“); Verhaltensanpassungen (Ausweichreaktionen) erscheinen als eigene Annahme mit Standardwert aus der Quelle.
- Steuern, deren Aufkommen den Ländern zusteht (Art. 106 Abs. 2 GG: Vermögensteuer, Erbschaftsteuer), wirken mit Bund-Anteil 0 auf die Bilanz; die Seite sagt das ausdrücklich und zeigt das Gesamtaufkommen daneben.
- Keine Wertung: „Wer hat das beschlossen“ nennt Datum, Gesetz oder Urteil, beschließende Koalition und zuständige Minister mit Quelle, sonst nichts.
- Teilen-Link trägt aktive Steuer-Szenarien und ihre Annahmen.

## Review Focus

1. **Bund-Anteil**: Erbschaft- und Vermögensteuer dürfen die Bund-Bilanz nicht verbessern; der Nutzer sieht Gesamtaufkommen und „davon Bund: 0“. Test in Task 2.
2. **Annahmen außerhalb des Bereichs** (negativer Satz, Freibetrag größer als Bemessungsgrundlage) dürfen keine negativen Aufkommen erzeugen. Test in Task 2.
3. **Link mit unbekanntem Szenario oder unbekannter Annahme**: wird ignoriert und gemeldet wie unbekannte Titel. Test in Task 3.
4. **Jahreswechsel**: Modelle beziehen sich auf eine Aufkommensbasis eines Jahres; in anderen Jahren wird die Basis mit dem Bruttoinlandsprodukt-Verhältnis nicht skaliert, sondern der Hinweis „Basis <Jahr>“ gezeigt. Test in Task 2.
5. **Fehlende Quelle** in der YAML stoppt den Build. Test in Task 1.

---

### Task 1: Datenmodell und Pipeline (`steuern.yaml` → `steuern.json`)

**Files:**
- Create: `data/manual/steuern.yaml`, `pipeline/src/bhtracker/steuern.py`
- Modify: `pipeline/src/bhtracker/cli.py` (Aufruf), `pipeline/README.md`
- Test: `pipeline/tests/test_steuern.py`

**Interfaces:**
- YAML-Form:
  ```yaml
  szenarien:
    - id: vermoegensteuer
      name: Vermögensteuer (1 % oberhalb Freibetrag)
      kurz: Vermögensteuer
      status: ausgesetzt            # erhoben | ausgesetzt | nie_eingefuehrt
      empfaenger: laender           # bund | laender | gemeinsam
      bund_anteil: 0.0              # Anteil des Aufkommens, der beim Bund landet
      beschreibung: zwei Sätze
      modell:
        art: satz_mal_basis         # aufkommen = basis × satz × (1 − ausweich)
        basis: {wert: 4200000000000, text: "Steuerpflichtiges Nettovermögen oberhalb 1 Mio € Freibetrag", jahr: 2024, quelle: URL}
        annahmen:
          - {id: satz, text: "Steuersatz", wert: 0.01, min: 0, max: 0.05, schritt: 0.0025, einheit: "%", quelle: URL}
          - {id: ausweich, text: "Ausweichreaktionen (Aufkommensverlust)", wert: 0.3, min: 0, max: 0.6, schritt: 0.05, einheit: "%", quelle: URL}
      geschichte:
        - {datum: 1995-06-22, titel: "BVerfG: Einheitswerte verfassungswidrig", text: ..., akteure: "Bundesverfassungsgericht, 2 BvL 37/91", quelle: URL}
  ```
  Modellarten: `satz_mal_basis` (Aufkommen = basis × satz × (1 − ausweich)), `satzaenderung` (Aufkommen = basis_pro_punkt × (satz_neu − satz_alt), für den Spitzensteuersatz), `basis_mal_faktor` (Aufkommen = basis × (faktor − 1), z. B. Erbschaftsteuer ohne Verschonung).
- Produces: `validate_steuern(data) -> list[str]`, `build_steuern(manual_file, out) -> Path` (schreibt `steuern.json`, bricht bei Fehlern ab).

- [ ] **Step 1: Failing tests** (`test_steuern.py`): gültige Repo-Datei → keine Fehler; Szenario ohne `quelle` an einer Annahme → Fehler mit „quelle“; `bund_anteil` außerhalb 0..1 → Fehler; Geschichte ohne Datum → Fehler; Build schreibt `steuern.json` mit allen Szenarien-IDs.
- [ ] **Step 2: FAIL** — `uv run pytest tests/test_steuern.py -q`.
- [ ] **Step 3: Implementieren** `steuern.py`, Aufruf in `cmd_build` nach `build_manual`.
- [ ] **Step 4: PASS**, Build laufen lassen.
- [ ] **Step 5: Commit** `"Steuer-Szenarien: Datenmodell und Build"`.

### Task 2: Rechenkern (`steuern.ts`, `balance`)

**Files:**
- Create: `web/src/lib/model/steuern.ts`
- Modify: `web/src/lib/model/types.ts` (Scenario.steuern, SteuerSzenario-Typen), `web/src/lib/model/scenario.ts` (balance), `web/src/lib/model/load.ts`, `web/src/lib/state.svelte.ts`
- Test: `web/tests/steuern.test.ts`, `web/tests/scenario.test.ts` (Ergänzung)

**Interfaces:**
- `Scenario.steuern: Record<string, Record<string, number>>` — aktive Szenarien mit Annahmewerten (Standardwerte beim Aktivieren).
- `aufkommen(szenario: SteuerSzenario, werte: Record<string, number>) -> { gesamt: number; bund: number }`; nie negativ; Werte werden auf `[min, max]` begrenzt.
- `steuerEinnahmen(szenarien: SteuerSzenario[], aktiv: Scenario["steuern"]) -> { gesamt, bund, je: {id, gesamt, bund}[] }`.
- `balance(data, factors, includeSv, extraBund = 0)`: `einnahmen += extraBund`, `neueSchulden` entsprechend; `delta` berücksichtigt es.
- `AppState`: `steuern` (geladen), `aktiveSteuern = $derived(steuerEinnahmen(...))`, `toggleSteuer(id)`, `setAnnahme(id, key, wert)`; `balance` erhält `aktiveSteuern.bund`.

- [ ] Tests: Vermögensteuer 1 % auf 4,2 Bio × (1 − 0,3) = 29,4 Mrd gesamt, Bund 0; Spitzensteuersatz +3 Punkte × basis_pro_punkt, Bund-Anteil 42,5 %; Werte außerhalb des Bereichs werden begrenzt; Bilanz mit extraBund 10 Mrd senkt neueSchulden um 10 Mrd. FAIL → implementieren → PASS → Commit.

### Task 3: Teilen-Link

**Files:** Modify `web/src/lib/model/share.ts`, Test `web/tests/share.test.ts`.
- Form: `;x=vermoegensteuer:satz=0.01:ausweich=0.3,spitzensatz:satz_neu=0.48`; unbekannte Szenarien/Annahmen → `unknownIds`.
- [ ] Tests (Roundtrip, unbekannt), FAIL, implementieren, PASS, Commit.

### Task 4: Oberfläche

**Files:**
- Create: `web/src/lib/ui/SteuerPanel.svelte` (Annahmen-Regler, Wirkung, Bund-Anteil-Hinweis, Zeitlinie „Wer hat das beschlossen“)
- Modify: `web/src/lib/ui/Presets.svelte` (Gruppe „Steuer-Modelle“ mit Status-Markierung), `web/src/lib/ui/Panel.svelte` (Weiche auf SteuerPanel, wenn `selected` mit `x:` beginnt), `web/src/lib/views/sankeyData.ts`/`sankeyGesamt.ts` (Knoten `x:<id>` in Spalte 0, gestrichelt, Farbe steuern, nur Bund-Anteil als Band; Gesamtaufkommen in der Beschriftung), `web/src/lib/ui/Kopfzeile.svelte` (Hinweis „inkl. Modell-Einnahmen“)
- Test: `web/tests/sankeyData.test.ts` (Modellknoten vorhanden, Wert = Bund-Anteil; bei Bund-Anteil 0 kein Band, aber Knoten mit Beschriftung „Länder“).
- [ ] Tests, FAIL, implementieren, PASS, Sichtprüfung im Browser (Vermögensteuer zuschalten: Gesamtaufkommen sichtbar, Bund-Bilanz unverändert; Spitzensatz +3 Punkte: Bund-Einnahmen steigen), Commit.

### Task 5: Inhalte prüfen und abschließen

- [ ] Alle Quellen-URLs in `steuern.yaml` erreichbar (Skript `uv run bht check-links` optional, sonst manuell `curl -I`).
- [ ] README: Abschnitt „Steuer-Modelle“ unter „Was der Bundeshaushaltstracker kann“.
- [ ] Spec §7 Stufe 1b abhaken; Issue 4 schließen.
