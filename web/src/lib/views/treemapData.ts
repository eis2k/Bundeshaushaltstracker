import { hierarchy, treemap, treemapSquarify, type HierarchyRectangularNode } from "d3-hierarchy";
import { effectiveValue, rowFactor } from "../model/scenario";
import type { BudgetRow, NodeId, Tree, TreeNode } from "../model/types";

export interface TNode {
  id: string;
  label: string;
  kind: "bund" | "epl" | "kap" | "titel";
  /** Fläche: Summe der positiven effektiven Werte. */
  value: number;
  original: number;
  changed: boolean;
  sv: boolean;
  children: TNode[];
}

export interface TRoot extends TNode {
  /** Summe der negativen Titel (Minderausgaben) im Wurzelbereich, ≤ 0. */
  minderausgaben: number;
}

function rowsOf(n: TreeNode): BudgetRow[] {
  return n.row ? [n.row] : n.children.flatMap(rowsOf);
}

function toTNode(n: TreeNode, factors: Record<NodeId, number>): TNode {
  let value = 0, original = 0, changed = false;
  for (const r of rowsOf(n)) {
    const v = effectiveValue(r, factors);
    if (v > 0) value += v;
    if (r.soll > 0) original += r.soll;
    if (rowFactor(r, factors) !== 1) changed = true;
  }
  return { id: n.id, label: n.label, kind: n.kind, value, original, changed, sv: n.sv, children: [] };
}

/** Wurzel der Karte: der tiefste gültige Fokusknoten (sonst der Bund) mit seinen direkten Kindern. */
export function treemapRoot(tree: Tree, factors: Record<NodeId, number>, focus: NodeId[]): TRoot {
  let focusNode: TreeNode | undefined;
  for (const id of focus) {
    const n = tree.byId.get(id);
    if (n && n.kind !== "titel") focusNode = n;
  }
  const children = focusNode ? focusNode.children : tree.roots;
  const rows = focusNode ? rowsOf(focusNode) : tree.roots.flatMap(rowsOf);
  let minderausgaben = 0;
  for (const r of rows) {
    const v = effectiveValue(r, factors);
    if (v < 0) minderausgaben += v;
  }
  const tChildren = children.map((c) => toTNode(c, factors));
  const base = focusNode ? toTNode(focusNode, factors) : {
    id: "bund", label: "Bundeshaushalt", kind: "bund" as const,
    value: tChildren.reduce((s, c) => s + c.value, 0), original: tChildren.reduce((s, c) => s + c.original, 0),
    changed: tChildren.some((c) => c.changed), sv: false, children: [],
  };
  return { ...base, children: tChildren, minderausgaben };
}

export function buildTreemap(root: TRoot, width: number, height: number): HierarchyRectangularNode<TNode> {
  const h = hierarchy<TNode>(root, (d) => (d === root ? d.children : undefined))
    .sum((d) => (d === root ? 0 : d.value))
    .sort((a, b) => (b.value ?? 0) - (a.value ?? 0));
  return treemap<TNode>().size([width, height]).padding(2).tile(treemapSquarify)(h);
}
