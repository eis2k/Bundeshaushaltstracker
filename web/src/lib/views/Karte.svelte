<script lang="ts">
  import { fmtEuro } from "../model/format";
  import { revenueGroups } from "../model/tree";
import { groupBy, type Schnitt } from "../model/schnitte";
  import { effectiveValue } from "../model/scenario";
  import type { NodeId, Scenario, YearData } from "../model/types";
  import { CHANGED_STROKE, colorFor } from "./colors";
  import { buildTreemap, treemapRoot } from "./treemapData";

  interface Props {
    data: YearData;
    scenario: Scenario;
    factors: Record<NodeId, number>;
    focus: NodeId[];
    selected: NodeId | null;
    schnitt?: Schnitt;
    onFocus: (path: NodeId[]) => void;
    onSelect: (id: NodeId | null) => void;
  }
  let { data, scenario, factors, focus, selected, schnitt = "ressort", onFocus, onSelect }: Props = $props();

  let width = $state(900);
  const height = $derived(width < 720 ? 480 : 400);

  const tree = $derived(groupBy(data, schnitt, scenario.includeSv));
  const root = $derived(treemapRoot(tree, factors, focus));
  const layout = $derived(buildTreemap(root, width, height));

  // Einnahmen-Streifen auf gleicher Skala wie die Ausgaben
  const revenue = $derived.by(() => {
    const groups = revenueGroups(data, scenario.includeSv).filter((g) => !g.isKredit);
    const items = groups.map((g) => ({ id: g.id, label: g.label, value: g.rows.reduce((s, r) => s + effectiveValue(r, factors), 0), steuer: g.id.startsWith("E:steuern") }));
    const einnahmen = items.reduce((s, i) => s + i.value, 0);
    const ausgaben = root.id === "bund" ? root.value + root.minderausgaben : null;
    const schulden = ausgaben !== null ? Math.max(0, ausgaben - einnahmen) : 0;
    return { items, einnahmen, schulden, total: einnahmen + schulden };
  });

  function colorKeyFor(id: string, kind: string): string {
    if (kind === "epl") return id;
    return id.split("-")[0];
  }
  function pathFor(id: string, kind: string): NodeId[] {
    if (id.includes(":")) return [id];                       // Schnitt-Wurzel (ka:…, ea:…)
    if (schnitt !== "ressort" && kind === "titel") return focus; // Titel im Schnitt: nur auswählen
    const parts = id.split("-");
    if (kind === "epl") return [parts[0]];
    if (kind === "kap") return [parts[0], id];
    return [parts[0], `${parts[0]}-${parts[1]}`, id];
  }
  function click(id: string, kind: string) {
    onSelect(id);
    if (kind !== "titel") onFocus(pathFor(id, kind));
    else onFocus(pathFor(id, kind));
  }
  function back() {
    const next = focus.slice(0, -1);
    onFocus(next);
    onSelect(next.length ? next[next.length - 1] : null);
  }
  const crumbs = $derived(focus.map((id) => tree.byId.get(id)?.label ?? id));
</script>

