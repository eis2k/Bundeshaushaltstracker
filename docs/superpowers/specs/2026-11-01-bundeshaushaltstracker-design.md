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

### 4.6a Empfänger, Stufe 2 (Festlegung nach Florians Antworten vom 1.11.2026)

**Florians Vorgaben.** Die Empfänger-Seite beantwortet drei Fragen, in dieser Reihenfolge: (1) Woher kommt das Geld (Jahr, Titel, Kapitel, Ministerium, zehn Jahre), (2) wer steht hinter dem Empfänger (Vorstand, Geschäftsführung, Aufsichtsgremium mit Zeitraum und Fundstelle), (3) welche **belegten Verbindungen** zwischen den Entscheidern über dieses Geld und dem Empfänger gibt es. Die Verbindungen stehen ganz oben. Jeder Endpunkt, der gesetzlich veröffentlichen muss (Lobbyregister, Jahresabschluss, Rechenschaftsbericht), bekommt diese **Pflichtangaben im Tracker abrufbar**, einschließlich der Verwendung der Mittel laut eigenem Jahresabschluss. Verwandtschaft und andere persönliche Beziehungen erscheinen nur, wenn ein amtliches Dokument sie nennt; Presse und Vermutung reichen nicht. Hinweise sind Tatsachensätze mit Quelle und Datum, keine Warnfarbe, kein „Verdacht“: „A ist laut bundestag.de Mitglied des Beirats von B. B erhielt 2024 3,2 Mio. € aus Titel X des Ministeriums, dem A als Staatssekretär angehört.“

**Datenbasis (geprüft am 1.11.2026).**

| Quelle | Was sie liefert | Zugang |
|---|---|---|
| Bundeshaushalt (eigene Build-Daten) | Titel, deren Zweckbestimmung den Empfänger nennt („Zuschuss an …“, „… e. V.“, „Stiftung …“); 2025: 124 Titel, rund 13 Mrd € (davon 10 Mrd € Postbeamtenversorgungskasse) | bereits im Build |
| Lobbyregister des Bundestags | Amtliches JSON für alle 7.025 Einträge (`/sucheJson`, Detailprofile `/sucheJson/<R-Nr>/<Id>`): Rechtsform, Sitz, **gesetzliche Vertreter mit Funktion** (6.672 Organisationen), Kennzeichen „jüngste Regierungsfunktion“ (220), **Zuwendungen der öffentlichen Hand je Geldgeber mit Betragsspanne und Zweck** (1.428 mit Bundesmitteln, Untergrenzen zusammen 26 Mrd €), Hauptfinanzierungsquellen, Spendensumme, Mitgliedsbeiträge, Lobbyausgaben, Mitgliedschaften, **Jahresabschluss-PDF** (6.096), Versionen mit Gültigkeitsdatum | Download ohne Anmeldung |
| Förderkatalog des Bundes (foerderportal.bund.de) | Projektförderung von BMFTR, BMWE, BMUV, BMLEH, BMV, BMJV: Förderkennzeichen, Ressort, Empfänger, Ausführende Stelle, Thema, Laufzeit, Bundesanteil in Euro | Suche je Empfängername mit Sitzung, CSV-Export des Ergebnisses; kein Gesamtexport |
| bundestag.de, Biografien | „Veröffentlichungspflichtige Angaben“ je Abgeordnetem: Funktionen in Unternehmen, Körperschaften, Vereinen/Verbänden/Stiftungen, entgeltliche Tätigkeiten; Ausschüsse; Selbstauskunft | HTML, Liste über Ajax-Endpunkt |
| DIP-API des Bundestags | Antworten der Bundesregierung mit Zuwendungslisten (Suche nach Empfängername) | öffentlicher API-Key bis Mai 2027, auf der API-Hilfeseite veröffentlicht |
| Jahresabschlüsse der Empfänger | Erträge gesamt, davon öffentliche Hand, Personalaufwand, Projektförderung/weitergeleitete Mittel, Jahresergebnis; Prüfvermerk | PDF (oft gescannt), Link aus dem Lobbyregister; Kennzahlen von Hand mit Seitenangabe |

**Festlegungen des Builders.**

