# GUI-Weiterentwicklung – Review vom 02.11.2026

## Ausgangslage
README und web/package.json geprüft. Stufe 1 ist lokal lauffähig; Svelte 5, Vite 8, TypeScript 6, D3-Sankey/Hierarchy/Force und Vitest sind vorhanden. Dies ist eine konzeptionelle UX-Prüfung, kein vollständiges Codeaudit oder Browser-Test.

## Gestaltungsrichtung
Ein klares, zugängliches Civic-Data-Produkt mit drei Hauptwegen: **Verstehen**, **Vergleichen**, **Gestalten**. Desktop mit kompakter Seitenleiste; mobil mit vereinfachter Navigation. Light Mode als Standard, Dark Mode optional. Keine wertenden Warnfarben für politische Ausgaben.

## Mockup A: Überblick
KPI-Zeile (Einnahmen, Ausgaben, Saldo, Investitionen), Jahr- und Soll/Ist-Wahl, zentrale interaktive Sankey-Grafik. Bei Auswahl eines Flusses öffnet sich ein Detailpanel mit Betrag, Haushaltsstruktur, Quelle und Abrufdatum. Keine frei erfundenen Summen; fehlende Daten explizit kennzeichnen.

## Mockup B: Haushaltssimulator
Zwei Spalten: links Eingriffe mit Zahlenfeldern und Reglern, rechts Differenz zum offiziellen Haushalt und Folgen für betroffene Kassen. Szenarien zurücksetzen, teilen und als CSV exportieren. Stets Label **Modellrechnung, keine Prognose**; rechtliche Voraussetzungen und Annahmen offenlegen. Doppelzählungen zwischen Bund und Sozialkassen vermeiden.

## Mockup C: Zeitvergleich und Recherche
Zeitreihen mit Soll/Ist-Umschalter und optional realen Preisen, Rangliste der größten absoluten und relativen Veränderungen, Filter nach Ressort/Kapitel/Titel und Quellenpanel. Vergleichbarkeit bei Ressortzuschnitten und Titeländerungen explizit erklären.

## Umsetzung – priorisiert
1. Informationsarchitektur und Design Tokens (Typografie, Abstände, Farben, Zustände) festlegen.
2. Globale Datenstatus-Komponente: Jahr, Soll/Ist, Stand, Quelle, fehlende Daten.
3. Sankey-Interaktion inkl. Breadcrumbs, Tastaturbedienung und Detaildrawer.
4. Simulator mit reversiblen Änderungen, Validierung, Szenario-Link und erklärbarer Bilanz.
5. Zeitvergleich mit Inflation, Titelmapping und sichtbarer Datenabdeckung.
6. Mobile Ansichten, WCAG-Tests, Performance-Budgets und visuelle Regressionstests.
7. Empfänger- und Personenrecherche erst bei belastbarer, menschlich geprüfter Zuordnung erweitern.

## Akzeptanzkriterien
- Jede veröffentlichte Zahl ist mit Quelle, Stand und Datentyp verknüpft.
- Soll, Ist und Simulation sind optisch und semantisch unterscheidbar.
- Nutzer können von einer Gesamtzahl bis zum Titel navigieren und zurück.
- Kein stillschweigendes Addieren inkompatibler Finanzströme.
- Alle wesentlichen Interaktionen funktionieren per Tastatur und auf Mobilgeräten.
- Screenshots/Designentwürfe sind illustrative Mockups, nicht amtliche Daten.

## Nächste technische Prüfung
Svelte-Komponentenstruktur, bestehende Mockups, Datenverträge, Pipeline-Summenprüfungen, Tests und Bundlegröße im Detail untersuchen, bevor Komponenten ersetzt werden.
