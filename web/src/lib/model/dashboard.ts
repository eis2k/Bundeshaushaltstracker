/** Dashboard (Spec §4.11): Kennzahlen, Herkunft und Verwendung, Entwicklung als Index. Alles aus den Jahresdaten, nichts addiert über Quellen. */

import type { EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import { balance, effectiveValue, type Factors } from "./scenario";
import { includeRow, revenueGroups } from "./tree";
import type { YearData } from "./types";
import type { Series, Zeitreihe } from "./zeitreihe";

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
export function kennzahlen(data: YearData, vorjahr: YearData | null, includeSv: boolean, factors: Factors, empfaenger: EmpfaengerIndex | null, personen: PersonIndex | null, roh: YearData = data, extraBund = 0): Kennzahlen {
  const b = balance(data, factors, includeSv, extraBund);
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
export function herkunftVerwendung(data: YearData, includeSv: boolean, factors: Factors, extraBund = 0): { herkunft: Posten[]; verwendung: Posten[] } {
  const gruppen = revenueGroups(data, includeSv);
  // Kredite aus der Bilanz des Szenarios (wie Seitenkopf und Fluss), nicht aus den Kreditzeilen des Plans
  const kredite = balance(data, factors, includeSv, extraBund).neueSchulden;
  const herkunftRoh = gruppen.map((g) => ({ id: g.id, label: g.label, wert: g.isKredit ? kredite : g.rows.reduce((s, r) => s + effectiveValue(r, factors), 0) })).filter((x) => x.wert !== 0);
  if (extraBund > 0) herkunftRoh.push({ id: "modell", label: "Steuer-Modelle (Annahme)", wert: extraBund });
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

/** Summe der Reihen je Jahr; bei Ist nur Ist (eine Reihe mit Soll, aber ohne Ist → Jahr null, kein Mischen). */
function summenJeJahr(reihen: Series[], jahre: number, stand: "soll" | "ist"): (number | null)[] {
  return jahre === 0 ? [] : Array.from({ length: jahre }, (_, i) => {
    let s = 0;
    let hat = false;
    for (const serie of reihen) {
      const w = stand === "ist" ? serie.ist[i] : serie.soll[i];
      if (w == null) { if (serie.soll[i] != null) return null; continue; }
      s += w; hat = true;
    }
    return hat ? s : null;
  });
}

function alsIndex(summen: (number | null)[]): (number | null)[] {
  const basis = summen.find((s) => s != null && s > 0) ?? null;
  return summen.map((s) => (basis && s != null ? Math.round((s / basis) * 1000) / 10 : null));
}

/** Hauptgruppen 7 (Baumaßnahmen) und 8 (sonstige Investitionen) nach Gruppierungsplan: erste Ziffer der Titelnummer. */
export function istInvestition(titelId: string): boolean {
  const nr = titelId.split("-")[2] ?? "";
  return nr.startsWith("7") || nr.startsWith("8");
}

/** Gesamtausgaben und Investitionen (Hauptgruppen 7/8 aus den Titelreihen) je Jahr als Index (erstes Jahr mit Wert = 100), ohne Sondervermögen. */
export function entwicklungIndex(z: Zeitreihe, stand: "soll" | "ist"): { jahr: number; gesamt: number | null; investitionen: number | null }[] {
  const ausgaben = Object.values(z.epl).filter((s) => s.art === "A" && !s.sv);
  const investitionen = Object.entries(z.titel ?? {}).filter(([id, s]) => s.art === "A" && !s.sv && istInvestition(id)).map(([, s]) => s);
  const g = alsIndex(summenJeJahr(ausgaben, z.jahre.length, stand));
  const inv = alsIndex(summenJeJahr(investitionen, z.jahre.length, stand));
  return z.jahre.map((jahr, i) => ({ jahr, gesamt: g[i] ?? null, investitionen: inv[i] ?? null }));
}