- **Empfänger-Stamm** in `data/manual/empfaenger.yaml`: id, Name, Aliasse, Lobbyregister-Nummer, Haushaltstitel-IDs, Förderkatalog-Suchname, Rechtsform, Sitz, `geprueft`. Namensabgleich zwischen den Quellen wird automatisch vorgeschlagen (normalisierte Namen) und in `data/review/` abgelegt; veröffentlicht wird nur, was bestätigt ist oder exakt übereinstimmt.
- **Umfang der ersten Fassung:** alle Organisationen mit Bundesmitteln laut Lobbyregister plus alle im Haushalt namentlich genannten Empfänger, rund 1.500 Seiten, automatisch gebaut. Jahresabschluss-Kennzahlen von Hand für die 100 nach Bundesmitteln größten.
- **Geld je Quelle getrennt, nie addiert.** Haushaltstitel (Soll/Ist, Euro), Lobbyregister (Spannen, Eigenangabe, Geschäftsjahr) und Förderkatalog (Projektsummen über Laufzeiten) sind drei Blicke auf dasselbe Geld und werden nebeneinander gezeigt, jeder mit Etikett. Rechnungen mit Lobbyregister-Beträgen nutzen die Untergrenze und sagen das.
- **Eigenangaben** (Lobbyregister-Profil, Jahresabschluss, Biografie-Selbstauskunft) tragen das Etikett „Eigenangabe, Stand <Datum>“. Offensichtliche Erfassungsfehler werden nicht korrigiert, sondern so gezeigt und mit Hinweis versehen.
- **Verbindungstypen in Stufe 2:** (a) Abgeordneter oder Regierungsmitglied mit Funktion beim Empfänger laut bundestag.de; (b) gesetzlicher Vertreter des Empfängers mit „jüngster Regierungsfunktion“ laut Lobbyregister; (c) als Zusatzzeile die Zuständigkeit: Ausschuss oder Ressort der verbundenen Person und das Ressort, aus dem der Empfänger Geld erhält. Verbindungen Person ↔ Organisation werden automatisch erzeugt. **Florians Entscheidung (1.11.2026):** Stimmt der Organisationsname in beiden Quellen nach Normalisierung exakt überein, wird die Verbindung automatisch veröffentlicht, mit beiden Belegen verlinkt und dem Etikett „automatisch abgeglichen“; nur ähnliche Namen landen als Kandidaten in `data/review/verbindungen_kandidaten.yaml` und bleiben unsichtbar, bis sie in `data/manual/verbindungen.yaml` mit `geprueft: true` bestätigt sind. Verwandtschaft nur von Hand mit amtlicher Quelle. Parteispenden und die Netz-Ansicht bleiben Stufe 3.
- **Seitenaufbau:** Kopf (Name, Rechtsform, Sitz, Lobbyregister-Nummer, Website); Block „Belegte Verbindungen“ (bei keiner: „In den ausgewerteten Quellen keine belegte Verbindung, Stand <Datum>“); Block „Geld vom Bund“ (drei Quellen getrennt, Zeitreihe aus den Titeln); Block „Wer steht dahinter“; Block „Pflichtangaben des Empfängers“ (Finanzierungsquellen, Spenden, Mitgliedsbeiträge, Lobbyausgaben, Jahresabschluss mit Kennzahlen und Seitenangabe); Block „Quellen und Stand“; Knopf „Fehler melden / Beleg einreichen“ (vorausgefülltes Issue).
- **Einstiege:** neue Ansicht „Empfänger“ (Liste mit Suche, Sortierung nach Bundesmitteln, Filter nach Art), Link vom Titel im Fluss und im Panel, eigener Teilen-Link `#v1;e=<id>`. Der Empfänger-Art-Schnitt (Länder, Sozialkassen, Unternehmen, Vereine/Stiftungen, Ausland) kommt aus dem Gruppierungsplan der Titel in den bestehenden Schnittwechsel.
- **Personenkreis** bleibt wie §4.7: gesetzliche Vertreter (Vorstand, Geschäftsführung) und die im Lobbyregister benannten Interessenvertreter („entrusted persons“) eines Empfängers, Abgeordnete und Regierungsmitglieder. Mitglieder von Aufsichtsrat, Beirat oder Kuratorium erscheinen nur, wenn sie selbst zu diesem Kreis gehören (etwa ein Abgeordneter laut seiner Bundestags-Angaben); andere Namen aus Quellen werden nicht übernommen.
- **Keine Personen-Seiten in Stufe 2.** Personen stehen auf der Empfänger-Seite als Name, Funktion, Zeitraum und Beleg; eigene Akten mit Teilen-Link und Netz kommen in Stufe 3.
- **Personal-Regler verschoben.** Der Personal-Regler aus §4.9 (Stellen × Durchschnittskosten, Berater-Regler) ist ein eigenes Rechenmodell mit eigenen Quellen und wird aus Stufe 2 herausgenommen (eigene Stufe 2b nach den Empfängern).
- **Zeitraum der Verbindungen:** Stufe 2 wertet die Angaben der amtierenden Abgeordneten und der aktuellen Lobbyregister-Profile aus, jeweils mit Stand-Datum. Frühere Wahlperioden (Webarchiv des Bundestags) und ältere Profil-Versionen folgen in Stufe 3b; die Zeitlinie zeigt bis dahin Geld ab 2015 und Posten ab Beginn der Wahlperiode.
- **Empfänger im Fluss:** Nur Titel, deren Zweckbestimmung den Empfänger nennt, lösen zur Empfänger-Seite auf. Alle anderen Titel enden mit „Empfänger nicht veröffentlicht“ und zwei Links: zur Empfänger-Liste, gefiltert auf das Ressort („bekannte Empfänger dieses Ministeriums laut Lobbyregister“, ohne Titelzuordnung, nicht als Band), und zur IFG-Anfrage bei FragDenStaat. Beträge aus Lobbyregister oder Förderkatalog werden nie in den Sankey eingerechnet.
- **Veröffentlichungsschalter:** Der Build kennt einen Schalter `personen`, mit dem die Blöcke „Wer steht dahinter“ und „Belegte Verbindungen“ getrennt vom Rest veröffentlicht werden können. **Florians Entscheidung (1.11.2026):** Der Schalter steht auf „an“; die Personenblöcke gehen mit dem übrigen Tracker online. Die rechtliche Prüfung aus §10 bleibt Empfehlung, kein Tor.

