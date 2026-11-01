# Bundeshaushaltstracker

**Wo bleibt das Geld?** Deutschland nimmt mehr Steuern ein als je zuvor, und trotzdem wird gekürzt: bei der Rente, bei den Krankenkassen, fast überall. Der Bundeshaushaltstracker macht den Weg des Geldes sichtbar, von der Lohnsteuer und dem Rentenbeitrag über Bund und Sozialkassen bis zu dem, der es am Ende bekommt. Zurück bis 2015, bis auf den einzelnen Haushaltstitel, mit Quelle an jeder Zahl.

Und weil Zuschauen nicht reicht: Jeder kann den Haushalt umbauen. Rentenzuschuss halbieren, Verteidigung verdoppeln, einen Titel streichen, und sofort sehen, was das mit Einnahmen, Ausgaben und Schulden macht. Den eigenen Haushalt teilt man als Link.

> Status: Konzeptphase. Das Konzept ist fertig, der Code noch nicht begonnen. Siehe [Konzept](docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md) und die Mockups unter `docs/mockups/`.

---

## Was der Bundeshaushaltstracker kann (wenn es fertig ist)

**Dem Geld folgen.** Die Standardansicht ist ein Geldfluss: links Steuern (blau) und Beiträge (lila), in der Mitte die Töpfe Bundeshaushalt, Rentenkasse, Krankenkassen, Pflege und Arbeitslosenversicherung, rechts wofür und an wen. Jeder Klick auf ein Band hängt eine Spalte an: Ministerium, Kapitel, Titel, Empfänger. Woher das Geld kommt, bleibt immer sichtbar. Wem die Flüsse zu viel sind, schaltet auf die Karte (jeder Euro ist Fläche) oder auf zwei Säulen (Einnahmen gegen Ausgaben).

**Den Haushalt umbauen.** An jedem Titel, Kapitel und Ministerium ein Regler. Oben die Bilanz, die bei jeder Bewegung mitläuft: Einnahmen, Ausgaben, neue Schulden, Abstand zum Original. Presets für die üblichen Streitfragen, kombinierbar, eigene speicherbar. Was gesetzlich festgelegt ist, trägt die Markierung *Gesetz*: ändern darf man es trotzdem, aber die Seite sagt, dass dafür ein Gesetz geändert werden müsste. Wer den Rentenzuschuss halbiert, sieht beim Bund weniger Schulden und bei der Rentenkasse ein Loch in gleicher Höhe.

**Zehn Jahre zurück.** Eine Jahresleiste von 2015 bis 2025, zum Ziehen oder Abspielen, umschaltbar zwischen Plan (Soll), tatsächlicher Ausgabe (Ist) und inflationsbereinigt. Dazu die Rangliste **„Was ist gewachsen?“**: jeder Titel mit Wert damals, Wert heute, Zuwachs und Verlaufskurve, filterbar nach Zuwendungen an Vereine, Firmen, Personal oder Geschrumpftes. Auffälliges rutscht von selbst nach oben.

**Wer bekommt es.** Jeder Empfänger hat eine Seite: Geld vom Bund über zehn Jahre, aus welchen Titeln und Ministerien, Rang unter Empfängern gleicher Art, Rechtsform, Lobbyregister-Eintrag, Vorstand und Geschäftsführung. Und eine Zeitlinie, in der Zahlungen und Postenwechsel nebeneinanderstehen.

**Wer entscheidet.** Jede Person in öffentlicher Funktion (Regierung, Staatssekretäre, Abgeordnete, Vorstände von Empfängern, registrierte Lobbyisten) hat eine Akte: Ämter, Mandate, Posten, Nebentätigkeiten, mit Zeitraum und Quelle. Ein Knopf „Umfeld zeigen“ öffnet ein Netz, zwei Schritte weit, nie das ganze Knäuel. Das Netz dient zum Finden, die Akte zum Belegen.

**Vergleichen.** Deutschland neben Schweden, Dänemark, Norwegen, Niederlande, Österreich, mit Kennzahlen aus OECD und Eurostat. Für Rente, Gesundheit und Verwaltung gibt es außerdem Presets „System übernehmen“, die die Regeln des anderen Landes auf deutsche Zahlen übertragen, mit jeder Annahme offen daneben, als Modell gekennzeichnet.

**Anders schneiden.** Derselbe Haushalt nach Kostenart (Personal, Sachkosten, Zinsen, Zuschüsse, Investitionen) oder nach Empfänger-Art (Länder, Sozialkassen, Firmen, Vereine, Ausland). Personal-Regler: Stellen je Behörde mal Durchschnittskosten, Berater- und Gutachterkosten als eigener Regler. Die Auswirkung zeigt immer den Anteil am Gesamthaushalt.

## Grundsätze

Der Bundeshaushaltstracker ist ein Werkzeug zum Nachprüfen, kein Pranger. Vier Regeln gelten ohne Ausnahme:

1. **Ohne Quelle kein Eintrag.** Jede Zahl, jeder Pfeil, jeder Posten trägt ein Quellen-Etikett mit Link, Datum der Quelle und Datum der Aufnahme.
2. **Belege, keine Urteile.** Die Seite zeigt, was wann war. Keine Wertungen, keine Verdachtsfarben, keine Vermutungen. Die Schlussfolgerung zieht der Leser.
3. **Nur öffentliche Funktionen.** Gezeigt werden Personen in Regierungsamt, Mandat, Vorstand oder Geschäftsführung eines Empfängers oder im Lobbyregister. Keine Sachbearbeiter, keine Privatpersonen.
4. **Ehrliche Rechnung.** Auswirkungen sind Rechnung, keine Prognose, und stehen immer im Verhältnis zum Ganzen. Wer am Personal spart, sieht Zehntelprozente, und soll sie sehen.

