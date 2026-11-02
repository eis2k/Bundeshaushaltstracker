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