### 4.7 Personen-Akten und Netz

Personenkreis: Mitglieder der Bundesregierung, Parlamentarische und beamtete Staatssekretäre, Mitglieder des Bundestags, Vorstände und Geschäftsführer von Empfängern, registrierte Lobbyisten laut Lobbyregister. Keine anderen.

Akte: Name, Funktion(en) mit Zeitraum, Posten in Organisationen mit Zeitraum, welche dieser Organisationen Geld aus welchen Titeln bekamen, Nebentätigkeiten laut Bundestag, Parteispenden der verbundenen Organisationen laut Bundestagsdrucksache, Zeitlinie, Quellen. Jeder Eintrag trägt Quelle, Datum der Quelle und Datum der Aufnahme.

Netz: Knoten sind Personen, Organisationen, Ministerien/Ausschüsse; Kanten sind Geld (blau), Posten (rot), Spende (grün), jeweils mit Zeitraum. Nur zwei Schritte um den Startknoten. Kein Vollnetz.

Hinweis- und Korrekturweg: Auf jeder Akte und Empfänger-Seite ein Knopf "Fehler melden / Beleg einreichen". Einreichungen werden vor Veröffentlichung von einem Menschen geprüft. Betroffene können Gegendarstellung verlangen; der Weg dazu steht im Impressum.

### 4.7a Personen-Akten und Netz, Stufe 3 (Festlegung nach Florians Antworten vom 2.11.2026)

**Florians Vorgaben.** Alle Menschen, die das Lobbyregister als gesetzliche Vertreter oder Interessenvertreter von Empfängern nennt, bekommen eine Akte, nicht nur Politiker und Personen mit belegter Verbindung (rund 11.300 Namen, dazu 639 Abgeordnete und die Bundesregierung). Das Netz („Umfeld zeigen“) ist der Kern der Stufe.

