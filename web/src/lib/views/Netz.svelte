<script lang="ts">
  import { forceCenter, forceCollide, forceLink, forceManyBody, forceSimulation, type SimulationLinkDatum, type SimulationNodeDatum } from "d3-force";
  import { select } from "d3-selection";
  import { zoom, zoomIdentity, type ZoomTransform } from "d3-zoom";
  import { fmtEuro } from "../model/format";
  import { KNOTEN_LABELS, kanteBeschreibung, kantenStil, legende, type NetzKante, type NetzKnoten, type Umfeld } from "../model/netz";
  import type { AppState } from "../state.svelte";

  /** kompakt: eingebettete Vorschau (Spec §4.12) ohne Kopf, Belegpanel und Legende; Knotenklick öffnet die Seite, „Umfeld zeigen“ die volle Ansicht. */
  let { app, umfeld, kompakt = false, onVoll }: { app: AppState; umfeld: Umfeld; kompakt?: boolean; onVoll?: () => void } = $props();

  type N = NetzKnoten & SimulationNodeDatum;
  type L = SimulationLinkDatum<N> & { kante: NetzKante };

  let width = $state(900);
  const height = $derived(kompakt ? 300 : 560);
  let nodes = $state<N[]>([]);
  let links = $state<L[]>([]);
  let transform = $state<ZoomTransform>(zoomIdentity);
  let svgEl: SVGSVGElement | undefined = $state();
  let hover = $state<{ x: number; y: number; text: string } | null>(null);
  /** Belegpanel: gewählte Kante (Klick oder Enter). */
  let gewaehlt = $state<NetzKante | null>(null);
  const knotenById = $derived(Object.fromEntries(umfeld.knoten.map((k) => [k.id, k])) as Record<string, NetzKnoten>);
  const beleg = $derived(gewaehlt ? kanteBeschreibung(gewaehlt, knotenById) : null);
  $effect(() => { umfeld.start; gewaehlt = null; });

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
    // kompakt: Mausrad scrollt die Seite, Zoom nur mit Strg (Spec §4.12)
    const z = zoom<SVGSVGElement, unknown>().scaleExtent([0.4, 4]).filter((e: Event) => !kompakt || e.type !== "wheel" || (e as WheelEvent).ctrlKey).on("zoom", (e) => (transform = e.transform));
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
    else if (n.art === "ministerium") app.zeigeImFluss([n.id.slice(2)]);
  }
  function zentrum(n: N) { void app.openNetz(n.id); }
  const startKnoten = $derived(umfeld.knoten.find((k) => k.id === umfeld.start));
  const invK = $derived(1 / transform.k);
</script>

