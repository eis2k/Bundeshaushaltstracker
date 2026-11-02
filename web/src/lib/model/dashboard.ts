/** Dashboard (Spec §4.11): Kennzahlen, Herkunft und Verwendung, Entwicklung als Index. Alles aus den Jahresdaten, nichts addiert über Quellen. */

import type { EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import { balance, effectiveValue, type Factors } from "./scenario";
import { includeRow, revenueGroups } from "./tree";
import type { YearData } from "./types";
import type { Zeitreihe } from "./zeitreihe";

export interface Kennzahlen {
  haushalt: number;
  /** Veränderung der Ausgaben gegen das Vorjahr in Prozent, null ohne Vorjahr. */
  veraenderung: number | null;
  einnahmen: number;
  steuern: number;
  empfaengerMitSeite: number;
  aktenSichtbar: number;
}

/** `roh` = unveränderte Soll-Daten des Jahres für die Veränderung zum Vorjahr (nominal, ohne Faktoren, ohne Ist- oder Preisumrechnung); Vorgabe `data`. */
export function kennzahlen(data: YearData, vorjahr: YearData | null, includeSv: boolean, factors: Factors, empfaenger: EmpfaengerIndex | null, personen: PersonIndex | null, roh: YearData = data): Kennzahlen {
  const b = balance(data, factors, includeSv);
  const r = balance(roh, {}, includeSv);
  const v = vorjahr ? balance(vorjahr, {}, includeSv) : null;
  const steuern = revenueGroups(data, includeSv).filter((g) => g.id.startsWith("E:steuern")).reduce((s, g) => s + g.soll, 0);
  return {
    haushalt: b.ausgaben,
    veraenderung: v && v.ausgaben > 0 ? Math.round(((r.ausgaben - v.ausgaben) / v.ausgaben) * 1000) / 10 : null,
    einnahmen: b.einnahmen,
    steuern,
    empfaengerMitSeite: empfaenger?.eintraege.length ?? 0,
    aktenSichtbar: personen?.eintraege.filter((p) => p.sichtbar).length ?? 0,
  };
}

export interface Posten { label: string; wert: number; anteil: number; id: string }

/** Herkunft aus den Einnahmegruppen; Verwendung (negative Posten wie die Globale Minderausgabe bleiben sichtbar, damit die Anteile 100 ergeben) nach Ministerien (alle Einzelpläne außer 32 und 60), Allgemeine Finanzverwaltung (60), Bundesschuld (32). */
export function herkunftVerwendung(data: YearData, includeSv: boolean, factors: Factors): { herkunft: Posten[]; verwendung: Posten[] } {
  const gruppen = revenueGroups(data, includeSv);
  const herkunftRoh = gruppen.map((g) => ({ id: g.id, label: g.label, wert: g.rows.reduce((s, r) => s + effectiveValue(r, factors), 0) })).filter((x) => x.wert !== 0);
  const hs = herkunftRoh.reduce((s, x) => s + x.wert, 0) || 1;
  const herkunft = herkunftRoh.sort((a, b) => b.wert - a.wert).map((x) => ({ ...x, anteil: Math.round((x.wert / hs) * 1000) / 10 }));

  const klassen: Record<string, number> = { ministerien: 0, finanzverwaltung: 0, schuld: 0 };
  for (const r of data.rows) {
    if (r.art !== "A" || !includeRow(r, includeSv)) continue;
    const w = effectiveValue(r, factors);
    if (r.epl === "32") klassen.schuld += w;
    else if (r.epl === "60") klassen.finanzverwaltung += w;
    else klassen.ministerien += w;
  }
  const vs = Object.values(klassen).reduce((s, x) => s + x, 0) || 1;
  const verwendung = [
    { id: "ministerien", label: "Ministerien", wert: klassen.ministerien },
    { id: "finanzverwaltung", label: "Allgemeine Finanzverwaltung", wert: klassen.finanzverwaltung },
    { id: "schuld", label: "Bundesschuld", wert: klassen.schuld },
  ].filter((x) => x.wert !== 0).sort((a, b) => b.wert - a.wert).map((x) => ({ ...x, anteil: Math.round((x.wert / vs) * 1000) / 10 }));
  return { herkunft, verwendung };
}

/** Gesamtausgaben je Jahr als Index (erstes Jahr mit Wert = 100). Ist nur, wenn alle Reihen Ist haben (kein Mischen mit Soll). Investitionen liegen in der Zeitreihe nicht als Reihe vor → null. */
export function entwicklungIndex(z: Zeitreihe, stand: "soll" | "ist"): { jahr: number; gesamt: number | null; investitionen: number | null }[] {
  const summen = z.jahre.map((_, i) => {
    let s = 0;
    let hat = false;
    for (const serie of Object.values(z.epl)) {
      if (serie.art !== "A" || serie.sv) continue;
      const w = stand === "ist" ? serie.ist[i] : serie.soll[i];
      if (w == null) { if (serie.soll[i] != null) return null; continue; }
      s += w; hat = true;
    }
    return hat ? s : null;
  });
  const basis = summen.find((s) => s != null && s > 0) ?? null;
  return z.jahre.map((jahr, i) => ({ jahr, gesamt: basis && summen[i] != null ? Math.round((summen[i]! / basis) * 1000) / 10 : null, investitionen: null }));
}
