/** Knoten-IDs: "11" (Einzelplan), "11-1102" (Kapitel), "11-1102-63681" (Titel),
 *  Einnahmen: "E:steuern", "E:steuern:011" (Gruppierung), "E:sonstige", "E:kredite". */
export type NodeId = string;

export interface BudgetRow {
  id: NodeId;
  art: "E" | "A";
  epl: string;
  kap: string;
  titel: string;
  text: string;
  fkt: string;
  flex: boolean | null;
  tgr: string | null;
  soll: number;
  ist: number | null;
  sv: boolean;
}

export interface Quelle {
  dokument: string;
  datei?: string;
  url: string;
  abgerufen: string | null;
}

export interface YearData {
  jahr: number;
  stand: "soll";
  quelle: { soll: Quelle | null; ist: Quelle | null; hinweise: string[] };
  epl: Record<string, string>;
  kap: Record<string, string>;
  rows: BudgetRow[];
}

export interface Index {
  jahre: number[];
  ist_bis: number | null;
  summen: Record<string, { ausgaben: number; einnahmen: number; kredite: number }>;
  erzeugt: string;
}

export interface Scenario {
  jahr: number;
  /** Faktor je Knoten-ID, 1 = Original. Nur Abweichungen werden gespeichert. */
  factors: Record<NodeId, number>;
  presets: string[];
  includeSv: boolean;
}

export interface Balance {
  ausgaben: number;
  einnahmen: number;
  neueSchulden: number;
  ausgabenOriginal: number;
  einnahmenOriginal: number;
  neueSchuldenOriginal: number;
  /** Verbesserung gegenüber Original: neueSchuldenOriginal − neueSchulden (positiv = weniger Schulden). */
  delta: number;
}

export type NodeKind = "epl" | "kap" | "titel";

export interface TreeNode {
  id: NodeId;
  label: string;
  kind: NodeKind;
  soll: number;
  ist: number | null;
  sv: boolean;
  children: TreeNode[];
  row?: BudgetRow;
}

export interface Tree {
  roots: TreeNode[];
  byId: Map<NodeId, TreeNode>;
}

export interface RevenueGroup {
  id: NodeId;
  label: string;
  soll: number;
  ist: number | null;
  isKredit: boolean;
  rows: BudgetRow[];
}

export type ViewId = "fluss" | "karte" | "saeulen" | "gewachsen";
