# Mockup- und Implementierungsplan: „Wer profitiert?“
Stand: 2026-11-02. **Nur Konzept, keine Codeänderung.**

## Ziel
Vom amtlichen Geldfluss zu konkreten Empfängern und von dort zu nachweisbaren öffentlichen Funktionen und Beziehungen navigieren. Die Startansicht bleibt Geldfluss-zentriert, mit durchgehend heller, ruhiger Oberfläche.

## Bildschirmaufbau
1. Oben Jahr, Soll/Ist, Quelle, Suchfeld und Datenstand.
2. Links Herkunft → Ministerium → Kapitel/Titel → dokumentierter Empfänger als navigierbarer Sankey.
3. Rechts ausgewählter Empfänger: belegte Beträge, Zeitraum, Rolle der Zahlung und Datenabdeckung.
4. Darunter Netzwerk mit getrennten Kantenarten: Zahlung, öffentliches Amt, Organfunktion, registrierte Interessenvertretung, veröffentlichte Parteispende.
5. Bei Auswahl einer Kante: Belegpanel mit Originalfundstelle, Datum, Erhebungszeitraum, Status und eventueller Unsicherheit.
6. Zeitverlauf und Verträge/Projekte nur dort, wo Quellen die konkrete Zuordnung ermöglichen.

## Rechercheablauf
Geldquelle auswählen → Ressort und Titel auswählen → Empfänger auswählen → dessen veröffentlichte Vertreter öffnen → belegte Kontakte/Funktionen ansehen → Quellen prüfen. Ein Klick darf die Geldfluss-Herkunft nicht verlieren; Breadcrumbs bleiben erhalten.

## Verbindungsmodell (für spätere Umsetzung)
Knoten: Haushaltsstelle, Ressort, Empfängerorganisation, natürliche Person in öffentlicher Funktion, Partei, Projekt.
Kanten: Zuwendung, Zuständigkeit, Organfunktion, Lobbyregisterbeziehung, Parteispende, dokumentierte Entscheidung. Jede Kante benötigt Quelle, Gültigkeitszeitraum und Belegstatus.
Identitätsauflösung nur mit belastbaren Kennungen oder manueller Prüfung; gleiche Namen reichen nicht.
Keine Vermengung von Titelansatz und tatsächlicher Auszahlung; keine Summierung unterschiedlicher Datenquellen ohne fachliche Prüfung.

## Kennzeichnung
- Belegt: amtliche oder nachvollziehbar dokumentierte Relation.
- Nicht öffentlich / unbekannt: keine verifizierte Empfänger- oder Personenrelation.
- In Prüfung: nicht öffentlich als Tatsache anzeigen.
- Auffälligkeit: rein erklärbarer Datenfilter, **keine** Korruptions- oder Schuldzuweisung.
Eine zeitliche Korrelation oder Verbindung beweist keine Einflussnahme.

## Priorisierte Umsetzung für den Entwickler
P0: Informationsarchitektur, Quellen-/Kantenmodell, Datenstatus und Klickpfad.
P1: Sankey-Drilldown und Empfänger-Detailkarte mit Quellen.
P2: Netzwerkansicht mit Filter nach Relationstyp und Zeitraum.
P3: Zeitverlauf, Projekte, Verträge und nachvollziehbare Recherchefilter.
P4: Mobilansicht, Tastaturbedienung, Performance und Exporte.

## Akzeptanzkriterien
- Nutzer gelangt in maximal vier fachlichen Auswahlstufen von Geldherkunft zum belegten Empfänger.
- Jede sichtbare Relation hat eine aufrufbare Quelle und einen Zeitraum.
- Unbekannte Endempfänger werden nicht erfunden.
- Zuständigkeit eines Ministers wird nicht als persönliche Mitwirkung an jeder Zahlung dargestellt.
- Leichte Navigation ohne schwarzen Seitenbalken; mobil verständliche Stufenansicht.
- Mockup-Werte und Beispielnamen sind ausdrücklich fiktiv; Screenshots sind keine Tatsachenbehauptung.

## Übergabe
Dies ist ein Umsetzungsplan zur späteren Bearbeitung durch einen anderen Entwickler. Keine Änderungen an src/, web/, Pipeline, Tests oder Konfiguration.
