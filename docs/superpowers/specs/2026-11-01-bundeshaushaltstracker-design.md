# Bundeshaushaltstracker – Konzept

Name des Projekts: **Bundeshaushaltstracker** (Florians Entscheidung, 1.11.2026). „Haushaltsbaukasten“ bezeichnet im Weiteren den Umbau-Teil (Regler, Presets, Teilen) innerhalb des Bundeshaushaltstrackers.

Stand: 1. November 2026. Ergebnis des Brainstormings mit Florian. Die Mockups, auf die dieses Dokument sich bezieht, liegen unter `docs/mockups/` (Dateien 01 bis 06; es sind HTML-Fragmente aus dem Brainstorming-Werkzeug, im Browser ohne Rahmen-CSS nur grob darstellbar).

## 1. Absicht und Warum

Deutschland hat Rekordsteuereinnahmen, und trotzdem werden Leistungen gekürzt, in der Rente, bei den Krankenkassen, an vielen Stellen. Das Werkzeug soll die Frage beantwortbar machen: **Wo bleibt das Geld, wenn mehr hereinkommt als je zuvor?** Und es soll die Vermutung prüfbar machen, dass sich Einzelne an öffentlichen Mitteln bereichern, indem es Geldflüsse und belegte Personenverbindungen nebeneinanderlegt.

Die offiziellen Daten sind vollständig vorhanden (bundeshaushalt.de liefert jeden Haushalt seit 2012 bis auf Titelebene), aber die Darstellung ist schlecht, eine Auswertung ist nicht möglich, Sozialkassen fehlen, Empfänger fehlen, Personen fehlen. Diese Lücke füllt der Haushaltsbaukasten.

Das Werkzeug ist eine **öffentliche Website für alle**, keine private Analyseumgebung.

## 2. Ziele, Nicht-Ziele, Anti-Ziele

### Ziele

1. Jeder kann den Geldfluss des Staates von Steuern und Beiträgen bis zum Empfänger verfolgen, zurück bis 2015.
2. Jeder kann den Haushalt umbauen, wie er es für richtig hält (Regler, Presets, eigene Presets), sieht die Wirkung sofort und kann sein Ergebnis per Link teilen.
3. Auffälliges rutscht von selbst nach oben: Eine Rangliste zeigt, was über zehn Jahre gewachsen ist, filterbar nach Empfänger-Art.
4. Jeder Empfänger und jede Person in öffentlicher Funktion hat eine Seite mit belegten Geldflüssen, Posten und einer Zeitlinie, in der Geld und Posten nebeneinanderstehen.
5. Jede Zahl und jeder Pfeil trägt eine sichtbare, anklickbare Quelle.
6. Arbeit daran und Benutzung sollen Spaß machen. Die Oberfläche ist kein Behördenportal.

### Nicht-Ziele (bewusst nicht Teil des Vorhabens)

- Keine Prognosen über Folgen in der echten Welt (Armutsquoten, Wirtschaftswachstum). Auswirkungen sind Rechnung, nicht Modell, mit einer Ausnahme: die "System übernehmen"-Presets im Ländervergleich, die als Modell gekennzeichnet sind.
- Keine Landes- und Kommunalhaushalte in der ersten Fassung. Länder tauchen nur als Empfänger von Bundesgeld auf.
- Keine Benutzerkonten, kein Login, keine serverseitige Speicherung von Nutzerdaten. Geteilte Haushalte stecken vollständig im Link.
- Keine eigene Recherche jenseits öffentlicher, amtlicher oder registerbasierter Quellen (keine Presseberichte als alleinige Quelle für Personenverbindungen).

### Anti-Ziele (das wäre ein Fehlschlag, auch wenn es technisch funktioniert)

- Die Seite behauptet oder suggeriert Korruption oder Bereicherung. Sie zeigt Belege, nie Urteile. Keine Wertungen, keine Farbcodierung "verdächtig", keine Vermutungen.
- Eine Verbindung oder Zahl ohne Quelle erscheint auf der Seite.
- Eine Privatperson ohne öffentliche Funktion wird gezeigt.
- Die Seite wirkt wie eine Verschwörungstafel (Vollnetz aller Knoten). Das Netz zeigt immer nur einen Ausschnitt.
- Der Nutzer dreht am Personal und glaubt, er habe den Haushalt saniert, weil die Seite den Anteil am Gesamthaushalt verschweigt.

