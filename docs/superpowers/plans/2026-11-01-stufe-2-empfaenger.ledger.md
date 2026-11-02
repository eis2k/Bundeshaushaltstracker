# SDD ledger — plan: docs/superpowers/plans/2026-11-01-stufe-2-empfaenger.md
Spec: docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md §4.6a (gelesen)
Setup: Ruling: Branch `stufe-2` im selben Checkout statt Worktree — wie Stufe 1 und 1b (Dev-Server, Rohdaten unter data/raw bleiben nutzbar, Florian hat Restentscheidungen delegiert) — Kosten falls falsch: keine Isolation gegen main (main bleibt unberührt, da Branch).
Pre-flight (geteilte Schnittstellen):
- T1→T4/T5: Profil/Person/Zuwendung/Spanne (lobbyregister.py) ↔ verbindungen_aus_profil, baue_stamm — konsistent (Felder nummer, name, personen[].regierungsfunktion, zuwendungen[].typ/spanne).
- T2→T4: Abgeordneter/Angabe ↔ verbindungen_aus_angaben; Test in T4 baut Abgeordneter positional (name, fraktion, url, mdb_id, ausschuesse, angaben, stand, hinweis) — Reihenfolge in T2 so festgelegt, konsistent.
- T3→T5: Projekt ↔ foerderkatalog-Block der Seite (fkz, ressort, thema, von, bis, summe, foerderart) — konsistent.
- T4→T5: Stamm(id, name, aliasse, …Standardwerte), norm_name, slug, ressort_zu_epl, verbindungssatz — konsistent nach Plan-Korrektur.
- T5→T6/T8: index.json mit eintraege[].epls und titel-Karte; Seite ohne Feld "gesamt" — konsistent.
- T6→T7/T8: openEmpfaenger, openEmpfaengerListe({epl}), empfaengerByTitel — konsistent.
Task 1: Ruling: Testerwartung „16 Bundeszuwendungen“ war die Gesamtzahl aller öffentlichen Zuwendungen; der Bund stellt 7 davon — Test prüft jetzt beides — Kosten falls falsch: keine.
Task 1: complete (commits 4fdcdb9..5af63db, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_lobbyregister.py' → 5 passed in 0.14s)
Task 2: complete (commits 5af63db..a01a6bd, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_bundestag.py' → 4 passed in 0.07s)
Task 3: complete (commits a01a6bd..90e8178, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_foerderkatalog.py' → 6 passed in 0.10s)
Task 4: Ruling: empfaenger.yaml startet mit 18 statt 30 geprüften Titel-Empfängern — von den 30 größten Zuwendungstiteln nennen nur 18 einen einzelnen Empfänger, der Rest sind Sammeltitel („Zuschüsse an kulturelle Einrichtungen in Berlin“) — Kosten falls falsch: weniger Titel-Zeitreihen auf Seiten, nachpflegbar.
Task 4: Ruling: Titeltexte stehen gebeugt („an das Deutsche Jugendinstitut“); die Pipeline rät keine Grammatik, sondern löst gebeugte Formen über Aliasse in empfaenger.yaml auf; ohne Alias landet der Name als Kandidat in data/review — Kosten falls falsch: mehr Handarbeit bei Aliassen.
Task 4: complete (commits 90e8178..59c343b, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_empfaenger.py' → 9 passed in 0.38s)
Task 5: offen — build_empfaenger/baue_stamm implementiert und committet (WIP), tests/test_empfaenger_build.py vorhanden, noch nicht grün. Fehlt: CLI (fetch-empfaenger mit --quellen/--limit/--pause, build-Hook nach sozialkassen, --ohne-personen) und lobbyregister.split_gesamtexport/fetch_gesamtexport (Gesamtexport sucheDetailJson statt 6.700 Einzelabrufe; Ruling: eine Anfrage ist schonender, gleiche Daten). Achtung: Patch per Bash-Heredoc hat Steuerzeichen in String-Literale geschrieben → Dateien zurückgesetzt; Patches nur per Write-Tool oder Python-Skriptdatei. Bundestags-Biografien laden im Hintergrund nach data/raw/bundestag (Log im Scratchpad recon/fetch_bundestag.log); Lobbyregister-Gesamtexport liegt im Scratchpad recon/lobby_detail_all.json (484 MB).
Task 6: Ruling: Task 6 vor Abschluss von Task 5 ausgeführt — Task 5 wartet auf den Förderkatalog-Abruf (Stunden) und den Build; Task 6 hängt nur von der JSON-Form aus Task 5 ab, die festliegt — Kosten falls falsch: Nacharbeit an Typen, falls der Build die Form ändert.
Task 6: complete (commits 6eee5ff..1e79ea3, tests: bash -c 'cd web && npm test' →    Duration  589ms (import 45%, transform 27%, tests 17%, worker 11%, environment 1%))
Task 5: complete (commits 59c343b..ddf0a4c, tests: bash -c 'cd pipeline && uv run pytest -q' → 94 passed in 2.55s)
Task 7: Browser-Prüfung: Liste lädt (1.595 Einträge), Suche, Seite Amadeu Antonio Stiftung mit allen Blöcken, Teilen-Link e= lädt direkt, unbekannte Id zeigt Liste mit Hinweis (per Zustandstest), keine Konsolenfehler.
Task 7: Ruling: Hinweistext für die Ansicht Empfänger steht in App.svelte als eigene Seitenleiste statt in Panel.svelte — Panel.svelte ist titelgebunden, ein eigenes Aside hält es sauber — Kosten falls falsch: keine.
Task 8: Browser-Prüfung: Fokus 05 → 0504 → 68740 zeigt im Panel „Empfänger: Goethe-Institut e. V. – Empfänger-Seite öffnen“, Klick öffnet die Seite mit zwei Titeln über zwölf Jahre.
Task 8: Ruling: Suffix „für …“ wird nicht mehr vom Titelnamen abgeschnitten („Stiftung Denkmal für die ermordeten Juden Europas“); zu lange Namen landen als Kandidaten statt falsch zu passen — Kosten falls falsch: etwas mehr Prüfarbeit.
Task 7: complete (commits 1e79ea3..e205b0f, tests: bash -c 'cd web && npm run check' → 1793580559945 COMPLETED 129 FILES 0 ERRORS 0 WARNINGS 0 FILES_WITH_PROBLEMS)
Task 8: complete (commits 6ce2d6c..e205b0f, tests: bash -c 'cd web && npm test' →    Duration  578ms (import 46%, transform 26%, tests 17%, worker 10%))
Task 9: Ruling: 22 statt 25 Empfänger mit Kennzahlen — bei meet2respect (30 gescannte Seiten), Misereor/KZE und vzbv (Jahresberichte ohne lesbare GuV) und Diakonie Deutschland (nur Bilanz) waren keine Zahlen zuverlässig ablesbar; drei Jahresberichte (WWF, DVV, Union der Akademien) nur teilweise — Kosten falls falsch: weniger Kennzahlen-Tabellen, Lücken sind als null mit Hinweis sichtbar.
Task 9: Ruling: Zahlen aus Textextraktion der PDFs (pypdf) übernommen, gescannte Seiten als Bild gelesen (AAS, EZE, Union); je Eintrag Seitenzahl des PDF und Hinweis zu nicht getrennten Posten — Kosten falls falsch: Ablesefehler sind über die Seitenangabe nachprüfbar.
Task 9: complete (commits e205b0f..e689c06, tests: bash -c 'cd pipeline && uv run pytest -q' → 95 passed in 2.69s)
Final review: opus-Subagent auf dem ganzen Branch, 2 kritisch, 5 wichtig, 6 klein; alle 140 automatischen Verbindungen vom Reviewer gegen die Rohnamen geprüft, keine falsch.
Final: Ruling Task 8 war falsch — Titelnamen ohne Stamm-Treffer wurden als eigene Seite veröffentlicht statt als Kandidat; jetzt bekommen nur manuelle Einträge und Lobbyregister-Organisationen eine Seite, Titelnamen ohne Treffer stehen in data/review (test_titel_empfaenger_ohne_stamm_wird_nur_kandidat RED→GREEN).
Final: fixed Verbindungssatz deutete Spenden, entgeltliche und beendete Tätigkeiten als Funktion — eigene Satzvorlage je Kategorie, Vergangenheitsform bei „bis …“ (test_verbindungssatz_je_kategorie_keine_falschen_funktionen RED→GREEN).
Final: fixed Ressort-Zuordnung riet per Rückwärts-Präfix und über „Bund“ — kein Rückwärts-Präfix mehr, Epl 60 nur exakt, Mehrdeutiges bleibt null (test_ressort_zu_epl_ohne_rueckwaerts_praefix_und_exakte_aliasse RED→GREEN).
Final: fixed Prüfliste mit Abgeordnetennamen lag im öffentlichen Repo und blieb bei --ohne-personen gefüllt — data/review/*_kandidaten.yaml in .gitignore, aus dem Index entfernt, ohne Personen leer (test_ohne_personen_leert_verbindungs_prueflisten RED→GREEN).
Final: fixed Förderkatalog-Export auf 100 Zeilen gekappt ohne Hinweis — Feld foerderkatalog_auszug und Hinweistext auf der Seite (test_foerderkatalog_auszug_wird_markiert RED→GREEN).
Final: fixed Titelwerte aus Jahren mit anderem Empfängertext — _werte prüft je Jahr, ob die Zweckbestimmung den Empfänger nennt (test_werte_nur_aus_jahren_mit_passendem_titeltext RED→GREEN).
Final: fixed automatische Verbindungen mit nur einem Beleg und ohne Eigenangabe-Etikett — zweiter Beleg (Lobbyregister oder bundeshaushalt.de) angehängt (test_automatische_verbindung_traegt_beide_belege RED→GREEN).
Final: fixed Laufzeit O(n·m) — StammIndex mit Token-Index, Stoppwörtern und Normen-Cache für Stamm-Aufbau und Verbindungen; suite 103/103.
Final: minor (deferred): e=index lädt index.json als Seite und bricht die Ansicht ab (Id gegen den Index prüfen).
Final: minor (deferred): Biografie ohne Angaben schreibt keinen Logeintrag.
Final: minor (deferred): Klickbare Tabellenzeilen in Empfaenger.svelte ohne Rolle/Link, Leertaste scrollt.
Final: minor (deferred): lade_projekte prüft CSV-Zeilen nicht gegen den Empfängernamen.
Final: minor (deferred): Ids hängen von der Profilreihenfolge ab („-2“-Suffixe), Teilen-Links könnten bei Wegfall eines Profils wechseln.
Final: minor (deferred): Hinweistexte aus ressorts.yaml (KfW, DAAD, GIZ) erscheinen nicht auf der Seite.
Final: Ruling: Gesetzliche Vertreter kleiner Vereine werden genannt — Spec §4.7 zählt Vorstände und Geschäftsführer von Empfängern ausdrücklich zum Personenkreis — Kosten falls falsch: Nennung von Personen, die Florian nicht meinte; der Schalter --ohne-personen bleibt.
Final: Ruling: Aktualität der Biografien (ausgeschiedene Abgeordnete) wird nicht geprüft; jede Verbindung trägt das Abrufdatum — Kosten falls falsch: eine Funktion wird als laufend gezeigt, obwohl das Mandat endete; die Quelle ist verlinkt.
Final: Ruling: Rote Randfarbe der „Id fehlt“-Meldung bleibt — sie betrifft einen kaputten Link, keinen Empfänger — Kosten falls falsch: keine.
Task 10: Förderkatalog-Abruf abgeschlossen (1.440 Empfänger gesucht, 226 mit Projekten, Summe 3,6 Mrd €, ein Export am 100-Zeilen-Limit); Neubau 1.440 Seiten; Tests: pytest 103, vitest 114, svelte-check 0 Fehler, Build ok.
Task 10: complete — README, Spec §7 (Stufe 2 ✅, 2b Personal-Regler), Pipeline-README, Ledger; ff-Merge nach main und Push am 2.11.2026.
