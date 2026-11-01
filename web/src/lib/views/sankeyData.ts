import { balance, effectiveValue, rowFactor } from "../model/scenario";
import { revenueGroups, revenueKind } from "../model/tree";
import type { BudgetRow, NodeId, Scenario, YearData } from "../model/types";

export type SNodeKind = "revenue" | "kredit" | "minderausgabe" | "topf" | "epl" | "kap" | "titel" | "rest" | "empfaenger" | "abzug";

export interface SNode {
  id: string;
  label: string;
  column: number;
  kind: SNodeKind;
  /** Bandbreite: Summe der positiven Titel. */
  original: number;
  effective: number;
  /** Beschriftung: Nettosumme inkl. negativer Titel (Minderausgaben). */
  netOriginal: number;
  netEffective: number;
  changed: boolean;
  dim: boolean;
  isKredit?: boolean;
  /** Farbe der Quelle (Einzelplan) für Bänder und Knoten. */
  colorKey: string;
}

export interface SLink {
  source: string;
  target: string;
  value: number;
  colorKey: string;
  dim: boolean;
}

export interface SGhost {
  id: string;
  /** original − effective; > 0 gestrichen, < 0 hinzugefügt. */
  diff: number;
}

export interface SankeyData {
  nodes: SNode[];
  links: SLink[];
  ghosts: SGhost[];
  /** Summe der negativen Ausgabentitel (Globale Minderausgaben) nach Faktor, ≤ 0. */
  minderausgaben: number;
}

export const TOPF_BUND = "topf:bund";
export const ABZUEGE = "abzuege";
export const EMPFAENGER_UNBEKANNT = "empfaenger:unbekannt";

interface Agg { id: string; label: string; rows: BudgetRow[]; original: number; effective: number; netOriginal: number; netEffective: number; changed: boolean; colorKey: string }

function aggregate(id: string, label: string, rows: BudgetRow[], factors: Record<NodeId, number>, colorKey: string): Agg {
  let original = 0, effective = 0, netOriginal = 0, netEffective = 0, changed = false;
  for (const r of rows) {
    const v = effectiveValue(r, factors);
    if (rowFactor(r, factors) !== 1) changed = true;
    if (r.soll > 0) original += r.soll;
    if (v > 0) effective += v;
    netOriginal += r.soll;
    netEffective += v;
  }
  return { id, label, rows, original, effective, netOriginal, netEffective, changed, colorKey };
}

/** Wählt den Fokusknoten plus die größten übrigen; der Rest wird zu "Alle anderen" zusammengefasst. */
function pick(aggs: Agg[], focusId: string | undefined, max: number, restId: string): { shown: Agg[]; rest: Agg | null } {
  const sorted = [...aggs].sort((a, b) => b.effective - a.effective);
  const shown: Agg[] = [];
  const focus = sorted.find((a) => a.id === focusId);
  if (focus) shown.push(focus);
  for (const a of sorted) {
    if (shown.length >= max) break;
    if (a !== focus && a.effective > 0) shown.push(a);
  }
  const restAggs = sorted.filter((a) => !shown.includes(a) && a.effective > 0);
  if (!restAggs.length) return { shown, rest: null };
  const rest: Agg = {
    id: restId, label: "Alle anderen", rows: restAggs.flatMap((a) => a.rows),
    original: restAggs.reduce((s, a) => s + a.original, 0),
    effective: restAggs.reduce((s, a) => s + a.effective, 0),
    netOriginal: restAggs.reduce((s, a) => s + a.netOriginal, 0),
    netEffective: restAggs.reduce((s, a) => s + a.netEffective, 0),
    changed: restAggs.some((a) => a.changed), colorKey: "rest",
  };
  return { shown, rest };
}