<div class="netz" class:kompakt bind:clientWidth={width}>
  {#if !kompakt}
  <div class="kopf">
    <button class="back" onclick={() => void app.closeNetz()}>‹ zurück</button>
    <h2>Umfeld: {startKnoten?.label ?? umfeld.start}</h2>
    <span class="muted">{umfeld.knoten.length} Knoten, {umfeld.kanten.length} Kanten, zwei Schritte{#if umfeld.weitere} · {umfeld.weitere} weitere Knoten nicht gezeigt (die größten nach Geld zuerst){/if}</span>
  </div>
  {/if}
  <svg bind:this={svgEl} {width} {height} role="group" aria-label="Netz der Geldflüsse, Posten und Spenden rund um {startKnoten?.label ?? umfeld.start}">
    <g transform={transform.toString()}>
      {#each links as l}
        {@const s = l.source as N}
        {@const t = l.target as N}
        {@const st = kantenStil(l.kante.art)}
        {@const aktiv = gewaehlt === l.kante}
        <line x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke={aktiv ? "var(--accent)" : "var(--header)"} stroke-opacity={aktiv ? 1 : 0.45} stroke-width={aktiv ? st.width + 1.5 : st.width} stroke-dasharray={st.dasharray || undefined} role="presentation" />
        <!-- breite, unsichtbare Trefferfläche: klickbar und per Tastatur erreichbar -->
        <line class="treffer" x1={s.x} y1={s.y} x2={t.x} y2={t.y} stroke="transparent" stroke-width="12" role="button" tabindex="0" aria-label={l.kante.text}
              onclick={() => { if (!kompakt) gewaehlt = aktiv ? null : l.kante; }} onkeydown={(e) => { if (!kompakt && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); gewaehlt = aktiv ? null : l.kante; } }}
              onmouseenter={(e) => (hover = { x: e.clientX, y: e.clientY, text: `${l.kante.text} · ${l.kante.quelle.kurz}${l.kante.quelle.etikett ? " · " + l.kante.quelle.etikett : ""}${l.kante.stand ? " · Stand " + l.kante.stand : ""}` })}
              onmouseleave={() => (hover = null)} />
      {/each}
      {#each nodes as n (n.id)}
        <g class="knoten" class:start={n.id === umfeld.start} class:klickbar={!!n.seite} {...(n.seite ? { role: "button", tabindex: 0 } : {})}
           onclick={() => klick(n)} ondblclick={() => zentrum(n)} onkeydown={(e) => e.key === "Enter" && klick(n)}
           onmouseenter={(e) => (hover = { x: e.clientX, y: e.clientY, text: `${KNOTEN_LABELS[n.art] ?? n.art}: ${n.label}${n.art === "person" && !n.seite ? " (keine freigeschaltete Akte)" : ""}` })} onmouseleave={() => (hover = null)}>
          <path d={form(n)} fill={n.art === "person" && !n.seite ? "var(--bg)" : "var(--panel)"} stroke="var(--header)" stroke-width={n.id === umfeld.start ? 2.5 : 1.5} />
          <text x={n.x} y={(n.y ?? 0) + (n.id === umfeld.start ? 26 : 22)} text-anchor="middle" style="font-size:{10 * invK}px">{n.label.length > 28 ? n.label.slice(0, 27) + "…" : n.label}</text>
        </g>
      {/each}
    </g>
  </svg>
  {#if hover}<div class="tip" style="left:{hover.x + 12}px;top:{hover.y + 12}px">{hover.text}</div>{/if}
  {#if beleg && !kompakt}
    <aside class="beleg" aria-label="Beleg der gewählten Kante">
      <div class="beleg-kopf"><span class="tag">{beleg.art}</span><button class="schliessen" onclick={() => (gewaehlt = null)} aria-label="Belegpanel schließen">×</button></div>
      <p class="satz">{beleg.titel}</p>
      {#if beleg.betrag != null}<p><b class="tabular">{fmtEuro(beleg.betrag)}</b> <span class="muted">{beleg.art === "Geld" ? "Untergrenze bzw. Soll laut Quelle" : ""}</span></p>{/if}
      <p class="muted">Quelle: {#if beleg.quelle.url}<a href={beleg.quelle.url} target="_blank" rel="noopener">{beleg.quelle.kurz}</a>{:else}{beleg.quelle.kurz}{/if}{#if beleg.quelle.etikett} · {beleg.quelle.etikett}{/if}{#if beleg.stand} · Stand {beleg.stand}{/if}</p>
      <p class="knoten-links">
        {#if beleg.von}<button class="link" disabled={!beleg.von.seite} onclick={() => beleg?.von && klick(beleg.von as N)}>{KNOTEN_LABELS[beleg.von.art] ?? beleg.von.art}: {beleg.von.label}</button>{/if}
        {#if beleg.nach}<button class="link" disabled={!beleg.nach.seite} onclick={() => beleg?.nach && klick(beleg.nach as N)}>{KNOTEN_LABELS[beleg.nach.art] ?? beleg.nach.art}: {beleg.nach.label}</button>{/if}
      </p>
      <p class="muted small">Belegte Beziehung, keine Wertung.{#if beleg.art === "Geld"} Zuständigkeit für einen Einzelplan ist keine Entscheidung über eine einzelne Zahlung.{/if}</p>
    </aside>
  {/if}
  {#if kompakt}
  <div class="legende"><span class="muted">{umfeld.knoten.length} Knoten, {umfeld.kanten.length} Kanten, zwei Schritte. Klick auf einen Knoten öffnet seine Seite.</span>{#if onVoll}<button class="voll" onclick={onVoll}>Umfeld zeigen</button>{/if}</div>
  {:else}
  <div class="legende">
    {#each legende() as l}
      {@const st = kantenStil(l.art)}
      <span><svg width="34" height="8"><line x1="2" y1="4" x2="32" y2="4" stroke="var(--header)" stroke-width={st.width} stroke-dasharray={st.dasharray || undefined} /></svg> {l.label}</span>
    {/each}
    <span>Kreis Person · Quadrat Organisation · Raute Ministerium · Sechseck Partei · hell: Person ohne freigeschaltete Akte</span>
    <span>Klick auf einen Knoten öffnet Akte oder Seite, Doppelklick macht ihn zur Mitte, Mausrad zoomt. Klick auf eine Kante zeigt den Beleg mit Quelle und Stand. Keine Wertung: Das Netz zeigt belegte Beziehungen, nicht mehr.</span>
  </div>
  {/if}
</div>

<style>
  .netz { font-size: 12px; position: relative; }
  .treffer { cursor: pointer; outline: none; }
  .treffer:focus-visible { stroke: var(--accent); stroke-opacity: .55; }
  .beleg { position: absolute; right: 12px; top: 48px; width: 300px; max-width: calc(100% - 24px); background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius-s); padding: 12px 14px; box-shadow: 0 6px 20px rgba(23, 60, 102, .10); }
  .beleg-kopf { display: flex; justify-content: space-between; align-items: center; }
  .beleg .tag { background: var(--chip-blau); color: var(--header); border-radius: 999px; padding: 2px 8px; font-weight: 600; font-size: 11px; }
  .schliessen { background: none; border: 0; font-size: 18px; line-height: 1; cursor: pointer; color: var(--muted); }
  .beleg .satz { margin: 8px 0 4px; color: var(--fg); }
  .beleg p { margin: 4px 0; }
  .knoten-links { display: flex; flex-direction: column; gap: 2px; }
  .link { background: none; border: 0; color: var(--accent); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; text-align: left; }
  .link:disabled { color: var(--muted); text-decoration: none; cursor: default; }
  .small { font-size: 11px; }
  @media (max-width: 900px) { .beleg { position: static; width: auto; margin-top: 8px; } }
  .kopf { display: flex; gap: 12px; align-items: baseline; flex-wrap: wrap; margin-bottom: 6px; }
  .back { background: none; border: 0; color: var(--header); cursor: pointer; font: inherit; font-size: 12px; padding: 0; }
  h2 { margin: 0; font-size: 15px; }
  svg { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; width: 100%; height: 560px; touch-action: none; }
  .kompakt svg { height: 300px; background: var(--bg); }
  .voll { margin-left: auto; font: inherit; font-size: 12px; font-weight: 600; background: var(--nav-on); color: var(--nav-on-fg); border: 0; border-radius: 10px; padding: 6px 10px; cursor: pointer; }
  .knoten text { fill: var(--fg); pointer-events: none; }
  .knoten.klickbar { cursor: pointer; }
  .knoten.start path { fill: var(--accent); }
  .tip { position: fixed; z-index: 10; max-width: 360px; background: var(--nav-on); color: var(--nav-on-fg); font-size: 11px; padding: 6px 8px; border-radius: 6px; pointer-events: none; }
  .legende { display: flex; gap: 14px; flex-wrap: wrap; margin-top: 6px; color: var(--muted); font-size: 11px; }
  .legende span { display: inline-flex; align-items: center; gap: 4px; }
  .muted { color: var(--muted); }
</style>
