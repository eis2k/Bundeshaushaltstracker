/** Globale Suche (Spec §4.11): Einzelpläne, Empfänger mit Seite und sichtbare Akten; nicht freigeschaltete Akten erscheinen nicht. */

import { suchNorm, type EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import type { YearData } from "./types";

export interface Treffer { art: "ministerium" | "empfaenger" | "person"; id: string; label: string; neben: string }

export function suche(q: string, data: YearData | null, empfaenger: EmpfaengerIndex | null, personen: PersonIndex | null, max = 8): Treffer[] {
  const nq = suchNorm(q.trim());
  if (!nq) return [];
  const out: Treffer[] = [];
  for (const [epl, name] of Object.entries(data?.epl ?? {})) {
    if (epl === nq || epl.startsWith(nq) || suchNorm(name).includes(nq)) out.push({ art: "ministerium", id: epl, label: name, neben: `Einzelplan ${epl}` });
  }
  for (const e of empfaenger?.eintraege ?? []) {
    if (suchNorm(e.name).includes(nq)) out.push({ art: "empfaenger", id: e.id, label: e.name, neben: e.rechtsform || "Empfänger" });
  }
  for (const p of personen?.eintraege ?? []) {
    if (p.sichtbar && suchNorm(p.name).includes(nq)) out.push({ art: "person", id: p.id, label: p.name, neben: p.funktion_kurz });
  }
  return out.slice(0, max);
}
