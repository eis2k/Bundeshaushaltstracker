# Prüflisten (automatisch erzeugt)

Die Pipeline schreibt hierher, was sie nicht sicher zuordnen konnte. Nichts aus diesem Ordner erscheint auf der Website.

- `empfaenger_kandidaten.yaml`: Namen aus Haushaltstiteln, Lobbyregister und Förderkatalog, die einander ähneln, aber nicht exakt gleich sind. Bestätigen: Alias in `data/manual/empfaenger.yaml` eintragen.
- `verbindungen_kandidaten.yaml`: Organisationen aus den veröffentlichungspflichtigen Angaben von Abgeordneten, die einem Empfänger ähneln, aber nicht exakt gleich heißen. Bestätigen: Eintrag in `data/manual/verbindungen.yaml` mit `geprueft: true` und Quelle.

Regel aus der Spec §4.6a: Veröffentlicht wird nur, was exakt übereinstimmt oder von einem Menschen bestätigt wurde.
