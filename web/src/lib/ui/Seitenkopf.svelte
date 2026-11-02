<script lang="ts">
  import { fmtDelta, fmtEuro } from "../model/format";
  import { titelFuer } from "../model/navigation";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const kopf = $derived(titelFuer(app.view));
  const b = $derived(app.balance);
  const gesamt = $derived(app.view === "fluss" && app.topf !== "bund" ? app.toepfe : null);
  const kennzahlen = $derived(["fluss", "karte", "saeulen", "gewachsen", "ministerien", "simulator"].includes(app.view));
  let showToepfe = $state(false);
</script>

<div class="seitenkopf">
  <div class="titel">
    <h1>{kopf.titel}{#if app.real}<small class="real">in Preisen von {app.bezugsjahr}</small>{/if}</h1>
    <p>{kopf.untertitel}</p>
  </div>
  {#if kennzahlen && b && gesamt}
    <div class="karte"><small>Steuern + Beiträge{#if b.modellEinnahmen > 0} · inkl. Modell{/if}</small><b class="tabular">{fmtEuro(b.einnahmen + gesamt.beitraege)}</b></div>
    <div class="karte"><small>Ausgaben gesamt</small><b class="tabular">{fmtEuro(gesamt.gesamtAusgaben)}</b></div>
    <div class="karte" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}><small>{b.neueSchulden >= 0 ? "Neue Schulden (Bund)" : "Überschuss (Bund)"}</small><b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b></div>
    <div class="karte" class:good={b.delta > 0} class:bad={b.delta < 0}><small>ggü. Original (Bund)</small><b class="tabular">{fmtDelta(b.delta)}</b></div>
    <button class="karte toepfe" onclick={() => (showToepfe = !showToepfe)} title="Saldo je Sozialkasse"><small>Kassen-Salden {showToepfe ? "▴" : "▾"}</small><b class="tabular" class:bad={gesamt.toepfe.some((t) => t.saldo < 0)}>{gesamt.toepfe.filter((t) => t.saldo < 0).length} im Minus</b></button>
  {:else if kennzahlen && b}
    <div class="karte"><small>Einnahmen{#if b.modellEinnahmen > 0} · inkl. Modell{/if}</small><b class="tabular">{fmtEuro(b.einnahmen)}</b></div>
    <div class="karte"><small>Ausgaben</small><b class="tabular">{fmtEuro(b.ausgaben)}</b></div>
    <div class="karte" class:bad={b.neueSchulden > 0} class:good={b.neueSchulden <= 0}><small>{b.neueSchulden >= 0 ? "Neue Schulden" : "Überschuss"}</small><b class="tabular">{fmtEuro(Math.abs(b.neueSchulden))}</b></div>
    <div class="karte" class:good={b.delta > 0} class:bad={b.delta < 0}><small>ggü. Original</small><b class="tabular">{fmtDelta(b.delta)}</b></div>
  {/if}
</div>
{#if gesamt && showToepfe}
  <div class="salden">
    {#each gesamt.toepfe as t (t.id)}
      <span class:bad={t.saldo < 0} class:good={t.saldo >= 0}><b>{t.kurz}</b> {t.saldo >= 0 ? "Rücklage" : "Defizit"} {fmtEuro(Math.abs(t.saldo))}{#if t.saldo !== t.saldoOriginal} <i>(war {fmtDelta(t.saldoOriginal)})</i>{/if}{#if t.geschaetzt} <i title="Zwischen Stützjahren interpoliert">· geschätzt</i>{/if}</span>
    {/each}
  </div>
{/if}

<style>
  .seitenkopf { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; padding: 4px 0 0; }
  .titel { margin-right: auto; min-width: 240px; }
  h1 { margin: 0; font-size: 24px; color: var(--header); letter-spacing: -0.3px; line-height: 1.15; }
  h1 .real { display: block; font-size: 11px; font-weight: 400; color: var(--muted); letter-spacing: 0; }
  .titel p { margin: 3px 0 0; color: var(--muted); font-size: 13px; max-width: 720px; }
  .karte { display: flex; flex-direction: column; line-height: 1.15; min-width: 120px; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px 14px; }
  .karte small { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  .karte b { font-size: 16px; color: var(--header); }
  .karte.bad b { color: var(--bad); }
  .karte.good b { color: var(--good); }
  .karte.toepfe { cursor: pointer; text-align: left; font: inherit; }
  .salden { display: flex; gap: 14px; flex-wrap: wrap; padding: 6px 0; font-size: 12px; color: var(--fg); }
  .salden .bad { color: var(--bad); } .salden .good { color: var(--good); }
  .salden i { font-style: normal; color: var(--muted); }
  @media (max-width: 900px) {
    .titel { width: 100%; }
    h1 { font-size: 19px; }
    .karte { min-width: 0; flex: 1 1 40%; padding: 8px 10px; }
    .karte b { font-size: 14px; }
  }
</style>
