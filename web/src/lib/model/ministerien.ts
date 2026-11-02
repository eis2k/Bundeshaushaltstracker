/** Ministerien-Ansicht (Spec §4.10): je Einzelplan Name, Ausgaben des Jahres (wie im Fluss gezählt), Leitung laut Bundesregierung
 *  nur für das gewählte Jahr und Zahl der Empfänger mit Seite. Keine Zuordnung ohne Beleg: ohne Zeitraum nur im aktuellen Jahr, mit Hinweis. */

import type { EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import { includeRow } from "./tree";
import type { YearData } from "./types";

export interface Leitung { id: string; name: string; amt: string; seit: string | null; bis: string | null; partei?: string | null }

export interface Ministerium {
  epl: string;
  name: string;
  ausgaben: number;
  leitung: Leitung[];
  /** Erklärung, wenn keine oder nur unsicher datierte Leitung gezeigt wird. */
  leitungHinweis: string | null;
  empfaenger: number;
}

/** Ministerinnen und Minister (und Kanzler, Kanzleramtschef) vor Staatsministern und Parlamentarischen Staatssekretären. */
function rang(amt: string): number {
  const a = amt.toLowerCase();
  if (a.startsWith("bundeskanzler")) return 0;
  if (a.startsWith("bundesminister") || a.startsWith("chef")) return 1;
  if (a.startsWith("staatsminister")) return 2;
  if (a.startsWith("parlamentarische")) return 3;
  return 4;
}

function imJahr(l: Leitung, jahr: number): boolean {
  if (!l.seit) return false;
  const von = Number(l.seit.slice(0, 4));
  const bis = l.bis ? Number(l.bis.slice(0, 4)) : Infinity;
  return jahr >= von && jahr <= bis;
}

export function ministerien(data: YearData, stand: "soll" | "ist", includeSv: boolean, jahr: number, aktuellesJahr: number,
                            personen: PersonIndex | null, empfaenger: EmpfaengerIndex | null): Ministerium[] {
  const ausgaben = new Map<string, number>();
  for (const r of data.rows) {
    if (r.art !== "A" || !includeRow(r, includeSv)) continue;
    const wert = stand === "ist" ? (r.ist ?? r.soll) : r.soll;
    ausgaben.set(r.epl, (ausgaben.get(r.epl) ?? 0) + wert);
  }
  const zaehler = new Map<string, number>();
  for (const e of empfaenger?.eintraege ?? []) for (const epl of e.epls ?? []) zaehler.set(epl, (zaehler.get(epl) ?? 0) + 1);

  const alle = new Map<string, Leitung[]>();
  for (const p of personen?.eintraege ?? []) {
    if (!p.sichtbar || !p.arten?.includes("regierung")) continue;
    for (const l of p.epl_leitung ?? []) {
      if (!l.epl) continue;
      alle.set(l.epl, [...(alle.get(l.epl) ?? []), { id: p.id, name: p.name, amt: l.amt, seit: l.seit ?? null, bis: l.bis ?? null, partei: p.partei ?? null }]);
    }
  }
  const epls = new Set<string>([...Object.keys(data.epl), ...ausgaben.keys()]);
  return [...epls]
    .map((epl) => {
      const kandidaten = alle.get(epl) ?? [];
      let leitung = kandidaten.filter((l) => imJahr(l, jahr));
      let hinweis: string | null = null;
      // Im aktuellen Jahr zählen auch Personen ohne belegtes Datum (Stand des Kabinettsabrufs), zusätzlich zu datierten (Spec §4.12).
      if (jahr === aktuellesJahr) {
        const undatiert = kandidaten.filter((l) => !l.seit);
        if (undatiert.length) { leitung = [...leitung, ...undatiert]; hinweis = `Ernennungsdatum nicht belegt: ${undatiert.map((l) => l.name).join(", ")}; Stand des Kabinettsabrufs`; }
      }
      if (!leitung.length) hinweis = `Leitung für ${jahr} nicht erfasst`;
      leitung.sort((a, b) => rang(a.amt) - rang(b.amt) || (b.seit ?? "").localeCompare(a.seit ?? "") || a.name.localeCompare(b.name, "de"));
      return { epl, name: data.epl[epl] ?? `Einzelplan ${epl}`, ausgaben: ausgaben.get(epl) ?? 0, leitung, leitungHinweis: hinweis, empfaenger: zaehler.get(epl) ?? 0 };
    })
    .sort((a, b) => b.ausgaben - a.ausgaben || a.epl.localeCompare(b.epl));
}

/** Leitung an der Spitze (Kanzler, Minister, Kanzleramtschef): nach der Sortierung die zuletzt amtierende; sonst die erste Person. */
export function chef(leitung: Leitung[]): Leitung | null {
  return leitung.find((l) => rang(l.amt) <= 1) ?? leitung[0] ?? null;
}

/** Weitere Personen an der Spitze im selben Jahr (Wechseljahr), meist mit `bis`. */
export function vorgaenger(leitung: Leitung[], chef: Leitung | null): Leitung[] {
  return leitung.filter((l) => rang(l.amt) <= 1 && l !== chef);
}

/** Tabellenansicht (Spec §4.12): Änderung zum Vorjahr nominal, Soll gegen Soll, ohne Regler; null ohne Vorjahr oder ohne positiven Vorjahreswert. */
export function ministerienTabelle(liste: Ministerium[], vorjahr: YearData | null, includeSv: boolean): (Ministerium & { veraenderung: number | null })[] {
  const vj = new Map<string, number>();
  if (vorjahr) for (const r of vorjahr.rows) if (r.art === "A" && includeRow(r, includeSv)) vj.set(r.epl, (vj.get(r.epl) ?? 0) + r.soll);
  return liste.map((m) => {
    const v = vj.get(m.epl);
    return { ...m, veraenderung: v && v > 0 ? Math.round(((m.ausgaben - v) / v) * 1000) / 10 : null };
  });
}
