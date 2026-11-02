<script lang="ts">
  import { onDestroy } from "svelte";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const jahre = $derived(app.index?.jahre ?? []);

  let timer: ReturnType<typeof setInterval> | null = null;
  let playing = $state(false);
  const svVerfuegbar = $derived((app.index?.sv_jahre ?? []).includes(app.jahr));

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
    playing = false;
  }
  function play() {
    if (timer) return stop();
    const start = jahre[0];
    if (app.jahr === jahre[jahre.length - 1]) void app.setJahr(start);
    playing = true;
    timer = setInterval(() => {
      const i = jahre.indexOf(app.jahr);
      if (i >= jahre.length - 1) return stop();
      void app.setJahr(jahre[i + 1]);
    }, 1200);
  }
  onDestroy(stop);
</script>

<div class="years">
  <button class="play" onclick={play} aria-label={playing ? "Anhalten" : "Jahre abspielen"}>{playing ? "❚❚" : "▶"} {playing ? "Stopp" : "Abspielen"}</button>
  <div class="track" role="tablist" aria-label="Haushaltsjahr">
    {#each jahre as j}
      <button role="tab" aria-selected={app.jahr === j} class:on={app.jahr === j} onclick={() => { stop(); void app.setJahr(j); }}>{j}</button>
    {/each}
  </div>
  <div class="mode">
    <button class:on={app.stand === "soll"} onclick={() => app.setStand("soll")} title="Beschlossener Haushaltsplan">Soll</button>
    <button class:on={app.stand === "ist"} disabled={!app.istVerfuegbar} onclick={() => app.setStand("ist")} title={app.istVerfuegbar ? "Tatsächliche Ausgaben laut Haushaltsrechnung" : "Für dieses Jahr liegt noch keine Haushaltsrechnung vor"}>Ist</button>
    <label class="sv" title="Alle Beträge in Preisen von {app.bezugsjahr} (Verbraucherpreisindex, Destatis)">
      <input type="checkbox" checked={app.real} onchange={(e) => void app.setReal((e.target as HTMLInputElement).checked)} />
      inflationsbereinigt
    </label>
    <label class="sv" class:off={!svVerfuegbar} title={svVerfuegbar ? "Sondervermögen (Bundeswehr, Klima- und Transformationsfonds, Infrastruktur …) mit anzeigen; Zahlungen zwischen Kern und Sondervermögen zählen dann nur einmal" : `Für ${app.jahr} veröffentlicht das Portal keine Wirtschaftspläne der Sondervermögen (nur ${(app.index?.sv_jahre ?? []).join(", ")})`}>
      <input type="checkbox" checked={app.scenario.includeSv} disabled={!svVerfuegbar} onchange={(e) => app.setIncludeSv((e.target as HTMLInputElement).checked)} />
      Nebenhaushalte{#if !svVerfuegbar} <small>(keine Daten {app.jahr})</small>{/if}
    </label>
  </div>
</div>

<style>
  .years { display: flex; align-items: center; gap: 10px; font-size: 12px; flex-wrap: wrap; flex: 1; min-width: 0; color: var(--fg); }
  .play { background: var(--nav-on); color: var(--nav-on-fg); border: 0; border-radius: 8px; padding: 4px 9px; font-weight: 700; cursor: pointer; font-size: 12px; white-space: nowrap; }
  .track { display: flex; flex: 1; min-width: 240px; }
  .track button { flex: 1; background: none; border: 0; color: var(--muted); padding: 5px 0; cursor: pointer; font-size: 12px; border-bottom: 2px solid transparent; }
  .track button.on { font-weight: 800; color: var(--nav-on); border-bottom-color: var(--nav-on); }
  .mode { display: flex; gap: 4px; align-items: center; }
  .mode button { background: var(--nav-bg); border: 0; color: var(--header); padding: 4px 8px; border-radius: 6px; cursor: pointer; font-size: 12px; }
  .mode button.on { background: var(--nav-on); color: var(--nav-on-fg); font-weight: 700; }
  .mode button:disabled { opacity: .3; cursor: not-allowed; }
  .sv { display: flex; gap: 4px; align-items: center; margin-left: 8px; color: var(--fg); cursor: pointer; }
  .sv.off { opacity: .4; cursor: not-allowed; }
  .sv small { font-size: 10px; }
  @media (max-width: 720px) {
    .track { order: 3; width: 100%; }
    .track button { font-size: 10px; padding: 4px 0; }
  }
</style>
