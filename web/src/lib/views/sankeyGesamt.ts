import { balance, effectiveValue, rowFactor } from "../model/scenario";
import { revenueGroups, revenueKind } from "../model/tree";
import type { SozialkassenYear } from "../model/toepfe";
import type { BudgetRow, NodeId, Scenario, YearData } from "../model/types";
import { ABZUEGE, TOPF_BUND, type SGhost, type SLink, type SNode, type SankeyData } from "./sankeyData";

interface Agg { id: string; label: string; original: number; effective: number; netOriginal: number; netEffective: number; changed: boolean }

function aggregate(id: string, label: string, rows: BudgetRow[], factors: Record<NodeId, number>): Agg {
  let original = 0, effective = 0, netOriginal = 0, netEffective = 0, changed = false;
  for (const r of rows) {
    const v = effectiveValue(r, factors);
    if (rowFactor(r, factors) !== 1) changed = true;
    if (r.soll > 0) original += r.soll;
    if (v > 0) effective += v;
    netOriginal += r.soll;
    netEffective += v;
  }
  return { id, label, original, effective, netOriginal, netEffective, changed };
}

/**
 * Gesamtfluss: Steuern und Beiträge → Töpfe (Bund, Rentenkasse, Krankenkassen, Pflege, Arbeitslosenversicherung) → Verwendung.
 * Bundesmittel an die Kassen erscheinen beim Bund als Verwendung ("Zuschüsse an Sozialkassen") und bei der Kasse als
 * Zufluss ("Bundesmittel"); die Gesamtsumme in der Kopfzeile zählt sie einmal. `only` zeigt nur eine Kasse.
 */
