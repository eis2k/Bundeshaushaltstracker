<script lang="ts">
  import { fmtEuro, fmtPct } from "../model/format";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
</script>

<div class="presets">
  <span class="label">Presets</span>
  {#each app.presets as p (p.id)}
    <button class="chip" class:on={app.scenario.presets.includes(p.id)} title={p.beschreibung} onclick={() => app.togglePreset(p.id)}>{p.name}</button>
  {/each}
  {#if app.solver}
    <span class="solver" class:warn={!app.solver.erreichbar}>
      {#if app.solver.erreichbar}
        Schwarze Null: freie Titel auf {fmtPct(app.solver.faktor)} gekürzt, zusammen {fmtEuro(app.solver.gekuerzt)}.
      {:else}
        Schwarze Null nicht erreichbar: Selbst ohne alle freien Titel ({fmtEuro(app.solver.gekuerzt)} gestrichen) übersteigen die gebundenen Ausgaben die Einnahmen.
      {/if}
    </span>
  {/if}
  {#if app.fromShare}
    <span class="share-hint">Du siehst den Haushalt von jemand anderem. Du kannst daran weiterbauen.</span>
  {/if}
</div>

<style>
  .presets { display: flex; gap: 8px; padding: 10px 16px; background: var(--bg); border-bottom: 1px solid var(--border); flex-wrap: wrap; align-items: center; }
  .label { font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-right: 2px; }
  .chip { font-size: 12px; padding: 6px 10px; border-radius: 999px; border: 1px solid #d1d1d6; background: var(--panel); cursor: pointer; white-space: nowrap; color: var(--fg); }
  .chip.on { background: var(--header); color: #fff; border-color: var(--header); }
  .solver { font-size: 12px; color: var(--fg); background: #fef9c3; border-radius: 8px; padding: 4px 10px; }
  .solver.warn { background: #fee2e2; }
  .share-hint { font-size: 12px; color: var(--muted); font-style: italic; }
</style>
