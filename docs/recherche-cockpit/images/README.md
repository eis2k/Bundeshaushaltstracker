# Detail-Mockups (Leitlinie für die Oberfläche)

Drei ausgearbeitete Entwürfe aus dem Design-Chat (2.11.2026), von Florian als Vorlage freigegeben. Alle Zahlen, Namen, Logos, Porträts und Verbindungen darin sind **illustrativ** und keine Tatsachenbehauptung.

| Datei | Inhalt |
|---|---|
| `01-recherche-cockpit.webp` | Collage: Recherche-Cockpit (Kennzahlen, Geldfluss-Überblick, Schnelleinstiege, Entwicklung), Verflechtungsnavigator (Netz mit Porträts und Logos, Detailkarte), Vergabeanalyse, Auffälligkeiten-Explorer, Entwicklungsplan in vier Phasen, Datenquellen |
| `02-wer-profitiert-deutsche-bahn.webp` | Empfänger-Detailseite „Wer profitiert?“: Profilkarte mit Logo, Geldquelle → Empfänger → Verwendung, „Auf einen Blick“ (Ministerium, Minister, Vorstand), Verbindungsnetz, Personen mit Porträts und Parteikennung, Zeitverlauf der Zahlungen, Verträge, politische Verbindungen, Quellen |
| `03-geldfluesse-und-profiteure.webp` | Dashboard: Seitenleiste (Dashboard, Haushalt, Geldflüsse & Profiteure, Ministerien, Empfänger & Verträge, Haushaltssimulator, Zeitvergleich, Politik & Verantwortung, Analysen, Berichte & Export), Kopf mit Suche und Jahr, Sankey Steuern → Bundeshaushalt → Ministerien → Empfänger mit Logos, Karte „Politische Verantwortung“ mit Ministerporträt, Teaser für Empfänger, Ministerium, Politik, Simulator |

Umsetzung: Spec §4.10/§4.11 (Stufen 4a bis 4c). Vergabeanalyse und Auffälligkeiten-Explorer brauchen eigene Datenquellen und eine rechtliche Entscheidung (§7, Stufen 5 und 6).

## Übergabepaket vom 2.11.2026 (Zip „Alle freigegebenen Mockups“)

Geprüft am 2.11.2026. Inhalt und Befund:

| Teil | Befund |
|---|---|
| `01_Original_PNG` (3 Dateien, je ~2 MB) | Dieselben drei Collagen wie oben, gleiche Pixelmaße; hier bleiben die kleineren WebP-Fassungen, die PNG-Originale liegen im Zip bei Florian. |
| `02_Zusaetzliche_Ansichten_PNG` → [`../skizzen/`](../skizzen/) (9 PNG) | **Neu.** Laut Übergabe-README „vereinfachte, neu erstellte Layoutskizzen, keine Original-Renderings“. Alle neun folgen einer Schablone: Seitenleiste, Titel mit Unterzeile, Filterleiste „Zeitraum · Soll/Ist · Ressort · Empfänger · Quellenstatus“, „Recherchepfad“ aus vier Schrittkarten, rechts „Quellen & Prüfpunkte“ (drei Grundsätze). Ansichten: Geldfluss, Empfänger, Verflechtungen, Vergaben, Auffälligkeiten, Simulator, Zeitvergleich, Titelansicht, Mobil. |
| `03_Editierbare_SVG` → [`../skizzen/`](../skizzen/) (9 SVG) | Dieselben Skizzen als SVG. |
| `04_Dokumentation` → [`../uebergabe/`](../uebergabe/) | README, Entwicklungsplan (7 Punkte, Abnahmekriterien), Bildauswahl. |

**Was daraus übernommen wird.** Die Grundsätze der Prüfpunkte (Soll/Ist getrennt, Beleg je Relation, Zuwendung ≠ Vergabe ≠ Auszahlung, Datenlücken sichtbar, Hinweis ist keine Schuldzuweisung) sind bereits Regeln des Projekts (Spec §2, §4.6a, §4.11). Der „Recherchepfad“ entspricht dem bestehenden Pfad (Spur) und wird als Schrittkarten gestaltet. Die Skizzen-Seitenleiste (mit Vergaben, Auffälligkeiten, Titelansicht, Mobil) ersetzt **nicht** die Navigation der Detail-Collage; Leitlinie bleiben laut Übergabe-README die drei Original-PNGs.