Jede Empfänger-Seite und jede Akte hat einen Knopf „Fehler melden / Beleg einreichen“. Einreichungen werden von einem Menschen geprüft, bevor sie erscheinen. Betroffene können eine Gegendarstellung verlangen; der Weg dazu steht im Impressum.

## Datenquellen

Alles, was der Bundeshaushaltstracker zeigt, ist öffentlich. Die Arbeit liegt darin, es zusammenzuführen.

| Quelle | Liefert |
|---|---|
| [bundeshaushalt.de](https://www.bundeshaushalt.de) (Bundesfinanzministerium) | Soll-Haushalte seit 2012 bis auf Titelebene, mit Kostenart und Funktion |
| Haushaltsrechnung des Bundes | Ist-Zahlen je Titel |
| Rentenversicherungsbericht, GKV-Statistiken, Pflege, Bundesagentur | Einnahmen und Ausgaben der Sozialkassen |
| Förderdatenbank, Zuwendungslisten aus Antworten der Bundesregierung ([dip.bundestag.de](https://dip.bundestag.de)) | Wer Zuwendungen bekommt |
| [Lobbyregister](https://www.lobbyregister.bundestag.de) des Bundestags | Organisationen, Lobbyisten, Finanzierung, Auftraggeber |
| [bundestag.de](https://www.bundestag.de) | Mandate, Ausschüsse, Nebentätigkeiten der Abgeordneten |
| Vereins- und Handelsregister, Bundesanzeiger | Vorstände, Geschäftsführer, Jahresabschlüsse |
| Parteispenden (Bundestagsdrucksachen) | Spenden über 10.000 Euro |
| EU-Transparenzregister | EU-Lobbyeinträge |
| OECD, Eurostat, Destatis | Ländervergleich, Inflation, Personalstand |

Wo ein Titel seine Empfänger nicht veröffentlicht, endet der Fluss mit „Empfänger nicht veröffentlicht“ und einem Hinweis, wie man per Informationsfreiheitsgesetz nachfragt.

## Wie es gebaut wird

- **Website ohne Server-Logik.** Alle Daten werden vorab berechnet und als Dateien ausgeliefert. Der Browser zeichnet. Kein Login, keine Datenbank, kein Tracking. Ein geteilter Haushalt steckt komplett im Link.
- **Pipeline getrennt davon.** Ein Programm liest die Quellen ein, prüft die Summen gegen die amtlichen Gesamtzahlen und verdichtet alles zu den Datendateien. Bricht ab, wenn eine Summe nicht stimmt.
- **Beziehungen als gepflegte Liste.** Personen und Organisationen liegen als lesbare Dateien mit Quelle und Datum in diesem Repository. Wer einen Beleg hat, reicht ihn als Pull Request oder Issue ein.
- **Hosting** auf einem eigenen Linux-Server bei Hostinger, statische Auslieferung über nginx, HTTPS.

Geplante Struktur:

```
bundeshaushaltstracker/
├── web/        Oberfläche (statische Website)
├── pipeline/   Einlesen, Prüfen, Verdichten der Quellen
├── data/
│   ├── raw/        Rohdaten mit Abrufdatum (archiviert)
│   ├── build/      berechnete Datendateien für die Website
│   ├── entities/   Personen und Organisationen, je eine Datei, mit Quellen
│   └── texts/      Erklärtexte zu Titeln, zwei Sätze, mit Quelle
└── docs/       Konzept, Entscheidungen, Mockups
```

Die Ausbaustufen, jede für sich veröffentlichbar:

1. **Bund 2015–2025**: Fluss, Karte, Säulen, Regler, Presets, Teilen, Jahresleiste, „Was ist gewachsen?“, Kostenarten-Schnitt. Sozialkassen als grobe Töpfe.
2. **Empfänger**: Empfänger-Seiten mit Zeitlinie, Empfänger-Art-Schnitt, Personal-Regler.
3. **Personen**: Akten, Netz, Melde- und Korrekturweg.
4. **Ländervergleich**: Tafeln, dann „System übernehmen“-Presets.

## Mitmachen

Der Bundeshaushaltstracker lebt davon, dass viele nachprüfen. Drei Wege:

- **Beleg einreichen.** Du kennst eine amtliche Quelle für eine Zahlung, einen Posten, eine Verbindung, die fehlt? Issue oder Pull Request mit Link, Datum und dem, was die Quelle belegt. Ohne amtliche Quelle wird nichts aufgenommen, auch nicht, wenn es plausibel klingt.
- **Fehler melden.** Eine Zahl stimmt nicht, eine Zuordnung ist falsch, ein Text ist unklar? Issue mit Link auf die Stelle.
- **Erklärtexte schreiben.** Jeder Haushaltstitel soll in zwei Sätzen erklärt sein, was er ist und wer ihn bekommt, mit Paragraf oder Quelle. Es sind einige tausend. Jede Hilfe zählt.

Code-Beiträge sind willkommen, sobald die erste Stufe steht. Bis dahin ist das Konzept die beste Stelle für Kritik.

## Lizenz

Code unter MIT. Daten und Texte unter CC BY 4.0, mit Nennung der amtlichen Ursprungsquellen. Die zugrunde liegenden amtlichen Daten unterliegen ihren jeweiligen Lizenzen (überwiegend Datenlizenz Deutschland 2.0).

## Was der Bundeshaushaltstracker nicht ist

Keine Prognose. Keine Bewertung. Keine Enthüllung. Der Bundeshaushaltstracker legt öffentliche Zahlen und öffentliche Posten so nebeneinander, dass man sie lesen kann. Was man darin sieht, ist Sache des Lesers.
