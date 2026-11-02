# Recherche-Cockpit – Entwicklungsplan (nur Konzept)
Stand: 02.11.2026. **Keine Änderungen an Anwendungscode, Build, Pipeline oder Tests.**

## Zielbild
Eine zusammenhängende Rechercheoberfläche, deren Hauptnavigation Geldflüsse → Empfänger → Beziehungen → Vergaben → Auffälligkeiten folgt. Der Geldfluss bleibt als Kontext in allen Ansichten erreichbar. Durchgehend helles, ruhiges Design statt schwarzer Navigation.

## Vier zusammenhängende Screens
1. **Recherche-Cockpit:** Suche, Jahr, Soll/Ist, Herkunft, Ressort, Haushaltstitel, Empfänger und Quellenstatus; Einstieg über Geldfluss.
2. **Verflechtungsnavigator:** ausgewählte Organisation in der Mitte, Personen in öffentlichen Funktionen, Ministerien, belegte Lobbyregisterbeziehungen und veröffentlichte Spenden als getrennte Kantenarten. Zeitfilter, Legende und Kanten-Detailpanel.
3. **Vergabeanalyse:** Auftraggeber, Auftragnehmer, Vergabeart, Projekt, Vertragswert und Vergabedatum; Filter, Ranglisten und Konzentrationsdiagramme. Bundeshaushaltstitel sind nicht automatisch Einzelvergaben.
4. **Auffälligkeiten-Explorer:** erklärbare Muster (Kostenanstieg, Empfängerkonzentration, wiederkehrende Vergaben, zeitliche Überschneidung). Nur als **Recherchehinweise** und nie als Korruptionsbewertung.

## Einheitliche Interaktion
Globale Auswahl: Zeitraum, Ressort, Titel, Empfänger, Quelle. Eine Auswahl im Sankey filtert Netzwerk und Vergaben; ein Klick auf eine Netzwerk-Kante zeigt die Originalfundstelle. Zurück-Navigation erhält die Recherchehistorie. Nicht belegte Beziehungen erscheinen nicht als Tatsachen.

## Daten- und Belegmodell für den Entwickler
Entitäten: Haushaltstitel, Kapitel, Ressort, Projekt, Vergabe, Empfängerorganisation, öffentliche Person, Partei, Quelle.
Kanten: Mittelansatz, tatsächliche Auszahlung, Auftragsvergabe, Organfunktion, Ressortzuständigkeit, registrierte Interessenvertretung, dokumentierte Spende, nachgewiesene Entscheidung.
Pro Kante: Entitäts-IDs, Typ, Betrag und Währung falls zutreffend, Zeitfenster, Quell-URL, Fundstelle, Abrufdatum, Belegstatus. Gleiche Namen nicht ohne verlässliche Kennungen zusammenführen. Zahlungen, Vergaben, Lobbyregister-Spannen und Haushaltsansätze nicht addieren.

## UX- und Qualitätsanforderungen
- Jahr, Soll/Ist, Datenstand und Quellenstatus jederzeit sichtbar.
- Keine erfundenen Empfänger oder Personenverbindungen.
- Ministerielle Zuständigkeit nicht mit individueller Entscheidung über eine Zahlung verwechseln.
- Datenlücken, historische Änderungen von Ressortzuschnitten und unterschiedliche Veröffentlichungsstände anzeigen.
- Kanten per Tastatur erreichbar; responsive Detailansicht; Quellen auch im Export.
- Keine politisch wertenden Risikowerte. Regelbasierte Hinweise mit offenem Schwellenwert und erklärter Grundgesamtheit.

## Umsetzungsreihenfolge
**Phase 0 – Bestandsaufnahme:** vorhandene Svelte-5-Views, D3-Geldfluss und JSON-Datenverträge prüfen. Mockup-Screens auf vorhandene Komponenten abbilden.
**Phase 1 – Fundament:** globale Filter, Beleg-/Entitätsmodell, Zustände für fehlende Daten, Navigation und Design Tokens.
**Phase 2 – Geldfluss & Vergaben:** Drilldown, Empfängerkarte, Vergabefilter und Datenherkunft.
**Phase 3 – Verflechtungen:** Netzwerk, Kantenfilter, Personen-/Organisationsakten und Quellenpanel.
**Phase 4 – Auffälligkeiten & Dossiers:** nachvollziehbare Regeln, Zeitachse, Rechercheexport, Accessibility und Performancetests.

## Abnahmekriterien
1. Ein ausgewählter Geldfluss bleibt beim Wechsel der Ansichten nachvollziehbar.
2. Jede veröffentlichte Relation hat eine überprüfbare Quelle und Gültigkeitsdauer.
3. Kein stillschweigendes Mischen von Soll/Ist, Vergabevolumen und Auszahlung.
4. Jede Auffälligkeit nennt Regel, Eingabedaten, Zeitraum und Grenzen der Aussage.
5. Mobile Bedienung und Tastaturbedienung für zentrale Recherchepfade.
6. Die Mockups sind explizit illustrativ und keine belegten realen Datensätze.

## Grenzen
Das Konzept setzt Verfügbarkeit und rechtliche Nutzbarkeit passender Daten voraus. Insbesondere konkrete Endempfänger und vollständige Vergaben sind nicht aus jedem Haushaltstitel ableitbar. Kein fertiger Code, keine Implementierungszusage.
