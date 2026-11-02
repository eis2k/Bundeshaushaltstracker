<script lang="ts">
  import { onMount } from "svelte";
  import { fmtDelta, fmtEuro } from "../model/format";
  import { rankGrowth, totalGrowth, type Ebene, type GrowthFilter, type GrowthRow } from "../model/zeitreihe";
  import type { AppState } from "../state.svelte";
  import { colorFor } from "./colors";

  let { app }: { app: AppState } = $props();

  const jahre = $derived(app.index?.jahre ?? []);
  let von = $state(2015);
  let bis = $state(2025);
  let ebene = $state<Ebene>("titel");
  let sort = $state<"pct" | "abs">("pct");
  let filter = $state<GrowthFilter>("alle");
  let limit = $state(50);
  let min = $state(50_000_000);
  const minOptions = [0, 10_000_000, 50_000_000, 500_000_000, 1_000_000_000];

  onMount(() => {
    void app.ensureZeitreihe();
    if (jahre.length) { von = jahre[0]; bis = app.istVerfuegbar || app.stand === "soll" ? Math.min(app.jahr, jahre[jahre.length - 1]) : jahre[jahre.length - 1]; }
    if (bis <= von) bis = jahre[jahre.length - 1];
  });

  const istBis = $derived(app.index?.ist_bis ?? null);
  const bisEffective = $derived(app.stand === "ist" && istBis !== null ? Math.min(bis, istBis) : bis);

  const rows = $derived<GrowthRow[]>(app.zeitreihe
    ? rankGrowth(app.zeitreihe, { von, bis: bisEffective, ebene, stand: app.stand, sort, filter, real: app.real, vpi: app.vpi ?? undefined, includeSv: app.scenario.includeSv, min, konkordanz: app.konkordanz })
    : []);
  const shown = $derived(rows.slice(0, limit));
  const total = $derived(app.zeitreihe
    ? (() => { const t = totalGrowth(app.zeitreihe!, { von, bis: bisEffective, stand: app.stand, real: app.real, vpi: app.vpi ?? undefined }); return { a: t.von, b: t.bis }; })()
    : null);

  const filters: { id: GrowthFilter; label: string; title: string }[] = [
    { id: "alle", label: "Alle Ausgaben", title: "Alle Ausgabentitel" },
    { id: "zuwendungen", label: "Zuwendungen und Zuschüsse", title: "Gruppen 63 bis 69 und 88/89: Zuschüsse an Sozialversicherung, Länder, Unternehmen, Vereine, Ausland" },
    { id: "personal", label: "Personal", title: "Hauptgruppe 4" },
    { id: "geschrumpft", label: "Geschrumpft", title: "Titel, die kleiner wurden" },
    { id: "neu", label: "Neu", title: "Titel, die es im Startjahr nicht gab" },
  ];

  function spark(v: (number | null)[]): string {
    const vals = v.map((x) => x ?? 0);
    const max = Math.max(...vals.map(Math.abs), 1);
    const w = 120, h = 22;
    return vals.map((x, i) => `${(i / Math.max(1, vals.length - 1)) * w},${h - 2 - (Math.max(0, x) / max) * (h - 4)}`).join(" ");
  }
  function open(r: GrowthRow) {
    const parts = r.id.split("-");
    const path = ebene === "epl" ? [parts[0]] : ebene === "kap" ? [parts[0], r.id] : [parts[0], `${parts[0]}-${parts[1]}`, r.id];
    void app.setJahr(bisEffective);
    app.zeigeImFluss(path, r.id);
  }
  function pctLabel(r: GrowthRow): string {
    if (r.neu) return "neu";
    if (r.pct === null) return "–";
    const p = Math.round(r.pct * 100);
    return `${p > 0 ? "+" : ""}${p} %`;
  }
  // Keine Wertungsfarben: Wachstum und Rückgang unterscheiden sich nur durch das Vorzeichen im Text
  function heat(_r: GrowthRow): string { return ""; }
</script>

