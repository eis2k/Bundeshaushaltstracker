/** Ministerien-Ansicht (Spec §4.10): je Einzelplan Name, Ausgaben des Jahres, Leitung laut Bundesregierung und Zahl der Empfänger mit Seite. */

import type { EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import type { YearData } from "./types";

export interface Ministerium {
  epl: string;
  name: string;
  ausgaben: number;
  leitung: { id: string; name: string; funktion: string }[];
  empfaenger: number;
}

export function ministerien(data: YearData, stand: "soll" | "ist", personen: PersonIndex | null, empfaenger: EmpfaengerIndex | null): Ministerium[] {
  const ausgaben = new Map<string, number>();
  for (const r of data.rows) {
    if (r.art !== "A") continue;
    const wert = stand === "ist" ? (r.ist ?? r.soll) : r.soll;
    ausgaben.set(r.epl, (ausgaben.get(r.epl) ?? 0) + wert);
  }
  const zaehler = new Map<string, number>();
  for (const e of empfaenger?.eintraege ?? []) for (const epl of e.epls ?? []) zaehler.set(epl, (zaehler.get(epl) ?? 0) + 1);
  const leitung = new Map<string, { id: string; name: string; funktion: string }[]>();
  for (const p of personen?.eintraege ?? []) {
    if (!p.sichtbar || !p.arten?.includes("regierung")) continue;
    for (const epl of p.epl_leitung ?? []) leitung.set(epl, [...(leitung.get(epl) ?? []), { id: p.id, name: p.name, funktion: p.funktion_kurz }]);
  }
  const epls = new Set<string>([...Object.keys(data.epl), ...ausgaben.keys()]);
  return [...epls]
    .map((epl) => ({ epl, name: data.epl[epl] ?? `Einzelplan ${epl}`, ausgaben: ausgaben.get(epl) ?? 0, leitung: leitung.get(epl) ?? [], empfaenger: zaehler.get(epl) ?? 0 }))
    .sort((a, b) => b.ausgaben - a.ausgaben || a.epl.localeCompare(b.epl));
}
