# Pipeline (`bhtracker`)

Lädt die amtlichen Haushaltsdaten von bundeshaushalt.de, prüft sie gegen die veröffentlichten Gesamtsummen und verdichtet sie zu den JSON-Dateien, die die Website ausliefert.

```bash
cd pipeline
uv sync
uv run bht fetch --from 2015 --to 2026     # Rohdateien nach data/raw (Cache, Abruflog)
uv run bht build --from 2015 --to 2026     # data/build/bund/<jahr>.json, zeitreihe.json, index.json
uv run bht check 2025                      # nur Summenprüfung eines Jahres
uv run pytest -q
```

## Quellen und Regeln

- **Download-Portal**: `GET /internalapi/dataportalConfig` liefert je Jahr die Kategorien (`soll_YYYY`, `soll_YYYY_nK` Nachträge, `soll_YYYY_e` Entwurf, `ist_YYYY`); `GET /internalapi/dataportal?year=&category=&filter=hh` die Dateien unter `/static/daten/<jahr>/...`. Lizenz laut Portal: öffentliche Daten ohne urheberrechtlichen Schutz; rechtlich verbindlich ist stets das amtliche Dokument.
- **Soll** je Titel kommt aus der Portal-CSV (Beträge in Tsd €; bevorzugt die `_ALL`-Variante mit Anlagen). Nachtrags-CSVs enthalten nur geänderte Titel (Spalten `soll`/`bisher`) und werden in Reihenfolge n1, n2 … darübergelegt.
- **Haushaltsrechnung** (`rechnung_<jahr>.xml`, Beträge in Euro) liefert **Ist** und den **Soll-Endstand** inkl. aller Nachträge. Liegt sie vor, ersetzt ihr Soll die CSV-Werte. Die XML führt keine Kapiteltexte (werden aus der CSV ergänzt) und enthält leere Platzhalter-Titel (`nr=""`), die übersprungen werden.
- **Anlagen** (`anlage`): Kapitel mit Nummer `??9?` außerhalb des Kernhaushalts. Liegt neben der `_ALL`- auch die Kern-Datei vor, gilt die Differenzmenge; sonst `data/manual/sondervermoegen.yaml` plus Muster. Davon sind nur Sondervermögen und das NATO-Programm **zuschaltbare Nebenhaushalte** (`sv: true`); EU-Anlagen (Durchlauf, im Kern schon als Weiterleitung enthalten) und Behörden-Wirtschaftspläne (aus Kern-Zuschüssen finanziert) werden nicht in den Build geschrieben, sonst zählten sie doppelt. Anlagen liegen im Portal nur für 2015 und ab 2023 vor (`sv_jahre` im Index); 2016–2022 gibt es keine `_ALL`-Dateien.
- **Transfers** (`transfer: true`): Zahlungen zwischen Kern und Sondervermögen (Zuweisung an den KTF, an die Aufbauhilfe …) und Einnahmen der Sondervermögen aus dem Bundeshaushalt oder anderen Sondervermögen, erkannt an der Zweckbestimmung. Die Website lässt sie bei zugeschalteten Nebenhaushalten weg, damit nichts doppelt zählt.
- **Summenprüfung**: `data/manual/gesamtplan_summen.yaml` enthält je Jahr die amtlich veröffentlichten Gesamtausgaben des Kernhaushalts (Toleranz 100 Mio €). Zusätzlich muss Ausgaben = Einnahmen (ohne Kredite) + Kreditaufnahme gelten. Schlägt eine Prüfung fehl, wird das Jahr nicht geschrieben und `bht build` endet mit Exit 1.
- **Kredite** (Gruppe 325) zählen nicht als Einnahme; sie erscheinen im Index als `kredite`.

## Bekannte Eigenheiten der Rohdaten

| Jahr | Eigenheit | Umgang |
|---|---|---|
| 2015 | Nachträge nur als XLSX/PDF; Grundhaushalt-CSV 299,1 Mrd | Soll-Endstand 306,9 Mrd aus der Haushaltsrechnung |
| 2016, 2020, 2021, 2023 | Nachtrags-CSVs sind Änderungslisten | kumulativ angewandt; Endstand aus der Rechnung |
| 2021 | Datei der Kategorie `soll_2021` heißt bereits `hh_2021_n2_utf8.csv` | normal behandelt |
| 2023 | Kapitel zweistellig (`"01"` statt `"0101"`), Art kleingeschrieben (`e`/`a`); `HH_2023.csv` enthält Anlagen ohne `_ALL`-Suffix | Parser stellt Einzelplan voran; Anlagen über Kapitelmuster |
| 2024, 2026 | nur `_ALL`-Datei, keine Kern-Datei | Anlagen über Kapitelmuster |
| alle | Kopfzeilen variieren (`einahmen-ausgaben`, `soll ` mit Leerzeichen, `-art` statt `-text`), Encodings UTF-8/BOM/cp1252, negative Beträge mit nachgestelltem Minus | normalisiert in `parse_csv.py` / `model.py` |

