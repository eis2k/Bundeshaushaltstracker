<script lang="ts">
  import { fmtEuro } from "../model/format";
  import { effectiveValue } from "../model/scenario";
  import { revenueGroups } from "../model/tree";
import { groupBy, type Schnitt } from "../model/schnitte";
  import type { NodeId, Scenario, YearData } from "../model/types";
  import { CHANGED_STROKE, colorFor } from "./colors";
  import { treemapRoot } from "./treemapData";

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

  const tree = $derived(groupBy(data, schnitt, scenario.includeSv));
  const root = $derived(treemapRoot(tree, factors, focus));

  // Einnahmen brutto (nur positive Titel je Gruppe); negative Titel (EU-Eigenmittel, Länderanteile)
  // erscheinen rechts als Block "Weiterleitung an EU und Länder".
  const revenue = $derived.by(() => {
    const groups = revenueGroups(data, scenario.includeSv).filter((g) => !g.isKredit);
    return groups.map((g) => {
      let value = 0, original = 0;
      for (const r of g.rows) { const v = effectiveValue(r, factors); if (v > 0) value += v; if (r.soll > 0) original += r.soll; }
      return { id: g.id, label: g.label, steuer: g.id.startsWith("E:steuern"), value, original };
    }).filter((g) => g.value > 0);
  });
  const abzuege = $derived.by(() => {
    let sum = 0;
    for (const r of data.rows) {
      if (r.art !== "E" || (r.sv && !scenario.includeSv) || r.titel.slice(0, 3) === "325") continue;
      const v = effectiveValue(r, factors);
      if (v < 0) sum -= v;
    }
    return sum;
  });
  const brutto = $derived(revenue.reduce((s, g) => s + g.value, 0));
  const einnahmen = $derived(brutto - abzuege);
  const ausgaben = $derived(root.value);
  const ausgabenOriginal = $derived(root.original);
  const schulden = $derived(root.id === "bund" ? Math.max(0, ausgaben + root.minderausgaben - einnahmen) : 0);
  const rightTotal = $derived(root.id === "bund" ? ausgabenOriginal + abzuege : ausgabenOriginal);
  const scale = $derived(Math.max(brutto + schulden, rightTotal, 1));
  const gestrichen = $derived(Math.max(0, ausgabenOriginal - ausgaben));

  const H = 360;
  const px = (v: number) => (v / scale) * H;

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
    onFocus(pathFor(id, kind));
  }
  function back() {
    const next = focus.slice(0, -1);
    onFocus(next);
    onSelect(next.length ? next[next.length - 1] : null);
  }
  const crumbs = $derived(focus.map((id) => tree.byId.get(id)?.label ?? id));
  const shown = $derived([...root.children].sort((a, b) => b.value - a.value));
</script>

