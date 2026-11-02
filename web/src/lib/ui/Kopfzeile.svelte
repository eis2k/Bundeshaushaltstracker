<script lang="ts">
  import { fmtDelta, fmtEuro } from "../model/format";
  import { titelFuer } from "../model/navigation";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();

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
  const kopf = $derived(titelFuer(app.view, app.gestalten));
  const modell = $derived(Object.keys(app.scenario.factors).length > 0 || app.scenario.presets.length > 0 || Object.keys(app.scenario.steuern ?? {}).length > 0);
  let showToepfe = $state(false);
</script>

<header class="top">
  <div class="titel">
    <h1>{kopf.titel}{#if app.real}<small class="real">in Preisen von {app.bezugsjahr}</small>{/if}</h1>
    <p>{kopf.untertitel}</p>
  </div>
  {#if b && gesamt}
    <div class="karte"><small>Steuern + Beiträge{#if b.modellEinnahmen > 0} · inkl. Modell{/if}</small><b class="tabular">{fmtEuro(b.einnahmen + gesamt.beitraege)}</b></div>
    <div class="karte"><small>Ausgaben gesamt</small><b class="tabular">{fmtEuro(gesamt.gesamtAusgaben)}</b></div>
    <div class="karte" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}>
      <small>{b.neueSchulden >= 0 ? "Neue Schulden (Bund)" : "Überschuss (Bund)"}</small>
      <b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b>
    </div>
    <div class="karte" class:good={b.delta > 0} class:bad={b.delta < 0}>
      <small>ggü. Original (Bund)</small><b class="tabular">{fmtDelta(b.delta)}</b>
    </div>
    <button class="karte toepfe" onclick={() => (showToepfe = !showToepfe)} title="Saldo je Sozialkasse">
      <small>Kassen-Salden {showToepfe ? "▴" : "▾"}</small>
      <b class="tabular" class:bad={gesamt.toepfe.some((t) => t.saldo < 0)}>{gesamt.toepfe.filter((t) => t.saldo < 0).length} im Minus</b>
    </button>
  {:else if b}
    <div class="karte"><small>Einnahmen{#if b.modellEinnahmen > 0} · inkl. Modell{/if}</small><b class="tabular">{fmtEuro(b.einnahmen)}</b></div>
    <div class="karte"><small>Ausgaben</small><b class="tabular">{fmtEuro(b.ausgaben)}</b></div>
    <div class="karte" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}>
      <small>{b.neueSchulden >= 0 ? "Neue Schulden" : "Überschuss"}</small>
      <b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b>
    </div>
    <div class="karte" class:good={b.delta > 0} class:bad={b.delta < 0}>
      <small>ggü. Original</small><b class="tabular">{fmtDelta(b.delta)}</b>
    </div>
  {/if}
  <div class="actions">
    {#if modell}
      <span class="chip modell" title="Regler, Presets oder Steuer-Modelle sind aktiv">Modellrechnung, keine Prognose</span>
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
  .top { display: flex; align-items: center; gap: 12px; padding: 18px 20px 8px; flex-wrap: wrap; }
  .titel { margin-right: auto; min-width: 220px; }
  h1 { margin: 0; font-size: 23px; color: var(--header); letter-spacing: -0.3px; line-height: 1.15; }
  h1 .real { display: block; font-size: 11px; font-weight: 400; color: var(--muted); letter-spacing: 0; }
  .titel p { margin: 3px 0 0; color: var(--muted); font-size: 14px; }
  .karte { display: flex; flex-direction: column; line-height: 1.15; min-width: 120px; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 14px; }
  .karte small { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  .karte b { font-size: 16px; color: var(--header); }
  .karte.bad b { color: var(--bad); }
  .karte.good b { color: var(--good); }
  .karte.toepfe { cursor: pointer; text-align: left; font: inherit; }
  .actions { display: flex; gap: 8px; align-items: center; flex-wrap: wrap; }
  .chip.modell { background: var(--chip-orange); color: var(--header); border-radius: 999px; padding: 5px 10px; font-size: 11px; font-weight: 600; }
  .share { background: var(--nav-on); color: var(--nav-on-fg); font-weight: 700; border: 0; border-radius: 10px; padding: 9px 14px; cursor: pointer; font-size: 13px; }
  .ghost { background: var(--panel); border: 1px solid var(--border); color: var(--header); border-radius: 10px; padding: 8px 12px; cursor: pointer; font-size: 13px; }
  .salden { display: flex; gap: 14px; flex-wrap: wrap; padding: 6px 20px; font-size: 12px; color: var(--fg); }
  .salden .bad { color: var(--bad); } .salden .good { color: var(--good); }
  .salden i { font-style: normal; color: var(--muted); }
  @media (max-width: 900px) {
    .top { padding: 12px 12px 6px; gap: 8px; }
    .titel { width: 100%; }
    h1 { font-size: 19px; }
    .karte { min-width: 0; flex: 1 1 40%; padding: 8px 10px; }
    .karte b { font-size: 14px; }
    .actions { width: 100%; justify-content: flex-end; }
  }
</style>
