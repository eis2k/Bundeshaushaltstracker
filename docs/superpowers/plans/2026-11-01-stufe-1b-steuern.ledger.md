# SDD ledger — plan: docs/superpowers/plans/2026-11-01-stufe-1b-steuern.md
Spec: docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md §4.8a, §9 (gelesen)
Setup: Branch `stufe-1b` im selben Checkout (wie Stufe 1), Ausgangspunkt main nach Merge der Stufe 1.
Pre-flight (geteilte Schnittstellen):
- T1→T2: steuern.json-Form {szenarien:[{id, modell:{art, basis, satz_alt?, annahmen[]}, geschichte[]}]} ↔ SteuerSzenario in steuern.ts — konsistent.
- T2→T3: aufkommen()/steuerEinnahmen() ↔ AppState.aktiveSteuern, balance(..., extraBund) — konsistent.
- T3→T4: aktiveSteuern.je {id,kurz,gesamt,bund,empfaenger} ↔ Modell-Typ in sankeyData.ts — konsistent.
Task 1: Ruling: Vier Szenarien statt drei — Abgeltungsteuer ergänzt, weil sie die einzige der vier ist, deren Aufkommen überwiegend beim Bund landet und damit im Bundeshaushalt sichtbar wird — Kosten falls falsch: ein Szenario mehr zu pflegen.
Task 1: Ruling: Erbschaftsteuer-Faktor (1,0–2,5) ist eine reine Nutzerannahme; der Umfang der Verschonungen ist amtlich nicht beziffert, daher Standard 1,0 (kein Mehraufkommen, bis der Nutzer den Regler bewegt) — Kosten falls falsch: Modell wirkt im Standard „leer“, ist aber ehrlich.
Task 1: complete (commit a60de07, tests: cd pipeline && uv run pytest -q → 61 passed)
Task 2–3: Ruling: Länder-Steuern (Vermögen-, Erbschaftsteuer) erhöhen die Bund-Einnahmen um 0 €, werden aber im Fluss und in der Kopfzeile als Gesamtaufkommen gezeigt — Spec §4.8a verlangt beides (Bund-Anteil nach Art. 106 GG, Gesamtwirkung sichtbar) — Kosten falls falsch: Leser erwartet weniger Schulden und sieht keine Änderung; das Panel erklärt den Grund ausdrücklich.
Task 2–3: complete (commit 16bf851, tests: npm test → 101 passed, svelte-check 0 errors)
Task 4: Ruling: Modell-Knoten bekommen d3-sankey `fixedValue` = Gesamtaufkommen, statt eines Geists (gestrichelter Umriss) über dem Knoten — der Geist überlappte Nachbarknoten; mit fixedValue ist der Kasten das Gesamtaufkommen, das Band der Bund-Anteil, der leere Rest der Länder-Anteil — Kosten falls falsch: ein Knoten ohne Band (Vermögensteuer) wirkt ungewohnt; Legende und Tooltip erklären ihn.
Task 4: Ruling: Modell-Beschriftung nur bei ausreichender Knotenhöhe oder Auswahl (wie bei allen Knoten), Vollinfo im Tooltip und Panel — zwei Zeilen „immer“ überlappten bei kleinen Beträgen die Nachbarn — Kosten falls falsch: kleine Modelle sind im Fluss nur als Kasten erkennbar.
Task 4: Ruling: Chip-Klick aktiviert und wählt das Modell; ein zweiter Klick auf den bereits gewählten aktiven Chip schaltet es ab — konsistent mit Preset-Chips (an/aus), ohne das Panel beim ersten Klick zu überspringen — Kosten falls falsch: ein Klick zu viel.
Task 4: Ruling: Basiswerte werden nicht auf das gewählte Haushaltsjahr umgerechnet (Basisjahr steht im Panel) — Fortschreibung je Jahr braucht eigene Quellen und ist in der Spec als offen vermerkt — Kosten falls falsch: Modell-Aufkommen in Altjahren zu hoch; der Hinweis im Panel sagt das.
Task 4: complete (commit 0754541, tests: npm test → 102 passed, svelte-check 0 errors, npm run build ok)
Task 5: Ruling: Quelle zum Erbschaftsteuerreformgesetz von dejure.org auf das Bundesgesetzblatt (bgbl.de) umgestellt — Quellenregel §9: nur amtliche Quellen; dejure antwortete beim Linkcheck zudem mit 429 — Kosten falls falsch: keine.
Task 5: Linkcheck: alle 22 Quellen-URLs in steuern.yaml HTTP 200 (1.11.2026).
Task 5: complete (commit 3b85704, tests: pytest 61 passed, npm test 102 passed, build ok)
Final review: opus-Subagent auf dem ganzen Branch (inkl. Arbeitskopie), 0 kritisch, 7 wichtig, 6 klein.
Final: fixed Modell-Knoten im Gesamtfluss nicht anklickbar (click() kehrte im gesamtModus vorher zurück) — Browser-Check Gesamtfluss → Panel öffnet; keine Komponententests im Projekt.
Final: fixed Abgeltungsteuer-Regler erlaubte 20–25 % und kappte die Mindereinnahme auf 0 € — test_satzaenderung_slider_must_not_go_below_satz_alt RED→GREEN (Validator: min < satz_alt ist ein Fehler), min auf 0,25 gesetzt, suite 62/62.
Final: fixed Spitzensteuersatz-Extrapolation über 45 % hinaus unmarkiert — Annahme-Text nennt jetzt, dass die Quelle nur 45 % beziffert und darüber linear fortgeschrieben wird.
Final: fixed „Aufkommen gesamt“ las sich bei Erbschaftsteuer Faktor 1,0 wie „die Steuer bringt 0 €“ — überall „Mehreinnahmen (gegenüber heutigem Recht)“ in Panel, Knotenlabel, Tooltip und Legende.
Final: fixed Erbschaftsteuer-Beschreibung („Verschonung zweimal beanstandet“) widersprach der eigenen Chronik — jetzt „2006 die Bewertung und 2014 die Verschonung“.
Final: fixed Abgeltungsteuer-Beschreibung nannte Dividenden und „Kapitalertragsteuer“, Basis ist aber nur Zins- und Veräußerungserträge — Text an die Basis angepasst.
Final: fixed Modell-Beträge nominal zum Basisjahr, kein Hinweis außerhalb des Panels — Legende und Tooltip sagen es jetzt; Umrechnung je Haushaltsjahr/VPI bleibt offen (Spec §7).
Final: fixed (klein, mit erledigt) Fallback „Länder, Bund 0 €“ auch bei Gemeinschaftsteuer mit 0 € Mehreinnahmen — Label zeigt immer Mehreinnahmen und Bund-Anteil.
Final: fixed (klein, mit erledigt) Werte aus Teilen-Links weder begrenzt noch auf bekannte Annahmen geprüft — normalisiere() in steuern.ts, Test „drops unknown scenarios and keys, clamps values“ RED→GREEN, suite 103/103; Panel zeigt begrenzte Werte.
Final: fixed (klein, mit erledigt) Chips ohne aria-pressed, Regler ohne aria-valuetext/aria-describedby, „seit 1997“ für jeden ausgesetzten Status hart kodiert.
Final: minor (deferred): Unbekannte x:-Ids im Teilen-Link bekommen den Hinweis „betreffen Titel, die es … nicht gibt“ (Panel.svelte); eigener Text für Modelle fehlt.
Final: minor (deferred): Aktiver, nicht gewählter Chip schaltet beim ersten Klick nicht ab, sondern wählt (bewusst, Ruling Task 4).
Final: Ruling: Soli (100 % Bund) nicht in den Bund-Anteil der ESt/Abgeltungsteuer eingerechnet — Art. 106 GG ist die genannte Quelle, der Soli ist eine eigene Steuer — Kosten falls falsch: Bund-Anteil um bis zu 5,5 % des Mehraufkommens zu niedrig.
Final: Ruling: Erbschaftsteuer-Faktor bleibt Nutzerannahme ohne Zahl (Quelle ist das BVerfG-Urteil zur Verschonung, nicht eine Betragsschätzung) — der Umfang der Verschonung ist amtlich nicht beziffert, der Text sagt das — Kosten falls falsch: eine Annahme ohne amtliche Zahl dahinter.
Final: Ruling: Wendungen „weitgehend verschont“, „bleibt im Kern erhalten“ bleiben — sie beschreiben die Rechtslage (BVerfG 2014, ErbStG §§13a/b), keine Wertung — Kosten falls falsch: Leser liest eine Tendenz hinein.
Final: Ruling: „53 % bis 1999“ bleibt als Regler-Obergrenze, obwohl die Einkommensgrenze damals anders lag — der Annahme-Text nennt die Fortschreibung ausdrücklich — Kosten falls falsch: Mehreinnahmen am oberen Ende zu hoch geschätzt.
