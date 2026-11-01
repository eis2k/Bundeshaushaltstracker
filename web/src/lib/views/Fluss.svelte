<script lang="ts">
  import { onMount } from "svelte";
  import { select } from "d3-selection";
  import { zoom as d3zoom, zoomIdentity, type ZoomTransform } from "d3-zoom";
  import { sankey as d3sankey, sankeyLinkHorizontal } from "d3-sankey";
  import type { SankeyLink, SankeyNode } from "d3-sankey";
  import { fmtEuro } from "../model/format";
  import type { NodeId, Scenario, YearData } from "../model/types";
  import { CHANGED_STROKE, GHOST_STROKE, colorFor } from "./colors";
  import { buildSankey, type SLink, type SNode } from "./sankeyData";
  import { buildGesamtSankey } from "./sankeyGesamt";
  import type { SozialkassenYear } from "../model/toepfe";
  import type { TopfId } from "../model/share";

  interface Props {
    data: YearData;
    scenario: Scenario;
    factors: Record<NodeId, number>;
    focus: NodeId[];
    selected: NodeId | null;
    topf?: TopfId;
    sozialkassen?: SozialkassenYear | null;
    onFocus: (path: NodeId[]) => void;
    onSelect: (id: NodeId | null) => void;
    onTopf?: (topf: TopfId) => void;
  }
  let { data, scenario, factors, focus, selected, topf = "bund", sozialkassen = null, onFocus, onSelect, onTopf }: Props = $props();
  const gesamtModus = $derived(topf !== "bund" && sozialkassen !== null);

  let width = $state(900);

  // Mausrad zoomt, Ziehen verschiebt; Doppelklick oder Knopf setzt zurück
  let svgEl = $state<SVGSVGElement | null>(null);
  let transform = $state<ZoomTransform>(zoomIdentity);
  const zoomed = $derived(transform.k !== 1 || transform.x !== 0 || transform.y !== 0);
  const zoomBehavior = d3zoom<SVGSVGElement, unknown>()
    .scaleExtent([1, 8])
    .filter((e: Event) => e.type !== "dblclick" && !(e.type === "mousedown" && (e as MouseEvent).button !== 0))
    .on("zoom", (e) => (transform = e.transform));
  onMount(() => {
    if (!svgEl) return;
    const sel = select(svgEl);
    sel.call(zoomBehavior);
    sel.on("dblclick.zoom", null);
    return () => { sel.on(".zoom", null); };
  });
  function resetZoom() {
    if (svgEl) select(svgEl).call(zoomBehavior.transform, zoomIdentity);
    else transform = zoomIdentity;
  }
  $effect(() => {
    // Beim Wechsel von Fokus oder Topf zurück auf die Gesamtansicht
    void focus; void topf;
    if (svgEl) select(svgEl).call(zoomBehavior.transform, zoomIdentity);
  });
  /** Bei Zoom bleiben Schrift und Linienstärken lesbar: Gegenskalierung. */
  const invK = $derived(1 / transform.k);
  const columnsNeeded = $derived(focus.length >= 2 ? 6 : focus.length === 1 ? 4 : 3);
  const height = $derived((width < 720 ? 560 : 440) + Math.max(0, columnsNeeded - 4) * 80 + (gesamtModus ? 200 : 0));
  const maxPerColumn = $derived(width < 720 ? 5 : columnsNeeded >= 6 ? 6 : 8);

  const sdata = $derived(gesamtModus
    ? buildGesamtSankey(data, sozialkassen!, scenario, factors, { maxPerColumn, maxRevenue: width < 720 ? 4 : 6, only: topf === "gesamt" ? undefined : topf })
    : buildSankey(data, scenario, factors, focus, { maxPerColumn, maxRevenue: width < 720 ? 5 : 7 }));

  type LNode = SankeyNode<SNode, SLink>;
  type LLink = SankeyLink<SNode, SLink>;

  const layout = $derived.by(() => {
    const columns = Math.max(...sdata.nodes.map((n) => n.column)) + 1;
    const gen = d3sankey<SNode, SLink>()
      .nodeId((d) => d.id)
      .nodeWidth(12)
      .nodePadding(width < 720 ? 6 : 10)
      .nodeAlign((n) => (n as unknown as SNode).column)
      .nodeSort(null)
      .extent([[1, 36], [width - 1, height - 30]]);
    const graph = gen({
      nodes: sdata.nodes.map((n) => ({ ...n })),
      links: sdata.links.map((l) => ({ ...l })),
    });
    return { ...graph, columns };
  });

  const linkPath = sankeyLinkHorizontal<SNode, SLink>();

  function labelX(n: LNode): number {
    return (n.x0 ?? 0) < width / 2 ? (n.x1 ?? 0) + 6 : (n.x0 ?? 0) - 6;
  }
  function labelAnchor(n: LNode): string {
    return (n.x0 ?? 0) < width / 2 ? "start" : "end";
  }
  function nodeHeight(n: LNode): number {
    return Math.max(0, (n.y1 ?? 0) - (n.y0 ?? 0));
  }
  /** Pixel je Euro aus dem Topf-Knoten (d3 bemisst alle Knoten mit demselben Maßstab). */
  const pxPerEuro = $derived.by(() => {
    const topf = (layout.nodes as LNode[]).find((n) => n.kind === "topf" && (n.value ?? 0) > 0);
    return topf ? nodeHeight(topf) / (topf.value ?? 1) : 0;
  });
  function ghostHeight(n: LNode): number {
    const g = sdata.ghosts.find((g) => g.id === n.id);
    if (!g || g.diff <= 0) return 0;
    return Math.min(g.diff * pxPerEuro, height * 0.4);
  }
  function ghostFor(n: LNode) {
    return sdata.ghosts.find((g) => g.id === n.id) ?? null;
  }
  function pathFor(n: SNode): NodeId[] {
    if (n.kind === "epl") return [n.id];
    if (n.kind === "kap") return [n.id.split("-")[0], n.id];
    if (n.kind === "titel") { const [epl, kap] = n.id.split("-"); return [epl, `${epl}-${kap}`, n.id]; }
    return [];
  }
  function click(n: SNode) {
    if (gesamtModus) {
      if (n.kind === "topf") {
        const id = n.id.replace("topf:", "") as TopfId;
        onTopf?.(id === "bund" ? "bund" : topf === id ? "gesamt" : id);
        if (id !== "bund") onSelect(n.id);   // nach dem Topfwechsel, sonst setzt der Wechsel die Auswahl zurück
      } else if (n.id.startsWith("posten:") || n.id.startsWith("beitraege:") || n.id.startsWith("defizit:") || n.id.startsWith("ruecklage:")) {
        onSelect(n.id);
      } else if (n.kind === "epl") {
        onFocus([n.id]);
        onSelect(n.id);
      }
      return;
    }
    if (n.kind === "topf" || n.kind === "rest" || n.kind === "empfaenger" || n.kind === "abzug") { onFocus([]); onSelect(null); return; }
    if (n.kind === "revenue" || n.kind === "kredit" || n.kind === "minderausgabe") { onSelect(n.kind === "revenue" ? n.id : null); return; }
    onFocus(pathFor(n));
    onSelect(n.id);
  }
  function shortLabel(n: LNode): string {
    const perColumn = width / Math.max(1, layout.columns);
    const max = Math.max(10, Math.min(width < 720 ? 18 : 30, Math.floor(perColumn / 6.5)));
    return n.label.length > max ? n.label.slice(0, max - 1) + "…" : n.label;
  }
  /** Beschriftung nur, wenn der Knoten groß genug ist; bei vielen Spalten nur für nicht verblasste Knoten. */
  function showLabel(n: LNode): boolean {
    if (n.id === selected || focus.includes(n.id)) return true;
    if (layout.columns >= 5 && n.dim) return false;
    return nodeHeight(n) >= 9;
  }
  const columnTitles = $derived(gesamtModus ? (topf === "gesamt" ? ["Woher", "Bund", "Kassen · Ministerien", "Wofür"] : ["Woher", "Kasse", "Wofür"]) : ["Woher", "Topf", "Ministerium", "Kapitel", "Titel", "Empfänger"]);
