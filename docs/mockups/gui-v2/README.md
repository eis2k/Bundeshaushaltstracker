# GUI v2 – Mockup-Galerie

Sieben SVG-Konzeptentwürfe für Dashboard, Geldfluss, Simulator, Zeitvergleich, Empfänger, Haushaltstitel und Mobilansicht. Alle dargestellten Werte sind **Platzhalter**, keine amtlichen Haushaltszahlen.

| Ansicht | Datei | Schwerpunkt |
|---|---|---|
| Dashboard | [dashboard.svg](dashboard.svg) | Kennzahlen und Einstieg |
| Geldfluss | [geldfluss.svg](geldfluss.svg) | Navigierbarer Geldfluss |
| Simulator | [simulator.svg](simulator.svg) | Modellrechnung |
| Zeitvergleich | [zeitvergleich.svg](zeitvergleich.svg) | Soll/Ist und Inflation |
| Empfänger | [empfaenger.svg](empfaenger.svg) | Belegbare Zuordnung |
| Haushaltstitel | [titelansicht.svg](titelansicht.svg) | Detail und Quelle |
| Mobil | [mobil.svg](mobil.svg) | Responsive Konzept |

## Design- und Umsetzungsnotizen
- Informationshierarchie: Verstehen → Vergleichen → Gestalten.
- Jede Zahl mit Jahr, Soll/Ist, Quelle, Abrufdatum und Datenstatus.
- Modellwerte eindeutig als Modellrechnung markieren; keine Prognose suggerieren.
- Fehlende Empfängerzuordnungen nicht automatisch behaupten.
- Svelte 5 und bestehende D3-Komponenten schrittweise wiederverwenden; keine komplette Neuentwicklung ohne Codeaudit.
- Nächster Schritt: Komponenten-Mapping, responsive High-Fidelity-Screens und Accessibility-Tests.

Siehe auch [GUI-Review](../../gui-review-2026-11-02.md).
