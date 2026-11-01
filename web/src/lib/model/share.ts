import { revenueGroupId } from "./tree";
import type { NodeId, Scenario, ViewId, YearData } from "./types";
import { EMPFAENGERART_LABELS, KOSTENART_LABELS, type Schnitt } from "./schnitte";

const VIEWS: ViewId[] = ["fluss", "karte", "saeulen", "gewachsen"];
const SCHNITTE: Schnitt[] = ["ressort", "kostenart", "empfaengerart"];
export const TOEPFE = ["gesamt", "bund", "grv", "gkv", "spv", "ba"] as const;
export type TopfId = (typeof TOEPFE)[number];

/**
 * Zustand → Hash (ohne "#"), z. B.
 * v1;j=2025;a=fluss;f=11/1102/63681;p=rentenzuschuss_halbieren;o=11-1102-63681:50,14:200;sv=1
 * Nur Abweichungen von 100 % werden gespeichert, Prozent ganzzahlig.
 */
export function encodeScenario(s: Scenario, view: ViewId, focus: NodeId[], schnitt: Schnitt = "ressort", topf: TopfId = "gesamt"): string {
  const parts = ["v1", `j=${s.jahr}`, `a=${view}`];
  if (schnitt !== "ressort") parts.push(`sc=${schnitt}`);
  if (topf !== "gesamt") parts.push(`t=${topf}`);
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
  for (const k of Object.keys(KOSTENART_LABELS)) ids.add(`ka:${k}`);
  for (const k of Object.keys(EMPFAENGERART_LABELS)) ids.add(`ea:${k}`);
  return ids;
}

export function decodeScenario(hash: string, data: YearData): { scenario: Scenario; view: ViewId; focus: NodeId[]; unknownIds: NodeId[]; schnitt: Schnitt; topf: TopfId } {
  const fallback = { scenario: { jahr: data.jahr, factors: {}, presets: [], includeSv: false } as Scenario, view: "fluss" as ViewId, focus: [] as NodeId[], unknownIds: [] as NodeId[], schnitt: "ressort" as Schnitt, topf: "gesamt" as TopfId };
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
  const schnitt = (SCHNITTE as string[]).includes(kv.get("sc") ?? "") ? (kv.get("sc") as Schnitt) : "ressort";
  const topf = (TOEPFE as readonly string[]).includes(kv.get("t") ?? "") ? (kv.get("t") as TopfId) : "gesamt";
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
      const raw = Number.parseInt(item.slice(i + 1), 10);
      if (!Number.isFinite(raw)) continue;
      const pct = Math.min(1000, Math.max(0, raw));
      if (!known.has(id)) { unknownIds.push(id); continue; }
      if (pct !== 100) factors[id] = pct / 100;
    }
  }
  return {
    scenario: { jahr: Number.isFinite(jahr) ? jahr : data.jahr, factors, presets, includeSv: kv.get("sv") === "1" },
    view, focus, unknownIds, schnitt, topf,
  };
}
