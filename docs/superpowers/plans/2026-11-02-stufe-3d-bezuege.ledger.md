# SDD ledger — plan: docs/superpowers/plans/2026-11-02-stufe-3d-bezuege.md
Spec: docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md §4.7b (gelesen)
Setup: Ruling: Branch `stufe-3d` im selben Checkout (wie Stufen 2 und 3) — Kosten falls falsch: keine Isolation gegen main.
Pre-flight (geteilte Schnittstellen):
- T1→T3: Abgeordneter.aemter (Strings „Rolle: Gremium“), mitglied_seit (ISO) ↔ Funktion.aemter, Funktion.seit — konsistent.
- T2→T3: berechne_bezuege(list[dict], saetze, stand) mit Dict-Schlüsseln art/text/seit/bis/stand/amt/aemter ↔ asdict(Funktion) liefert diese Schlüssel plus weitere — konsistent (zusätzliche Schlüssel werden ignoriert).
- T3→T4: Akte.bezuege {zeilen, summe_person, summe_aufwand, hinweise, nicht_bezifferbar, wp_beginn} ↔ Bezuege-Typ in personen.ts — konsistent.
Task 1: complete (commits 2629396..dadb22d, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_bundestag.py' → 6 passed in 0.08s)
Task 2: complete (commits dadb22d..5aa4287, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_bezuege.py' → 9 passed in 0.11s)
Task 3: complete (commits 5aa4287..0a457c0, tests: bash -c 'cd pipeline && uv run pytest -q' → 159 passed in 4.37s)
Task 4: Ruling: neue Hilfe fmtEuroCent statt fmtEuro — fmtEuro rundet auf Euro und kürzt ab einer Million zu „Mio €“, gesetzliche Beträge brauchen Cent — Kosten falls falsch: eine zusätzliche Formatfunktion.
Task 4: complete (commits 0a457c0..7cd5fc1, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  610ms (import 45%, transform 28%, tests 16%, worker 10%))
Task 5: Ruling: Kürzungszeile bekommt Beginn und Ende als Datum (Schnitt der Zeiträume) statt Monatskürzel — im Browser-Check aufgefallen, Test ergänzt — Kosten falls falsch: Anzeige.
Task 5: complete (commits 7cd5fc1..a33f7a1, tests: bash -c 'cd pipeline && uv run pytest -q && cd ../web && npm run check && npm test -- --run' →    Duration  656ms (import 46%, transform 26%, tests 17%, worker 10%, environment 1%))
Final review: Opus-Subagent, ganzer Branch 2629396..b826abf — 2 Critical, 5 Important, 13 Minor; Re-Grading: alle Critical/Important bleiben (I1 und I2 waren als Spec-Fragen markiert, Florian hat die Entscheidungen delegiert → Builder entscheidet).
Final: fixed C1 30-%-Kappung § 29 Abs. 1 AbgG — test_parlamentarischer_staatssekretaer_mit_mandat_kappung RED→GREEN (min aus 50 % Entschädigung und 30 % Amtsgehalt je Monat)
Final: fixed C2 Nachrücker ohne Eintritt — test_parse_bio_liest_nachfolger, test_nachruecker_erbt_eintritt_vom_vorgaenger RED→GREEN (Tag nach dem Ausscheiden des Vorgängers, dessen Biografie als Quelle)
Final: fixed I1 Teilmonate § 32 AbgG — test_abgeordnete_seit_wahlperiode, test_nachruecker_und_ausgeschiedene RED→GREEN (Erst-/Austrittsmonat tageweise 1/30, Kostenpauschale bis Ende Folgemonat)
Final: fixed I2 Beschriftung der Summen — Textänderung in Akte.svelte und Spec („Gesetzlicher Anspruch“, „Höchstbeträge“), kein Test (reiner Text), svelte-check grün
Final: fixed I3 Rechnungsprüfungsausschuss — test_rolle_amt_und_amtszulage RED→GREEN
Final: fixed I4 Eintritt „laut Biografie“ — test_seit_hinweis_wird_uebernommen, test_parse_bio_eintritt_nur_jahr RED→GREEN (Jahr ohne Monat liefert kein Datum; Hinweis im Kopf und im Block)
Final: fixed I5 Ernennungen 6.5.2025 — regierung.yaml: Reiche, Hubig, Prien, Wildberger mit Plenarprotokoll 21/2 (Eidesleistung), test_repo_regierung_yaml_ist_gueltig grün
Final: suite pipeline 163/163, web 126/126, svelte-check 0 Fehler
Final: Ruling: I1 tageweise Rechnung nach § 32 Abs. 8 AbgG umgesetzt statt Florian zu fragen — er hat die Entscheidungen delegiert, und volle Monate überzeichnen jede Summe systematisch — Kosten falls falsch: Rechenregel in bezuege.py änderbar, Summen ändern sich um einen Teilmonat.
Final: Ruling: I1 Beginn der Ansprüche bleibt der 25.3.2025 (konstituierende Sitzung), obwohl § 32 Abs. 1 AbgG auf die Feststellung des Bundeswahlausschusses abstellt — das Datum der Feststellung ist nicht belegt — Kosten falls falsch: wenige Tage je Abgeordnetem zu wenig.
Final: Ruling: I2 Beschriftungen „Gesetzlicher Anspruch“ / „Höchstbeträge“ statt „ausgezahlt“ / „aufgewendet“ — die Quellen belegen Ansprüche und Höchstbeträge, keine Auszahlungen — Kosten falls falsch: Florians Wortwahl war „ausgezahlt“, die Beschriftung ist vorsichtiger als sein Satz.
Final: Ruling (Declined 1): Juli/August-Technik 2026 aus Drs. 21/6330 selbst gelesen (Gesetzestext § 1), steht; für im Juli 2026 Ausgeschiedene gerechnet mit 11.833,47 € — Kosten falls falsch: eine Akte um 497,01 € zu niedrig.
Final: Ruling (Declined 2): Kostenpauschale 2025 bleibt leer, WD 3-099/25 nennt nur den Wert ab Januar 2026 — steht.
Final: Ruling (Declined 3): VG Berlin VG 5 K 805/22 nicht gelesen, Spec-Regel „Amtierende ohne Zulage“ steht — Kosten falls falsch: sieben Akten ohne 1.775,02 €/Monat.
Final: Ruling (Declined 4): November 2026 zählt bei Stand 2.11. voll (Zahlung im Voraus) — steht.
Final: Ruling (Declined 5): keine Kürzung bei fehlendem seit (Bilger, Linnemann, Warken, Schweitzer) — Spec-Festlegung mit Hinweis, steht — Kosten: Summe der Entschädigung dieser vier zu hoch, im Block benannt.
Final: Ruling (Declined 6–8): Paragrafen der Sachleistungen ergänzt (§§ 16, 17), Kabinettsdaten aus Stufe 3 und Staatsminister ohne Mandat nicht Teil dieses Branches.
Final: minor (deferred): Quelle je Zeile nennt nur den letzten Satz, nicht alle verwendeten Drucksachen
Final: minor (deferred): Zeitraum der Kürzung über alle Funktionen gebildet; nur bei einem Regierungsamt exakt
Final: minor (deferred): Präsident/Vizepräsident ohne Gremiumsprüfung erkannt, Testformat „Präsidium“ erfunden
Final: minor (deferred): Hinweis „Beginn des Vorsitzes nicht belegt“ auch für das Präsidium (Wahl 25.3.2025 als vorsitz_ab pflegbar)
Final: minor (deferred): bezuege.yaml: `ab` teils Stand- statt Gültigkeitsdatum, `datum` uneinheitlich (Drucksache vs. Abruf)
Final: minor (deferred): § 12 Abs. 6 AbgG (Dienstwagen −25 % Kostenpauschale) bei Regierungsmitgliedern und Präsidium nicht abgezogen, nur genannt
Final: minor (deferred): UI zeigt „(0 Monate)“ statt „Zeitraum nicht belegt“ bei leeren Summen; Zeitraum der Kostenpauschale zeigt Funktionszeitraum statt gedecktes Intervall; Daten ISO statt deutsch
Final: minor (deferred): validate_bezuege prüft weder doppelte (art, ab) noch Beträge ≤ 0
Final: minor (deferred): schwacher Test summe_person < summe_person + summe_aufwand
Final: minor (deferred): WP_BEGINN ohne Quelle im Hinweis (Plenarprotokoll 21/1)
Final: minor (deferred): doppelte Hinweise bei mehreren Funktionen (mit merke() entschärft), B-11-Hinweis je Regierungsamt
