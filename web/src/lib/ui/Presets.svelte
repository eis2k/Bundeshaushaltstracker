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
  {#if app.steuern.length}
    <span class="label sep">Steuer-Modelle</span>
    {#each app.steuern as s (s.id)}
      <button class="chip steuer" class:on={!!app.scenario.steuern?.[s.id]} aria-pressed={!!app.scenario.steuern?.[s.id]} title={s.beschreibung}
              onclick={() => { const aktiv = !!app.scenario.steuern?.[s.id]; if (aktiv && app.selected === `x:${s.id}`) { app.toggleSteuer(s.id); return; } if (!aktiv) app.toggleSteuer(s.id); app.setSelected(`x:${s.id}`); }}>
        {s.kurz}{#if s.status === "ausgesetzt"} <small>ausgesetzt</small>{/if}{#if s.empfaenger === "laender"} <small>Länder</small>{/if}
      </button>
    {/each}
  {/if}
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
  .presets { display: flex; gap: 8px; padding: 8px 20px 0; flex-wrap: wrap; align-items: center; }
  .label { font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--muted); margin-right: 2px; }
  .chip { font-size: 12px; padding: 6px 10px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); cursor: pointer; white-space: nowrap; color: var(--header); }
  .chip.on { background: var(--nav-on); color: var(--nav-on-fg); border-color: var(--nav-on); }
  .chip.steuer { border-style: dashed; }
  .chip small { font-size: 9px; opacity: .7; margin-left: 2px; }
  .label.sep { margin-left: 10px; }
  .solver { font-size: 12px; color: var(--fg); background: var(--chip-orange); border-radius: 8px; padding: 4px 10px; }
  .solver.warn { background: var(--bad-bg); }
  .share-hint { font-size: 12px; color: var(--muted); font-style: italic; }
</style>
