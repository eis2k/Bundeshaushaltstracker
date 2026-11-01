import { balance } from "../model/scenario";
import { buildToepfe, type SozialkassenYear } from "../model/toepfe";
import { includeRow, revenueGroups, revenueKind } from "../model/tree";
import type { BudgetRow, NodeId, Scenario, YearData } from "../model/types";
import { ABZUEGE, MINDEREINNAHMEN, TOPF_BUND, addModelle, aggregate, negatives, pick, type Modell, type SGhost, type SLink, type SNode, type SankeyData } from "./sankeyData";

/**
 * Gesamtfluss: Steuern und Beiträge → Bund → Sozialkassen und Bund-Verwendung → Kassen-Verwendung.
 * Spalte 0 Zuflüsse, Spalte 1 Bund, Spalte 2 die Kassen (mit Querband Bund → Kasse für die Bundesmittel)
 * und die Verwendung des Bundes, Spalte 3 die Verwendung der Kassen. Die Salden je Kasse stammen aus
 * buildToepfe, damit Kopfzeile und Fluss dieselbe Rechnung zeigen. `only` zeigt nur eine Kasse (Spalten 0–2).
 */
export function buildGesamtSankey(bund: YearData, sk: SozialkassenYear, scenario: Scenario, factors: Record<NodeId, number>,
                                  opts: { maxPerColumn: number; maxRevenue?: number; only?: string; modelle?: Modell[] }): SankeyData {
  const nodes: SNode[] = [];
  const links: SLink[] = [];
  const ghosts: SGhost[] = [];
  const add = (n: Omit<SNode, "dim" | "netOriginal" | "netEffective"> & { dim?: boolean; netOriginal?: number; netEffective?: number }) => {
    nodes.push({ dim: false, netOriginal: n.original, netEffective: n.effective, ...n });
  };
  const link = (source: string, target: string, value: number, colorKey: string) => {
    if (value > 0) links.push({ source, target, value, colorKey, dim: false });
  };
  const rows = bund.rows.filter((r) => includeRow(r, scenario.includeSv));
  const showBund = !opts.only;
  const kassenColumn = showBund ? 2 : 1;
  const toepfe = buildToepfe(bund, sk, factors, scenario.includeSv);
  const linkedIds = new Set<string>();
  for (const t of Object.values(sk.toepfe)) for (const b of t.bundesmittel) linkedIds.add(b.titel);

  let minderausgaben = 0, absetzungen = 0;
  if (showBund) {
    const extraBund = (opts.modelle ?? []).reduce((s, m) => s + m.bund, 0);
    const b = balance(bund, factors, scenario.includeSv, extraBund);
    const ausgaben = rows.filter((r) => r.art === "A");
    const neg = negatives(rows, factors);
    minderausgaben = neg.minderausgaben;
    absetzungen = neg.absetzungen;

    // Spalte 0: Steuern (gefaltet), sonstige Einnahmen, Kredite
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
      const a = aggregate(g.id, g.label, g.rows, factors, g.colorKey);
      add({ id: a.id, label: a.label, column: 0, kind: "revenue", original: a.original, effective: a.effective, changed: a.changed, colorKey: g.colorKey });
      link(a.id, TOPF_BUND, a.effective, g.colorKey);
    }
    addModelle(opts.modelle, add, link, TOPF_BUND);
    add({ id: "E:kredite", label: "Neue Schulden (Bund)", column: 0, kind: "kredit", original: b.neueSchuldenOriginal, effective: b.neueSchulden, changed: b.neueSchulden !== b.neueSchuldenOriginal, isKredit: true, colorKey: "kredit" });
    link("E:kredite", TOPF_BUND, b.neueSchulden, "kredit");

    // Spalte 1: Bund
    add({ id: TOPF_BUND, label: "Bundeshaushalt", column: 1, kind: "topf", original: b.ausgabenOriginal, effective: b.ausgaben, changed: b.ausgaben !== b.ausgabenOriginal, colorKey: "topf" });

    // Spalte 2: Weiterleitung, Mindereinnahmen, Einzelpläne ohne die an die Kassen verknüpften Titel
    if (neg.abzuege > 0 || neg.abzuegeOriginal > 0) {
      add({ id: ABZUEGE, label: "Weiterleitung an EU und Länder", column: 2, kind: "abzug", original: neg.abzuegeOriginal, effective: neg.abzuege, changed: neg.abzuege !== neg.abzuegeOriginal, colorKey: "abzug" });
      link(TOPF_BUND, ABZUEGE, neg.abzuege, "abzug");
    }
    if (neg.mindereinnahmen > 0 || neg.mindereinnahmenOriginal > 0) {
      add({ id: MINDEREINNAHMEN, label: "Globale Mindereinnahmen", column: 2, kind: "abzug", original: neg.mindereinnahmenOriginal, effective: neg.mindereinnahmen, changed: neg.mindereinnahmen !== neg.mindereinnahmenOriginal, colorKey: "minder" });
      link(TOPF_BUND, MINDEREINNAHMEN, neg.mindereinnahmen, "minder");
    }
    const byEpl = new Map<string, BudgetRow[]>();
    for (const r of ausgaben) {
      if (linkedIds.has(r.id)) continue;
      (byEpl.get(r.epl) ?? byEpl.set(r.epl, []).get(r.epl)!).push(r);
    }
    const eplAggs = [...byEpl.entries()].map(([epl, rs]) => aggregate(epl, bund.epl[epl] ?? `Einzelplan ${epl}`, rs, factors, epl));
    const c2 = pick(eplAggs, undefined, Math.max(1, opts.maxPerColumn - 1), "rest:2");
    for (const a of [...c2.shown, ...(c2.rest ? [c2.rest] : [])]) {
      add({ id: a.id, label: a.id === "rest:2" ? "Alle anderen Ministerien" : a.label, column: 2, kind: a.id === "rest:2" ? "rest" : "epl", original: a.original, effective: a.effective, netOriginal: a.netOriginal, netEffective: a.netEffective, changed: a.changed, colorKey: a.colorKey });
      link(TOPF_BUND, a.id, a.effective, a.colorKey);
      if (a.id !== "rest:2" && a.changed && a.original !== a.effective) ghosts.push({ id: a.id, diff: a.original - a.effective });
    }
  }

  // Sozialkassen
  for (const t of toepfe.toepfe) {
    if (opts.only && opts.only !== t.id) continue;
    const topfId = `topf:${t.id}`;
    const beitraege = t.einnahmenListe.filter((e) => e.id === "beitraege").reduce((s, e) => s + e.betrag, 0);
    const sonstige = t.einnahmenListe.filter((e) => e.id !== "beitraege" && e.id !== "bund").reduce((s, e) => s + e.betrag, 0);
    const tableBund = t.einnahmenListe.filter((e) => e.id === "bund").reduce((s, e) => s + e.betrag, 0);
    // Bundesmittel: effektiv aus den verknüpften Bund-Titeln (buildToepfe), sonst der Tabellenwert
    const bundesmittel = t.bundesmittelOriginal > 0 ? t.bundesmittel : tableBund;
    const bundesmittelOriginal = t.bundesmittelOriginal > 0 ? t.bundesmittelOriginal : tableBund;

    if (beitraege > 0) {
      add({ id: `beitraege:${t.id}`, label: `Beiträge ${t.kurz}`, column: 0, kind: "beitraege", original: beitraege, effective: beitraege, changed: false, colorKey: "beitraege" });
      link(`beitraege:${t.id}`, topfId, beitraege, "beitraege");
    }
    if (showBund) {
      // Querband Bund → Kasse
      link(TOPF_BUND, topfId, bundesmittel, "steuern");
      if (bundesmittel !== bundesmittelOriginal) ghosts.push({ id: topfId, diff: bundesmittelOriginal - bundesmittel });
    } else if (bundesmittel > 0 || bundesmittelOriginal > 0) {
      add({ id: `bundesmittel:${t.id}`, label: `Bundesmittel ${t.kurz}`, column: 0, kind: "revenue", original: bundesmittelOriginal, effective: bundesmittel, changed: bundesmittel !== bundesmittelOriginal, colorKey: "steuern" });
      link(`bundesmittel:${t.id}`, topfId, bundesmittel, "steuern");
      if (bundesmittel !== bundesmittelOriginal) ghosts.push({ id: `bundesmittel:${t.id}`, diff: bundesmittelOriginal - bundesmittel });
    }
    if (sonstige > 0) {
      add({ id: `sonstige:${t.id}`, label: `Sonstige Einnahmen ${t.kurz}`, column: 0, kind: "revenue", original: sonstige, effective: sonstige, changed: false, colorKey: "sonstige" });
      link(`sonstige:${t.id}`, topfId, sonstige, "sonstige");
    }
    if (t.saldo < 0) {
      add({ id: `defizit:${t.id}`, label: `Defizit ${t.kurz}`, column: 0, kind: "kredit", original: Math.max(0, -t.saldoOriginal), effective: -t.saldo, changed: t.saldo !== t.saldoOriginal, isKredit: true, colorKey: "kredit" });
      link(`defizit:${t.id}`, topfId, -t.saldo, "kredit");
    }
    add({ id: topfId, label: t.name, column: kassenColumn, kind: "topf", original: t.ausgaben, effective: t.ausgaben, changed: t.einnahmen !== t.einnahmenOriginal, colorKey: "beitraege" });
    for (const p of t.ausgabenListe) {
      if (p.betrag <= 0) continue;
      add({ id: `posten:${t.id}:${p.id}`, label: p.text, column: kassenColumn + 1, kind: "titel", original: p.betrag, effective: p.betrag, changed: false, colorKey: "beitraege" });
      link(topfId, `posten:${t.id}:${p.id}`, p.betrag, "beitraege");
    }
    if (t.saldo > 0) {
      add({ id: `ruecklage:${t.id}`, label: `Rücklage ${t.kurz}`, column: kassenColumn + 1, kind: "ruecklage", original: Math.max(0, t.saldoOriginal), effective: t.saldo, changed: t.saldo !== t.saldoOriginal, colorKey: "rest" });
      link(topfId, `ruecklage:${t.id}`, t.saldo, "rest");
    }
  }

  return { nodes, links, ghosts, minderausgaben, absetzungen };
}
