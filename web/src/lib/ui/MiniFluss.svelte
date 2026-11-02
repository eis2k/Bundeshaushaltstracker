<script lang="ts">
  /** Kompakter Geldfluss für das Dashboard (Spec §4.11): Einnahmegruppen → Bundeshaushalt → größte Einzelpläne, Klick führt in den Fluss. */
  import { sankey, sankeyLinkHorizontal, sankeyJustify, type SankeyLink, type SankeyNode } from "d3-sankey";
  import { fmtEuro } from "../model/format";
  import { balance, effectiveValue, type Factors } from "../model/scenario";
  import { includeRow, revenueGroups } from "../model/tree";
  import type { YearData } from "../model/types";
  import type { AppState } from "../state.svelte";

  let { app, data, factors, includeSv, extraBund = 0, max = 5, height = 300 }: { app: AppState; data: YearData; factors: Factors; includeSv: boolean; extraBund?: number; max?: number; height?: number } = $props();
  type N = { id: string; label: string; wert: number; art: "einnahme" | "haushalt" | "epl" | "rest" };
  type L = { source: string; target: string; value: number };

  let width = $state(720);
  const graph = $derived.by(() => {
    const nodes: N[] = [];
    const links: L[] = [];
    const bilanz = balance(data, factors, includeSv, extraBund);
    const alle = revenueGroups(data, includeSv).map((g) => ({ id: g.id, label: g.label, wert: g.isKredit ? bilanz.neueSchulden : g.rows.reduce((s, r) => s + effectiveValue(r, factors), 0), kredit: g.isKredit })).filter((g) => g.wert > 0);
    // Einnahmeseite kompakt: die größten Steuerarten einzeln, der Rest gebündelt, Kredite immer eigener Knoten.
    const steuern = alle.filter((g) => !g.kredit).sort((a, b) => b.wert - a.wert);
    const gruppen = steuern.slice(0, max);
    const restE = steuern.slice(max).reduce((s, g) => s + g.wert, 0);
    if (restE > 0) gruppen.push({ id: "E:weitere", label: "Weitere Einnahmen", wert: restE, kredit: false });
    gruppen.push(...alle.filter((g) => g.kredit));
    for (const g of gruppen) { nodes.push({ id: g.id, label: g.label, wert: g.wert, art: "einnahme" }); links.push({ source: g.id, target: "haushalt", value: g.wert }); }
    const ausgaben = new Map<string, number>();
    for (const r of data.rows) if (r.art === "A" && includeRow(r, includeSv)) ausgaben.set(r.epl, (ausgaben.get(r.epl) ?? 0) + effectiveValue(r, factors));
    const gesamt = [...ausgaben.values()].reduce((s, x) => s + x, 0);
    nodes.push({ id: "haushalt", label: `Bundeshaushalt ${data.jahr}`, wert: gesamt, art: "haushalt" });
    const sortiert = [...ausgaben.entries()].sort((a, b) => b[1] - a[1]);
    let rest = 0;
    sortiert.forEach(([epl, w], i) => {
      if (i < max) { nodes.push({ id: `epl:${epl}`, label: data.epl[epl] ?? `Einzelplan ${epl}`, wert: w, art: "epl" }); links.push({ source: "haushalt", target: `epl:${epl}`, value: w }); }
      else rest += w;
    });
    if (rest > 0) { nodes.push({ id: "rest", label: "Weitere Einzelpläne", wert: rest, art: "rest" }); links.push({ source: "haushalt", target: "rest", value: rest }); }
    const gen = sankey<N, L>().nodeId((d) => d.id).nodeWidth(14).nodePadding(10).nodeAlign(sankeyJustify).extent([[8, 8], [Math.max(320, width) - 8, height - 30]]);
    return gen({ nodes: nodes.map((n) => ({ ...n })), links: links.map((l) => ({ ...l })) });
  });
  const pfad = sankeyLinkHorizontal();
  function klick(n: SankeyNode<N, L>) {
    if (n.art === "epl") app.zeigeImFluss([n.id.slice(4)]);
    else { app.spur = []; app.setTopf("bund"); app.setView("fluss"); }
  }
  function farbe(n: SankeyNode<N, L>): string {
    if (n.art === "einnahme") return n.id.startsWith("E:steuern") ? "var(--steuern)" : n.id.includes("kredit") ? "var(--bad)" : "var(--beitraege)";
    if (n.art === "haushalt") return "var(--header)";
    if (n.art === "rest") return "#9fb3c8";
    return "var(--nav-on)";
  }
</script>

<div class="mini" bind:clientWidth={width}>
  <svg {width} {height} role="img" aria-label="Geldfluss von den Einnahmen über den Bundeshaushalt zu den größten Einzelplänen">
    {#each graph.links as l}
      {@const s = l.source as SankeyNode<N, L>}
      <path d={pfad(l as SankeyLink<N, L>) ?? ""} fill="none" stroke={farbe(s)} stroke-opacity="0.18" stroke-width={Math.max(1, l.width ?? 1)} />
    {/each}
    {#each graph.nodes as n}
      <g class="knoten" role="button" tabindex="0" onclick={() => klick(n)} onkeydown={(e) => e.key === "Enter" && klick(n)}>
        <rect x={n.x0} y={n.y0} width={(n.x1 ?? 0) - (n.x0 ?? 0)} height={Math.max(2, (n.y1 ?? 0) - (n.y0 ?? 0))} rx="4" fill={farbe(n)} />
        <text x={n.art === "einnahme" ? (n.x1 ?? 0) + 6 : n.art === "haushalt" ? ((n.x0 ?? 0) + (n.x1 ?? 0)) / 2 : (n.x0 ?? 0) - 6} y={n.art === "haushalt" ? (n.y1 ?? 0) + 14 : ((n.y0 ?? 0) + (n.y1 ?? 0)) / 2} dy="0.35em"
              text-anchor={n.art === "einnahme" ? "start" : n.art === "haushalt" ? "middle" : "end"} class:hell={n.art === "haushalt"}>
          {n.label.length > 30 ? n.label.slice(0, 29) + "…" : n.label} · {fmtEuro(n.wert)}
        </text>
      </g>
    {/each}
  </svg>
</div>

<style>
  .mini { width: 100%; }
  svg { display: block; width: 100%; }
  .knoten { cursor: pointer; }
  .knoten:focus-visible rect { outline: 2px solid var(--accent); }
  text { font-size: 11px; fill: var(--fg); }
  text.hell { fill: var(--fg); font-weight: 700; }
</style>