<div class="saeulen">
  <div class="crumbs">
    {#if focus.length}<button class="back" onclick={back}>‹ Zurück</button>{/if}
    <span>Bundeshaushalt {data.jahr}</span>
    {#each crumbs as c}<span>› {c}</span>{/each}
    <span class="hint">gleiche Skala · Klick zoomt hinein</span>
  </div>
  <div class="cols">
    <div class="col">
      <div class="head">Einnahmen · {fmtEuro(einnahmen)}{#if abzuege > 0} <span class="muted">(brutto {fmtEuro(brutto)})</span>{/if}</div>
      <div class="stack" style="height:{H}px">
        <div class="spacer" style="height:{H - px(brutto + schulden)}px"></div>
        {#if schulden > 0}
          <div class="blk kredit" style="height:{px(schulden)}px" title="Neue Schulden: {fmtEuro(schulden)}">
            {#if px(schulden) > 16}Neue Schulden <small>{fmtEuro(schulden)}</small>{/if}
          </div>
        {/if}
        {#each revenue as g (g.id)}
          <button class="blk" class:selected={selected === g.id} class:changed={g.value !== g.original}
                  style="height:{px(g.value)}px; background:{colorFor(g.steuer ? 'steuern' : 'sonstige')}"
                  onclick={() => onSelect(g.id)} title="{g.label}: {fmtEuro(g.value)}">
            {#if px(g.value) > 16}{g.label} <small>{fmtEuro(g.value)}</small>{/if}
          </button>
        {/each}
      </div>
    </div>
    <div class="col">
      <div class="head">Ausgaben{root.id !== "bund" ? ` · ${root.label}` : ""} · {fmtEuro(ausgaben + root.minderausgaben)}{#if gestrichen > 0} <span class="cut">(war {fmtEuro(ausgabenOriginal + root.minderausgaben)})</span>{/if}</div>
      <div class="stack" style="height:{H}px">
        <div class="spacer" style="height:{H - px(rightTotal)}px"></div>
        {#if root.id === "bund" && abzuege > 0}
          <div class="blk abzug" style="height:{px(abzuege)}px" title="Weiterleitung an EU und Länder (negative Einnahmetitel): {fmtEuro(abzuege)}">{#if px(abzuege) > 16}Weiterleitung an EU und Länder <small>{fmtEuro(abzuege)}</small>{/if}</div>
        {/if}
        {#if gestrichen > 0}
          <div class="blk ghost" style="height:{px(gestrichen)}px" title="gestrichen: {fmtEuro(gestrichen)}">{#if px(gestrichen) > 14}gestrichen <small>{fmtEuro(gestrichen)}</small>{/if}</div>
        {/if}
        {#each shown as c (c.id)}
          {#if c.value > 0}
            <button class="blk" class:selected={selected === c.id} class:changed={c.changed}
                    style="height:{px(c.value)}px; background:{colorFor(c.kind === 'epl' ? c.id : c.id.split('-')[0])}; opacity:{c.sv ? .6 : 1}"
                    onclick={() => click(c.id, c.kind)} title="{c.label}: {fmtEuro(c.value)}{c.changed ? ` (war ${fmtEuro(c.original)})` : ''}">
              {#if px(c.value) > 16}{c.label} <small>{fmtEuro(c.value)}{c.changed ? ` · war ${fmtEuro(c.original)}` : ""}</small>{/if}
            </button>
          {/if}
        {/each}
      </div>
    </div>
  </div>
  {#if root.minderausgaben !== 0}
    <div class="minder">Globale Minderausgaben {fmtEuro(root.minderausgaben)} sind in der Summe enthalten, aber nicht als Block darstellbar.</div>
  {/if}
</div>

<style>
  .saeulen { width: 100%; }
  .crumbs { display: flex; gap: 6px; align-items: center; font-size: 11px; color: var(--muted); margin-bottom: 8px; flex-wrap: wrap; }
  .crumbs .back { font-size: 11px; background: var(--bg); border: 1px solid var(--border); border-radius: 6px; padding: 2px 7px; cursor: pointer; color: var(--fg); }
  .crumbs .hint { margin-left: auto; }
  .cols { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; }
  .head { font-size: 11px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-bottom: 6px; font-weight: 600; }
  .head .cut { color: var(--bad); text-transform: none; letter-spacing: 0; }
  .stack { display: flex; flex-direction: column; border-radius: 6px; overflow: hidden; }
  .spacer { flex: none; }
  .blk { display: flex; justify-content: space-between; align-items: center; gap: 6px; padding: 0 8px; color: var(--on-color); font-size: 11px; font-weight: 600; border: 0; border-bottom: 1px solid rgba(255,255,255,.3); overflow: hidden; white-space: nowrap; cursor: pointer; font-family: inherit; text-align: left; flex: none; }
  .blk small { font-weight: 400; opacity: .9; }
  .blk.selected { outline: 3px solid var(--accent); outline-offset: -3px; }
  .blk.changed { box-shadow: inset 0 0 0 2px var(--accent); }
  .blk.kredit { background: repeating-linear-gradient(45deg, var(--bad-bg) 0 4px, var(--panel) 4px 8px); color: var(--bad); border: 1px dashed var(--bad); cursor: default; }
  .blk.abzug { background: repeating-linear-gradient(45deg, var(--abzug-bg) 0 4px, var(--panel) 4px 8px); color: var(--abzug-fg); border: 1px dashed var(--abzug-border); cursor: default; }
  .head .muted { color: var(--muted); text-transform: none; letter-spacing: 0; font-weight: 400; }
  .blk.ghost { background: repeating-linear-gradient(45deg, var(--bad-bg) 0 4px, var(--panel) 4px 8px); color: var(--bad); border: 1px dashed var(--bad); cursor: default; }
  .minder { font-size: 11px; color: var(--muted); margin-top: 8px; }
  @media (max-width: 720px) { .cols { gap: 10px; } .blk { font-size: 10px; padding: 0 4px; } }
</style>