**Die Akte.** Kopf: Name, öffentliche Funktionen mit Zeitraum und Fundstelle (Abgeordneter mit Fraktion, Ausschüssen und Wahlperiode; Regierungsmitglied, Parlamentarischer oder beamteter Staatssekretär mit Ressort; Vorstand, Geschäftsführung oder Interessenvertretung einer Organisation laut Lobbyregister). Block „Organisationen und ihr Geld vom Bund“: jede Organisation mit Posten der Person, daneben ihre Bundesmittel laut Lobbyregister (Untergrenze), Haushaltstitel und Förderkatalog aus den Empfänger-Daten der Stufe 2, nie addiert. Block „Veröffentlichungspflichtige Angaben“ (nur Abgeordnete): wörtlich aus bundestag.de, je Kategorie, mit Abrufdatum. Block „Parteispenden“: Spenden über 35.000 € (seit 5.3.2024, davor 50.000 €) der Organisationen, bei denen die Person Posten hat, laut bundestag.de mit Datum, Partei, Betrag und Fundstelle. Block „Zeitlinie“: Geldflüsse an verbundene Organisationen und Posten der Person auf einer Achse 2015 bis heute. Block „Quellen und Stand“ und der Knopf „Fehler melden / Beleg einreichen“. Formulierungen bleiben Tatsachensätze wie in §4.6a; keine Wertung, keine Warnfarbe.

**Identität und Namensgleichheit** (Festlegung des Builders, von Florian bestätigt): Eine Akte entsteht je Person und Quelle (Lobbyregister-Eintrag, bundestag.de-Biografie, Kabinettsliste). Zusammengeführt werden zwei Akten nur mit Beleg: (a) die Bundestags-Angabe der Person nennt genau die Organisation, deren Lobbyregister-Eintrag denselben Namen führt; (b) das Lobbyregister meldet für die Person eine frühere Mandats- oder Regierungsfunktion, die zur Biografie passt (Name und Funktion); (c) ein Eintrag in `data/manual/personen.yaml` mit Quelle. Gleiche Namen ohne Beleg bleiben getrennte Akten mit dem Hinweis „gleicher Name, nicht zusammengeführt“. Innerhalb des Lobbyregisters gilt derselbe Name bei verschiedenen Organisationen als eine Person nur, wenn Vorname und Nachname exakt gleich sind und die Organisationen sich in den Angaben gegenseitig nennen; sonst getrennt.

**Das Netz.** Knopf „Umfeld zeigen“ auf jeder Akte und jeder Empfänger-Seite öffnet einen Ausschnitt: Knoten sind Personen, Organisationen, Ministerien (Einzelpläne) und Parteien; Kanten sind Geld (Ministerium → Organisation, laut Lobbyregister-Spanne oder Haushaltstitel), Posten (Person – Organisation, Person – Ministerium bei Regierungsfunktion, Person – Bundestag bei Mandat) und Spende (Organisation → Partei). Zwei Schritte um den Startknoten, höchstens 60 Knoten (die größten nach Geld zuerst, Rest als „+ n weitere“). Jede Kante trägt Quelle und Zeitraum im Tooltip; Klick auf einen Knoten öffnet dessen Akte oder Seite; die drei Kantenarten unterscheiden sich durch Linienart und Legende, nicht durch Wertungsfarben. Das Netz ist statisch vorberechnet je Knoten als Nachbarschaftsliste (`data/build/netz/<id>.json`); die Seite rendert mit d3-force.

**Datenbasis (geprüft am 2.11.2026).**

| Quelle | Was sie liefert | Zugang |
|---|---|---|
| Lobbyregister-Detailprofile (aus Stufe 2) | Gesetzliche Vertreter und Interessenvertreter je Organisation mit Funktion, Kennzeichen und Details früherer Regierungs- oder Mandatsfunktion | bereits in `data/raw/lobbyregister` |
| bundestag.de-Biografien (aus Stufe 2) | Name, Fraktion, Wahlkreis, Ausschüsse, veröffentlichungspflichtige Angaben; Liste der ausgeschiedenen Abgeordneten der laufenden Wahlperiode | bereits in `data/raw/bundestag`; Ausgeschiedene: `/abgeordnete/biografien/ausgeschiedene` |
| bundesregierung.de, Bundeskabinett | Mitglieder der Bundesregierung mit Amt, je eine Seite | HTML-Liste `/breg-de/bundesregierung/bundeskabinett` |
| Staatssekretäre | Parlamentarische und beamtete Staatssekretäre je Ressort | von Hand in `data/manual/regierung.yaml` mit Quelle (Ministeriumsseite „Leitung“) und Datum; der Build prüft Pflichtfelder |
| bundestag.de, Parteienfinanzierung | Spenden über 35.000 € (ab 5.3.2024) bzw. 50.000 € (ab 1.7.2002): Spender, Partei, Betrag, Eingang, Veröffentlichung, je Jahr eine Seite | HTML `/parlament/praesidium/parteienfinanzierung/fundstellen50000/<jahr>`, 2015 bis heute |