## Ergebnis des Builds (Stand 1.11.2026)

| Jahr | Ausgaben Kern | Einnahmen ohne Kredite | Kredite | Ist |
|---|---|---|---|---|
| 2015 | 306,9 | 306,9 | 0,0 | ja |
| 2016 | 316,9 | 316,9 | 0,0 | ja |
| 2017 | 329,1 | 329,1 | 0,0 | ja |
| 2018 | 343,6 | 343,6 | 0,0 | ja |
| 2019 | 356,4 | 356,4 | 0,0 | ja |
| 2020 | 508,5 | 290,8 | 217,8 | ja |
| 2021 | 572,7 | 332,6 | 240,2 | ja |
| 2022 | 495,8 | 356,8 | 138,9 | ja |
| 2023 | 461,2 | 433,8 | 27,4 | ja |
| 2024 | 476,8 | 437,8 | 39,0 | ja |
| 2025 | 502,5 | 420,8 | 81,8 | ja |
| 2026 | 524,5 | 426,6 | 98,0 | nein |

Hinweis zu 2015–2019: In diesen Jahren weist die Kreditaufnahme 0 aus („schwarze Null“); Einnahmen und Ausgaben sind im Soll ausgeglichen.

## Dateiformate (data/build)

- `bund/<jahr>.json`: `{jahr, stand, quelle:{soll, ist, hinweise}, epl:{nr:text}, kap:{nr:text}, rows:[{id, art, epl, kap, titel, text, fkt, flex, tgr, soll, ist, sv}]}`; Beträge in Euro.
- `zeitreihe.json`: `{jahre:[…], titel:{id:{text, epl, kap, art, sv, soll:[…], ist:[…]}}, kap:{…}, epl:{…}}`; `null` für fehlende Jahre.
- `index.json`: `{jahre, ist_bis, summen:{jahr:{ausgaben, einnahmen, kredite}}, erzeugt}`.

## Empfänger-Daten (Stufe 2)

Drei amtliche Quellen liefern die Empfänger-Seiten; alle Abrufe laufen über `bht fetch-empfaenger`, der Build liest nur aus `data/raw/` und `data/manual/`.

| Quelle | Kommando | Rohdaten | Dauer |
|---|---|---|---|
| Lobbyregister des Bundestags, Gesamtexport aller Detailprofile (eine Anfrage, 480 MB) | `uv run bht fetch-empfaenger --quellen lobbyregister` | `data/raw/lobbyregister/R<Nr>_<Id>.json` (nur Organisationen) | 1 bis 2 Minuten |
| Biografien der Abgeordneten (bundestag.de), Liste über den Ajax-Endpunkt | `uv run bht fetch-empfaenger --quellen bundestag` | `data/raw/bundestag/<id>.html` plus `.url` | rund 640 Seiten, 15 Minuten bei 1,5 s Pause |
| Förderkatalog des Bundes, Suche je Empfängername mit CSV-Export | `uv run bht fetch-empfaenger --quellen foerderkatalog` | `data/raw/foerderkatalog/<empfaenger-id>.csv` (leer = kein Treffer) | rund 1.500 Empfänger, 1 bis 2 Stunden |

`--limit N` begrenzt die Zahl der Abrufe (Tests), `--pause` die Wartezeit zwischen Anfragen (Standard 1,5 s), `--gesamtexport DATEI` nutzt einen bereits geladenen Lobbyregister-Export. Vorhandene Rohdateien werden nicht erneut geladen; zum Aktualisieren löschen.

`bht build` schreibt danach `data/build/empfaenger/index.json` und je Empfänger `data/build/empfaenger/<id>.json`, außerdem die Prüflisten `data/review/empfaenger_kandidaten.yaml` (ähnliche Namen zwischen den Quellen) und `data/review/verbindungen_kandidaten.yaml` (Angaben von Abgeordneten, die einem Empfänger nur ähneln). `bht build --ohne-personen` lässt Personen und Verbindungen aus den Build-Dateien weg.

Pflegedaten: `data/manual/empfaenger.yaml` (Stamm, Aliasse, Titel-Zuordnung, Förderkatalog-Suchname), `data/manual/ressorts.yaml` (Geldgeber-Namen → Einzelplan), `data/manual/verbindungen.yaml` (von Hand bestätigte Verbindungen, nur mit `geprueft: true` und Quelle), `data/manual/jahresabschluss.yaml` (Kennzahlen aus Jahresabschlüssen mit Seitenangabe).

Regeln: Beträge aus Haushalt (Euro), Lobbyregister (Spannen, Eigenangabe) und Förderkatalog (Projektsummen) stehen getrennt nebeneinander und werden nie addiert. Verbindungen Person ↔ Organisation werden nur bei exakt gleichem normalisiertem Namen automatisch veröffentlicht; alles andere wartet in der Prüfliste.