export function buildGesamtSankey(bund: YearData, sk: SozialkassenYear, scenario: Scenario, factors: Record<NodeId, number>,
                                  opts: { maxPerColumn: number; maxRevenue?: number; only?: string }): SankeyData {
  const nodes: SNode[] = [];
  const links: SLink[] = [];
  const ghosts: SGhost[] = [];
  const add = (n: Omit<SNode, "dim" | "netOriginal" | "netEffective"> & { dim?: boolean; netOriginal?: number; netEffective?: number }) => {
    nodes.push({ dim: false, netOriginal: n.original, netEffective: n.effective, ...n });
  };
  const link = (source: string, target: string, value: number, colorKey: string) => {
    if (value > 0) links.push({ source, target, value, colorKey, dim: false });
  };
  const rowById = new Map(bund.rows.map((r) => [r.id, r]));
  const rows = bund.rows.filter((r) => scenario.includeSv || !r.sv);
  const showBund = !opts.only;

  // Bundesmittel je Topf (effektiv) und die verknüpften Bund-Titel (werden aus den Einzelplan-Bändern herausgenommen)
  const linkedIds = new Set<string>();
  const bmByTopf = new Map<string, { original: number; effective: number }>();
  for (const [tid, t] of Object.entries(sk.toepfe)) {
    let original = 0, effective = 0;
    for (const b of t.bundesmittel) {
      const row = rowById.get(b.titel);
      if (!row || (row.sv && !scenario.includeSv)) continue;
      linkedIds.add(row.id);
      original += row.soll;
      effective += effectiveValue(row, factors);
    }
    bmByTopf.set(tid, { original, effective });
  }

  let minderausgaben = 0;
  if (showBund) {
    const b = balance(bund, factors, scenario.includeSv);
    const ausgaben = rows.filter((r) => r.art === "A");
    for (const r of ausgaben) { const v = effectiveValue(r, factors); if (v < 0) minderausgaben += v; }
    let abzuege = 0, abzuegeOriginal = 0;
    for (const r of rows) {
      if (r.art !== "E" || revenueKind(r) === "kredite") continue;
      const v = effectiveValue(r, factors);
      if (v < 0) abzuege -= v;
      if (r.soll < 0) abzuegeOriginal -= r.soll;
    }

    // Spalte 0: Steuern (gefaltet), Kredite, Minderausgaben
    const maxRevenue = opts.maxRevenue ?? opts.maxPerColumn;
    const groups = revenueGroups(bund, scenario.includeSv).filter((g) => !g.isKredit);
    const taxes = groups.filter((g) => revenueKind(g.rows[0]) === "steuern" && g.id !== "E:steuern:rest").sort((x, y) => y.soll - x.soll);
    const shownTaxes = taxes.slice(0, Math.max(1, maxRevenue - 1));
    const restRows = [...(groups.find((g) => g.id === "E:steuern:rest")?.rows ?? []), ...taxes.slice(shownTaxes.length).flatMap((g) => g.rows)];
    const revenueList = [
      ...shownTaxes.map((g) => ({ id: g.id, label: g.label, rows: g.rows, colorKey: "steuern" })),
      ...(restRows.length ? [{ id: "E:steuern:rest", label: "Übrige Steuern", rows: restRows, colorKey: "steuern" }] : []),
      ...groups.filter((g) => revenueKind(g.rows[0]) !== "steuern").map((g) => ({ id: g.id, label: g.label, rows: g.rows, colorKey: "sonstige" })),
    ];
    for (const g of revenueList) {
      const a = aggregate(g.id, g.label, g.rows, factors);
      add({ id: a.id, label: a.label, column: 0, kind: "revenue", original: a.original, effective: a.effective, changed: a.changed, colorKey: g.colorKey });
      link(a.id, TOPF_BUND, a.effective, g.colorKey);
    }
    add({ id: "E:kredite", label: "Neue Schulden (Bund)", column: 0, kind: "kredit", original: b.neueSchuldenOriginal, effective: b.neueSchulden, changed: b.neueSchulden !== b.neueSchuldenOriginal, isKredit: true, colorKey: "kredit" });
    link("E:kredite", TOPF_BUND, b.neueSchulden, "kredit");
    if (minderausgaben !== 0) {
      add({ id: "minderausgabe", label: "Globale Minderausgaben", column: 0, kind: "minderausgabe", original: -minderausgaben, effective: -minderausgaben, changed: false, colorKey: "minder" });
      link("minderausgabe", TOPF_BUND, -minderausgaben, "minder");
    }

    // Spalte 1: Bund
    add({ id: TOPF_BUND, label: "Bundeshaushalt", column: 1, kind: "topf", original: b.ausgabenOriginal, effective: b.ausgaben, changed: b.ausgaben !== b.ausgabenOriginal, colorKey: "topf" });

    // Spalte 2: Zuschüsse an Sozialkassen, Weiterleitung, Einzelpläne ohne die verknüpften Titel
    let zuOriginal = 0, zuEffective = 0;
    for (const v of bmByTopf.values()) { zuOriginal += v.original; zuEffective += v.effective; }
    if (zuEffective > 0 || zuOriginal > 0) {
      add({ id: "zuschuesse:bund", label: "Zuschüsse an Sozialkassen", column: 2, kind: "epl", original: zuOriginal, effective: zuEffective, changed: zuEffective !== zuOriginal, colorKey: "steuern" });
      link(TOPF_BUND, "zuschuesse:bund", zuEffective, "steuern");
      if (zuEffective !== zuOriginal) ghosts.push({ id: "zuschuesse:bund", diff: zuOriginal - zuEffective });
    }
    if (abzuege > 0) {
      add({ id: ABZUEGE, label: "Weiterleitung an EU und Länder", column: 2, kind: "abzug", original: abzuegeOriginal, effective: abzuege, changed: abzuege !== abzuegeOriginal, colorKey: "abzug" });
      link(TOPF_BUND, ABZUEGE, abzuege, "abzug");
    }
    const byEpl = new Map<string, BudgetRow[]>();
    for (const r of ausgaben) {
      if (linkedIds.has(r.id)) continue;
      (byEpl.get(r.epl) ?? byEpl.set(r.epl, []).get(r.epl)!).push(r);
    }
    const eplAggs = [...byEpl.entries()].map(([epl, rs]) => ({ ...aggregate(epl, bund.epl[epl] ?? `Einzelplan ${epl}`, rs, factors), colorKey: epl }))
      .sort((x, y) => y.effective - x.effective);
    const shown = eplAggs.slice(0, Math.max(1, opts.maxPerColumn - 1));
    const rest = eplAggs.slice(shown.length);
    for (const a of shown) {
      if (a.effective <= 0) continue;
      add({ id: a.id, label: a.label, column: 2, kind: "epl", original: a.original, effective: a.effective, netOriginal: a.netOriginal, netEffective: a.netEffective, changed: a.changed, colorKey: a.colorKey });
      link(TOPF_BUND, a.id, a.effective, a.colorKey);
      if (a.changed && a.original !== a.effective) ghosts.push({ id: a.id, diff: a.original - a.effective });
    }
    const restEff = rest.reduce((s, a) => s + a.effective, 0);
    if (restEff > 0) {
      add({ id: "rest:2", label: "Alle anderen Ministerien", column: 2, kind: "rest", original: rest.reduce((s, a) => s + a.original, 0), effective: restEff, changed: rest.some((a) => a.changed), colorKey: "rest" });
      link(TOPF_BUND, "rest:2", restEff, "rest");
    }
  }

  // Sozialkassen
  for (const [tid, t] of Object.entries(sk.toepfe)) {
    if (opts.only && opts.only !== tid) continue;
    const bm = bmByTopf.get(tid) ?? { original: 0, effective: 0 };
    const tableBund = t.einnahmen.filter((e) => e.id === "bund").reduce((s, e) => s + e.betrag, 0);
    const beitraege = t.einnahmen.filter((e) => e.id === "beitraege").reduce((s, e) => s + e.betrag, 0);
    const sonstige = t.einnahmen.filter((e) => e.id !== "beitraege" && e.id !== "bund").reduce((s, e) => s + e.betrag, 0);
    const bundesmittelOriginal = t.bundesmittel.length ? bm.original : tableBund;
    const bundesmittel = t.bundesmittel.length ? bm.effective : tableBund;
    const ausgaben = t.ausgaben.reduce((s, e) => s + e.betrag, 0);
    const einnahmen = beitraege + sonstige + bundesmittel;
    const topfId = `topf:${tid}`;

    if (beitraege > 0) {
      add({ id: `beitraege:${tid}`, label: `Beiträge ${t.kurz}`, column: 0, kind: "beitraege", original: beitraege, effective: beitraege, changed: false, colorKey: "beitraege" });
      link(`beitraege:${tid}`, topfId, beitraege, "beitraege");
    }
    if (bundesmittel > 0 || bundesmittelOriginal > 0) {
      add({ id: `bundesmittel:${tid}`, label: `Bundesmittel ${t.kurz}`, column: 0, kind: "revenue", original: bundesmittelOriginal, effective: bundesmittel, changed: bundesmittel !== bundesmittelOriginal, colorKey: "steuern" });
      link(`bundesmittel:${tid}`, topfId, bundesmittel, "steuern");
      if (bundesmittel !== bundesmittelOriginal) ghosts.push({ id: `bundesmittel:${tid}`, diff: bundesmittelOriginal - bundesmittel });
    }
    if (sonstige > 0) {
      add({ id: `sonstige:${tid}`, label: `Sonstige Einnahmen ${t.kurz}`, column: 0, kind: "revenue", original: sonstige, effective: sonstige, changed: false, colorKey: "sonstige" });
      link(`sonstige:${tid}`, topfId, sonstige, "sonstige");
    }
    const saldo = einnahmen - ausgaben;
    if (saldo < 0) {
      add({ id: `defizit:${tid}`, label: `Defizit ${t.kurz}`, column: 0, kind: "kredit", original: Math.max(0, ausgaben - (beitraege + sonstige + bundesmittelOriginal)), effective: -saldo, changed: true, isKredit: true, colorKey: "kredit" });
      link(`defizit:${tid}`, topfId, -saldo, "kredit");
    }
    add({ id: topfId, label: t.name, column: 1, kind: "topf", original: ausgaben, effective: ausgaben, changed: bundesmittel !== bundesmittelOriginal, colorKey: "beitraege" });
    for (const p of t.ausgaben) {
      if (p.betrag <= 0) continue;
      add({ id: `posten:${tid}:${p.id}`, label: p.text, column: 2, kind: "titel", original: p.betrag, effective: p.betrag, changed: false, colorKey: "beitraege" });
      link(topfId, `posten:${tid}:${p.id}`, p.betrag, "beitraege");
    }
    if (saldo > 0) {
      add({ id: `ruecklage:${tid}`, label: `Rücklage ${t.kurz}`, column: 2, kind: "ruecklage", original: saldo, effective: saldo, changed: false, colorKey: "rest" });
      link(topfId, `ruecklage:${tid}`, saldo, "rest");
    }
  }

  return { nodes, links, ghosts, minderausgaben };
}
