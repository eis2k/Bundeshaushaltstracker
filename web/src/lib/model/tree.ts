import type { BudgetRow, RevenueGroup, Tree, TreeNode, YearData } from "./types";

export const KREDIT_GRUPPE = "325";

/** Steuerarten nach Gruppierungsplan (erste drei Ziffern des Titels, Hauptgruppe 0). */
export const TAX_LABELS: Record<string, string> = {
  "011": "Lohnsteuer",
  "012": "Veranlagte Einkommensteuer",
  "013": "Nicht veranlagte Steuern vom Ertrag",
  "014": "Körperschaftsteuer",
  "015": "Umsatzsteuer",
  "016": "Einfuhrumsatzsteuer",
  "018": "Abgeltungsteuer",
  "031": "Energiesteuer",
  "032": "Tabaksteuer",
  "036": "Versicherungsteuer",
  "037": "Stromsteuer",
  "039": "Kraftfahrzeugsteuer",
  "044": "Solidaritätszuschlag",
};

export type RevenueKind = "steuern" | "sonstige" | "kredite";

export function revenueKind(row: BudgetRow): RevenueKind {
  const gruppe = row.titel.slice(0, 3);
  if (gruppe === KREDIT_GRUPPE) return "kredite";
  if (row.titel[0] === "0") return "steuern";
  return "sonstige";
}

/** Gruppen-ID einer Einnahmezeile: "E:steuern:011", "E:steuern:rest", "E:sonstige", "E:kredite". */
export function revenueGroupId(row: BudgetRow): string {
  const kind = revenueKind(row);
  if (kind !== "steuern") return `E:${kind}`;
  const gruppe = row.titel.slice(0, 3);
  return TAX_LABELS[gruppe] ? `E:steuern:${gruppe}` : "E:steuern:rest";
}

function sumIst(rows: { ist: number | null }[]): number | null {
  const vals = rows.map((r) => r.ist).filter((v): v is number => v !== null);
  return vals.length ? vals.reduce((a, b) => a + b, 0) : null;
}

export function buildTree(data: YearData, includeSv: boolean): Tree {
  const byId = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];
  const eplNodes = new Map<string, TreeNode>();
  const kapNodes = new Map<string, TreeNode>();

  for (const row of data.rows) {
    if (row.art !== "A") continue;
    if (row.sv && !includeSv) continue;

    let epl = eplNodes.get(row.epl);
    if (!epl) {
      epl = { id: row.epl, label: data.epl[row.epl] ?? `Einzelplan ${row.epl}`, kind: "epl", soll: 0, ist: null, sv: false, children: [] };
      eplNodes.set(row.epl, epl);
      byId.set(epl.id, epl);
      roots.push(epl);
    }
    const kapId = `${row.epl}-${row.kap}`;
    let kap = kapNodes.get(kapId);
    if (!kap) {
      kap = { id: kapId, label: data.kap[row.kap] ?? `Kapitel ${row.kap}`, kind: "kap", soll: 0, ist: null, sv: row.sv, children: [] };
      kapNodes.set(kapId, kap);
      byId.set(kapId, kap);
      epl.children.push(kap);
    }
    const titel: TreeNode = { id: row.id, label: row.text, kind: "titel", soll: row.soll, ist: row.ist, sv: row.sv, children: [], row };
    kap.children.push(titel);
    byId.set(titel.id, titel);
  }

  for (const kap of kapNodes.values()) {
    kap.soll = kap.children.reduce((s, c) => s + c.soll, 0);
    kap.ist = sumIst(kap.children);
  }
  for (const epl of eplNodes.values()) {
    epl.soll = epl.children.reduce((s, c) => s + c.soll, 0);
    epl.ist = sumIst(epl.children);
  }
  roots.sort((a, b) => a.id.localeCompare(b.id));
  return { roots, byId };
}

export function revenueGroups(data: YearData, includeSv: boolean): RevenueGroup[] {
  const groups = new Map<string, RevenueGroup>();
  for (const row of data.rows) {
    if (row.art !== "E") continue;
    if (row.sv && !includeSv) continue;
    const id = revenueGroupId(row);
    let g = groups.get(id);
    if (!g) {
      const kind = revenueKind(row);
      const label =
        kind === "kredite" ? "Neue Schulden (Kredite)" :
        kind === "sonstige" ? "Sonstige Einnahmen" :
        id === "E:steuern:rest" ? "Übrige Steuern" : TAX_LABELS[row.titel.slice(0, 3)];
      g = { id, label, soll: 0, ist: null, isKredit: kind === "kredite", rows: [] };
      groups.set(id, g);
    }
    g.rows.push(row);
    g.soll += row.soll;
  }
  for (const g of groups.values()) g.ist = sumIst(g.rows);
  return [...groups.values()].sort((a, b) => {
    if (a.isKredit !== b.isKredit) return a.isKredit ? 1 : -1;
    return b.soll - a.soll;
  });
}
