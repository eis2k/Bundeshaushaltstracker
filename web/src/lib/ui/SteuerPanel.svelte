<script lang="ts">
  import { fmtEuro } from "../model/format";
  import { aufkommen, defaultWerte, type SteuerSzenario } from "../model/steuern";
  import type { AppState } from "../state.svelte";

  let { app, szenario }: { app: AppState; szenario: SteuerSzenario } = $props();

  const aktiv = $derived(!!app.scenario.steuern?.[szenario.id]);
  const werte = $derived(app.scenario.steuern?.[szenario.id] ?? defaultWerte(szenario));
  const ergebnis = $derived(aufkommen(szenario, werte));
  const statusText = $derived(szenario.status === "ausgesetzt" ? "wird nicht mehr erhoben" : szenario.status === "nie_eingefuehrt" ? "nie eingeführt" : "wird erhoben");
  const empfaengerText = $derived(szenario.empfaenger === "laender" ? "Das Aufkommen steht nach Art. 106 GG den Ländern zu. Für den Bundeshaushalt ändert sich nichts, solange das Grundgesetz nicht geändert wird."
    : szenario.empfaenger === "bund" ? "Das Aufkommen steht dem Bund zu."
    : `Gemeinschaftsteuer: der Bund erhält ${(szenario.bund_anteil * 100).toLocaleString("de-DE", { maximumFractionDigits: 1 })} % des Aufkommens (Art. 106 GG), der Rest geht an Länder und Gemeinden.`);

  function clamp(a: { min: number; max: number; wert: number; id: string }): number {
    const v = werte[a.id] ?? a.wert;
    return Number.isFinite(v) ? Math.min(a.max, Math.max(a.min, v)) : a.wert;
  }
  function fmtWert(a: { einheit: string }, v: number): string {
    if (a.einheit === "%") return `${(v * 100).toLocaleString("de-DE", { maximumFractionDigits: 2 })} %`;
    if (a.einheit === "×") return `${v.toLocaleString("de-DE", { maximumFractionDigits: 2 })}×`;
    return `${v}`;
  }
  function host(u: string): string {
    try { return new URL(u).hostname.replace("www.", ""); } catch { return u; }
  }
</script>

<div class="path">Steuer-Modell · {statusText}</div>
<h3>{szenario.name}</h3>
<p class="desc">{szenario.beschreibung}</p>

<button class="toggle" class:on={aktiv} onclick={() => app.toggleSteuer(szenario.id)}>{aktiv ? "Im Haushalt aktiv · abschalten" : "In den Haushalt aufnehmen"}</button>

<div class="box modell">
  <b>Das ist ein Modell.</b> Es rechnet mit den Annahmen unten; jede Annahme hat einen Beleg und ist selbst ein Regler. Keine Prognose.
  <div class="basis">Basis: {szenario.modell.basis.text} ({szenario.modell.basis.jahr}, {fmtEuro(szenario.modell.basis.wert)}) · <a href={szenario.modell.basis.quelle} target="_blank" rel="noopener">{host(szenario.modell.basis.quelle)}</a></div>
  {#if szenario.modell.basis.jahr !== app.jahr}<div class="muted">Die Basis stammt aus {szenario.modell.basis.jahr}; sie wird für {app.jahr} nicht umgerechnet.</div>{/if}
</div>

{#each szenario.modell.annahmen as a (a.id)}
  <div class="annahme">
    <div class="kv"><span>{a.text}</span><b class="tabular">{fmtWert(a, clamp(a))}</b></div>
    <input type="range" min={a.min} max={a.max} step={a.schritt} value={clamp(a)} disabled={!aktiv}
           oninput={(e) => app.setAnnahme(szenario.id, a.id, Number((e.target as HTMLInputElement).value))} aria-label={a.text} aria-valuetext={fmtWert(a, clamp(a))} aria-describedby={aktiv ? undefined : "steuer-inaktiv"} />
    <div class="scale"><span>{fmtWert(a, a.min)}</span><span>Standard {fmtWert(a, a.wert)}</span><span>{fmtWert(a, a.max)}</span></div>
    <div class="src">Beleg: <a href={a.quelle} target="_blank" rel="noopener">{host(a.quelle)}</a></div>
  </div>
{/each}

<div class="box">
  <b>Wirkung</b>
  <div class="kv"><span>Mehreinnahmen gesamt (gegenüber heutigem Recht)</span><b class="tabular">{fmtEuro(ergebnis.gesamt)}</b></div>
  <div class="kv"><span>davon beim Bund</span><b class="tabular" class:good={ergebnis.bund > 0}>{fmtEuro(ergebnis.bund)}</b></div>
  <p class="muted">{empfaengerText} <a href={szenario.bund_anteil_quelle} target="_blank" rel="noopener">Art. 106 GG</a></p>
  {#if !aktiv}<p class="muted" id="steuer-inaktiv">Noch nicht aktiv: Schalte das Modell oben ein, damit es in die Bilanz eingeht.</p>{/if}
</div>

<div class="box">
  <b>Wer hat das beschlossen</b>
  <div class="tl">
    {#each szenario.geschichte as g (g.datum + g.titel)}
      <div class="ev">
        <div class="yr">{g.datum.slice(0, 4)}</div>
        <div>
          <b>{g.titel}</b>
          <p>{g.text}</p>
          <p class="muted">{g.akteure} · <a href={g.quelle} target="_blank" rel="noopener">{host(g.quelle)}</a></p>
        </div>
      </div>
    {/each}
  </div>
  <p class="muted">Belege, keine Wertung: Datum, Entscheidung, Beteiligte und Fundstelle. Was daraus folgt, entscheidet der Leser.</p>
</div>

<style>
  .path { color: var(--muted); font-size: 11px; margin-bottom: 4px; }
  h3 { margin: 0 0 6px; font-size: 14px; }
  .desc { margin: 0 0 8px; }
  .toggle { width: 100%; font: inherit; font-size: 12px; padding: 7px 10px; border-radius: 8px; border: 1px solid var(--header); background: var(--nav-on); color: var(--nav-on-fg); cursor: pointer; margin-bottom: 8px; }
  .toggle.on { background: var(--accent); color: var(--header); border-color: var(--accent); }
  .box { background: var(--bg); border-left: 3px solid var(--accent); border-radius: 6px; padding: 8px 10px; margin-top: 8px; }
  .box.modell { border-left-color: var(--warn); }
  .basis { margin-top: 6px; font-size: 11px; }
  .annahme { margin: 8px 0; }
  .kv { display: flex; justify-content: space-between; gap: 8px; padding: 3px 0; }
  input[type="range"] { width: 100%; margin: 6px 0 2px; accent-color: var(--header); }
  .scale { display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); }
  .src { font-size: 10px; color: var(--muted); }
  .good { color: var(--good); }
  .muted { color: var(--muted); }
  .tl .ev { display: grid; grid-template-columns: 44px 1fr; gap: 8px; padding: 6px 0; border-top: 1px solid var(--border); }
  .tl .ev:first-child { border-top: 0; }
  .yr { font-weight: 800; color: var(--muted); }
  .tl p { margin: 2px 0; }
</style>