export function buildSankey(data: YearData, scenario: Scenario, factors: Record<NodeId, number>, focus: NodeId[],
                            opts: { maxPerColumn: number; maxRevenue?: number }): SankeyData {
  const nodes: SNode[] = [];
  const links: SLink[] = [];
  const ghosts: SGhost[] = [];
  const rows = data.rows.filter((r) => scenario.includeSv || !r.sv);
  const ausgaben = rows.filter((r) => r.art === "A");
  const b = balance(data, factors, scenario.includeSv);

  let minderausgaben = 0;
  for (const r of ausgaben) {
    const v = effectiveValue(r, factors);
    if (v < 0) minderausgaben += v;
  }
  // Negative Einnahmetitel (EU-Eigenmittel, Zuweisungen an Länder aus dem Steueraufkommen) sind
  // Abflüsse: sie verlassen den Topf als "Weiterleitung", damit Zu- und Abflüsse am Topf aufgehen.
  let abzuege = 0, abzuegeOriginal = 0;
  for (const r of rows) {
    if (r.art !== "E" || revenueKind(r) === "kredite") continue;
    const v = effectiveValue(r, factors);
    if (v < 0) abzuege -= v;
    if (r.soll < 0) abzuegeOriginal -= r.soll;
  }

  const add = (n: Omit<SNode, "dim" | "netOriginal" | "netEffective"> & { dim?: boolean; netOriginal?: number; netEffective?: number }) => {
    nodes.push({ dim: false, netOriginal: n.original, netEffective: n.effective, ...n });
    return n.id;
  };
  const link = (source: string, target: string, value: number, colorKey: string, dim = false) => {
    if (value > 0) links.push({ source, target, value, colorKey, dim });
  };
  const ghost = (a: Agg) => { if (a.changed && a.original !== a.effective) ghosts.push({ id: a.id, diff: a.original - a.effective }); };

  // Spalte 0: Einnahmen. Kleine Steuerarten werden zu "Übrige Steuern" zusammengefasst,
  // damit höchstens maxRevenue Steuer-Knoten erscheinen.
  const maxRevenue = opts.maxRevenue ?? opts.maxPerColumn;
  const groups = revenueGroups(data, scenario.includeSv).filter((g) => !g.isKredit);
  const taxGroups = groups.filter((g) => revenueKind(g.rows[0]) === "steuern" && g.id !== "E:steuern:rest");
  const restGroup = groups.find((g) => g.id === "E:steuern:rest");
  const sortedTaxes = [...taxGroups].sort((x, y) => y.soll - x.soll);
  const shownTaxes = sortedTaxes.slice(0, Math.max(1, maxRevenue - 1));
  const foldedTaxes = sortedTaxes.slice(shownTaxes.length);
  const restRows = [...(restGroup?.rows ?? []), ...foldedTaxes.flatMap((g) => g.rows)];
  const revenueList: { id: string; label: string; rows: BudgetRow[]; colorKey: string }[] = [
    ...shownTaxes.map((g) => ({ id: g.id, label: g.label, rows: g.rows, colorKey: "steuern" })),
    ...(restRows.length ? [{ id: "E:steuern:rest", label: "Übrige Steuern", rows: restRows, colorKey: "steuern" }] : []),
    ...groups.filter((g) => revenueKind(g.rows[0]) !== "steuern").map((g) => ({ id: g.id, label: g.label, rows: g.rows, colorKey: "sonstige" })),
  ];
  for (const g of revenueList) {
    const a = aggregate(g.id, g.label, g.rows, factors, g.colorKey);
    add({ id: a.id, label: a.label, column: 0, kind: "revenue", original: a.original, effective: a.effective, changed: a.changed, colorKey: g.colorKey });
    link(a.id, TOPF_BUND, a.effective, g.colorKey);
  }
  add({ id: "E:kredite", label: "Neue Schulden", column: 0, kind: "kredit", original: b.neueSchuldenOriginal, effective: b.neueSchulden, changed: b.neueSchulden !== b.neueSchuldenOriginal, isKredit: true, colorKey: "kredit" });
  link("E:kredite", TOPF_BUND, b.neueSchulden, "kredit");
  if (minderausgaben !== 0) {
    add({ id: "minderausgabe", label: "Globale Minderausgaben", column: 0, kind: "minderausgabe", original: -minderausgaben, effective: -minderausgaben, changed: false, colorKey: "minder" });
    link("minderausgabe", TOPF_BUND, -minderausgaben, "minder");
  }

  // Spalte 1: Topf
  add({ id: TOPF_BUND, label: "Bundeshaushalt", column: 1, kind: "topf", original: b.ausgabenOriginal, effective: b.ausgaben, changed: b.ausgaben !== b.ausgabenOriginal, colorKey: "topf" });

  // Spalte 2: Weiterleitungen (negative Einnahmetitel) und Einzelpläne
  if (abzuege > 0) {
    add({ id: ABZUEGE, label: "Weiterleitung an EU und Länder", column: 2, kind: "abzug", original: abzuegeOriginal, effective: abzuege, changed: abzuege !== abzuegeOriginal, dim: focus.length > 0, colorKey: "abzug" });
    link(TOPF_BUND, ABZUEGE, abzuege, "abzug", focus.length > 0);
  }
  const byEpl = new Map<string, BudgetRow[]>();
  for (const r of ausgaben) (byEpl.get(r.epl) ?? byEpl.set(r.epl, []).get(r.epl)!).push(r);
  const eplAggs = [...byEpl.entries()].map(([epl, rs]) => aggregate(epl, data.epl[epl] ?? `Einzelplan ${epl}`, rs, factors, epl));
  const focusEpl = focus[0];
  const c2 = pick(eplAggs, focusEpl, opts.maxPerColumn, "rest:2");
  for (const a of [...c2.shown, ...(c2.rest ? [c2.rest] : [])]) {
    const dim = focusEpl !== undefined && a.id !== focusEpl;
    add({ id: a.id, label: a.label, column: 2, kind: a.id === "rest:2" ? "rest" : "epl", original: a.original, effective: a.effective, netOriginal: a.netOriginal, netEffective: a.netEffective, changed: a.changed, dim, colorKey: a.colorKey });
    link(TOPF_BUND, a.id, a.effective, a.colorKey, dim);
    if (a.id !== "rest:2") ghost(a);
  }

  // Spalte 3: Kapitel des Fokus-Einzelplans
  const focusKap = focus[1];
  if (focusEpl && byEpl.has(focusEpl)) {
    const byKap = new Map<string, BudgetRow[]>();
    for (const r of byEpl.get(focusEpl)!) {
      const id = `${r.epl}-${r.kap}`;
      (byKap.get(id) ?? byKap.set(id, []).get(id)!).push(r);
    }
    const kapAggs = [...byKap.entries()].map(([id, rs]) => aggregate(id, data.kap[rs[0].kap] ?? `Kapitel ${rs[0].kap}`, rs, factors, focusEpl));
    const c3 = pick(kapAggs, focusKap, opts.maxPerColumn, "rest:3");
    for (const a of [...c3.shown, ...(c3.rest ? [c3.rest] : [])]) {
      const dim = focusKap !== undefined && a.id !== focusKap;
      add({ id: a.id, label: a.label, column: 3, kind: a.id === "rest:3" ? "rest" : "kap", original: a.original, effective: a.effective, netOriginal: a.netOriginal, netEffective: a.netEffective, changed: a.changed, dim, colorKey: focusEpl });
      link(focusEpl, a.id, a.effective, focusEpl, dim);
      if (a.id !== "rest:3") ghost(a);
    }

    // Spalte 4: Titel des Fokus-Kapitels, Spalte 5: Empfänger
    if (focusKap && byKap.has(focusKap)) {
      const focusTitel = focus[2];
      const titelAggs = byKap.get(focusKap)!.map((r) => aggregate(r.id, r.text, [r], factors, focusEpl));
      const c4 = pick(titelAggs, focusTitel, opts.maxPerColumn, "rest:4");
      let sum = 0;
      for (const a of [...c4.shown, ...(c4.rest ? [c4.rest] : [])]) {
        const dim = focusTitel !== undefined && a.id !== focusTitel;
        add({ id: a.id, label: a.label, column: 4, kind: a.id === "rest:4" ? "rest" : "titel", original: a.original, effective: a.effective, netOriginal: a.netOriginal, netEffective: a.netEffective, changed: a.changed, dim, colorKey: focusEpl });
        link(focusKap, a.id, a.effective, focusEpl, dim);
        link(a.id, EMPFAENGER_UNBEKANNT, a.effective, focusEpl, dim);
        sum += a.effective;
        if (a.id !== "rest:4") ghost(a);
      }
      add({ id: EMPFAENGER_UNBEKANNT, label: "Empfänger nicht veröffentlicht", column: 5, kind: "empfaenger", original: sum, effective: sum, changed: false, colorKey: "rest" });
    }
  }

  return { nodes, links, ghosts, minderausgaben };
}
