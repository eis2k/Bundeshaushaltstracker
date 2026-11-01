import { revenueGroupId } from "./tree";
import type { NodeId, Scenario, ViewId, YearData } from "./types";

const VIEWS: ViewId[] = ["fluss", "karte", "saeulen", "gewachsen"];

/**
 * Zustand → Hash (ohne "#"), z. B.
 * v1;j=2025;a=fluss;f=11/1102/63681;p=rentenzuschuss_halbieren;o=11-1102-63681:50,14:200;sv=1
 * Nur Abweichungen von 100 % werden gespeichert, Prozent ganzzahlig.
 */
export function encodeScenario(s: Scenario, view: ViewId, focus: NodeId[]): string {
  const parts = ["v1", `j=${s.jahr}`, `a=${view}`];
  if (focus.length) parts.push(`f=${focus.map((id) => id.split("-").pop()).join("/")}`);
  if (s.presets.length) parts.push(`p=${s.presets.join(",")}`);
  const o = Object.entries(s.factors)
    .sort(([a], [b]) => a.localeCompare(b))
    .map(([id, f]) => [id, Math.round(f * 100)] as const)
    .filter(([, pct]) => pct !== 100)
    .map(([id, pct]) => `${id}:${pct}`);
  if (o.length) parts.push(`o=${o.join(",")}`);
  if (s.includeSv) parts.push("sv=1");
  return parts.join(";");
}

export function knownIds(data: YearData): Set<string> {
  const ids = new Set<string>();
  for (const row of data.rows) {
    if (row.art === "A") {
      ids.add(row.epl);
      ids.add(`${row.epl}-${row.kap}`);
      ids.add(row.id);
    } else {
      ids.add(row.id);
      ids.add(revenueGroupId(row));
    }
  }
  ids.add("E:steuern");
  ids.add("E:sonstige");
  ids.add("E:kredite");
  return ids;
}

export function decodeScenario(hash: string, data: YearData): { scenario: Scenario; view: ViewId; focus: NodeId[]; unknownIds: NodeId[] } {
  const fallback = { scenario: { jahr: data.jahr, factors: {}, presets: [], includeSv: false } as Scenario, view: "fluss" as ViewId, focus: [] as NodeId[], unknownIds: [] as NodeId[] };
  const raw = hash.startsWith("#") ? hash.slice(1) : hash;
  const parts = raw.split(";");
  if (parts[0] !== "v1") return fallback;
  const kv = new Map<string, string>();
  for (const p of parts.slice(1)) {
    const i = p.indexOf("=");
    if (i > 0) kv.set(p.slice(0, i), p.slice(i + 1));
  }
  const jahr = Number.parseInt(kv.get("j") ?? "", 10);
  const view = (VIEWS as string[]).includes(kv.get("a") ?? "") ? (kv.get("a") as ViewId) : "fluss";
  const focus: NodeId[] = [];
  if (kv.get("f")) {
    let acc = "";
    for (const seg of kv.get("f")!.split("/")) {
      acc = acc ? `${acc}-${seg}` : seg;
      focus.push(acc);
    }
  }
  const presets = kv.get("p") ? kv.get("p")!.split(",").filter(Boolean) : [];
  const known = knownIds(data);
  const factors: Record<NodeId, number> = {};
  const unknownIds: NodeId[] = [];
  if (kv.get("o")) {
    for (const item of kv.get("o")!.split(",")) {
      const i = item.lastIndexOf(":");
      if (i <= 0) continue;
      const id = item.slice(0, i);
      const pct = Number.parseInt(item.slice(i + 1), 10);
      if (!Number.isFinite(pct)) continue;
      if (!known.has(id)) { unknownIds.push(id); continue; }
      if (pct !== 100) factors[id] = pct / 100;
    }
  }
  return {
    scenario: { jahr: Number.isFinite(jahr) ? jahr : data.jahr, factors, presets, includeSv: kv.get("sv") === "1" },
    view, focus, unknownIds,
  };
}
