import { buildTree } from "./tree";
import type { BudgetRow, Tree, TreeNode, YearData } from "./types";

/** Drei Schnitte durch dieselben Ausgaben: nach Ressort, nach Kostenart (Hauptgruppen), nach Empfänger-Art (Gruppierungsplan). */
export type Schnitt = "ressort" | "kostenart" | "empfaengerart";

export type Kostenart = "personal" | "sach" | "zinsen" | "zuweisungen" | "bau" | "investitionen" | "finanzierung";

export const KOSTENART_LABELS: Record<Kostenart, string> = {
  personal: "Personal",
  sach: "Sachausgaben",
  zinsen: "Zinsen",
  zuweisungen: "Zuweisungen und Zuschüsse",
  bau: "Baumaßnahmen",
  investitionen: "Sonstige Investitionen",
  finanzierung: "Besondere Finanzierungsausgaben",
};

/** Hauptgruppen des Gruppierungsplans: 4 Personal, 5 Sachausgaben (56/57 Zinsen), 6 Zuweisungen, 7 Bau, 8 Investitionen, 9 Finanzierung. */
export function kostenart(titel: string): Kostenart {
  const hg = titel[0];
  const og = titel.slice(0, 2);
  if (hg === "4") return "personal";
  if (hg === "5") return og === "56" || og === "57" ? "zinsen" : "sach";
  if (hg === "6") return "zuweisungen";
  if (hg === "7") return "bau";
  if (hg === "8") return "investitionen";
  return "finanzierung";
}

export type EmpfaengerArt =
  | "bund_selbst" | "glaeubiger" | "sozialversicherung" | "laender_gemeinden" | "unternehmen"
  | "vereine_inland" | "privatpersonen" | "ausland" | "uebrige";

export const EMPFAENGERART_LABELS: Record<EmpfaengerArt, string> = {
  bund_selbst: "Bund selbst (Personal, Sachkosten, Bau)",
  glaeubiger: "Gläubiger (Zinsen)",
  sozialversicherung: "Sozialversicherung",
  laender_gemeinden: "Länder und Gemeinden",
  unternehmen: "Unternehmen",
  vereine_inland: "Vereine, Verbände, sonstige im Inland",
  privatpersonen: "Privatpersonen (Sozialleistungen)",
  ausland: "Ausland und internationale Organisationen",
  uebrige: "Übrige",
};

/**
 * Empfänger-Art nach dem Gruppierungsplan des Bundes (Zweckbestimmung der Gruppen 6xx/8xx):
 * 61x/63x/88x Länder und Gemeinden, 636 Sozialversicherung, 68x/89x nach zweiter Ziffer
 * (681 Privatpersonen, 682/683 und 892/893 Unternehmen, 684/685 und 894 Vereine/sonstige Inland,
 * 686/687 und 896 Ausland). Hauptgruppen 4, 5 (ohne Zinsen), 7 sind Ausgaben des Bundes selbst.
 */
export function empfaengerArt(titel: string): EmpfaengerArt {
  const hg = titel[0];
  const g = titel.slice(0, 3);
  const og = titel.slice(0, 2);
  if (hg === "4" || hg === "7") return "bund_selbst";
  if (hg === "5") return og === "56" || og === "57" ? "glaeubiger" : "bund_selbst";
  if (g === "636") return "sozialversicherung";
  if (og === "61" || og === "63" || og === "88") return "laender_gemeinden";
  if (og === "68" || og === "89") {
    const third = titel[2];
    if (og === "68" && third === "1") return "privatpersonen";
    if (third === "2" || third === "3") return "unternehmen";
    if (third === "4" || third === "5") return "vereine_inland";
    if (third === "6" || third === "7") return "ausland";
    return "uebrige";
  }
  if (og === "62" || og === "69" || og === "87") return "uebrige";
  if (hg === "8") return "unternehmen";
  return "uebrige";
}

function groupTree(data: YearData, includeSv: boolean, prefix: string, keyOf: (r: BudgetRow) => string, labels: Record<string, string>): Tree {
  const byId = new Map<string, TreeNode>();
  const roots: TreeNode[] = [];
  const groups = new Map<string, TreeNode>();
  for (const row of data.rows) {
    if (row.art !== "A") continue;
    if (row.sv && !includeSv) continue;
    const key = keyOf(row);
    const id = `${prefix}:${key}`;
    let g = groups.get(id);
    if (!g) {
      g = { id, label: labels[key] ?? key, kind: "epl", soll: 0, ist: null, sv: false, children: [] };
      groups.set(id, g);
      byId.set(id, g);
      roots.push(g);
    }
    const t: TreeNode = { id: row.id, label: row.text, kind: "titel", soll: row.soll, ist: row.ist, sv: row.sv, children: [], row };
    g.children.push(t);
    byId.set(row.id, t);
  }
  for (const g of groups.values()) {
    g.soll = g.children.reduce((s, c) => s + c.soll, 0);
    const ist = g.children.map((c) => c.ist).filter((v): v is number => v !== null);
    g.ist = ist.length ? ist.reduce((a, b) => a + b, 0) : null;
  }
  roots.sort((a, b) => b.soll - a.soll);
  return { roots, byId };
}

export function groupBy(data: YearData, schnitt: Schnitt, includeSv: boolean): Tree {
  if (schnitt === "ressort") return buildTree(data, includeSv);
  if (schnitt === "kostenart") return groupTree(data, includeSv, "ka", (r) => kostenart(r.titel), KOSTENART_LABELS);
  return groupTree(data, includeSv, "ea", (r) => empfaengerArt(r.titel), EMPFAENGERART_LABELS);
}