## 3. Entscheidungen aus dem Brainstorming (so, wie Florian sie getroffen hat)

| Thema | Entscheidung |
|---|---|
| Hauptansicht | **Geldfluss (Sankey) ist Standard.** Karte (Treemap) und Säulen (zwei Säulen Einnahmen/Ausgaben) sind per Umschalter erreichbar. |
| Einnahmen und Ausgaben | Stehen in jeder Ansicht gegenüber. Beide Seiten sind veränderbar. |
| Hineinzoomen | Im Fluss hängt jeder Klick rechts eine Spalte an (Woher → Topf → Ministerium → Kapitel → Titel → Empfänger); die Herkunft bleibt links sichtbar; nicht fokussierte Flüsse verblassen; gestrichene Beträge bleiben als Geisterband sichtbar. Karte und Säulen zoomen klassisch hinein. |
| Sozialkassen | **Beides:** Startbild ist der Gesamtfluss (Steuern blau, Beiträge lila → Töpfe: Bundeshaushalt, Rentenkasse, Krankenkassen, Pflege, Arbeitslosenversicherung → Wofür → Empfänger). Klick auf einen Topf folgt nur ihm. Bundeszuschüsse sind als Querband Bund → Sozialkasse gezeichnet und in der Gesamtsumme nur einmal gezählt. |
| Zeit | **Jahresleiste 2015 bis 2025** in der Kopfzeile zum Ziehen, mit Abspielen. Umschalter Soll / Ist / inflationsbereinigt. Dazu die Ansicht **"Was ist gewachsen?"**: Rangliste aller Titel mit Wert Startjahr, Wert Endjahr, Zuwachs, Verlaufskurve; sortierbar nach Prozent oder Euro; Filter: Zuwendungen an Vereine/NGOs, Firmen, Personal, Geschrumpft. Jede Zeile öffnet den Titel im Fluss. |
| Presets | Vorgefertigte Szenarien als Chips (z. B. Rentenzuschuss halbieren, Verteidigung verdoppeln, Entwicklungshilfe streichen, Schwarze Null), kombinierbar, plus eigene Presets. Individuelle Einstellung jedes Titels weiterhin möglich. |
| Auswirkung | Exakte Rechnung in der Bilanz (Einnahmen, Ausgaben, neue Schulden, Abstand zum Original). Pro Regler ein Satz Einordnung ("entspricht etwa 15 % der Rentenausgaben"), gekennzeichnet als Rechnung, keine Prognose. |
| Empfänger | Eigene Seite pro Empfänger: Geld vom Bund über zehn Jahre, aus welchen Titeln und Ministerien, Rang unter Empfängern gleicher Art; Organisation (Rechtsform, Lobbyregister, Vorstand/Geschäftsführung); belegte Verbindungen zur Entscheidungsseite; Zeitlinie Geld und Posten nebeneinander. |
| Personenverbindungen | **Beides: Netz zum Finden, Akte zum Belegen.** Jede Person in öffentlicher Funktion hat eine Akte (Ämter, Mandate, Posten, Zeitlinie, Quellen). Ein Knopf "Umfeld zeigen" öffnet das Netz nur für den Ausschnitt zwei Schritte weit. Klick auf einen Knoten öffnet dessen Akte. Die Akte ist das, was geteilt wird. |
| Ländervergleich | **Beides: Tafel als Beleg, Preset als Spiel.** Vergleichstafel (DE, SE, DK, NO, NL, AT) mit Kennzahlen aus OECD/Eurostat auf jeder Themenseite. Für drei bis vier Themen (Rente, Gesundheit, Verwaltung) zusätzlich ein "System übernehmen"-Preset, das die Regeln des anderen Landes auf deutsche Zahlen überträgt; jede Annahme sichtbar und selbst ein Regler; groß als Modell gekennzeichnet. |
| Personal und Kostenstruktur | Dritter Schnitt desselben Haushalts: **nach Kostenart** (Hauptgruppen: Personal, Sachausgaben, Zinsen, Zuweisungen/Zuschüsse, Investitionen) und **nach Empfänger-Art** (Länder, Sozialkassen, Firmen, Vereine, Ausland). Personal-Regler: Stellen pro Behörde × Durchschnittskosten je Stelle; eigener Regler für Berater- und Gutachterkosten. Auswirkung zeigt immer den Anteil am Gesamthaushalt. |
| Quellenregel | Jede Zahl, jeder Pfeil trägt ein Quellen-Etikett mit Link. Ohne Quelle kein Eintrag. Nur Personen in öffentlichen Funktionen (Minister, Staatssekretäre, Abgeordnete, Vorstände und Geschäftsführer von Empfängern). |
| Technik und Betrieb | Statische Website ohne Server-Logik, Daten vorab berechnet, getrennte Daten-Pipeline, Beziehungen als gepflegte Liste mit Quelle und Datum. **Hosting auf einem Hostinger-VPS** (Florians Entscheidung). Programmiersprache und Bibliotheken überlässt Florian dem Builder (meine Vorschläge unten). |