**Was nicht übernommen wird und warum.** Vergaben und Auffälligkeiten: Stufen 5 und 6, Entscheidung offen (keine Datenquelle, rechtliche Prüfung). „Titelansicht“ als eigene Seite: der Weg Einzelplan → Kapitel → Titel existiert im Fluss; eine Titel-Detailseite mit Historie wäre ein eigener Schritt. Filter „Quellenstatus“: es gibt noch kein Statusfeld je Datensatz, das sich filtern ließe; Kandidat für eine spätere Stufe.

## Viertes Bild: „Vollständiges Mockup-Paket – Alle Navigationseinträge“ (2.11.2026, von Florian)

`04-mockup-paket-alle-navigationseintraege.png`: Collage mit 16 Kacheln, eine je Navigationseintrag des Entwurfs. Geprüft gegen Spec §4.11 und den Stand von Stufe 4c:

| Kachel | Stand | Befund |
|---|---|---|
| 01 Recherche-Cockpit (Startseite) | gebaut | entspricht dem Dashboard (Kennzahlen, Geldfluss-Überblick); Zähler „Auffälligkeiten“ bewusst nicht. |
| 02 Geldflüsse (Donut Ausgaben nach Bereich, Reiter Überblick/Einnahmen/Ausgaben/Geldströme/Entwicklung) | teilweise | Sankey, Herkunft/Verwendung und Zeitvergleich sind da; **Donut „Ausgaben nach Bereich“** fehlt – aus den Einzelplänen direkt baubar (Kandidat Stufe 4d). |
| 03 Ministerien (Tabelle mit Änderung zum Vorjahr, Anteil) | teilweise | Detailkarte und Karten sind da; **Tabellenansicht mit Veränderung ggü. Vorjahr** fehlt – Vorjahr wird seit 4c geladen, also baubar (Kandidat 4d). Reiter „Ressortwechsel“: Ressortzuschnitte wechseln, dafür gibt es keine Konkordanz im Bestand → offen. |
| 04 Empfänger (Top-Empfänger, Nach Branche, Nach Ministerium, Entwicklung) | weitgehend | Liste mit Filtern nach Art und Einzelplan vorhanden; „Branche“ = unsere Empfänger-Art; Entwicklung je Empfänger steht auf der Detailseite. |
| 05 Vergabenanalyse | nicht gebaut | Stufe 5, Florians Entscheidung (Datenquelle service.bund.de/TED). |
| 06 Auffälligkeiten-Explorer | nicht gebaut | Stufe 6, rechtliche Prüfung, Florians Entscheidung. |
| 07 Zeitachse (Ereignisse: Entwürfe, Förderprogramme, Gesetzesänderungen) | nicht gebaut | braucht eine gepflegte Ereignisliste mit Quellen (Drucksachen, Bundesgesetzblatt); keine Datenquelle im Bestand → eigene Stufe, falls gewünscht. |
| 08 Dossiers, 14 Favoriten, 15 Einstellungen (Hell/Dunkel, Benachrichtigungen) | nicht gebaut | Nutzerkonten und gespeicherte Recherchen gibt es nicht (keine Konten, keine Cookies); Teilen-Links übernehmen die Rolle. Dunkelmodus wäre über die Tokens machbar (Kandidat 4d, klein). |
| 09 Daten & Quellen (Tabelle Quelle, Inhalt, Aktualisiert, Status) | teilweise | Datenstatus-Leiste und Fußzeile nennen Stand und Quelle; **eine eigene Seite „Daten & Quellen“** mit allen Quellen, Abrufdatum und Lizenz fehlt – aus dem Index baubar (Kandidat 4d). |
| 10 Verflechtungsnavigator | gebaut | Netz „Umfeld zeigen“ mit Belegpanel; Porträts/Logos in 4b. |
| 11 Simulation | gebaut | Haushaltssimulator mit Reglerkarten und Ergebniskarte. |
| 12 Regionen & Karte (Bundesländer) | nicht gebaut | Der Bundeshaushalt weist Ausgaben nicht nach Ländern aus; nur der Förderkatalog nennt Orte → eigene Stufe mit klarer Beschränkung auf Projektförderung, falls gewünscht. |
| 13 Vergleich & Entwicklung | gebaut | Zeitvergleich und Dashboard-Entwicklung. |
| 16 Mobilansicht | gebaut | untere Navigation mit „Mehr“, Karten statt Tabellen. |

**Baubar ohne neue Datenquelle (Vorschlag Stufe 4d, klein):** Donut „Ausgaben nach Bereich“ auf Geldflüsse, Ministerien-Tabelle mit Veränderung zum Vorjahr, Seite „Daten & Quellen“, Dunkelmodus. Alles andere braucht Daten oder Florians Entscheidung (Stufen 5, 6, Zeitachse, Regionen, Konten).