<div class="karte" bind:clientWidth={width}>
  <div class="crumbs">
    {#if focus.length}<button class="back" onclick={back}>‹ Zurück</button>{/if}
    <span>Bundeshaushalt {data.jahr}</span>
    {#each crumbs as c}<span>› {c}</span>{/each}
    <span class="hint">Fläche = Betrag · Klick zoomt hinein</span>
  </div>

  {#if root.id === "bund"}
    <div class="strip" title="Einnahmen und neue Schulden auf derselben Skala wie die Ausgaben">
      {#each revenue.items as it (it.id)}
        {#if it.value > 0}
          <button class="seg" style="flex:{it.value}; background:{colorFor(it.steuer ? 'steuern' : 'sonstige')}" class:selected={selected === it.id} onclick={() => onSelect(it.id)} title="{it.label}: {fmtEuro(it.value)}">
            {#if it.value / revenue.total > 0.08}{it.label}{/if}
          </button>
        {/if}
      {/each}
      {#if revenue.schulden > 0}
        <div class="seg kredit" style="flex:{revenue.schulden}" title="Neue Schulden: {fmtEuro(revenue.schulden)}">Neue Schulden {fmtEuro(revenue.schulden)}</div>
      {/if}
    </div>
  {/if}

  <svg viewBox="0 0 {width} {height}" {width} {height} role="img" aria-label="Karte der Ausgaben">
    {#each layout.leaves() as leaf (leaf.data.id)}
      {@const w = leaf.x1 - leaf.x0}
      {@const h = leaf.y1 - leaf.y0}
      {@const dark = ["60", "10", "11", "14", "25", "20", "30"].includes(colorKeyFor(leaf.data.id, leaf.data.kind))}
      <g class="tile" role="button" tabindex="0" onclick={() => click(leaf.data.id, leaf.data.kind)} onkeydown={(e) => (e.key === "Enter" || e.key === " ") && click(leaf.data.id, leaf.data.kind)}>
        <rect x={leaf.x0} y={leaf.y0} width={Math.max(0, w)} height={Math.max(0, h)} rx="3"
              fill={colorFor(colorKeyFor(leaf.data.id, leaf.data.kind))} fill-opacity={leaf.data.sv ? 0.55 : 0.9}
              stroke={leaf.data.id === selected || leaf.data.changed ? CHANGED_STROKE : "#fff"} stroke-width={leaf.data.id === selected ? 3 : leaf.data.changed ? 2 : 1}
              stroke-dasharray={leaf.data.changed && leaf.data.id !== selected ? "4 2" : undefined} />
        {#if w > 60 && h > 24}
          <text x={leaf.x0 + 6} y={leaf.y0 + 14} class="t" class:dark>{leaf.data.label.length > w / 6.5 ? leaf.data.label.slice(0, Math.max(3, Math.floor(w / 6.5)) - 1) + "…" : leaf.data.label}</text>
          {#if h > 38}
            <text x={leaf.x0 + 6} y={leaf.y0 + 28} class="a" class:dark>{fmtEuro(leaf.data.value)}{leaf.data.changed ? ` · war ${fmtEuro(leaf.data.original)}` : ""}{leaf.data.sv ? " · Nebenhaushalt" : ""}</text>
          {/if}
        {/if}
        <title>{leaf.data.label}: {fmtEuro(leaf.data.value)}{leaf.data.changed ? ` (Original ${fmtEuro(leaf.data.original)})` : ""}</title>
      </g>
    {/each}
  </svg>
  {#if root.minderausgaben !== 0}
    <div class="minder">Nicht als Fläche darstellbar: Globale Minderausgaben {fmtEuro(root.minderausgaben)} (Einsparvorgaben ohne eigenen Titel).</div>
  {/if}
</div>

<style>
  .karte { width: 100%; }
  .crumbs { display: flex; gap: 6px; align-items: center; font-size: 11px; color: var(--muted); margin-bottom: 6px; flex-wrap: wrap; }
  .crumbs .back { font-size: 11px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 2px 7px; cursor: pointer; color: var(--fg); }
  .crumbs .hint { margin-left: auto; }
  .strip { display: flex; height: 26px; border-radius: 4px; overflow: hidden; margin-bottom: 8px; font-size: 10px; color: #fff; font-weight: 600; }
  .seg { display: flex; align-items: center; padding: 0 6px; white-space: nowrap; overflow: hidden; border: 0; color: inherit; cursor: pointer; font: inherit; }
  .seg.selected { outline: 2px solid var(--accent); outline-offset: -2px; }
  .seg.kredit { background: repeating-linear-gradient(45deg, #fecaca 0 4px, #fff 4px 8px); color: var(--bad); border: 1px dashed var(--bad); cursor: default; }
  svg { display: block; width: 100%; height: auto; }
  .tile { cursor: pointer; }
  .t { font-size: 11px; font-weight: 600; fill: #fff; pointer-events: none; }
  .a { font-size: 10px; fill: rgba(255,255,255,.9); pointer-events: none; }
  .t.dark, .a.dark { fill: #fff; }
  .minder { font-size: 11px; color: var(--muted); margin-top: 6px; }
</style>
