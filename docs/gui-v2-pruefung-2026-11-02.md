# Prüfung der GUI-v2-Mockups und Entwicklungspläne (2.11.2026)

Geprüft: Pull Request 8 (`docs/mockups/gui-v2`, sieben SVG-Mockups, Galerie, Plan „Wer profitiert?“), Pull Request 9 (`docs/recherche-cockpit`, vier SVG-Mockups, Entwicklungsplan, Bildauswahl) und `docs/gui-review-2026-11-02.md` auf `main`. Beide PRs enthalten nur Dokumentation; sie können gefahrlos gemergt werden (Florians Entscheidung, siehe Empfehlung 4). Maßstab der Prüfung: die Spec (`docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md`), die Quellenregel (§2) und der heutige Stand der Anwendung (Stufen 1 bis 3d).

## Ergebnis in einem Satz

Die Prinzipien sind gut und decken sich mit dem, was gebaut ist; die Mockups sind zu grob, um sie eins zu eins umzusetzen, liefern aber drei brauchbare Strukturentscheidungen; zwei Vorschläge (Vergabeanalyse, Auffälligkeiten-Explorer) sind neue Stufen mit eigener Daten- und Rechtsfrage und brauchen Florians Entscheidung.

## Was die Mockups zeigen

- Elf SVG-Wireframes mit identischem Raster: helle Seitenleiste (v2: Geldflüsse, Ministerien, Empfänger, Verbindungen, Zeitvergleich, Simulator; Cockpit: Recherche-Cockpit, Geldflüsse, Verflechtungen, Vergaben, Auffälligkeiten, Quellen), drei Kennzahlenkarten mit „Datenstatus · Quellenbeleg“, ein Hauptfeld „Geldfluss und Verbindungen“ mit den Spalten Steueraufkommen → Ressort/Titel → Empfänger/Person, rechts eine Spalte „Recherche-Details“ beziehungsweise „Beleg · Datum · Relationstyp“.
- Alle Inhalte sind Platzhalter („Auswahl / Detail“); kein Mockup zeigt echte Daten, Zustände, Regler oder Fehlerfälle. Die in `BILDAUSWAHL.md` genannten detaillierten PNG-Entwürfe aus dem Chat liegen nicht im Repository.
- Farbe und Ton: hell, blau-weiß, ruhig; keine dunkle Navigation. Das passt zur heutigen Seite.

## Abgleich mit Spec und Stand

| Vorschlag | Stand heute | Bewertung |
|---|---|---|
| Jede Zahl mit Jahr, Soll/Ist, Quelle, Abrufdatum, Datenstatus | Jahresleiste, Soll/Ist-Schalter, Quellen je Titel, Akten und Bezüge mit Fundstelle; kein zentraler Datenstatus-Balken | Gut, umsetzen: eine Datenstatus-Leiste, die auf jeder Ansicht Jahr, Soll/Ist, Stand und Quelle zeigt |
| Keine erfundenen Empfänger, gleiche Namen nicht zusammenführen, Quellen nie addieren | Seit Stufe 2 und 3 so gebaut (Spec §4.6a, §4.7a) | Erfüllt, nichts zu tun |
| Zuständigkeit ≠ persönliche Entscheidung über eine Zahlung | Netz zeigt nur belegte Kanten, Minister nur als Posten-Kante zum Ministerium | Erfüllt |
| Seitenleiste als Hauptnavigation statt Reiterleiste | Reiter in der Kopfzeile (Fluss, Karte, Säulen, Gewachsen, Empfänger, Personen) | Gut, umsetzen: Seitenleiste auf dem Desktop, untere Leiste mobil; Ordnung nach „Verstehen · Vergleichen · Gestalten · Recherchieren“ |
| Breadcrumbs / Recherchepfad, der die Geldfluss-Herkunft nicht verliert | Zustand steckt im Link; zurück-Knöpfe je Ansicht, kein durchgehender Pfad | Gut, umsetzen: Recherchepfad (Topf → Einzelplan → Titel → Empfänger → Person → Umfeld) mit Rücksprung |
| Belegpanel beim Klick auf eine Kante (Fundstelle, Datum, Zeitraum, Status) | Kanten haben Quelle und Stand nur als Tooltip | Gut, umsetzen: Klick auf Kante öffnet Belegpanel |
| Mobile Stufenansicht des Geldflusses | Sankey skaliert, keine Stufenansicht | Sinnvoll, zweite Priorität |
| Tastaturbedienung, Design Tokens, Zustände für fehlende Daten | Teilweise (Netz-Knoten, Hinweise) | Sinnvoll, mitnehmen |
| Simulator mit CSV-Export, „Modellrechnung, keine Prognose“ | Regler, Presets, Steuer-Modelle, Teilen-Link vorhanden; kein Export | Kleiner Zusatz, später |
| Vergabeanalyse (Auftraggeber, Auftragnehmer, Vergabeart, Vertragswert) | Nicht vorhanden, keine Datenquelle angebunden | Neue Stufe: braucht Vergabedaten (service.bund.de, TED) und eine Zuordnung zu Titeln, die der Haushalt nicht hergibt; Florians Entscheidung |
| Auffälligkeiten-Explorer (Kostenanstieg, Konzentration, zeitliche Überschneidung) | Nicht vorhanden; „Was ist gewachsen?“ zeigt Veränderungen neutral | Konflikt mit der Quellenregel „keine Wertung“, auch wenn als „Recherchehinweis“ benannt; rechtlich heikel vor der Veröffentlichung; Florians Entscheidung |
| „Projekte und Verträge“ je Empfänger | Förderkatalog je Empfänger vorhanden (gekappt auf 100 Zeilen) | Teilweise erfüllt |

## Was nicht passt oder fehlt

- Die Mockups treffen keine Entscheidung, die über die Struktur hinausgeht: kein Umgang mit 1.440 Empfängern, 12.000 Akten oder einem Sankey mit 8.000 Titeln. Dafür gibt es die heutigen Ansichten (Suche, Kappung, Umfeld), die die Mockups nicht zeigen.
- „Ministerien“ als eigene Ansicht gibt es heute indirekt (Einzelplan im Fluss, Empfängerliste nach Einzelplan). Ob eine eigene Ministeriumsseite mit Leitung, Titeln und Empfängern sinnvoll ist, folgt aus der Seitenleiste; sie wäre eine kleine Zusatzansicht.
- Die Entwicklungspläne nennen keine Tests, keine Datenverträge und keine Reihenfolge, die zum bestehenden Code passt; die Phase 0 „Bestandsaufnahme“ ist dieses Dokument.

## Empfehlung

1. **Umsetzen als Stufe 4a „GUI v2“** (Spec §4.10): Seitenleiste mit vier Gruppen, Datenstatus-Leiste, Recherchepfad mit Rücksprung, Belegpanel für Kanten im Netz, mobile untere Navigation, Design Tokens zusammengefasst; alles auf den vorhandenen Ansichten, keine Neuentwicklung.
2. **Nicht jetzt:** Vergabeanalyse und Auffälligkeiten-Explorer. Beide brauchen eine Entscheidung über Datenbeschaffung und rechtliches Risiko; Vorschlag ist, sie als Stufen 5 und 6 in §7 zu notieren und erst nach dem öffentlichen Start zu bewerten.
3. Die Mockup-PNGs aus dem Chat nachreichen, falls sie mehr zeigen als die SVGs; sonst gelten die SVGs als Strukturvorgabe.
4. Pull Requests 8 und 9 mergen (nur Dokumentation), damit Mockups und Pläne neben diesem Bericht in `main` liegen.
