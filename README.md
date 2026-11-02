# Bundeshaushaltstracker

**Wo bleibt das Geld?** Deutschland nimmt mehr Steuern ein als je zuvor, und trotzdem wird gekürzt: bei der Rente, bei den Krankenkassen, fast überall. Der Bundeshaushaltstracker macht den Weg des Geldes sichtbar, von der Lohnsteuer und dem Rentenbeitrag über Bund und Sozialkassen bis zu dem, der es am Ende bekommt. Zurück bis 2015, bis auf den einzelnen Haushaltstitel, mit Quelle an jeder Zahl.

Und weil Zuschauen nicht reicht: Jeder kann den Haushalt umbauen. Rentenzuschuss halbieren, Verteidigung verdoppeln, einen Titel streichen, und sofort sehen, was das mit Einnahmen, Ausgaben und Schulden macht. Den eigenen Haushalt teilt man als Link.

> Status: Stufe 1 im Aufbau, lokal lauffähig (Bund 2015–2026 mit Soll und Ist, Sozialkassen grob, Fluss/Karte/Säulen/Rangliste, Presets, Teilen). Noch nicht veröffentlicht. Siehe [Konzept](docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md), [Umsetzungsplan Stufe 1](docs/superpowers/plans/2026-11-01-stufe-1-bund.md) und die Mockups unter `docs/mockups/`.

---

## Was der Bundeshaushaltstracker kann (wenn es fertig ist)

**Dem Geld folgen.** Die Standardansicht ist ein Geldfluss: links Steuern (blau) und Beiträge (lila), in der Mitte die Töpfe Bundeshaushalt, Rentenkasse, Krankenkassen, Pflege und Arbeitslosenversicherung, rechts wofür und an wen. Jeder Klick auf ein Band hängt eine Spalte an: Ministerium, Kapitel, Titel, Empfänger. Woher das Geld kommt, bleibt immer sichtbar. Wem die Flüsse zu viel sind, schaltet auf die Karte (jeder Euro ist Fläche) oder auf zwei Säulen (Einnahmen gegen Ausgaben).

**Den Haushalt umbauen.** An jedem Titel, Kapitel und Ministerium ein Regler. Oben die Bilanz, die bei jeder Bewegung mitläuft: Einnahmen, Ausgaben, neue Schulden, Abstand zum Original. Presets für die üblichen Streitfragen, kombinierbar, eigene speicherbar. Was gesetzlich festgelegt ist, trägt die Markierung *Gesetz*: ändern darf man es trotzdem, aber die Seite sagt, dass dafür ein Gesetz geändert werden müsste. Wer den Rentenzuschuss halbiert, sieht beim Bund weniger Schulden und bei der Rentenkasse ein Loch in gleicher Höhe.

**Steuer-Modelle.** Auf der Einnahmenseite lassen sich Steuern durchspielen, die es nicht mehr gibt oder die anders aussehen könnten: Vermögensteuer (seit 1997 nicht mehr erhoben), höhere Erbschaftsteuer, Spitzensteuersatz wie vor 2000, Abgeltungsteuer. Jedes Modell rechnet mit offenen Annahmen (Bemessungsgrundlage, Satz, Ausweichreaktion), jede Annahme hat einen Beleg und ist selbst ein Regler. Der Geldfluss zeigt, was davon beim Bund ankommt und was nach Art. 106 GG den Ländern zusteht. Daneben steht der Kasten **„Wer hat das beschlossen“**: Datum, Entscheidung, beteiligte Regierung und Fraktionen, Fundstelle (Drucksache, Gesetzblatt, Urteil). Belege, keine Wertung.

**Zehn Jahre zurück.** Eine Jahresleiste von 2015 bis 2025, zum Ziehen oder Abspielen, umschaltbar zwischen Plan (Soll), tatsächlicher Ausgabe (Ist) und inflationsbereinigt. Dazu die Rangliste **„Was ist gewachsen?“**: jeder Titel mit Wert damals, Wert heute, Zuwachs und Verlaufskurve, filterbar nach Zuwendungen an Vereine, Firmen, Personal oder Geschrumpftes. Auffälliges rutscht von selbst nach oben.

**Wer bekommt es.** Jeder Empfänger von Bundesmitteln, der aus amtlichen Quellen hervorgeht, hat eine Seite (Ansicht „Empfänger“): ganz oben die **belegten Verbindungen** zu Abgeordneten und Regierungsmitgliedern als Tatsachensätze mit Fundstelle, dann das Geld vom Bund aus drei Quellen nebeneinander (Haushaltstitel über zehn Jahre, Zuwendungen laut Lobbyregister in Spannen, Projekte aus dem Förderkatalog; nie addiert), dann wer dahintersteht (gesetzliche Vertreter und Interessenvertreter laut Lobbyregister) und die Pflichtangaben des Empfängers (Finanzierungsquellen, Spenden, Lobbyausgaben, Jahresabschluss mit abgelesenen Kennzahlen und Seitenangabe). Eigenangaben sind als solche gekennzeichnet. Verbindungen erscheinen automatisch nur bei exakt gleichem Organisationsnamen in beiden Quellen; alles Ähnliche wartet in einer Prüfliste (`data/review/`) auf einen Menschen. Im Geldfluss führt ein Titel, dessen Zweckbestimmung den Empfänger nennt, direkt zur Empfänger-Seite; alle anderen enden bei „Empfänger nicht veröffentlicht“ mit Link zur Liste des Ministeriums und zur IFG-Anfrage.

