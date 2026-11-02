<script lang="ts">
  import { aktiverEintrag, unteransichten } from "../model/navigation";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const reiter = $derived(unteransichten(aktiverEintrag(app.view, app.gestalten)));
  function oeffne(view: string) {
    if (view === "personen") app.openPersonenListe();
    else if (view === "netz") app.setView("netz");
    else app.setView(view as typeof app.view);
  }
</script>

{#if reiter.length > 1}
  <div class="reiter" role="tablist" aria-label="Unteransichten">
    {#each reiter as r (r.view)}
      <button role="tab" aria-selected={app.view === r.view} class:on={app.view === r.view} onclick={() => oeffne(r.view)}>{r.label}</button>
    {/each}
  </div>
{/if}

<style>
  .reiter { display: inline-flex; gap: 4px; background: var(--nav-bg); border-radius: 10px; padding: 3px; margin-bottom: 10px; }
  .reiter button { background: none; border: 0; color: var(--header); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; opacity: .75; }
  .reiter button.on { background: var(--panel); opacity: 1; box-shadow: 0 1px 2px rgba(23, 60, 102, .08); }
</style>