## 4. Das Produkt im Detail

### 4.1 Startbild

Kopfzeile: Logo, Bilanz (Steuern + Beiträge, Ausgaben gesamt, neue Schulden, Abstand zum Original), Ansichtswechsel (Fluss, Karte, Säulen, Was ist gewachsen?). Darunter die Jahresleiste mit Abspielen und Soll/Ist/inflationsbereinigt. Darunter die Preset-Chips mit Teilen-Knopf. Dann der Gesamtfluss. Rechts ein Panel, das immer das zeigt, was gerade ausgewählt ist (Pfad, Original, Dein Wert, Schieber, Schnellwerte 0/50/100/150 %, Betragseingabe, Erklärtext in zwei Sätzen, Auswirkung in einem Satz, Markierung Gesetz/frei, Empfänger, Quellen).

Mobil: Panel wird zur Schublade von unten; Fluss wird vertikal gescrollt oder auf Karte umgestellt. Der Builder entscheidet die Details; die Seite muss auf dem Handy benutzbar sein, weil geteilte Links dort geöffnet werden.

### 4.2 Hierarchie und Regler

Vier Ebenen wie im echten Haushalt: Bund → Einzelplan → Kapitel → Titel. Regler auf jeder Ebene. Ein Regler auf höherer Ebene skaliert alle Titel darunter proportional, außer solchen, die der Nutzer einzeln gesetzt hat. Jeder Titel trägt eine Markierung **Gesetz** (gesetzlich festgelegt, z. B. Zinsen, Rentenzuschuss nach § 213 SGB VI) oder **frei**; veränderbar ist trotzdem alles, aber die Seite sagt, dass dafür ein Gesetz geändert werden müsste.

Einnahmenseite: Steuerarten (Lohnsteuer, Umsatzsteuer, Einkommen-/Körperschaftsteuer, Energiesteuer, übrige) und sonstige Einnahmen, ebenfalls mit Reglern. Für die Sozialkassen: Beiträge mit Beitragssatz als Regler.

### 4.3 Sozialkassen

Töpfe: Bundeshaushalt, Gesetzliche Rentenversicherung, Gesetzliche Krankenversicherung, Soziale Pflegeversicherung, Arbeitslosenversicherung. Jeder Topf hat Einnahmen (Beiträge, Bundeszuschüsse, sonstige) und Ausgaben in der Gliederung, die die jeweilige Statistik hergibt (gröber als der Bundeshaushalt). Der Bundeszuschuss ist in beiden Töpfen dieselbe Zahl: drehen im Bund ändert ihn in der Rentenkasse. Doppelzählungen werden in der Gesamtsumme herausgerechnet und erklärt.

### 4.4 Teilen

Der komplette Zustand (Jahr, Ansicht, alle vom Original abweichenden Werte, aktive Presets) ist im Link kodiert. Öffnen eines geteilten Links zeigt den Haushalt des anderen mit Hinweis "Haushalt von jemand anderem, du kannst weiterbauen". Keine Speicherung auf dem Server. Der Link soll eine Vorschau (Open-Graph-Bild mit Bilanz) erzeugen können; der Builder entscheidet, ob das in der ersten Fassung vorgerendert wird.

### 4.5 "Was ist gewachsen?"

Siehe Entscheidungstabelle. Zusätzlich: Umschalter der Ebene (Einzelplan, Kapitel, Titel), Zeitraum wählbar (Start- und Endjahr), Spalte "neu" für Titel, die es im Startjahr nicht gab. Jede Zeile trägt ihre Quelle.