**Wer entscheidet.** Jede Person in öffentlicher Funktion hat eine Akte (Ansicht „Personen“): Abgeordnete mit Fraktion und Ausschüssen, Mitglieder der Bundesregierung und Staatssekretäre mit Ressort, Vorstände, Geschäftsführungen und Interessenvertreter der Empfänger laut Lobbyregister. Die Akte zeigt die Organisationen der Person und deren Geld vom Bund, die veröffentlichungspflichtigen Angaben aus dem Bundestag wörtlich, Parteispenden der verbundenen Organisationen und eine Zeitlinie, alles mit Quelle und Datum. Gleiche Namen werden nur mit Beleg zusammengeführt. Öffentlich sichtbar sind Akten nach einer Relevanzregel wie bei Wikipedia (öffentliches Amt, belegte Verbindung oder Freigabe durch einen Prüfer); alle anderen Personen stehen auf der Seite ihrer Organisation. Ein Knopf „Umfeld zeigen“ öffnet auf jeder Akte und jeder Empfänger-Seite ein Netz zwei Schritte weit: Geld, Posten und Spenden als Kanten, Ministerien und Parteien als Randknoten, nie das ganze Knäuel. Das Netz dient zum Finden, die Akte zum Belegen. Korrekturen laufen als Pull Request über GitHub (`CONTRIBUTING.md`).

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

## Lokal starten

```bash
cd pipeline && uv sync && uv run bht fetch && uv run bht build   # Daten laden und aufbereiten (einmalig, ~2 Minuten)
cd ../web && npm install && npm run dev                           # Entwicklungsserver auf http://localhost:5173
```

Tests: `cd pipeline && uv run pytest` und `cd web && npm test && npm run check`.

## Deployment

**Oberfläche (GUI v3, Stufen 4a und 4c):** Kopfleiste mit Jahr und Suche (Einzelpläne, Empfänger, Akten), weiße Seitenleiste mit neun Einträgen (Dashboard, Haushalt, Geldflüsse & Profiteure, Ministerien, Empfänger & Zuwendungen, Haushaltssimulator, Zeitvergleich, Politik & Verantwortung, Verflechtungen), Dashboard mit Kennzahlen, Herkunft/Verwendung, kompaktem Geldfluss und Teaser-Karten, Geldflüsse mit Empfänger-Spalte und Karte „Politische Verantwortung“, Empfänger-Detailseite „Wer profitiert?“, Ministerien-Detailkarte, Kabinett mit Partei-Etikett, Haushaltssimulator mit Reglerkarten und Ergebniskarte. Stufe 4d ergänzt: Investitionen-Linie auf dem Dashboard, Reiter „Nach Bereichen“ mit Ring, Ministerien-Tabelle mit Vorjahresänderung, Seite „Daten & Quellen“ (Stände, Lizenzen, Lücken, JSON-Downloads), Dunkelmodus (Hell | Dunkel | System, im Browser gespeichert), eingebettetes Umfeld auf der Empfänger-Seite. Leitlinie sind die Detail-Mockups unter `docs/recherche-cockpit/images/` (Spec §4.10 bis §4.12); Porträts und Logos sind bis Stufe 4b Platzhalter mit Initialen. Die Tokens stehen in `web/src/app.css`, Symbole aus Lucide (ISC).

**Lokal im Browser testen (Docker):** `docker compose up -d --build` baut die Seite samt Daten in ein nginx-Image und startet sie unter http://localhost:8080, unabhängig vom Dev-Server; nach einem neuen `bht build` denselben Befehl erneut ausführen, `docker compose down` stoppt den Container. Ein öffentliches Deployment gibt es erst nach rechtlicher Prüfung.

`npm run build` erzeugt in `web/dist/` die komplette Seite samt Daten. `deploy/deploy.sh` baut und spielt sie per rsync auf den Server (Zugang über die Umgebungsvariablen `BHT_HOST`, `BHT_USER`, optional `BHT_PATH`). Die nginx-Konfiguration liegt in `deploy/nginx.conf`; HTTPS kommt über certbot. Vor der Veröffentlichung sind `web/public/impressum.html` und `web/public/datenschutz.html` mit den Betreiberangaben zu füllen.

## Mitmachen

Der Bundeshaushaltstracker lebt davon, dass viele nachprüfen. Drei Wege:

- **Beleg einreichen.** Du kennst eine amtliche Quelle für eine Zahlung, einen Posten, eine Verbindung, die fehlt? Issue oder Pull Request mit Link, Datum und dem, was die Quelle belegt. Ohne amtliche Quelle wird nichts aufgenommen, auch nicht, wenn es plausibel klingt. Auf jeder Empfänger-Seite öffnet „Fehler melden / Beleg einreichen“ ein vorausgefülltes Issue; die Prüflisten unter `data/review/` zeigen, welche Zuordnungen noch auf Bestätigung warten.
- **Fehler melden.** Eine Zahl stimmt nicht, eine Zuordnung ist falsch, ein Text ist unklar? Issue mit Link auf die Stelle.
- **Erklärtexte schreiben.** Jeder Haushaltstitel soll in zwei Sätzen erklärt sein, was er ist und wer ihn bekommt, mit Paragraf oder Quelle. Es sind einige tausend. Jede Hilfe zählt.

Code-Beiträge sind willkommen, sobald die erste Stufe steht. Bis dahin ist das Konzept die beste Stelle für Kritik.

## Lizenz

Code unter MIT. Daten und Texte unter CC BY 4.0, mit Nennung der amtlichen Ursprungsquellen. Die zugrunde liegenden amtlichen Daten unterliegen ihren jeweiligen Lizenzen (überwiegend Datenlizenz Deutschland 2.0).

## Was der Bundeshaushaltstracker nicht ist

Keine Prognose. Keine Bewertung. Keine Enthüllung. Der Bundeshaushaltstracker legt öffentliche Zahlen und öffentliche Posten so nebeneinander, dass man sie lesen kann. Was man darin sieht, ist Sache des Lesers.
