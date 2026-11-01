import { effectiveValue, rowFactor } from "./scenario";
import { includeRow, revenueKind } from "./tree";
import type { BudgetRow, GesetzFreiEintrag, GesetzFreiMap, NodeId, Preset, Scenario, SolverReport, YearData } from "./types";

type Factors = Record<NodeId, number>;

/** "HG:4" → alle Ausgabentitel der Hauptgruppe 4, "G:526" → alle Titel der Gruppe 526, sonst die ID selbst. */
export function expandTarget(ziel: string, data: YearData): NodeId[] {
  if (ziel.startsWith("HG:")) {
    const hg = ziel.slice(3);
    return data.rows.filter((r) => r.art === "A" && r.titel[0] === hg).map((r) => r.id);
  }
  if (ziel.startsWith("G:")) {
    const g = ziel.slice(2);
    return data.rows.filter((r) => r.titel.slice(0, 3) === g).map((r) => r.id);
  }
  if (ziel.startsWith("E:") || ziel.startsWith("ka:") || ziel.startsWith("ea:")) return [ziel];
  // Einzelplan oder Kapitel: auf Titel ausrollen, damit Preset-Regeln untereinander vergleichbar sind
  // (die zuletzt angewandte Regel gewinnt je Titel) und Nutzer-Regler auf höherer Ebene sie verdrängen können
  const parts = ziel.split("-");
  if (parts.length === 1) return data.rows.filter((r) => r.art === "A" && r.epl === ziel).map((r) => r.id);
  if (parts.length === 2) return data.rows.filter((r) => r.art === "A" && r.epl === parts[0] && r.kap === parts[1]).map((r) => r.id);
  return [ziel];
}

/** Gesetz/frei-Status eines Ausgabenknotens: Titel, dann Kapitel, dann Einzelplan; null = ungeprüft. */
export function gesetzStatus(id: NodeId, map: GesetzFreiMap): GesetzFreiEintrag | null {
  const parts = id.split("-");
  for (let n = parts.length; n >= 1; n--) {
    const e = map[parts.slice(0, n).join("-")];
    if (e) return e;
  }
  return null;
}

function userTouches(row: BudgetRow, userFactors: Factors): boolean {
  return rowFactor(row, userFactors) !== 1 || userFactors[row.id] !== undefined;
}

/**
 * Effektive Faktoren eines Szenarios: Preset-Regeln in Reihenfolge, dann Nutzer-Faktoren (schlagen Presets),
 * zuletzt die Nebenbedingung "schwarze_null" auf alle freien, nicht einzeln gesetzten Ausgabentitel.
 */
export function applyPresets(data: YearData, scenario: Scenario, presets: Preset[], gesetz: GesetzFreiMap
): { factors: Factors; solver: SolverReport | null } {
  const byId = new Map(presets.map((p) => [p.id, p]));
  const factors: Factors = {};
  let schwarzeNull = false;
  for (const pid of scenario.presets) {
    const p = byId.get(pid);
    if (!p) continue;
    for (const rule of p.regeln) {
      if ("bedingung" in rule) {
        if (rule.bedingung === "schwarze_null") schwarzeNull = true;
        continue;
      }
      for (const id of expandTarget(rule.ziel, data)) factors[id] = rule.faktor;
    }
  }
  // Nutzer-Regler schlagen Presets: auch alle Preset-Einträge unterhalb eines gesetzten Einzelplans/Kapitels
  for (const key of Object.keys(scenario.factors)) {
    const prefix = key + "-";
    for (const k of Object.keys(factors)) if (k.startsWith(prefix)) delete factors[k];
  }
  Object.assign(factors, scenario.factors);
  if (!schwarzeNull) return { factors, solver: null };

  // Nebenbedingung: Ausgaben = Einnahmen (ohne Kredite)
  let einnahmen = 0, feste = 0, freie = 0;
  const freieRows: BudgetRow[] = [];
  for (const row of data.rows) {
    if (!includeRow(row, scenario.includeSv)) continue;
    if (row.art === "E") {
      if (revenueKind(row) !== "kredite") einnahmen += effectiveValue(row, factors);
      continue;
    }
    const value = effectiveValue(row, factors);
    const gebunden = gesetzStatus(row.id, gesetz)?.status === "gesetz" || userTouches(row, scenario.factors);
    if (gebunden) feste += value;
    else { freie += value; freieRows.push(row); }
  }
  const luecke = einnahmen - feste;
  let k = freie > 0 ? luecke / freie : 1;
  const erreichbar = luecke >= 0;
  k = Math.min(1, Math.max(0, k));
  if (!erreichbar) k = 0;
  for (const row of freieRows) {
    const current = rowFactor(row, factors);
    if (current * k !== 1) factors[row.id] = current * k;
  }
  return { factors, solver: { gekuerzt: Math.round(freie * (1 - k)), faktor: k, erreichbar } };
}
