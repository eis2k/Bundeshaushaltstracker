<script lang="ts">
  import { onMount } from "svelte";
  import { select } from "d3-selection";
  import { zoom as d3zoom, zoomIdentity, type ZoomTransform } from "d3-zoom";
  import { sankey as d3sankey, sankeyLinkHorizontal } from "d3-sankey";
  import type { SankeyLink, SankeyNode } from "d3-sankey";
  import { fmtEuro } from "../model/format";
  import type { NodeId, Scenario, YearData } from "../model/types";
  import { CHANGED_STROKE, GHOST_STROKE, colorFor } from "./colors";
  import { EMPFAENGER_UNBEKANNT, buildSankey, type Modell, type SLink, type SNode } from "./sankeyData";
  import { buildGesamtSankey } from "./sankeyGesamt";
  import type { SozialkassenYear } from "../model/toepfe";
  import type { TopfId } from "../model/share";
  import { Coins, GraduationCap, HeartHandshake, Landmark, List, Share2, Shield, Stethoscope, TrainFront, Waypoints } from "lucide-svelte";
  import type { IconComp } from "../ui/icons";
  import Avatar from "../ui/Avatar.svelte";
  import type { EmpfaengerSpalteEintrag } from "./sankeyData";

  interface Props {
    data: YearData;
    scenario: Scenario;
    factors: Record<NodeId, number>;
    focus: NodeId[];
    selected: NodeId | null;
    topf?: TopfId;
    sozialkassen?: SozialkassenYear | null;
    modelle?: Modell[];
    empfaengerByTitel?: Record<string, { id: string; name: string }>;
    /** Vierte Spalte bei Fokus auf einen Einzelplan: Empfänger mit Seite (Spec §4.11). */
    empfaengerSpalte?: EmpfaengerSpalteEintrag[];
    empfaengerJahr?: number | null;
    onEmpfaenger?: (id: string) => void;
    /** Umschalter „Netzwerk“: Umfeld des fokussierten Einzelplans. */
    onNetz?: (epl: string) => void;
    onFocus: (path: NodeId[]) => void;
    onSelect: (id: NodeId | null) => void;
    onTopf?: (topf: TopfId) => void;
  }
  let { data, scenario, factors, focus, selected, topf = "bund", sozialkassen = null, modelle = [], empfaengerByTitel = {}, empfaengerSpalte = [], empfaengerJahr = null, onFocus, onSelect, onTopf, onEmpfaenger, onNetz }: Props = $props();
  /** Sankey | Netzwerk | Liste (Spec §4.11); Netzwerk springt ins Umfeld, Liste zeigt die Knoten der tiefsten Spalte als Tabelle. */
  let modus = $state<"sankey" | "liste">("sankey");
  const ICONS: Record<string, IconComp> = { "08": Coins, "14": Shield, "11": HeartHandshake, "30": GraduationCap, "12": TrainFront, "15": Stethoscope };
  function iconFor(epl: string): IconComp { return ICONS[epl] ?? Landmark; }
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
  const mitEmpfaengerSpalte = $derived(!gesamtModus && focus.length === 1 && empfaengerSpalte.some((e) => e.wert > 0));
  const height = $derived((width < 720 ? 560 : 440) + Math.max(0, columnsNeeded - 4) * 80 + (gesamtModus ? 200 : 0));
  const maxPerColumn = $derived(width < 720 ? 5 : columnsNeeded >= 6 ? 6 : 8);

  const sdata = $derived(gesamtModus
    ? buildGesamtSankey(data, sozialkassen!, scenario, factors, { maxPerColumn, maxRevenue: width < 720 ? 4 : 6, only: topf === "gesamt" ? undefined : topf, modelle })
    : buildSankey(data, scenario, factors, focus, { maxPerColumn, maxRevenue: width < 720 ? 5 : 7, modelle, empfaengerByTitel }, empfaengerSpalte));

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
  function labelY(n: LNode): number {
    return ((n.y0 ?? 0) + (n.y1 ?? 0)) / 2;
  }
  function twoLines(n: LNode): boolean {
    return nodeHeight(n) >= 22 || (n.kind === "modell" && n.id === selected);
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
    if (n.kind === "modell") { onSelect(n.id); return; }
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
    if (n.kind === "empfaenger" && n.id !== EMPFAENGER_UNBEKANNT) { onEmpfaenger?.(n.id.slice("empfaenger:".length)); return; }
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
  const columnTitles = $derived(gesamtModus ? (topf === "gesamt" ? ["Woher", "Bund", "Kassen · Ministerien", "Wofür"] : ["Woher", "Kasse", "Wofür"]) : mitEmpfaengerSpalte ? ["Woher", "Topf", "Ministerium", `Kapitel · Empfänger${empfaengerJahr ? ` (Soll ${empfaengerJahr})` : ""}`] : ["Woher", "Topf", "Ministerium", "Kapitel", "Titel", "Empfänger"]);
  /** Anteil eines Knotens am Topf, für die Beschriftung der Ministerien (wie im Entwurf „(21,3 %)“). */
  const topfWert = $derived(sdata.nodes.find((n) => n.kind === "topf")?.effective ?? 0);
  function anteil(n: SNode): string { return topfWert > 0 && n.kind === "epl" ? ` (${(Math.round((n.effective / topfWert) * 1000) / 10).toLocaleString("de-DE")} %)` : ""; }
  /** Knoten der tiefsten Spalte für die Listenansicht. */
  const listenKnoten = $derived.by(() => {
    const tiefste = Math.max(...sdata.nodes.map((n) => n.column));
    const spalte = sdata.nodes.filter((n) => n.column === tiefste && n.kind !== "empfaenger");
    const quelle = spalte.length ? spalte : sdata.nodes.filter((n) => n.column === tiefste);
    return [...quelle].sort((a, b) => b.effective - a.effective);
  });
  const listenSumme = $derived(listenKnoten.reduce((s, n) => s + Math.max(0, n.netEffective), 0));
  const empfaengerKnoten = $derived(mitEmpfaengerSpalte ? sdata.nodes.filter((n) => n.kind === "empfaenger" && n.column === 3) : []);
  const TILE = 18;
</script>

<div class="fluss" bind:clientWidth={width}>
  {#if !gesamtModus}
    <div class="umschalter" role="tablist" aria-label="Darstellung">
      <button role="tab" aria-selected={modus === "sankey"} class:on={modus === "sankey"} onclick={() => (modus = "sankey")}><Waypoints size={13} /> Sankey</button>
      <button role="tab" aria-selected="false" disabled={!focus.length || !onNetz} title={focus.length ? "Umfeld des fokussierten Ministeriums" : "Erst ein Ministerium wählen"} onclick={() => onNetz?.(focus[0])}><Share2 size={13} /> Netzwerk</button>
      <button role="tab" aria-selected={modus === "liste"} class:on={modus === "liste"} onclick={() => (modus = "liste")}><List size={13} /> Liste</button>
    </div>
  {/if}
  {#if modus === "liste" && !gesamtModus}
    <table class="liste">
      <thead><tr><th>{columnTitles[Math.min(columnTitles.length - 1, layout.columns - 1)]}</th><th class="num">Betrag</th><th class="num">Anteil</th></tr></thead>
      <tbody>
        {#each listenKnoten as n (n.id)}
          <tr class:dim={n.dim}><td><button class="zeile" onclick={() => click(n)}>{#if n.kind === "epl"}{@const Icon = iconFor(n.id)}<span class="kachel" style="background:{colorFor(n.colorKey)}22;color:{colorFor(n.colorKey)}"><Icon size={14} /></span>{/if}{n.label}</button></td><td class="num tabular">{fmtEuro(n.netEffective)}</td><td class="num tabular">{listenSumme > 0 ? `${(Math.round((Math.max(0, n.netEffective) / listenSumme) * 1000) / 10).toLocaleString("de-DE")} %` : "–"}</td></tr>
        {/each}
      </tbody>
    </table>
    {#if empfaengerKnoten.length}
      <h4>Empfänger mit Seite{empfaengerJahr ? ` (Soll ${empfaengerJahr})` : ""}</h4>
      <ul class="empf">
        {#each empfaengerKnoten as n (n.id)}<li><Avatar name={n.label} art="organisation" size={24} /><button class="zeile" onclick={() => click(n)}>{n.label}</button><b class="tabular">{fmtEuro(n.effective)}</b></li>{/each}
      </ul>
    {/if}
  {:else}
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
          stroke-dasharray={link.colorKey === "kredit" || link.colorKey === "minder" || link.colorKey === "modell" ? "6 4" : undefined}
          opacity={link.dim ? 0.18 : 0.55}
          fill="none"
        >
          <title>{fmtEuro(link.value)}{link.quelle === "lobbyregister" ? " (Lobbyregister, Untergrenze – Eigenangabe)" : link.quelle === "haushalt" ? " (Haushalts-Soll aus Titeln mit genanntem Empfänger)" : ""}</title>
        </path>
      {/each}
    </g>
    <g class="nodes">
      {#each layout.nodes as n (n.id)}
        {@const node = n as LNode}
        <g
          class="node"
          class:dim={node.dim}
          class:clickable={node.id !== EMPFAENGER_UNBEKANNT}
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
            fill-opacity={node.kind === "kredit" || node.kind === "minderausgabe" || node.kind === "modell" ? 0.25 : 1}
          />
          {#if node.kind === "kredit" || node.kind === "minderausgabe" || node.kind === "modell"}
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
            {#if node.kind === "epl" && nodeHeight(node) >= 22}
              {@const Icon = iconFor(node.id)}
              {@const tx = labelAnchor(node) === "start" ? labelX(node) : labelX(node) - TILE}
              <rect x={tx} y={labelY(node) - TILE - 2} width={TILE} height={TILE} rx="5" fill={colorFor(node.colorKey)} fill-opacity="0.15" />
              <svg x={tx + 2} y={labelY(node) - TILE} width={TILE - 4} height={TILE - 4} style="color:{colorFor(node.colorKey)}"><Icon size={TILE - 4} /></svg>
            {:else if node.kind === "empfaenger" && node.id !== EMPFAENGER_UNBEKANNT && nodeHeight(node) >= 14}
              <foreignObject x={labelAnchor(node) === "start" ? labelX(node) : labelX(node) - 22} y={labelY(node) - 11} width="22" height="22"><Avatar name={node.label} art="organisation" size={20} /></foreignObject>
            {/if}
            <text x={labelX(node) + ((node.kind === "epl" && nodeHeight(node) >= 22) || (node.kind === "empfaenger" && node.id !== EMPFAENGER_UNBEKANNT && nodeHeight(node) >= 14) ? (labelAnchor(node) === "start" ? 24 : -24) : 0)} y={labelY(node)} dy={twoLines(node) ? "-0.2em" : "0.35em"} text-anchor={labelAnchor(node)} class="label" class:strong={node.id === selected || focus.includes(node.id)} style="font-size:{11 * invK}px">
              {shortLabel(node)}
              {#if node.kind === "modell" && twoLines(node)}
                <tspan class="amount" x={labelX(node)} dy="1.15em" style="font-size:{10 * invK}px">
                  Mehreinnahmen {fmtEuro(node.netEffective)} · Bund {fmtEuro(node.effective)}
                </tspan>
              {:else if nodeHeight(node) >= 22}
                <tspan class="amount" x={labelX(node) + (node.kind === "epl" ? (labelAnchor(node) === "start" ? 24 : -24) : node.kind === "empfaenger" && node.id !== EMPFAENGER_UNBEKANNT ? (labelAnchor(node) === "start" ? 24 : -24) : 0)} dy="1.15em" style="font-size:{10 * invK}px">
                  {fmtEuro(node.netEffective)}{anteil(node)}{#if node.changed && node.netOriginal !== node.netEffective} · war {fmtEuro(node.netOriginal)}{/if}
                </tspan>
              {/if}
            </text>
          {/if}
          <title>{node.kind === "modell" ? `${node.label}: Mehreinnahmen ${fmtEuro(node.netEffective)}, davon Bund ${fmtEuro(node.effective)} (nominal zum Basisjahr der Quelle)` : `${node.label}: ${fmtEuro(node.netEffective)}${node.changed ? ` (Original ${fmtEuro(node.netOriginal)})` : ""}`}</title>
        </g>
      {/each}
    </g>
    </g>
  </svg>
  {/if}
  {#if zoomed && modus === "sankey"}
    <button class="zoomreset" onclick={resetZoom} title="Zoom zurücksetzen (auch Doppelklick)">Zoom {Math.round(transform.k * 100)} % · zurücksetzen</button>
  {/if}
  <div class="legend">
    <span><i style="background:{colorFor('steuern')}"></i> Steuern</span>
    <span><i style="background:{colorFor('sonstige')}"></i> Sonstige Einnahmen</span>
    <span><i style="background:{colorFor('abzug')}"></i> Weiterleitung an EU und Länder (von den Steuern abgezogen)</span>
    <span><i style="background:{colorFor('minder')}"></i> Globale Mindereinnahmen</span>
    <span><i class="dash" style="border-color:{colorFor('kredit')}"></i> Neue Schulden</span>
    {#if modelle.length}<span><i class="dash" style="border-color:{colorFor('modell')}"></i> Steuer-Modell (Kasten = Mehreinnahmen gesamt, Band = Anteil des Bundes, leerer Rest = Länder und Gemeinden; nominal zum Basisjahr der Quelle, nicht auf das Haushaltsjahr umgerechnet und nicht inflationsbereinigt)</span>{/if}
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
    {#if mitEmpfaengerSpalte}
      <span class="minder">Empfänger-Spalte: die größten Empfänger mit Seite aus diesem Einzelplan, Betrag je Quelle (Haushalts-Soll oder Lobbyregister-Untergrenze), nicht addiert{#if empfaengerSpalte.length > empfaengerKnoten.length} · weitere Empfänger in der Empfängerliste{/if}.</span>
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
  .zoomreset { position: absolute; right: 10px; top: 28px; font-size: 11px; background: var(--nav-on); color: var(--nav-on-fg); border: 0; border-radius: 6px; padding: 4px 8px; cursor: pointer; opacity: .9; }

  .node.clickable { cursor: pointer; }
  .node.dim { opacity: .45; }
  .label { font-size: 11px; fill: var(--fg); cursor: pointer; }
  .label.strong { font-weight: 700; }
  .amount { font-size: 10px; fill: var(--muted); }
  .legend { display: flex; flex-wrap: wrap; gap: 12px; font-size: 11px; color: var(--muted); margin-top: 8px; align-items: center; }
  .legend i { display: inline-block; width: 12px; height: 8px; border-radius: 2px; vertical-align: middle; margin-right: 4px; }
  .legend i.dash { background: none; border: 2px dashed; height: 6px; width: 10px; }
  .legend .minder { color: var(--fg); }
  .umschalter { position: absolute; right: 0; top: -34px; display: inline-flex; gap: 2px; background: var(--nav-bg); border-radius: 10px; padding: 3px; }
  .umschalter button { display: inline-flex; align-items: center; gap: 4px; background: none; border: 0; color: var(--header); padding: 4px 10px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; opacity: .75; }
  .umschalter button.on { background: var(--nav-on); color: var(--nav-on-fg); opacity: 1; }
  .umschalter button:disabled { opacity: .35; cursor: default; }
  table.liste { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 4px; }
  table.liste th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 6px 4px; }
  table.liste td { padding: 6px 4px; border-top: 1px solid var(--border); }
  table.liste tr.dim { opacity: .5; }
  .num { text-align: right; }
  .zeile { background: none; border: 0; padding: 0; font: inherit; color: var(--header); cursor: pointer; display: inline-flex; align-items: center; gap: 8px; text-align: left; }
  .zeile:hover { text-decoration: underline; }
  .kachel { width: 24px; height: 24px; border-radius: 7px; display: inline-flex; align-items: center; justify-content: center; }
  h4 { margin: 14px 0 6px; font-size: 12px; color: var(--header); }
  .empf { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
  .empf li { display: grid; grid-template-columns: 24px 1fr auto; gap: 8px; align-items: center; }
  .empf b { color: var(--header); }
  .reset { margin-left: auto; font-size: 11px; background: var(--panel); border: 1px solid var(--border); border-radius: 6px; padding: 4px 8px; cursor: pointer; color: var(--fg); }
</style>