<div class="gewachsen">
  <div class="controls">
    <label>von <select bind:value={von}>{#each jahre as j}<option value={j} disabled={j >= bisEffective}>{j}</option>{/each}</select></label>
    <label>bis <select bind:value={bis}>{#each jahre as j}<option value={j} disabled={j <= von || (app.stand === "ist" && istBis !== null && j > istBis)}>{j}</option>{/each}</select></label>
    <label>Ebene
      <select bind:value={ebene}>
        <option value="epl">Einzelplan</option><option value="kap">Kapitel</option><option value="titel">Titel</option>
      </select>
    </label>
    <label>Sortierung
      <select bind:value={sort}><option value="pct">Zuwachs in %</option><option value="abs">Zuwachs in €</option></select>
    </label>
    <label>mindestens
      <select bind:value={min}>{#each minOptions as m}<option value={m}>{m === 0 ? "alles" : fmtEuro(m)}</option>{/each}</select>
    </label>
    <span class="muted">{app.stand === "ist" ? "Ist" : "Soll"}{app.real ? `, in Preisen von ${app.bezugsjahr}` : ""}</span>
  </div>
  <div class="chips">
    {#each filters as f}
      <button class="chip" class:on={filter === f.id} title={f.title} onclick={() => (filter = f.id)}>{f.label}</button>
    {/each}
  </div>

  {#if total}
    <div class="total">Gesamtausgaben Bund: {fmtEuro(total.a)} ({von}) → {fmtEuro(total.b)} ({bisEffective}), {total.a > 0 ? `${total.b >= total.a ? "+" : ""}${Math.round(((total.b - total.a) / total.a) * 100)} %` : ""}. Was darüber liegt, ist stärker gewachsen als der Haushalt insgesamt.</div>
  {/if}

  {#if !app.zeitreihe}
    <div class="muted" style="padding:30px;text-align:center">Lade Zeitreihe …</div>
  {:else}
    <table>
      <thead><tr><th>{ebene === "titel" ? "Titel" : ebene === "kap" ? "Kapitel" : "Einzelplan"}</th><th class="num">{von}</th><th class="num">{bisEffective}</th><th class="num">Zuwachs</th><th>Verlauf</th></tr></thead>
      <tbody>
        {#each shown as r (r.id)}
          <tr onclick={() => open(r)} title="Im Fluss öffnen">
            <td>
              <span class="dot" style="background:{colorFor(r.epl ?? r.id.split('-')[0])}"></span>
              <b>{r.text}</b>
              <small class="muted">{r.id.replace(/-/g, " › ")}{r.hinweis ? ` · ${r.hinweis}` : ""}</small>
            </td>
            <td class="num tabular">{r.von ? fmtEuro(r.von) : "–"}</td>
            <td class="num tabular">{fmtEuro(r.bis)}</td>
            <td class="num tabular grow {heat(r)}">{pctLabel(r)}<small>{fmtDelta(r.abs)}</small></td>
            <td><svg viewBox="0 0 120 22" class="spark"><polyline points={spark(r.verlauf)} fill="none" stroke="#475569" stroke-width="1.5" /></svg></td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if rows.length > limit}
      <button class="more" onclick={() => (limit += 50)}>Weitere {Math.min(50, rows.length - limit)} von {rows.length} zeigen</button>
    {/if}
    <p class="muted small">Jede Zeile öffnet den Posten im Fluss. Prozent bezieht sich auf das Startjahr; „neu“ heißt: im Startjahr kein Ansatz. Ein Zuwachs ist für sich genommen weder gut noch schlecht; die Liste zeigt nur, wo sich etwas bewegt hat. Quelle: bundeshaushalt.de (Soll-Endstände, Haushaltsrechnungen).</p>
  {/if}
</div>

<style>
  .gewachsen { font-size: 12px; }
  .controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
  .controls label { display: flex; gap: 4px; align-items: center; color: var(--muted); }
  select { font: inherit; font-size: 12px; padding: 3px 6px; border: 1px solid var(--border); border-radius: 6px; background: var(--panel); color: var(--fg); }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
  .chip { font-size: 11px; padding: 5px 10px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); cursor: pointer; color: var(--fg); }
  .chip.on { background: var(--nav-on); color: var(--nav-on-fg); border-color: var(--nav-on); }
  .total { background: var(--bg); border-radius: 8px; padding: 6px 10px; margin-bottom: 10px; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 6px; border-bottom: 1px solid var(--border); }
  td { padding: 7px 6px; border-bottom: 1px solid var(--border); vertical-align: middle; }
  tbody tr { cursor: pointer; }
  tbody tr:hover { background: var(--nav-item); }
  td small { display: block; font-size: 10px; font-weight: 400; }
  .num { text-align: right; white-space: nowrap; }
  .grow { font-weight: 800; }
  .dot { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 6px; vertical-align: middle; }
  .spark { width: 120px; height: 22px; display: block; }
  .more { margin-top: 10px; font-size: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; cursor: pointer; color: var(--fg); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; margin-top: 10px; }
  @media (max-width: 720px) { .spark { width: 70px; } td { padding: 5px 4px; } }
</style>
