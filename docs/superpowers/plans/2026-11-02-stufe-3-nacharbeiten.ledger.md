# SDD ledger — plan: docs/superpowers/plans/2026-11-02-stufe-3-nacharbeiten.md
Spec: §4.7a/§4.7b (gelesen); Funde aus den Ledgern Stufe 3 und 3d
Setup: Ruling: Branch stufe-3-nacharbeiten im selben Checkout — wie bisher.
Pre-flight: T1→T2: Funktion.art regierungsfunktion ↔ FUNKTION_LABELS; Bezugszeile quellen[] ↔ UI zeigt weiter quelle — konsistent.
Task 1: Ruling: Kabinett-Test prüft eine Kachel mit unbekanntem Amt („Hofnarr“) statt eines geänderten „Lebenslauf“-Links — der Parser nimmt ohnehin den letzten Listenlink als Amt — Kosten falls falsch: keine.
Task 1: complete (commits 8b08aa2..08d722c, tests: bash -c 'cd pipeline && uv run pytest -q' → 172 passed in 4.22s)
Task 2: complete (commits 08d722c..eb4b6e1, tests: bash -c 'cd web && npm run check && npm test -- --run' →    Duration  621ms (import 46%, transform 27%, tests 17%, worker 10%))
Task 3: Daten-Build committed (9393308); Browser-Check im Docker nach dem Fix-Pass.
Final review: Opus-Subagent, Commits 08d722c..eb4b6e1 — 0 Critical, 3 Important, 8 Minor; alle Important im Fix-Pass.
Final: fixed I1 Empfänger-Seite nennt laufende Funktion „früher“ — test_laufende_regierungsfunktion_auf_der_empfaenger_seite RED→GREEN (Kategorie „Laufende …“, Satz „hat zugleich …“, Tag „öffentliche Funktion, laufend“)
Final: fixed I2 Haushalts-Soll Akte ≠ Empfängerliste — test_haushalt_soll_mit_globalem_jahr RED→GREEN (globales letztes Jahr wie in der Liste)
Final: fixed I3 Fundstelle von vorsitz_ab fehlt — test_vorsitz_ab_mit_fundstelle_im_hinweis_und_in_quellen RED→GREEN (Plenarprotokoll 21/1 im Hinweis und in quellen)
Final: suite pipeline 175/175, web 130/130, svelte-check 0
Final: Ruling (Declined): Amtszulage und Amtsaufwandsentschädigung Präsidium tageweise bzw. monatsweise wie geplant — Rechtsfrage offen — Kosten falls falsch: wenige Tage je Präsidiumsmitglied.
Final: Ruling (Declined): `ended: false` im Lobbyregister gilt als laufend — Datensemantik des Registers — Kosten falls falsch: Etikett „laufend“ bei beendeter, nicht gemeldeter Funktion.
Final: Ruling (Declined): Sichtbarkeit über `verbindung` auch für laufende Funktionen — eine laufende öffentliche Funktion ist eine stärkere Verbindung als eine frühere — Kosten falls falsch: etwas mehr sichtbare Akten (67).
Final: Ruling (Declined): Hashwechsel a=netz;n=X → a=netz lässt das alte Netz stehen — außerhalb des Fokus, selten — steht.
Final: minor (deferred): „Zeitraum nicht belegt“ auch wenn nur der Satz fehlt (Baerbock 2025) — Text „Betrag für den Zeitraum nicht belegt“ wäre genauer
Final: minor (deferred): quellen[] der Bezugszeile nicht im Web-Typ und nicht angezeigt
Final: minor (deferred): Amtsaufwandsentschädigung Präsidium zählt ganze Monate, im Hinweis nicht erklärt
Final: minor (deferred): _RECHTSFORM mit re.I trifft Nachnamen wie „Holding“; „Firma“ steht im Rohbestand in derselben Zeile, norm_name müsste es streichen
Final: minor (deferred): validate_bezuege prüft keine doppelten akte_id in vorsitz_ab und keine Existenz der Akten-Ids
Final: minor (deferred): parse_kabinett verwirft unbekannte Kacheln ohne Warnung
Final: minor (deferred): ISO-Daten in Pipeline-Hinweisen und Zeitlinie
Final: minor (deferred): zeigeBei blendet auch den Link zur Empfänger-Seite aus (0 Fälle im Build)