### 4.6 Empfänger-Seiten

Empfänger sind: Sozialversicherungsträger, Länder, Kommunen (aggregiert), Unternehmen, Vereine/NGOs/Verbände, internationale Organisationen, Ausland. Für die erste Fassung werden nur die Empfänger gezeigt, die aus amtlichen Listen eindeutig hervorgehen (Haushaltsrechnung, Zuwendungslisten aus Antworten der Bundesregierung, Förderdatenbank). Ein Titel, dessen Empfänger nicht aufgeschlüsselt vorliegen, endet im Fluss mit "Empfänger nicht veröffentlicht" und einem Hinweis, wie man eine Anfrage nach dem Informationsfreiheitsgesetz stellen kann (Link zu FragDenStaat).

### 4.7 Personen-Akten und Netz

Personenkreis: Mitglieder der Bundesregierung, Parlamentarische und beamtete Staatssekretäre, Mitglieder des Bundestags, Vorstände und Geschäftsführer von Empfängern, registrierte Lobbyisten laut Lobbyregister. Keine anderen.

Akte: Name, Funktion(en) mit Zeitraum, Posten in Organisationen mit Zeitraum, welche dieser Organisationen Geld aus welchen Titeln bekamen, Nebentätigkeiten laut Bundestag, Parteispenden der verbundenen Organisationen laut Bundestagsdrucksache, Zeitlinie, Quellen. Jeder Eintrag trägt Quelle, Datum der Quelle und Datum der Aufnahme.

Netz: Knoten sind Personen, Organisationen, Ministerien/Ausschüsse; Kanten sind Geld (blau), Posten (rot), Spende (grün), jeweils mit Zeitraum. Nur zwei Schritte um den Startknoten. Kein Vollnetz.

Hinweis- und Korrekturweg: Auf jeder Akte und Empfänger-Seite ein Knopf "Fehler melden / Beleg einreichen". Einreichungen werden vor Veröffentlichung von einem Menschen geprüft. Betroffene können Gegendarstellung verlangen; der Weg dazu steht im Impressum.

### 4.8 Ländervergleich

Themenseiten: Rente, Gesundheit, Verteidigung, Bildung/Forschung, Verwaltung. Tafel mit Kennzahlen und Quelle pro Zelle (OECD, Eurostat, Jahr). "System übernehmen"-Presets für Rente, Gesundheit und Verwaltung in der ersten Ausbaustufe; jedes Preset ist eine Liste von Annahmen, die zusammen die deutschen Regler setzen; die Annahmen sind sichtbar und einzeln veränderbar; die Wirkung erscheint in der normalen Bilanz, markiert als Modell.

### 4.8a Steuer-Presets mit Herkunft (Florians Ergänzung vom 1.11.2026)

Auf der Einnahmenseite gibt es Presets für Steuern, die es gab, gibt oder geben könnte: **Vermögensteuer** (seit 1997 nicht mehr erhoben, nachdem das Bundesverfassungsgericht 1995 die Einheitswerte beanstandete und die Regierung Kohl, CDU/CSU und FDP, keine Neuregelung beschloss; das Gesetz gilt formal weiter), **Erbschaftsteuer** (wird erhoben, Aufkommen steht den Ländern zu, Reformen 2009 und 2016 mit weitreichenden Verschonungsregeln für Betriebsvermögen), **Spitzensteuersatz / „Reichensteuer“** (Senkung von 53 % auf 42 % 2001–2005 unter Rot-Grün, Zuschlag 45 % ab 2007 unter der Großen Koalition), Finanztransaktionsteuer und ähnliche.

Jedes Steuer-Preset ist ein Modell mit offenen Annahmen (Steuersatz, Freibetrag, Bemessungsgrundlage, Aufkommensschätzung mit Quelle, z. B. DIW, ifo, Bundesfinanzministerium, Wissenschaftlicher Dienst des Bundestags) und wirkt auf die Einnahmen in der Bilanz. Steht das Aufkommen rechtlich den Ländern zu (Erbschaftsteuer, Vermögensteuer), sagt die Seite das ausdrücklich: der Bund hätte davon ohne Änderung des Grundgesetzes nichts.

