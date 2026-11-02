/** Reiter „Nach Bereichen“ (Spec §4.12): Ausgaben je Einzelplan mit denselben Werten wie der Fluss (includeRow, Faktoren), die größten einzeln, der Rest gebündelt. */

import { effectiveValue, type Factors } from "./scenario";
import { includeRow } from "./tree";
import type { YearData } from "./types";

export interface Bereich { epl: string | null; label: string; wert: number; anteil: number }

export function ausgabenNachEinzelplan(data: YearData, includeSv: boolean, factors: Factors, max = 8): Bereich[] {
  const je = new Map<string, number>();
  for (const r of data.rows) {
    if (r.art !== "A" || !includeRow(r, includeSv)) continue;
    je.set(r.epl, (je.get(r.epl) ?? 0) + effectiveValue(r, factors));
  }
  const sortiert = [...je.entries()].filter(([, w]) => w > 0).sort((a, b) => b[1] - a[1]);
  const gesamt = sortiert.reduce((s, [, w]) => s + w, 0) || 1;
  const anteil = (w: number) => Math.round((w / gesamt) * 1000) / 10;
  const top = sortiert.slice(0, max).map(([epl, wert]) => ({ epl, label: data.epl[epl] ?? `Einzelplan ${epl}`, wert, anteil: anteil(wert) }));
  const rest = sortiert.slice(max).reduce((s, [, w]) => s + w, 0);
  return rest > 0 ? [...top, { epl: null, label: "Weitere Einzelpläne", wert: rest, anteil: anteil(rest) }] : top;
}