**Festlegungen des Builders.**

- **Personen-Ids**: `slug(name)` plus Quellenkürzel bei Namensgleichheit (`-lr`, `-mdb`, `-breg`), stabil über Läufe durch Sortierung nach Quelle und Registernummer.
- **Umfang der ersten Fassung**: Akten für alle Personen des Lobbyregisters mit Bundesmitteln-Organisation, alle Abgeordneten der 21. Wahlperiode (auch ausgeschiedene), Bundeskabinett und Staatssekretäre; Parteispenden 2015 bis heute. Frühere Wahlperioden (Webarchiv) und Rechenschaftsberichte (Spenden ab 10.000 €) kommen später.
- **Spenden-Zuordnung**: Der Spendername wird wie die Empfängernamen normalisiert und nur bei exakter Übereinstimmung einer Organisation zugeordnet; Ähnliches landet in `data/review/spenden_kandidaten.yaml`. Spenden natürlicher Personen werden nur zugeordnet, wenn der Name exakt einer Akte entspricht und die Person im Lobbyregister oder Bundestag geführt ist; sonst erscheinen sie nicht (Anti-Ziel „keine Privatpersonen“).
- **Suche**: Ansicht „Personen“ mit Suchfeld und Filter nach Funktion (Abgeordnete, Regierung, Vertreter von Empfängern); Teilen-Link `#v1;a=personen;pe=<id>`; Netz-Ansicht `#v1;a=netz;n=<knoten-id>` (Knoten-Ids: `p:<person>`, `e:<empfaenger>`, `m:<epl>`, `partei:<name>`).
- **Schalter `--ohne-personen`** gilt weiter: ohne Personen werden keine Akten, keine Netz-Dateien und keine Personenblöcke gebaut.
- **Korrekturweg**: „Fehler melden / Beleg einreichen“ öffnet ein vorausgefülltes Issue; im Impressum steht der Weg zur Gegendarstellung (Text folgt mit dem Deployment).
- **Spenden natürlicher Personen** werden in Stufe 3 keiner Akte zugeordnet und nicht gezeigt; nur Spenden von Organisationen, deren Name exakt einem Empfänger entspricht, erscheinen bei der Organisation, in den Akten ihrer Vertreter und im Netz. (Korrigiert die frühere Formulierung; ein gleicher Name ist kein Beleg.)
- **Ältere Profil-Versionen des Lobbyregisters** kommen in eine Folgestufe 3b (Versionshistorie je Organisation, Zeiträume der Posten, frühere Vertreter). In Stufe 3 trägt jeder Posten „Stand <Gültigkeitsdatum der Version>“; die Zeitlinie zeigt Posten als Punkt mit Stand-Datum, Geld als Reihe.
- **Keine neuen Verbindungssätze auf Empfänger-Seiten.** Mehrstufige Ketten („Staatssekretär im Ressort, das B fördert“, „B spendete an die Partei von A“) werden nicht als Satz formuliert; sie sind im Netz und in der Akte als Kanten mit Quelle sichtbar, der Leser zieht den Schluss. Die Verbindungstypen aus §4.6a bleiben unverändert.
- **Knoten und Kanten im Netz.** Knoten: Personen, Organisationen (Empfänger), Ministerien (Einzelpläne), Parteien. Kein Knoten „Bundestag“ und keine Ausschuss-Knoten; Mandat, Fraktion und Ausschüsse stehen als Attribut am Personenknoten. Kanten: Geld (Ministerium → Organisation), Posten (Person – Organisation; Person – Ministerium für Regierungsmitglieder und Staatssekretäre), Spende (Organisation → Partei). Ministerien und Parteien sind Randknoten: Sie werden gezeigt, aber nicht weiter expandiert, damit das Umfeld nicht über einen Geldgeber auf hunderte Organisationen explodiert.
- **Gleiche Namen im Lobbyregister** gelten als eine Person, wenn Vor- und Nachname exakt gleich sind und (a) eine der beiden Organisationen die andere in ihren Mitgliedschaften nennt oder (b) beide Organisationen mindestens zwei gemeinsame Vertreternamen haben oder (c) `data/manual/personen.yaml` sie mit Quelle zusammenführt. Sonst getrennte Akten mit Hinweis „gleicher Name, nicht zusammengeführt“; die Fälle stehen in `data/review/personen_kandidaten.yaml`.
- **Sichtbarkeit der Akten (Florians Entscheidung vom 2.11.2026, nach dem Vorbild Wikipedia):** Gebaut werden alle Akten. Öffentlich sichtbar mit eigener Seite und Teilen-Link ist eine Akte, wenn (1) die Person ein öffentliches Amt hat (Abgeordnete, Regierungsmitglieder, Staatssekretäre), (2) eine belegte Verbindung zur Entscheidungsseite besteht (Verbindung aus §4.6a oder gemeldete frühere Regierungs- oder Mandatsfunktion), oder (3) ein Prüfer sie in `data/manual/personen.yaml` mit `freigabe: true` und Quelle freigeschaltet hat. Alle übrigen Personen erscheinen weiter namentlich auf der Empfänger-Seite und im Netz als Knoten ohne eigene Seite („Akte nicht freigeschaltet“). Der Build-Schalter `--akten alle` baut alle Akten mit Seite; er ist für Florians lokale Auswertung und eine nicht öffentliche Instanz gedacht, die öffentliche Seite wird mit der Standardeinstellung `--akten relevant` gebaut. Florian behält so jederzeit Zugriff auf den vollen Datenbestand; die Schranke schützt nur die Veröffentlichung.
- **Moderation über GitHub (Florians Entscheidung vom 2.11.2026):** Korrekturen, Belege und Freischaltungen sind Pull Requests auf die Pflegedateien unter `data/manual/`. Einreichen kann jeder mit GitHub-Konto; übernehmen dürfen Prüfer mit Schreibrecht, die Florian ernennt. Jede Änderung trägt Quelle, Datum und den Prüfer (Git-Historie). Die Regeln stehen in `CONTRIBUTING.md`, eine Pull-Request-Vorlage fragt Quelle und Datum ab. Keine eigene Nutzerverwaltung, kein Server. Der Knopf „Fehler melden / Beleg einreichen“ auf jeder Akte verweist auf diesen Weg.
- **Bundesregierung**: Stufe 3 erfasst das amtierende Kabinett (bundesregierung.de) und die amtierenden Staatssekretäre (`data/manual/regierung.yaml`, von Hand mit Quelle). Frühere Regierungen seit 2015 folgen als Pflegedaten in derselben Datei; da es keine Zuständigkeitssätze gibt, entsteht aus fehlenden Altdaten kein falscher Satz.

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
1b. **Steuer-Presets mit Herkunft** ✅ (umgesetzt am 1.11.2026, Branch `stufe-1b`, Plan `docs/superpowers/plans/2026-11-01-stufe-1b-steuern.md`) (§4.8a): Vermögensteuer, Erbschaftsteuer, Spitzensteuersatz und Abgeltungsteuer als Einnahmen-Modelle (`data/manual/steuern.yaml`) mit Annahme-Reglern, Bund-/Länder-Anteil nach Art. 106 GG und Kasten „Wer hat das beschlossen“. Offen: weitere Szenarien (z. B. Finanztransaktionsteuer), Fortschreibung der Bemessungsgrundlagen je Haushaltsjahr.
2. **Empfänger** ✅ (umgesetzt am 2.11.2026, Branch `stufe-2`, Plan `docs/superpowers/plans/2026-11-01-stufe-2-empfaenger.md`): rund 1.600 Empfänger-Seiten aus Lobbyregister (Zuwendungen des Bundes, gesetzliche Vertreter, Pflichtangaben, Jahresabschluss-Link), Haushaltstiteln mit genanntem Empfänger (Zeitreihe 2015–2026) und Förderkatalog; belegte Verbindungen zu Abgeordneten über deren veröffentlichungspflichtige Angaben (nur exakte Namen, Rest in Prüflisten); Kennzahlen aus 22 Jahresabschlüssen von Hand; Empfänger-Art-Schnitt war schon in Stufe 1. Offen: Prüflisten abarbeiten (Aliasse, Verbindungs-Kandidaten), weitere Jahresabschlüsse, frühere Wahlperioden.
2b. **Personal-Regler** (§4.9): Stellen je Behörde × Durchschnittskosten, Berater-Regler; eigene Quellen (Stellenpläne, Destatis, Kleine Anfragen), eigenes Link-Format.
3. **Personen** ✅ (umgesetzt am 2.11.2026, Branch `stufe-3`, Plan `docs/superpowers/plans/2026-11-02-stufe-3-personen.md`): 12.108 Akten aus Lobbyregister (Vertreter der Empfänger mit Bundesmitteln), Bundestag (639 Abgeordnete mit veröffentlichungspflichtigen Angaben) und Bundesregierung; Zusammenführung nur mit Beleg; Relevanzregel (950 Akten öffentlich, Rest als Name auf der Empfänger-Seite; `--akten alle` für den vollen Bestand); Parteispenden über 35.000 € seit 2015; Netz „Umfeld zeigen“ zwei Schritte weit mit Geld, Posten und Spenden; Moderation über GitHub (CONTRIBUTING.md). Offen: Staatssekretäre vollständig erfassen (regierung.yaml), Prüflisten (209 gleiche Namen, 286 Spender ohne Treffer) abarbeiten.
3b. **Personen, Vertiefung**: Versionshistorie des Lobbyregisters (Zeiträume der Posten, frühere Vertreter), frühere Wahlperioden (Webarchiv des Bundestags), frühere Bundesregierungen seit 2015, Rechenschaftsberichte der Parteien (Spenden ab 10.000 €).
4. **Ländervergleich**: Tafeln, dann "System übernehmen"-Presets.
3c. **Beitragsbemessungsgrenzen** (Florians Anforderung vom 2.11.2026): Regler für die Beitragsbemessungsgrenzen in Renten-, Kranken- und Pflegeversicherung (und die Versicherungspflichtgrenze) als Einnahmen-Modell der Sozialkassen, analog zu den Steuer-Modellen: Basis aus der Einkommensverteilung (Destatis, Lohn- und Einkommensteuerstatistik, DRV-Versichertenstatistik), jede Annahme mit Quelle und als Regler, Wirkung auf Beiträge und Leistungsansprüche getrennt ausgewiesen, Kasten „Wer hat das beschlossen“ (Sozialversicherungs-Rechengrößenverordnungen). Zeigt, was eine Anhebung oder Aufhebung der Grenze den Kassen brächte und was an späteren Rentenansprüchen dagegensteht.

