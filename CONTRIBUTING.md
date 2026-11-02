# Mitmachen und Moderation

Der Bundeshaushaltstracker wird wie ein Nachschlagewerk gepflegt: Jeder kann Korrekturen und Belege einreichen, Prüfer übernehmen sie, jede Änderung ist nachvollziehbar. Das läuft über GitHub, nicht über eigene Nutzerkonten.

## Wer darf was

- **Einreichen** kann jeder mit GitHub-Konto: als Issue („Fehler melden / Beleg einreichen“ auf jeder Seite öffnet eine Vorlage) oder als Pull Request auf die Pflegedateien unter `data/manual/`.
- **Übernehmen** dürfen Prüfer mit Schreibrecht im Repository. Prüfer ernennt der Betreiber. Ein Prüfer übernimmt keine eigene Einreichung ohne zweiten Blick.
- Jede Übernahme trägt in der Git-Historie Datum, Quelle und den Prüfer. Rückgängig machen ist jederzeit möglich; die Historie bleibt.

## Was ein Beleg ist

Nur amtliche Quellen oder Selbstauskünfte der Genannten zählen: Bundeshaushalt (bundeshaushalt.de), Haushaltsrechnung, Lobbyregister, Biografien und Drucksachen des Bundestags, Veröffentlichungen der Bundesregierung und der Ministerien, Register, Gerichtsentscheidungen, Jahresabschlüsse der Empfänger. Presseberichte, Wikipedia, Blogs und Vermutungen reichen nicht, auch nicht, wenn sie plausibel klingen. Jeder Beleg braucht eine URL und ein Datum.

## Was wo gepflegt wird

| Datei | Inhalt |
|---|---|
| `data/manual/empfaenger.yaml` | Empfänger-Stamm: Aliasse, Zuordnung zu Haushaltstiteln, Förderkatalog-Suchname, Art |
| `data/manual/verbindungen.yaml` | Von Hand belegte Verbindungen Person ↔ Organisation (nur mit `geprueft: true` und Quelle) |
| `data/manual/personen.yaml` | Zusammenführung oder Trennung gleicher Namen mit Beleg; Freischaltung von Akten (`freigabe`) |
| `data/manual/regierung.yaml` | Mitglieder der Bundesregierung, Staatsminister, Staatssekretäre mit Quelle und Datum |
| `data/manual/jahresabschluss.yaml` | Kennzahlen aus Jahresabschlüssen mit Seitenangabe |
| `data/manual/bezuege.yaml` | Gesetzlich festgelegte Bezüge (Abgeordnetenentschädigung, Pauschalen, B 11, Dienstaufwandsentschädigung) je Gültigkeitszeitraum mit Fundstelle; Beginn von Ausschussvorsitzen (`vorsitz_ab`) |
| `data/manual/ressorts.yaml` | Geldgeber-Namen → Einzelplan |
| `data/texts/titel/*.md` | Erklärtexte zu Haushaltstiteln (zwei Sätze, Quelle Pflicht) |

Die Prüflisten unter `data/review/` erzeugt die Pipeline bei jedem Build lokal; sie zeigen, was noch keine Zuordnung hat (ähnliche Namen, Spenden ohne Treffer, gleiche Personennamen). Wer eine Prüfliste abarbeitet, trägt das Ergebnis in die Pflegedatei ein.

## Relevanzregel für Personen-Akten

Gebaut werden Akten für alle Personen aus Lobbyregister (Vertreter von Empfängern mit Bundesmitteln), Bundestag und Bundesregierung. Öffentlich sichtbar mit eigener Seite ist eine Akte, wenn die Person ein öffentliches Amt hat, eine belegte Verbindung zur Entscheidungsseite besteht, oder ein Prüfer sie in `personen.yaml` unter `freigabe` mit Quelle freigeschaltet hat. Alle anderen Personen stehen namentlich auf der Seite ihrer Organisation und im Netz als Knoten ohne eigene Seite. Betroffene können jederzeit Korrektur oder Gegendarstellung verlangen; der Weg steht im Impressum.

## Regeln für Texte

Tatsachensätze mit Quelle und Datum. Keine Wertung, kein „Verdacht“, keine Warnfarben, keine Adressen, keine Spenden natürlicher Personen. Beträge aus verschiedenen Quellen werden nebeneinander gezeigt und nie addiert. Was daraus folgt, entscheidet der Leser.

## Ablauf eines Pull Requests

1. Pflegedatei ändern, Quelle und Datum eintragen (die Vorlage fragt beides ab).
2. `cd pipeline && uv run pytest -q` muss grün sein; die Tests prüfen Pflichtfelder und Quellen.
3. Ein Prüfer liest die Quelle gegen und übernimmt. Bei Personenangaben prüft er zusätzlich, ob der Personenkreis der Spec (§4.7) eingehalten ist.
4. Der nächste Build veröffentlicht die Änderung; die Prüflisten verkleinern sich entsprechend.