Zu jedem Steuer-Preset gehört ein Kasten **„Wer hat das beschlossen“**: eine Zeitlinie der Gesetze und Entscheidungen mit Datum, Gesetz oder Urteil, beschließender Koalition und zuständigem Minister, jeweils mit Quelle (Bundesgesetzblatt, Bundestagsdrucksache, Urteil). Es gilt die Quellenregel aus §2: Belege, keine Wertung. „Verantwortlich“ heißt auf der Seite: hat es eingebracht, beschlossen, nicht erneuert oder ausgesetzt, mit Beleg.

Umsetzung: Stufe 1b nach der Grundausstattung der Stufe 1 (eigener Plan).

### 4.9 Kostenarten-Schnitt und Personal

Siehe Entscheidungstabelle. Datenbasis: Hauptgruppen und Gruppierungsplan des Bundeshaushalts (liegen in den Titeldaten), Stellenpläne der Einzelpläne, Personalstandstatistik (Destatis), Beraterkosten aus Antworten auf Kleine Anfragen.

## 5. Datenquellen (alle öffentlich)

| Quelle | Was | Format / Zugang |
|---|---|---|
| bundeshaushalt.de (BMF) | Soll-Haushalte 2012 bis heute bis Titelebene, inkl. Gruppierung (Kostenart) und Funktion | Download CSV/JSON je Jahr; interne JSON-Endpunkte der Seite |
| Haushaltsrechnung des Bundes (BMF/Bundestag) | Ist-Zahlen je Titel | PDF, teils XLSX; Drucksachen des Bundestags |
| Rentenversicherungsbericht, DRV-Statistiken | Einnahmen/Ausgaben der GRV | PDF/XLSX |
| BMG, GKV-Spitzenverband (KV45, KJ1) | Einnahmen/Ausgaben der GKV | XLSX |
| BMG Pflegeversicherung, BA Haushalt | Pflege, Arbeitslosenversicherung | PDF/XLSX |
| Förderdatenbank des Bundes, Zuwendungsdatenbank (förderportal.bund.de) | Zuwendungsempfänger | HTML/CSV |
| Antworten der Bundesregierung auf Kleine Anfragen (dip.bundestag.de) | Zuwendungslisten an NGOs/Verbände, Beraterkosten | PDF; DIP-API |
| Lobbyregister des Bundestags | Organisationen, Lobbyisten, Finanzierung, Auftraggeber | JSON-Download, öffentlich |
| bundestag.de Abgeordnete | Mandate, Ausschüsse, veröffentlichungspflichtige Nebentätigkeiten | HTML, Open-Data-XML |
| Bundesanzeiger / Handels- und Vereinsregister (handelsregister.de) | Vorstände, Geschäftsführer, Jahresabschlüsse | HTML; eingeschränkter Massenabruf, siehe offene Punkte |
| Parteispenden (Bundestagsdrucksachen, bundestag.de) | Spenden über 35.000 € sofort, über 10.000 € in Rechenschaftsberichten | PDF/HTML |
| EU-Transparenzregister | EU-Lobbyeinträge | CSV |
| OECD (Pensions at a Glance, Health Statistics), Eurostat (ESSPROS, COFOG) | Ländervergleich | API/CSV |
| Destatis | Inflation (VPI) für Bereinigung, Personalstand | API |

## 6. Technische Vorschläge (Vorschläge des Builders, von Florian nicht festgelegt)

Florian hat Sprache, Bibliotheken und Architektur dem Builder überlassen. Vorschlag:

- **Frontend**: TypeScript, Svelte 5 mit Vite, D3 (d3-sankey, d3-hierarchy für Treemap). Statische Auslieferung. Alle Daten als vorberechnete JSON-Dateien je Jahr und Topf, lazy geladen. Zustand im URL-Fragment, komprimiert.
- **Pipeline**: Python 3.12, pandas, pydantic für Schemas. Ein Kommando pro Quelle (`fetch`), ein Kommando zum Zusammenführen (`build`), mit Prüfungen (Summen müssen den amtlichen Gesamtsummen entsprechen, sonst bricht der Build ab). Rohdaten werden mit Abrufdatum archiviert.
- **Offenheit (Florians Entscheidung):** Code und Daten liegen öffentlich auf GitHub. Lizenz, Vorschlag des Builders: Code unter MIT, Daten und Texte unter CC BY 4.0 mit Nennung der amtlichen Ursprungsquellen.
- **Beziehungsdaten**: YAML-Dateien pro Person und Organisation im öffentlichen Repository, Schema geprüft (Pflichtfelder: Quelle-URL, Quellendatum, Aufnahmedatum). Pull-Requests und vorausgefüllte Issues als Einreichweg.
- **Hosting**: Hostinger-VPS, Linux, nginx für die statischen Dateien, HTTPS per Let's Encrypt. Die Pipeline läuft auf demselben VPS per Cron oder von Hand bei neuem Haushalt. Kein Tracking, keine Cookies außer technisch notwendigen; Impressum und Datenschutzerklärung sind Pflicht.
- **Erklärtexte** je Titel (zwei Sätze): zunächst für die 200 größten Titel von Hand, Rest schrittweise. Texte liegen als Markdown neben den Daten.

## 7. Ausbaustufen (Reihenfolge, Vorschlag)

1. **Bund 2015–2026** ✅ (umgesetzt am 1.11.2026, Branch `stufe-1`, Plan `docs/superpowers/plans/2026-11-01-stufe-1-bund.md`): Soll und Ist bis Titelebene, Fluss/Karte/Säulen, Regler, Presets, Teilen, Jahresleiste, "Was ist gewachsen?", Kostenarten-Schnitt, Erklärtexte für die 54 größten Posten. Sozialkassen als Töpfe mit grober Gliederung im Gesamtfluss. Offen aus dieser Stufe: Deployment auf den VPS, Impressum, weitere Erklärtexte, Prüfung der VPI-Werte 2015–2019 und der mit `geprueft: false` markierten Sozialkassen-Posten.
1b. **Steuer-Presets mit Herkunft** (§4.8a): Vermögensteuer, Erbschaftsteuer, Spitzensteuersatz als Einnahmen-Modelle mit Kasten „Wer hat das beschlossen“.
2. **Empfänger**: Zuwendungsempfänger aus amtlichen Listen, Empfänger-Seiten mit Zeitlinie, Empfänger-Art-Schnitt, Personal-Regler.
3. **Personen**: Lobbyregister, Nebentätigkeiten, Register-Daten, Akten, Netz, Melde- und Korrekturweg.
4. **Ländervergleich**: Tafeln, dann "System übernehmen"-Presets.

Jede Stufe ist für sich veröffentlichbar.

## 8. Was dem Builder überlassen ist

- Genaue Bibliotheken und Projektstruktur, solange die Seite statisch ausgeliefert wird.
- Wie der Zustand im Link kodiert wird.
- Mobile Umsetzung des Flusses.
- Farbschema, solange Steuern (blau) und Beiträge (lila) unterscheidbar bleiben und keine "Verdachtsfarben" eingesetzt werden.
- Wie die Pipeline mit PDF-Quellen umgeht (Tabellenextraktion, Handarbeit, Mischung).
- Ob Open-Graph-Vorschaubilder vorgerendert werden.
- Wie weit die Sozialkassen in Stufe 1 aufgeschlüsselt werden.

## 9. Festlegungen nach der Prüferlesung (Entscheidungen des Builders, nicht Florians)

Ein unabhängiger Prüfer hat das Dokument gelesen. Diese Punkte habe ich daraufhin selbst festgelegt; Florian kann jeden davon kippen.