3d. **Bezüge der Amtsträger** (Florians Anforderung vom 2.11.2026: „wirklich alles, was dem Jeweiligen ausgezahlt wird“): Jede Akte mit Mandat oder Regierungsamt zeigt einen Block „Bezüge aus dem Amt“ mit allen gesetzlich festgelegten Zahlungen und Leistungen je Funktion und Zeitraum: Abgeordnete nach Abgeordnetengesetz (Abgeordnetenentschädigung § 11 mit jährlicher Anpassung, steuerfreie Kostenpauschale § 12 Abs. 2, Mitarbeiterpauschale § 12 Abs. 3 – gesondert ausgewiesen, weil sie an die Mitarbeiter und nicht an den Abgeordneten fließt –, Sachleistungen wie Büroausstattung, Bahncard, Dienstreisen, Zuschuss zur Krankenversicherung, Übergangsgeld und Altersentschädigung als Anwartschaft, Funktionszulagen von Präsidium und Fraktionen laut deren Rechenschaftsberichten); Regierungsmitglieder nach Bundesministergesetz (Amtsgehalt als Vielfaches von B 11, Ortszuschlag, Dienstaufwandsentschädigung, Kürzung der Abgeordnetenentschädigung bei Doppelbezug, Übergangsgeld, Ruhegehalt); Parlamentarische Staatssekretäre nach ParlStG; beamtete Staatssekretäre nach Besoldungsordnung B. Dargestellt werden Monats- und Jahresbeträge je Posten, zeitanteilig nach seit/bis, mit einer Summe „an die Person ausgezahlt“ (Entschädigung, Pauschalen, Zulagen) getrennt von „für die Person aufgewendet“ (Mitarbeiter, Sachleistungen, Versorgungsanwartschaft). Quellen nur amtlich: Gesetzestexte (gesetze-im-internet.de), Bekanntmachungen des Bundestagspräsidenten zur Anpassung (Drucksachen), Bundesbesoldungsgesetz, Rechenschaftsberichte der Fraktionen; jede Zahl mit Fundstelle und Gültigkeitszeitraum, keine Schätzung einzelner Reisekosten (nicht veröffentlicht, wird als Lücke benannt). GitHub-Issue 7.

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
