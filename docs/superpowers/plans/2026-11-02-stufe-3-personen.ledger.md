# SDD ledger — plan: docs/superpowers/plans/2026-11-02-stufe-3-personen.md
Spec: docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md §4.7a (gelesen)
Setup: Ruling: Branch `stufe-3` im selben Checkout (wie bisher; Rohdaten und Dev-Server bleiben nutzbar) — Kosten falls falsch: keine Isolation gegen main.
Pre-flight (geteilte Schnittstellen):
- T1→T3/T4: Spende(jahr, partei, betrag, spender, …, natuerliche_person) und zuordnen(spenden, stamm_normen) ↔ Akte.spenden, Netz-Kanten spende — konsistent.
- T2→T3/T4: Amtstraeger(name, amt, ressort, epl, seit, bis, quelle, stand, mdb_id) ↔ roh_identitaeten, Posten-Kanten p→m — konsistent.
- T3→T4/T5/T6: Akte (id, sichtbar, funktionen, organisationen, spenden, zeitlinie), shard(id), Index mit shard je Person ↔ build_netz, CLI, Web-Loader — konsistent; Netz-Index {knoten_id: shard} wird in T4 geschrieben, T6 liest ihn.
- T5→T7: Empfänger-Seite personen[].akte_id/akte_sichtbar ↔ EmpfaengerSeite-Links — konsistent.
Task 1: Ruling: Fixture hat drei statt vier Zeilen — in der 2025er Tabelle gibt es keine Zeile mit zwei Drucksachen-Links; Tests entsprechend (3 Zeilen, 1 natürliche Person) — Kosten falls falsch: Fall mit zwei Links ungetestet, Parser nimmt den ersten Link.
Task 1: complete (commits 7be9b10..e3f0980, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_spenden.py' → 4 passed in 0.51s)
Task 2: Ruling: Amtsbezeichnung steht in der Kabinettskachel als zweiter Listenlink (nach „Lebenslauf“), nicht als eigenes Element — Parser nimmt den letzten Listenlink, der nicht „Lebenslauf“ heißt; „Bundesministerium für Digitales und Staatsmodernisierung“ hat keinen eigenen Einzelplan → epl None — Kosten falls falsch: ein Ressort ohne Geld-Kante im Netz.
Task 2: complete (commits e3f0980..7ee75ff, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_regierung.py' → 6 passed in 0.43s)
Task 3: Ruling: Shard-Dateien enthalten nur sichtbare Akten; eine Shard-Datei ohne sichtbare Akte wird gar nicht geschrieben (Test angepasst) — Kosten falls falsch: Web muss fehlende Shard-Datei als „keine Akte“ behandeln (Task 6).
Task 3: Ruling: Kabinett ↔ Bundestag gleichen Namens wird nur mit mdb_id in regierung.yaml zusammengeführt; Titel (Dr., Prof.) zählen beim Namensvergleich nicht — Kosten falls falsch: Minister mit Mandat haben zwei Akten mit Hinweis, bis die mdb_id gepflegt ist.
Task 3: complete (commits 7ee75ff..8b76124, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_personen.py' → 10 passed in 0.54s)
Task 4: Ruling: Ein Ministerium oder eine Partei als Startknoten zeigt seine direkten Nachbarn (gekappt), expandiert aber nicht weiter; als Nachbar im zweiten Schritt erscheint es als Knoten, ohne dass seine Nachbarn folgen — Kosten falls falsch: Umfeld eines Ministeriums ist eine lange Liste, aber keine Explosion.
Task 4: complete (commits 8b76124..32aa2ce, tests: bash -c 'cd pipeline && uv run pytest -q tests/test_netz.py' → 6 passed in 0.56s)
Task 6: complete (commits b4d82be..2775d20, tests: bash -c 'cd web && npm test' →    Duration  585ms (import 45%, transform 27%, tests 17%, worker 11%, environment 1%))
Task 5: complete (commits 32aa2ce..b4d82be, tests: bash -c 'cd pipeline && uv run pytest -q' → 135 passed in 4.57s)
Task 7: Ruling: Netz-Ansicht zeigt bei fehlendem Umfeld einen Satz mit Rückweg zur Personenliste statt leerer Fläche; Randknoten hell — Kosten falls falsch: Nutzer sieht bei nicht freigeschalteten Knoten eine Erklärung statt eines Graphen.
Task 7: complete (commits 2775d20..ed18ba7, tests: bash -c 'cd web && npm run check && npm test -- --run' → 0 errors, 124 passed; Browser: Netz e:amadeu-antonio-stiftung 7 Knoten/9 Kanten, Akte friedrich-merz rendert)
Task 8: Ruling: Nur Vertreter von Empfängern mit Seite bekommen eine Akte (12.108 statt 38.477); Staatssekretäre schrittweise in regierung.yaml (fünf mit Bundestags-Biografie erfasst) — Kosten falls falsch: fehlende Akten für Organisationen ohne Bundesmittel (bewusst), fehlende Staatssekretäre bis zur Pflege.
Task 8: complete (commits ed18ba7..3e617f2, tests: bash -c 'cd pipeline && uv run pytest -q' → 135 passed; Daten-Build committed)
Final review: Opus-Subagent, ganzer Branch 7be9b10..dd7b24b — 1 Critical, 10 Important, 13 Minor; Re-Grading: alle Critical/Important bleiben, Fix-Pass in Commit 0a33d6f.
Final: fixed Critical 1 ausgeschiedene Abgeordnete als amtierend — test_ausgeschiedene_abgeordnete_tragen_ende RED→GREEN (bis-Datum, Text „Mitglied des Bundestages bis …“, Verbindungssatz „MdB bis …“)
Final: fixed Important 1 MdB-Posten fehlen in Akte und Netz — test_mdb_posten_bei_empfaenger_steht_in_akte, test_posten_kante_aus_bundestagsangabe RED→GREEN
Final: fixed Important 2 Filter Bundesregierung verliert Minister mit Mandat — personen.test.ts Funktionsfilter RED→GREEN (Index-Feld arten)
Final: fixed Important 3 Zeitlinie addiert Quellen — personen.test.ts zeitlinieJahre RED→GREEN (lobby/haushalt/spenden getrennt, eigener Maßstab)
Final: fixed Important 4 Zusammenführen nur bei gleichem Namen — test_mdb_id_fuehrt_auch_bei_namensvariante_zusammen, test_manuelles_zusammenfuehren_ueber_namensgrenzen RED→GREEN; Wadephul mit mdb_id 1047914 in regierung.yaml
Final: fixed Important 5 unbelegte Amtsdaten — test_validate_regierung_pflichtfelder (seit optional) RED→GREEN; seit für Bilger, Linnemann, Warken entfernt
Final: fixed Important 6 Schalter — test_ohne_personen_loescht_alte_akten, test_committed_personen_index_ist_relevant, test_cli_akten_alle_braucht_eigenes_out RED→GREEN
Final: fixed Important 7 natürliche Personen in Prüflisten, Privatadresse in Fixture — test_natuerliche_person_mit_anrede_zusatz_und_co RED→GREEN; Fixture synthetisch (Musterfrau)
Final: fixed Important 8 „zurück“ verlässt die Seite — state.test.ts closeNetz RED→GREEN
Final: fixed Important 9 Spenden fehlen auf der Empfänger-Seite — test_ergaenze_akten_schreibt_parteispenden_auf_die_seite RED→GREEN; Abschnitt „Parteispenden der Organisation“
Final: fixed Important 10 personen.yaml ohne Pflichtfeldprüfung — test_validate_personen_pflichtfelder, test_build_personen_bricht_bei_ungueltiger_pflegedatei_ab RED→GREEN
Final: suite pipeline 147/147, web 125/125, svelte-check 0 Fehler
Final: Ruling: ausgeschiedene Abgeordnete der laufenden Wahlperiode bleiben „Amt“ (sichtbar) — sie hatten das Mandat in der betrachteten Periode, die Akte nennt das Ende — Kosten falls falsch: sechs Akten sichtbar, die ein strengerer Leser als „ohne Amt“ einstufen würde.
Final: Ruling: Privatname und Anschrift aus der Spenden-Fixture werden im aktuellen Stand ersetzt (Fixture, Test, Plan), die Historie wird nicht umgeschrieben — Name und Anschrift stehen schon im gepushten Plan-Commit 7be9b10 auf main, ein Rewrite von main (Force-Push) ist Florians Entscheidung — Kosten falls falsch: die Angabe bleibt in der Git-Historie des öffentlichen Repos auffindbar (sie stammt aus der amtlichen Veröffentlichung auf bundestag.de).
Final: Ruling (Declined 1): „≥ 2 gemeinsame Vertreternamen“ zählt die betrachtete Person mit — der Code steht; zwei gleiche Namen bei zwei Organisationen sind ein starker Beleg, die Spec zählt Namen, nicht „andere“ Namen — Kosten falls falsch: eine Zusammenführung zu viel bei zwei Namensvettern, Prüfliste zeigt sie.
Final: Ruling (Declined 2): Ids ohne Suffix können bei neuen Gleichnamigen kippen — Spec-Schema, bleibt; Teilen-Links auf Akten gelten mit Stand-Datum — Kosten falls falsch: alter Link zeigt Hinweis statt Akte.
Final: Ruling (Declined 3): Verbindungssatz für Ausgeschiedene in Stufe 2 mit behoben (gleiche Ursache, drei Zeilen) — Kosten: keine.
Final: Ruling (Declined 4): Digitalministerium ohne eigenen Einzelplan (Ruling Task 2) bleibt — nicht verifiziert — Kosten falls falsch: eine Geld-Kante fehlt.
Final: Ruling (Declined 5): Impressums-Zusage „innerhalb weniger Tage“ ist Betreiberentscheidung, bleibt für Florian zur Prüfung.
Final: Ruling (Declined 6): Netz-Sortiergewicht summiert Lobby- und Haushaltsbeträge nur für die Reihenfolge, nie angezeigt — steht.
Final: Ruling (Declined 7): Öffentlicher Index mit allen Namen (auch nicht freigeschaltete) — Spec erlaubt Namen auf Seiten und im Netz; Index enthält Name und Funktion, keine Akte — steht; Kosten falls falsch: Index auf sichtbare Akten kürzen (Stufe 3b).
Final: Ruling (Declined 8/9): Staatssekretärs-Einträge über die Biografien hinaus und Ort von Organisationsspendern in der lokalen Prüfliste — nicht geprüft bzw. lokal, steht.
Final: minor (deferred): Satzvorlagen — rf.beendet ignoriert, „Frühere öffentliche Funktion“ auch für laufende Mandate, Dopplungen „X bei X“, frühere Funktionen im Stand-Jahr der Zeitlinie
Final: minor (deferred): Partei-Knoten hell mit Tooltip „keine freigeschaltete Akte“
Final: minor (deferred): haushalt_soll_letztes_jahr summiert letztes Jahr je Titel (ausgelaufene Titel mischen sich)
Final: minor (deferred): Laufzeit umfeld (Gewicht/Adjazenz je Start neu); Doppelrechnung in build_akten_und_netz ist mit dem Fix-Pass entfallen
Final: minor (deferred): Spenden-Klassifikator: KG, OHG, KGaA, „Aktiengesellschaft“, Präfix „Firma“
Final: minor (deferred): Identitäts-Randfälle (trennen bei transitiver Kette, Regel b ohne Biografie-Abgleich, name_key faltet Umlaute)
Final: minor (deferred): parse_kabinett prüft Amt nicht gegen AEMTER
Final: minor (deferred): fetch_spenden lädt Vorjahr nie neu
Final: minor (deferred): Web — Wettläufe openAkte/openNetz, a=netz ohne n= zeigt „Lade …“, Netz-Effect bei Breitenänderung, role=button an nicht klickbaren Knoten
Final: minor (deferred): Hinweis „Akte nicht freigeschaltet“ ohne Link zur Empfänger-Seite
Final: minor (deferred): personen/index.json 2 MB für 950 Akten; Impressumssatz „nur auf der Seite ihrer Organisation“ ungenau (auch Netz und Index)
Final: minor (deferred): Plan baut Netz ohne Personen statt gar keins (Spec-Wortlaut)
Final: minor (deferred): Zeitlinie ohne durchgehende Achse, Wahlperiode fehlt, Geld-Kanten verlinken nur bundeshaushalt.de, Tests für Regel b/mdb_id/„≥2 Vertreter“ fehlten (teils im Fix-Pass ergänzt), test_cli nicht wie geplant erweitert
