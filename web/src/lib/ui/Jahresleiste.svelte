<script lang="ts">
  import { onDestroy } from "svelte";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const jahre = $derived(app.index?.jahre ?? []);

  let timer: ReturnType<typeof setInterval> | null = null;
  const playing = $derived(timer !== null);

  function stop() {
    if (timer) clearInterval(timer);
    timer = null;
  }
  function play() {
    if (timer) return stop();
    const start = jahre[0];
    if (app.jahr === jahre[jahre.length - 1]) void app.setJahr(start);
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
    <label class="sv" title="Sondervermögen, EU-Anlagen und Behörden-Wirtschaftspläne mit anzeigen">
      <input type="checkbox" checked={app.scenario.includeSv} onchange={(e) => app.setIncludeSv((e.target as HTMLInputElement).checked)} />
      Nebenhaushalte
    </label>
  </div>
</div>

<style>
  .years { display: flex; align-items: center; gap: 10px; padding: 8px 16px; background: #1f2937; color: #fff; font-size: 12px; flex-wrap: wrap; }
  .play { background: var(--accent); color: var(--header); border: 0; border-radius: 6px; padding: 4px 9px; font-weight: 700; cursor: pointer; font-size: 12px; white-space: nowrap; }
  .track { display: flex; flex: 1; min-width: 240px; }
  .track button { flex: 1; background: none; border: 0; color: inherit; opacity: .55; padding: 5px 0; cursor: pointer; font-size: 12px; border-bottom: 2px solid transparent; }
  .track button.on { opacity: 1; font-weight: 800; color: var(--accent); border-bottom-color: var(--accent); }
  .mode { display: flex; gap: 4px; align-items: center; }
  .mode button { background: rgba(255,255,255,.12); border: 0; color: inherit; opacity: .75; padding: 4px 8px; border-radius: 5px; cursor: pointer; font-size: 12px; }
  .mode button.on { background: #fff; color: var(--header); opacity: 1; font-weight: 700; }
  .mode button:disabled { opacity: .3; cursor: not-allowed; }
  .sv { display: flex; gap: 4px; align-items: center; margin-left: 8px; opacity: .85; cursor: pointer; }
  @media (max-width: 720px) {
    .track { order: 3; width: 100%; }
    .track button { font-size: 10px; padding: 4px 0; }
  }
</style>