- **Sondervermögen gehören dazu.** Der Topf "Bundeshaushalt" umfasst Kernhaushalt plus Sondervermögen (Bundeswehr, Klima- und Transformationsfonds, Wirtschaftsstabilisierungsfonds, Infrastruktur). Sie erscheinen als eigene Kapitel-Gruppe "Nebenhaushalte" und sind in der Rangliste ihrem Thema zugeordnet (Verteidigung = Epl. 14 + Sondervermögen Bundeswehr), mit Hinweis. "Neue Schulden" enthält ihre Kreditaufnahme. Bei Nachtragshaushalten gilt der letzte beschlossene Nachtrag als Soll. Grund: Wer 100 Milliarden außerhalb des Kernhaushalts weglässt, beantwortet die Frage "Wo bleibt das Geld?" falsch.
- **Titel über die Jahre.** Grundlage ist Einzelplan + Kapitel + Titelnummer. Dazu eine gepflegte Konkordanz auf Einzelplan- und Kapitelebene für die bekannten Umschnitte (Bauen 2022, Wirtschaft/Klima 2021, Digitales 2025). Titel, die per Zweckbestimmungstext als verschoben erkannt werden, bekommen die Markierung "verschoben" statt "neu" oder "geschrumpft". Nicht Zuordenbares wird als solches gekennzeichnet. Eine vollständige Titel-Konkordanz wächst schrittweise.
- **Regler über Jahre.** Eine Abweichung ist ein Prozentsatz je Titel und bleibt beim Jahreswechsel erhalten. Im Link stehen Prozentsätze, keine Beträge. Einzeln gesetzte Titel schlagen übergeordnete Regler und Presets.
- **Presets sind Regellisten mit Reihenfolge.** Ein Preset ist eine geordnete Liste von Regeln: entweder "setze Titel/Ebene X auf Y %" oder eine Nebenbedingung wie "Schwarze Null". Nebenbedingungen werden zuletzt angewandt und kürzen alle freien, nicht einzeln gesetzten Titel proportional, bis die Bilanz aufgeht; die Seite zeigt, was dabei gekürzt wurde.
- **Gesetz/frei.** Für die 200 größten Titel von Hand mit Paragraf als Quelle. Alle anderen tragen "nicht geprüft" statt einer Heuristik. Die Kennzeichnung wächst schrittweise.
- **Querflüsse zwischen Töpfen.** Alle Transfers zwischen Töpfen (Bundeszuschüsse, Krankenversicherung der Rentner GRV → GKV, Beiträge der Arbeitslosenversicherung an GRV/GKV, Beiträge des Bundes für Bürgergeld-Beziehende) werden in der Gesamtsumme einmal gezählt und als eigene Liste "Querflüsse" erklärt. Die Bilanz zeigt je Topf eine Zeile "Defizit/Rücklage": Wer den Rentenzuschuss halbiert, sieht beim Bund weniger Schulden und bei der Rentenkasse ein Loch in gleicher Höhe. "Neue Schulden" bleibt eine Zahl des Bundes.
- **"System übernehmen"-Presets.** Die Annahmen leitet der Builder aus den OECD-Tafelwerten her, mit eigener Quellenliste je Annahme; sie gehen vor Veröffentlichung durch eine Fachprüfung (Florian oder eine Person seiner Wahl).
- **Früher Zwischenstand ist erlaubt.** Florian hat die verbleibenden Entscheidungen dem Builder überlassen (1.11.2026). Festlegung: Die Seite geht online, sobald der Bund 2025 (Soll) in der Fluss-Ansicht mit Reglern und Teilen läuft, deutlich als „im Aufbau“ markiert. Zehn Jahre, Ist-Zahlen, Karte, Säulen und Rangliste wachsen danach öffentlich nach. Kein fester Termin; Orientierung ist der Haushalt 2026.
- **Erklärtexte.** Der Builder schreibt die Erklärtexte für die 200 größten Titel mit Paragraf oder Quelle; Florian liest gegen. Sie sind keine Voraussetzung für die Veröffentlichung und laufen nach. Titel ohne Text zeigen die amtliche Zweckbestimmung.
- **Melden ohne Server.** "Fehler melden / Beleg einreichen" öffnet ein vorausgefülltes Issue im öffentlichen Repository oder eine E-Mail; keine eigene Server-Logik, keine Speicherung auf dem VPS.

## 10. Offene Punkte, die nicht Florians Entscheidung brauchen, aber Arbeit bedeuten

- Massenabruf aus dem Vereins-/Handelsregister ist rechtlich und technisch beschränkt; Personen- und Vorstandsdaten werden in der ersten Fassung von Hand mit Quelle erfasst.
- Ist-Zahlen liegen teils nur als PDF vor; die Pipeline braucht eine Tabellenextraktion mit Prüfsummen.
- Namen von Empfängern sind in den Quellen nicht einheitlich geschrieben; es braucht eine Zuordnungstabelle (Alias → Organisation) mit menschlicher Prüfung.
- Rechtliche Prüfung von Impressum, Datenschutz und Persönlichkeitsrecht vor Veröffentlichung der Stufe 3 wird empfohlen.
