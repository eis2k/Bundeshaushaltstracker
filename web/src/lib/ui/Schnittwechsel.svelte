<script lang="ts">
  import type { Schnitt } from "../model/schnitte";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const schnitte: { id: Schnitt; label: string; title: string }[] = [
    { id: "ressort", label: "Nach Ministerium", title: "Einzelpläne, Kapitel, Titel" },
    { id: "kostenart", label: "Nach Kostenart", title: "Personal, Sachausgaben, Zinsen, Zuweisungen, Bau, Investitionen (Hauptgruppen des Gruppierungsplans)" },
    { id: "empfaengerart", label: "Nach Empfänger-Art", title: "Wer bekommt das Geld: Länder, Sozialversicherung, Unternehmen, Vereine, Privatpersonen, Ausland (nach Gruppierungsplan)" },
  ];
</script>

<div class="schnitt">
  <span class="label">Schnitt</span>
  {#each schnitte as s}
    <button class:on={app.schnitt === s.id} title={s.title} onclick={() => app.setSchnitt(s.id)}>{s.label}</button>
  {/each}
  {#if app.schnitt !== "ressort"}<span class="hint">Zuordnung nach Gruppierungsplan des Bundes; derselbe Haushalt, anders geschnitten.</span>{/if}
</div>

<style>
  .schnitt { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 10px; font-size: 11px; }
  .label { text-transform: uppercase; letter-spacing: .06em; color: var(--muted); font-size: 10px; }
  button { font-size: 11px; padding: 4px 9px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); cursor: pointer; color: var(--fg); }
  button.on { background: var(--nav-on); color: var(--nav-on-fg); border-color: var(--nav-on); }
  .hint { color: var(--muted); }
</style>
