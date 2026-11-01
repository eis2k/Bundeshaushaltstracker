<script lang="ts">
  import { fmtDelta, fmtEuro } from "../model/format";
  import type { ViewId } from "../model/types";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();

  const views: { id: ViewId; label: string }[] = [
    { id: "fluss", label: "Fluss" },
    { id: "karte", label: "Karte" },
    { id: "saeulen", label: "Säulen" },
    { id: "gewachsen", label: "Was ist gewachsen?" },
  ];

  let copied = $state(false);
  async function share() {
    const url = `${location.origin}${location.pathname}#${app.toHash()}`;
    try {
      await navigator.clipboard.writeText(url);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      prompt("Link zum Kopieren:", url);
    }
  }
  const b = $derived(app.balance);
  const gesamt = $derived(app.view === "fluss" && app.topf !== "bund" ? app.toepfe : null);
  let showToepfe = $state(false);
</script>

<header class="top">
  <div class="logo">Bundeshaushalts<span>tracker</span>{#if app.real}<small class="real">in Preisen von {app.bezugsjahr}</small>{/if}</div>
  {#if b && gesamt}
    <div class="stat"><small>Steuern + Beiträge</small><b class="tabular">{fmtEuro(b.einnahmen + gesamt.beitraege)}</b></div>
    <div class="stat"><small>Ausgaben gesamt</small><b class="tabular">{fmtEuro(gesamt.gesamtAusgaben)}</b></div>
    <div class="stat" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}>
      <small>{b.neueSchulden >= 0 ? "Neue Schulden (Bund)" : "Überschuss (Bund)"}</small>
      <b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b>
    </div>
    <button class="stat toepfe" onclick={() => (showToepfe = !showToepfe)} title="Saldo je Sozialkasse">
      <small>Kassen-Salden {showToepfe ? "▴" : "▾"}</small>
      <b class="tabular" class:bad={gesamt.toepfe.some((t) => t.saldo < 0)}>{gesamt.toepfe.filter((t) => t.saldo < 0).length} im Minus</b>
    </button>
  {:else if b}
    <div class="stat"><small>Einnahmen</small><b class="tabular">{fmtEuro(b.einnahmen)}</b></div>
    <div class="stat"><small>Ausgaben</small><b class="tabular">{fmtEuro(b.ausgaben)}</b></div>
    <div class="stat" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}>
      <small>{b.neueSchulden >= 0 ? "Neue Schulden" : "Überschuss"}</small>
      <b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b>
    </div>
    <div class="stat" class:good={b.delta > 0} class:bad={b.delta < 0}>
      <small>ggü. Original</small><b class="tabular">{fmtDelta(b.delta)}</b>
    </div>
  {/if}
  <nav class="views" aria-label="Ansicht">
    {#each views as v}
      <button class:on={app.view === v.id} onclick={() => app.setView(v.id)}>{v.label}</button>
    {/each}
  </nav>
  <div class="actions">
    {#if Object.keys(app.scenario.factors).length || app.scenario.presets.length}
      <button class="ghost" onclick={() => app.reset()} title="Alle Regler und Presets zurück auf Original">Zurücksetzen</button>
    {/if}
    <button class="share" onclick={share}>{copied ? "Link kopiert" : "Teilen"}</button>
  </div>
</header>
{#if gesamt && showToepfe}
  <div class="salden">
    {#each gesamt.toepfe as t (t.id)}
      <span class:bad={t.saldo < 0} class:good={t.saldo >= 0}>
        <b>{t.kurz}</b> {t.saldo >= 0 ? "Rücklage" : "Defizit"} {fmtEuro(Math.abs(t.saldo))}{#if t.saldo !== t.saldoOriginal} <i>(war {fmtDelta(t.saldoOriginal)})</i>{/if}{#if t.geschaetzt} <i title="Zwischen Stützjahren interpoliert">· geschätzt</i>{/if}
      </span>
    {/each}
  </div>
{/if}

<style>
  .top { display: flex; align-items: center; gap: 18px; padding: 10px 16px; background: var(--header); color: var(--header-fg); flex-wrap: wrap; }
  .logo { font-weight: 800; letter-spacing: -0.3px; font-size: 16px; white-space: nowrap; }
  .logo span { color: var(--accent); }
  .logo .real { display: block; font-size: 10px; font-weight: 400; opacity: .7; letter-spacing: 0; }
  .stat { display: flex; flex-direction: column; line-height: 1.15; min-width: 90px; }
  .stat small { font-size: 10px; opacity: .65; text-transform: uppercase; letter-spacing: .05em; }
  .stat b { font-size: 15px; }
  .stat.bad b { color: #f87171; }
  .stat.good b { color: #4ade80; }
  .views { display: flex; background: rgba(255,255,255,.12); border-radius: 8px; padding: 2px; margin-left: auto; }
  .views button { background: none; border: 0; color: inherit; opacity: .75; padding: 5px 10px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .views button.on { background: #fff; color: var(--header); opacity: 1; font-weight: 700; }
  .actions { display: flex; gap: 8px; }
  .stat.toepfe { background: none; border: 0; color: inherit; cursor: pointer; text-align: left; padding: 0; font: inherit; }
  .salden { display: flex; gap: 14px; flex-wrap: wrap; padding: 6px 16px; background: #1f2937; color: #fff; font-size: 12px; }
  .salden .bad { color: #f87171; } .salden .good { color: #4ade80; }
  .salden i { font-style: normal; opacity: .7; }
  .share { background: var(--accent); color: var(--header); font-weight: 700; border: 0; border-radius: 8px; padding: 7px 12px; cursor: pointer; font-size: 12px; }
  .ghost { background: none; border: 1px solid rgba(255,255,255,.35); color: inherit; border-radius: 8px; padding: 6px 10px; cursor: pointer; font-size: 12px; }
  @media (max-width: 720px) {
    .top { gap: 10px; }
    .stat { min-width: 70px; }
    .stat b { font-size: 13px; }
    .views { margin-left: 0; width: 100%; justify-content: space-between; }
  }
</style>
