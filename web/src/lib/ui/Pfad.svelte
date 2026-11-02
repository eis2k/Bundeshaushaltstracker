<script lang="ts">
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const glieder = $derived(app.pfad);
  // Angezeigt, sobald eine Spur existiert oder das aktuelle Glied mehr als den Topf nennt.
  const zeigen = $derived(app.spur.length > 0 || glieder[glieder.length - 1]?.label.includes(" › "));
</script>

{#if zeigen}
  <nav class="pfad" aria-label="Recherchepfad">
    {#each glieder as g, i (i)}
      {#if i < glieder.length - 1}
        <button class="glied" class:fern={i < glieder.length - 3} onclick={() => void app.springe(i + app.spur.length - (glieder.length - 1))}>{g.label}</button><span class="trenner" aria-hidden="true">›</span>
      {:else}
        <span class="aktuell" aria-current="page">{g.label}</span>
      {/if}
    {/each}
  </nav>
{/if}

<style>
  .pfad { display: flex; align-items: center; flex-wrap: wrap; gap: 4px 6px; margin: 6px 20px 0; font-size: 12px; color: var(--muted); }
  .glied { background: none; border: 0; padding: 2px 4px; color: var(--accent); cursor: pointer; font: inherit; border-radius: 6px; }
  .glied:hover { background: var(--chip-blau); }
  .trenner { color: var(--muted); }
  .aktuell { color: var(--header); font-weight: 600; }
  @media (max-width: 900px) {
    .pfad { margin: 6px 12px 0; }
    .glied.fern { display: none; }
    .glied.fern + .trenner { display: none; }
  }
</style>
