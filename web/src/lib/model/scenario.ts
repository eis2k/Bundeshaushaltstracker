import { empfaengerArt, kostenart } from "./schnitte";
import { includeRow, revenueGroupId, revenueKind } from "./tree";
import type { Balance, BudgetRow, NodeId, Scenario, YearData } from "./types";

type Factors = Record<NodeId, number>;

/** Faktor für eine Ausgaben-Knoten-ID: Titel schlägt Kapitel schlägt Einzelplan, sonst 1. */
export function effectiveFactor(id: NodeId, factors: Factors): number {
  const parts = id.split("-");
  for (let n = parts.length; n >= 1; n--) {
    const key = parts.slice(0, n).join("-");
    const f = factors[key];
    if (f !== undefined) return f;
  }
  return 1;
}

/** Faktor für eine konkrete Zeile; Einnahmen lösen Titel → Steuergruppe → alle Steuern/Sonstige auf. */
export function rowFactor(row: BudgetRow, factors: Factors): number {
  if (row.art === "A") {
    const own = effectiveFactor(row.id, factors);
    if (own !== 1) return own;
    // Regler aus dem Kostenarten- oder Empfänger-Art-Schnitt, unterhalb von Titel/Kapitel/Einzelplan
    const ka = factors[`ka:${kostenart(row.titel)}`];
    if (ka !== undefined) return ka;
    const ea = factors[`ea:${empfaengerArt(row.titel)}`];
    if (ea !== undefined) return ea;
    return 1;
  }
  if (factors[row.id] !== undefined) return factors[row.id];
  const groupId = revenueGroupId(row);
  if (factors[groupId] !== undefined) return factors[groupId];
  const kindId = `E:${revenueKind(row)}`;
  if (factors[kindId] !== undefined) return factors[kindId];
  return 1;
}

export function effectiveValue(row: BudgetRow, factors: Factors): number {
  return Math.round(row.soll * rowFactor(row, factors));
}

export function balance(data: YearData, factors: Factors, includeSv: boolean): Balance {
  let ausgaben = 0, einnahmen = 0, ausgabenOriginal = 0, einnahmenOriginal = 0;
  for (const row of data.rows) {
    if (!includeRow(row, includeSv)) continue;
    if (row.art === "A") {
      ausgabenOriginal += row.soll;
      ausgaben += effectiveValue(row, factors);
    } else if (revenueKind(row) !== "kredite") {
      einnahmenOriginal += row.soll;
      einnahmen += effectiveValue(row, factors);
    }
  }
  const neueSchulden = ausgaben - einnahmen;
  const neueSchuldenOriginal = ausgabenOriginal - einnahmenOriginal;
  return {
    ausgaben, einnahmen, neueSchulden,
    ausgabenOriginal, einnahmenOriginal, neueSchuldenOriginal,
    delta: neueSchuldenOriginal - neueSchulden,
  };
}

export function setFactor(scenario: Scenario, id: NodeId, factor: number): Scenario {
  const factors = { ...scenario.factors };
  if (factor === 1 || !Number.isFinite(factor)) delete factors[id];
  else factors[id] = factor;
  return { ...scenario, factors };
}

/** Explizit gesetzte Nachkommen eines Ausgaben-Knotens (für Hinweise im Panel). */
export function childFactorsOverridden(id: NodeId, factors: Factors): NodeId[] {
  return Object.keys(factors).filter((k) => k !== id && k.startsWith(id + "-"));
}
