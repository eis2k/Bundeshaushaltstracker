<script lang="ts">
  import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, type SimulationLinkDatum, type SimulationNodeDatum } from "d3-force";
  import { select } from "d3-selection";
  import { zoom, zoomIdentity, type ZoomTransform } from "d3-zoom";
  import { KNOTEN_LABELS, kantenStil, legende, type NetzKante, type NetzKnoten, type Umfeld } from "../model/netz";
  import type { AppState } from "../state.svelte";

  let { app, umfeld }: { app: AppState; umfeld: Umfeld } = $props();

  type N = NetzKnoten & SimulationNodeDatum;
  type L = SimulationLinkDatum<N> & { kante: NetzKante };

  let width = $state(900);
  const height = 560;
  let nodes = $state<N[]>([]);
  let links = $state<L[]>([]);
  let transform = $state<ZoomTransform>(zoomIdentity);
  let svgEl: SVGSVGElement | undefined = $state();
  let hover = $state<{ x: number; y: number; text: string } | null>(null);

  $effect(() => {
    const byId = new Map<string, N>();
    const ns: N[] = umfeld.knoten.map((k) => ({ ...k }));
    for (const n of ns) byId.set(n.id, n);
    const ls: L[] = umfeld.kanten.filter((k) => byId.has(k.von) && byId.has(k.nach)).map((k) => ({ source: byId.get(k.von)!, target: byId.get(k.nach)!, kante: k }));
    const start = byId.get(umfeld.start);
    if (start) { start.fx = width / 2; start.fy = height / 2; }
    const sim = forceSimulation(ns)
      .force("link", forceLink<N, L>(ls).id((d) => d.id).distance((l) => (l.kante.art === "geld" ? 110 : 80)).strength(0.6))
      .force("charge", forceManyBody().strength(-260))
      .force("collide", forceCollide(26))
      .force("center", forceCenter(width / 2, height / 2))
      .stop();
    for (let i = 0; i < 220; i++) sim.tick();
    nodes = ns;
    links = ls;
  });

  $effect(() => {
    if (!svgEl) return;
    const z = zoom<SVGSVGElement, unknown>().scaleExtent([0.4, 4]).on("zoom", (e) => (transform = e.transform));
    select(svgEl).call(z);
    return () => { select(svgEl!).on(".zoom", null); };
  });

  function form(n: N): string {
    const r = n.id === umfeld.start ? 14 : 10;
    const x = n.x ?? 0, y = n.y ?? 0;
    if (n.art === "organisation") return `M${x - r},${y - r}h${2 * r}v${2 * r}h${-2 * r}z`;
    if (n.art === "ministerium") return `M${x},${y - r}L${x + r},${y}L${x},${y + r}L${x - r},${y}z`;
    if (n.art === "partei") return `M${x + r},${y}L${x + r / 2},${y + r * 0.87}L${x - r / 2},${y + r * 0.87}L${x - r},${y}L${x - r / 2},${y - r * 0.87}L${x + r / 2},${y - r * 0.87}z`;
    return `M${x},${y}m${-r},0a${r},${r} 0 1,0 ${2 * r},0a${r},${r} 0 1,0 ${-2 * r},0`;
  }
  function klick(n: N) {
    if (!n.seite) return;
    if (n.art === "person") void app.openAkte(n.id.slice(2));
    else if (n.art === "organisation") void app.openEmpfaenger(n.id.slice(2));
    else if (n.art === "ministerium") { app.setTopf("bund"); app.setFocus([n.id.slice(2)]); app.setView("fluss"); }
  }
  function zentrum(n: N) { void app.openNetz(n.id); }
  const startKnoten = $derived(umfeld.knoten.find((k) => k.id === umfeld.start));
  const invK = $derived(1 / transform.k);
</script>

