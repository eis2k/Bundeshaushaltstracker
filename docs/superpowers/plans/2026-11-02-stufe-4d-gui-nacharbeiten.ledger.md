# SDD ledger — plan: docs/superpowers/plans/2026-11-02-stufe-4d-gui-nacharbeiten.md
Spec: §4.12 (gelesen); Branch stufe-4d im selben Checkout (Ruling wie 4c).
Pre-flight: T3 chef()/vorgaenger() → Verantwortung, Dashboard (T1 ändert Dashboard zuerst: Anteil, Linien; T3 ersetzt dort nur die Chef-Auswahl); T4 ViewId daten → share VIEWS, navigation, App; T5 Tokens → alle Ansichten (nach T1–T4, damit keine Konflikte) — konsistent.
Task 1: complete (commits 6ee6a0e..18fa536, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  861ms (import 42%, transform 33%, tests 16%, worker 10%))
Task 2: complete (commits 18fa536..9f49974, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  781ms (import 39%, transform 35%, tests 15%, worker 10%))
Task 3: complete (commits 9f49974..6fbafc3, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  747ms (import 44%, transform 30%, tests 16%, worker 10%))
Task 4: complete (commits 6fbafc3..1c44fe3, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  775ms (import 39%, transform 35%, tests 15%, worker 10%))
Task 5: complete (commits 1c44fe3..19c6a69, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  849ms (import 41%, transform 32%, tests 16%, worker 11%))
Task 6: Ruling: t=gesamt nur im Fluss (view fluss) bei Fokus; Karte/Säulen kodieren wie bisher ohne t= — Kosten: keine.
Task 6: complete (commit e35db7b); Browser-Check des eingebetteten Umfelds und npm run build stehen noch aus (Limit erreicht).
OFFEN: Review (Opus), Fix-Pass, ff-Merge nach main, Push, docker compose up -d --build.
Task 6: complete (commits 19c6a69..e35db7b, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  997ms (import 41%, transform 36%, tests 13%, worker 9%))
Final: fixed C1 Tabellenänderung aus Rohdaten (ministerienTabelle(liste, jahr, vorjahr)) — 'C1: Tabellenänderung nominal…' RED→GREEN
Final: fixed I1/I2 Kontrast dunkel (--nav-on #2563eb, Steuer-Umschalter nav-on/nav-on-fg) — Browser-Token geprüft
Final: fixed I3 Steuer-Modelle als Posten 'modell' in Herkunft und Mini-Fluss — 'I3: Steuer-Modelle…' RED→GREEN
Final: fixed I4 Sozialkassen-Zeile und Sondervermögen; Spec §4.12 korrigiert — 'I4: …' RED→GREEN. Ruling: Sozialkassen = DRV/BMG/BA, Sondervermögen gehören zur Haushaltszeile (Spec hatte SV und Sozialversicherung verwechselt) — Kosten: keine
Final: fixed I5 ringFarben ohne Doppelung — 'I5: …' RED→GREEN; Spec vermerkt
Final: fixed I6 Sortierung amtierend vor ausgeschieden — 'I6: …' RED→GREEN
Final: fixed M1 (Texte-Stand aus Texten, Steuer-Modelle ohne Stand), M2 (fmtDatum), M3 (Teaser-Betrag effektiv), M4 (Test Ist-Mischung), M5 (untrack), M6 (kompaktes Netz: Zoom nur mit Strg, keine Kantenklicks), M7 (Ringraster), M8 (Bereichszustand), M9 (Amt und Hinweis in der Tabelle), M10 (Legende, Leerzeichen, README, Theme-Inline-Skript)
