# SDD ledger — plan: docs/superpowers/plans/2026-11-02-stufe-4b-bilder.md
Spec: §4.13 (gelesen); Branch stufe-4b, nach dem Merge von 4d auf main rebased.
Pre-flight: T1 bilder.json-Schema → T2 Bild-Typ/T3 Bildnachweise; T2 Avatar id-Prop → alle Aufrufe — konsistent.
Task 1: Ruling: data/raw ist git-ignoriert; Rohantworten (raw/bilder) werden nicht versioniert, nur bilder.json — Kosten: Rebuild ohne Netz braucht einen vorherigen fetch-bilder.
Task 1: Ruling: SPARQL liefert je Bild eine Zeile; je Item zählt die erste (Dedupe nach qid), sonst wären 33 Personen fälschlich mehrdeutig — Test ergänzt.
Task 1: complete (commits 4264952..9b16460, tests: uv run pytest -q → 190 passed)
Task 2: complete (commits c8fbbda..2e7dbac, tests: npm run check && npm test -- --run → 196 passed)
Task 3: Ruling: Spec/Plan nannten data/raw/bilder im Commit; entfällt (ignoriert). Favicons bewusst nicht gebaut (§4.13).
Task 3: complete (commit 10a2ba2, tests: 197 web, 190 pipeline; Browser: Politik 14/14 Bilder geladen, Netz 3 Bilder, Bildnachweise 897 Zeilen)
Final: fixed W1 Datenschutzerklärung (Wikimedia-Absatz, no-referrer) — kein Modelltest (HTML)
Final: fixed W2 Suche ohne Mandat (uselang=de, ohne Titel, Label gleich, politiker|politician) — test_suche_nur_mit_gleichem_label… RED→GREEN; Namensvetter-Test RED→GREEN
Final: fixed W3 bilder.json bleibt ohne Rohdaten — test_build_bilder_ohne_rohdaten_behaelt_alte_datei RED→GREEN
Final: fixed W4 Urheber (versteckte Spans, Attribution, Unknown author, …, Restrictions, Thumb-Rückfall) — test_commons_meta_unbekannter_urheber_und_attribution RED→GREEN
Final: fixed W5 norm_person mit Wortgrenze — test_norm_person_laesst_vornamen… RED→GREEN
Final: fixed Minors 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 13, 14 (Prüfliste bei mehreren Nummern, Logos ohne P582 alphabetisch, Netz-Tooltip, object-position, --logo-bg, Akte-Porträt, quelle-Pflicht, Rohdateien am Ende, ohne_bild, Spec CC0/Impressum-Link, Thumb-Rückfall, erstes Bild)
Final: minor (deferred): 10 Vorschaubilder sind 120 px statt 96 px (Commons liefert feste Breiten); quelle/stand stehen einmal oben in bilder.json statt je Eintrag
Final: Ruling: SVG <image> bekommt kein referrerpolicy-Attribut (Typ kennt es nicht); stattdessen <meta name=referrer content=no-referrer> für die ganze Seite plus Attribut am <img> — Kosten: keine (die Seite sendet ohnehin keine Referrer an Dritte)
Final: Korrektur nach dem Fix-Pass: Backspace-Byte statt \b im Urheber-Muster (Heredoc-Artefakt) — Test grün nach Reparatur; Ergebnis 403 Porträts, 495 Logos, 10 verworfen (4 davon CC ohne Urheber), 2 in Prüfliste (K+S), 241 relevante Akten ohne Treffer.
