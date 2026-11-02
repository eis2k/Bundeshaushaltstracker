<script lang="ts">
  /** Ring („Donut“) wie Kachel 02 des Mockup-Pakets: Teile ohne Umsortierung, Innenradius 60 %, Mitte mit Summe. */
  import { arc, pie, type PieArcDatum } from "d3-shape";
  import { fmtEuro } from "../model/format";

  export interface Teil { id: string | null; label: string; wert: number; anteil: number; farbe: string }
  let { teile, mitte, onKlick, size = 240 }: { teile: Teil[]; mitte: { wert: string; label: string }; onKlick?: (id: string | null) => void; size?: number } = $props();

  const r = $derived(size / 2);
  const boegen = $derived.by(() => {
    const gen = pie<Teil>().value((t) => t.wert).sort(null).padAngle(0.012);
    const a = arc<PieArcDatum<Teil>>().innerRadius(r * 0.6).outerRadius(r - 2).cornerRadius(3);
    return gen(teile).map((d) => ({ d, pfad: a(d) ?? "" }));
  });
</script>

<svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label="Ausgaben nach Einzelplan">
  <g transform={`translate(${r},${r})`}>
    {#each boegen as b (b.d.data.id ?? "rest")}
      <path d={b.pfad} fill={b.d.data.farbe} class="teil" class:klickbar={!!onKlick && b.d.data.id !== null} role="button" tabindex="0"
            onclick={() => onKlick?.(b.d.data.id)} onkeydown={(e) => (e.key === "Enter" || e.key === " ") && onKlick?.(b.d.data.id)}>
        <title>{b.d.data.label}: {fmtEuro(b.d.data.wert)} ({b.d.data.anteil.toLocaleString("de-DE")} %)</title>
      </path>
    {/each}
    <text y="-4" text-anchor="middle" class="wert">{mitte.wert}</text>
    <text y="14" text-anchor="middle" class="label">{mitte.label}</text>
  </g>
</svg>

<style>
  svg { display: block; max-width: 100%; height: auto; }
  .teil { stroke: var(--panel); stroke-width: 1; }
  .teil.klickbar { cursor: pointer; }
  .teil.klickbar:hover, .teil:focus-visible { opacity: .85; outline: none; }
  .wert { font-size: 18px; font-weight: 700; fill: var(--header); }
  .label { font-size: 11px; fill: var(--muted); }
</style>