<div class="netz" bind:clientWidth={width}>
  <div class="kopf">
    <button class="back" onclick={() => void app.closeNetz()}>‹ zurück</button>
    <h2>Umfeld: {startKnoten?.label ?? umfeld.start}</h2>
    <span class="muted">{umfeld.knoten.length} Knoten, {umfeld.kanten.length} Kanten, zwei Schritte{#if umfeld.weitere} · {umfeld.weitere} weitere Knoten nicht gezeigt (die größten nach Geld zuerst){/if}</span>
  </div>
  <svg bind:this={svgEl} {width} {height} role="img" aria-label="Netz der Geldflüsse, Posten und Spenden rund um {startKnoten?.label ?? umfeld.start}">
    <g transform={transform.toString()}>
      {#each links as l}
        {@const s = l.source as N}
        {@const t = l.target as N}
        {@const st = kantenStil(l.kante.art)}
        <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="var(--header)" stroke-opacity="0.45" stroke-width={st.width} stroke-dasharray={st.dasharray || undefined}
              onmouseenter={(e) => (hover = { x: e.clientX, y: e.clientY, text: `${l.kante.text} · ${l.kante.quelle.kurz}${l.kante.quelle.etikett ? " · " + l.kante.quelle.etikett : ""}${l.kante.stand ? " · Stand " + l.kante.stand : ""}` })}
              onmouseleave={() => (hover = null)} role="presentation" />
      {/each}
      {#each nodes as n (n.id)}
        <g class="knoten" class:start={n.id === umfeld.start} class:klickbar={!!n.seite} role="button" tabindex="0"
           onclick={() => klick(n)} ondblclick={() => zentrum(n)} onkeydown={(e) => e.key === "Enter" && klick(n)}
           onmouseenter={(e) => (hover = { x: e.clientX, y: e.clientY, text: `${KNOTEN_LABELS[n.art] ?? n.art}: ${n.label}${n.seite ? "" : " (keine freigeschaltete Akte)"}` })} onmouseleave={() => (hover = null)}>
          <path d={form(n)} fill={n.seite ? "var(--panel)" : "var(--bg)"} stroke="var(--header)" stroke-width={n.id === umfeld.start ? 2.5 : 1.5} />
          <text x={n.x} y={(n.y ?? 0) + (n.id === umfeld.start ? 26 : 22)} text-anchor="middle" style="font-size:{10 * invK}px">{n.label.length > 28 ? n.label.slice(0, 27) + "…" : n.label}</text>
        </g>
      {/each}
    </g>
  </svg>
  {#if hover}<div class="tip" style="left:{hover.x + 12}px;top:{hover.y + 12}px">{hover.text}</div>{/if}
  <div class="legende">
    {#each legende() as l}
      {@const st = kantenStil(l.art)}
      <span><svg width="34" height="8"><line x1="2" y1="4" x2="32" y2="4" stroke="var(--header)" stroke-width={st.width} stroke-dasharray={st.dasharray || undefined} /></svg> {l.label}</span>
    {/each}
    <span>Kreis Person · Quadrat Organisation · Raute Ministerium · Sechseck Partei · hell: keine freigeschaltete Akte</span>
    <span>Klick öffnet Akte oder Seite, Doppelklick macht den Knoten zur Mitte, Mausrad zoomt. Jede Kante trägt Quelle und Stand (Mauszeiger). Keine Wertung: Das Netz zeigt belegte Beziehungen, nicht mehr.</span>
  </div>
</div>

<style>
  .netz { font-size: 12px; position: relative; }
  .kopf { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; margin-bottom: 6px; }
  .back { background: none; border: 0; color: var(--header); cursor: pointer; font: inherit; font-size: 12px; padding: 0; }
  h2 { margin: 0; font-size: 15px; }
  svg { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; width: 100%; height: 560px; touch-action: none; }
  .knoten text { fill: var(--fg); pointer-events: none; }
  .knoten.klickbar { cursor: pointer; }
  .knoten.start path { fill: var(--accent); }
  .tip { position: fixed; z-index: 10; max-width: 360px; background: var(--header); color: #fff; font-size: 11px; padding: 6px 8px; border-radius: 6px; pointer-events: none; }
  .legende { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 6px; color: var(--muted); font-size: 11px; }
  .legende span { display: inline-flex; align-items: center; gap: 4px; }
  .muted { color: var(--muted); }
</style>
