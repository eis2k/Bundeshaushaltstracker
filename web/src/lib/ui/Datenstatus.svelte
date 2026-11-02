<script lang="ts">
  import { datenstatus } from "../model/datenstatus";
  import type { AppState } from "../state.svelte";
  import Jahresleiste from "./Jahresleiste.svelte";

  let { app }: { app: AppState } = $props();
  const modell = $derived(Object.keys(app.scenario.factors).length > 0 || app.scenario.presets.length > 0 || Object.keys(app.scenario.steuern ?? {}).length > 0);
  const d = $derived(datenstatus({
    view: app.view, seite: app.view === "empfaenger" && !!app.empfaengerSeite, jahr: app.jahr, stand: app.stand, real: app.real, bezugsjahr: app.bezugsjahr,
    erzeugt: app.index?.erzeugt.slice(0, 10) ?? null, modell,
    empfaengerStand: app.empfaengerIndex?.stand || null, personenStand: app.personIndex?.stand || null,
    letztesJahr: app.index?.jahre.at(-1) ?? null,
  }));
</script>

<div class="status" role="region" aria-label="Datenstatus">
  <span class="label">Datenstatus</span>
  {#if d.jahresleiste}
    <Jahresleiste {app} />
  {:else if d.jahr}
    <span class="wert"><b>{d.jahr}</b></span>
  {/if}
  <span class="wert">{d.preise}</span>
  {#if d.stand}<span class="wert">Stand {d.stand}</span>{/if}
  <span class="wert quellen">Quelle: {d.quellen.join(", ")}</span>
  {#if d.modell}<span class="chip">Modellrechnung, keine Prognose</span>{/if}
</div>

<style>
  .status { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 6px 20px 0; padding: 8px 14px; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); font-size: 12px; color: var(--muted); }
  .label { font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); }
  .wert b { color: var(--header); }
  .chip { background: var(--chip-orange); color: var(--header); border-radius: 999px; padding: 3px 9px; font-weight: 600; }
  @media (max-width: 900px) {
    .status { margin: 6px 12px 0; overflow-x: auto; flex-wrap: nowrap; white-space: nowrap; }
  }
</style>