</script>

<div class="fluss" bind:clientWidth={width}>
  <div class="cols" style="grid-template-columns: repeat({layout.columns}, 1fr)">
    {#each columnTitles.slice(0, layout.columns) as t}<span>{t}</span>{/each}
  </div>
  <svg bind:this={svgEl} viewBox="0 0 {width} {height}" {width} {height} role="img" aria-label="Geldfluss des Bundeshaushalts {data.jahr}" class:zoomed ondblclick={resetZoom}>
    <g transform={transform.toString()}>
    <g class="links">
      {#each layout.links as l, i (i)}
        {@const link = l as LLink}
        <path
          d={linkPath(link) ?? ""}
          stroke={colorFor(link.colorKey)}
          stroke-width={Math.max(1, link.width ?? 1)}
          stroke-dasharray={link.colorKey === "kredit" || link.colorKey === "minder" ? "6 4" : undefined}
          opacity={link.dim ? 0.18 : 0.55}
          fill="none"
        >
          <title>{fmtEuro(link.value)}</title>
        </path>
      {/each}
    </g>
    <g class="nodes">
      {#each layout.nodes as n (n.id)}
        {@const node = n as LNode}
        <g
          class="node"
          class:dim={node.dim}
          class:clickable={node.kind !== "empfaenger"}
          role="button"
          tabindex="0"
          onclick={() => click(node)}
          onkeydown={(e) => (e.key === "Enter" || e.key === " ") && click(node)}
        >
          <rect
            x={node.x0} y={node.y0} width={(node.x1 ?? 0) - (node.x0 ?? 0)} height={nodeHeight(node)}
            fill={colorFor(node.colorKey)}
            stroke={node.id === selected ? CHANGED_STROKE : node.changed ? CHANGED_STROKE : "none"}
            stroke-width={node.id === selected ? 3 : 2}
            stroke-dasharray={node.changed && node.id !== selected ? "4 2" : undefined}
            fill-opacity={node.kind === "kredit" || node.kind === "minderausgabe" ? 0.25 : 1}
          />
          {#if node.kind === "kredit" || node.kind === "minderausgabe"}
            <rect x={node.x0} y={node.y0} width={(node.x1 ?? 0) - (node.x0 ?? 0)} height={nodeHeight(node)} fill="none" stroke={colorFor(node.colorKey)} stroke-dasharray="4 2" />
          {/if}
          {#if ghostHeight(node) > 0}
            <rect
              x={node.x0} y={(node.y0 ?? 0) - ghostHeight(node) - 2}
              width={(node.x1 ?? 0) - (node.x0 ?? 0)} height={ghostHeight(node)}
              fill="none" stroke={GHOST_STROKE} stroke-dasharray="3 2"
            />
          {/if}
          {#if showLabel(node) || transform.k >= 2.5}
            <text x={labelX(node)} y={((node.y0 ?? 0) + (node.y1 ?? 0)) / 2} dy={nodeHeight(node) >= 22 ? "-0.2em" : "0.35em"} text-anchor={labelAnchor(node)} class="label" class:strong={node.id === selected || focus.includes(node.id)} style="font-size:{11 * invK}px">
              {shortLabel(node)}
              {#if nodeHeight(node) >= 22}
                <tspan class="amount" x={labelX(node)} dy="1.15em">
                  {fmtEuro(node.netEffective)}{#if node.changed && node.netOriginal !== node.netEffective} · war {fmtEuro(node.netOriginal)}{/if}
                </tspan>
              {/if}
            </text>
          {/if}
          <title>{node.label}: {fmtEuro(node.netEffective)}{node.changed ? ` (Original ${fmtEuro(node.netOriginal)})` : ""}</title>
        </g>
      {/each}
    </g>
    </g>
  </svg>
  {#if zoomed}
    <button class="zoomreset" onclick={resetZoom} title="Zoom zurücksetzen (auch Doppelklick)">Zoom {Math.round(transform.k * 100)} % · zurücksetzen</button>
  {/if}
  <div class="legend">
    <span><i style="background:{colorFor('steuern')}"></i> Steuern</span>
    <span><i style="background:{colorFor('sonstige')}"></i> Sonstige Einnahmen</span>
    <span><i style="background:{colorFor('abzug')}"></i> Weiterleitung an EU und Länder (von den Steuern abgezogen)</span>
    <span><i style="background:{colorFor('minder')}"></i> Globale Mindereinnahmen</span>
    <span><i class="dash" style="border-color:{colorFor('kredit')}"></i> Neue Schulden</span>
    <span><i class="dash" style="border-color:{CHANGED_STROKE}"></i> von dir verändert</span>
    <span><i class="dash" style="border-color:{GHOST_STROKE}"></i> gestrichener Betrag</span>
    {#if sdata.minderausgaben !== 0 || sdata.absetzungen !== 0}
      <span class="minder">In der Summe enthalten, nicht als Band darstellbar:{#if sdata.minderausgaben !== 0} Globale Minderausgaben {fmtEuro(sdata.minderausgaben)} (Einsparvorgaben ohne eigenen Titel, Gruppe 97){/if}{#if sdata.minderausgaben !== 0 && sdata.absetzungen !== 0},{/if}{#if sdata.absetzungen !== 0} sonstige Absetzungen {fmtEuro(sdata.absetzungen)} (z. B. Disagio){/if}.</span>
    {/if}
    {#if gesamtModus && topf !== "gesamt"}
      <button class="reset" onclick={() => onTopf?.("gesamt")}>‹ Gesamtfluss</button>
    {:else if !gesamtModus && sozialkassen}
      <button class="reset" onclick={() => onTopf?.("gesamt")}>‹ Gesamtfluss mit Sozialkassen</button>
    {/if}
    {#if focus.length}
      <button class="reset" onclick={() => { onFocus([]); onSelect(null); }}>‹ Alle Ministerien</button>
    {/if}
    {#if gesamtModus}
      <span class="minder">Beiträge lila, Steuern blau. Die blauen Bänder vom Bund zu den Kassen sind die Bundesmittel (Zuschüsse, Beiträge für Kindererziehung, Erstattungen). Klick auf eine Kasse folgt ihr, Klick auf ein Ministerium öffnet den Bundeshaushalt.</span>
    {/if}
  </div>
</div>

<style>
  .fluss { width: 100%; position: relative; }
  .cols { display: grid; font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 2px; }
  .cols span:last-child { text-align: right; }
  svg { display: block; width: 100%; height: auto; overflow: hidden; cursor: grab; touch-action: none; }
  svg.zoomed { cursor: move; }
  .zoomreset { position: absolute; right: 10px; top: 28px; font-size: 11px; background: var(--header); color: #fff; border: 0; border-radius: 6px; padding: 4px 8px; cursor: pointer; opacity: .9; }

  .node.clickable { cursor: pointer; }
  .node.dim { opacity: .45; }
  .label { font-size: 11px; fill: var(--fg); cursor: pointer; }
  .label.strong { font-weight: 700; }
  .amount { font-size: 10px; fill: var(--muted); }
  .legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: var(--muted); margin-top: 8px; align-items: center; }
  .legend i { display: inline-block; width: 12px; height: 8px; border-radius: 2px; vertical-align: middle; margin-right: 4px; }
  .legend i.dash { background: none; border: 2px dashed; height: 6px; width: 10px; }
  .legend .minder { color: var(--fg); }
  .reset { margin-left: auto; font-size: 11px; background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; cursor: pointer; color: var(--fg); }
</style>
