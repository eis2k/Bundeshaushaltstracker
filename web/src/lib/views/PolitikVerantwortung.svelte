<script lang="ts">
  /** Politik & Verantwortung (Spec §4.11): Reiter Ministerien (Kabinett des Jahres) und Personen (Liste mit Avataren und Partei). */
  import { onMount } from "svelte";
  import { kabinett, parteiKurz } from "../model/verantwortung";
  import type { AppState } from "../state.svelte";
  import Avatar from "../ui/Avatar.svelte";
  import Partei from "../ui/Partei.svelte";
  import Personen from "./Personen.svelte";

  let { app }: { app: AppState } = $props();
  onMount(() => { void app.ensurePersonen(); });
  let reiter = $state<"ministerien" | "personen">("ministerien");
  const letztesJahr = $derived(app.index?.jahre.at(-1) ?? app.jahr);
  const mitglieder = $derived(kabinett(app.personIndex, app.jahr, letztesJahr));
  const LEITUNG = /^(bundeskanzler|bundesminister|chef)/i;
  const spitze = $derived(mitglieder.filter((m) => LEITUNG.test(m.amt)));
  const weitere = $derived(mitglieder.filter((m) => !LEITUNG.test(m.amt)));
  function ressort(epl: string | null): string { return epl ? (app.viewData?.epl[epl] ?? `Einzelplan ${epl}`) : ""; }
</script>

<div class="pv">
  <div class="reiter" role="tablist" aria-label="Politik & Verantwortung">
    <button role="tab" aria-selected={reiter === "ministerien"} class:on={reiter === "ministerien"} onclick={() => (reiter = "ministerien")}>Ministerien</button>
    <button role="tab" aria-selected={reiter === "personen"} class:on={reiter === "personen"} onclick={() => (reiter = "personen")}>Personen</button>
  </div>
  {#if reiter === "ministerien"}
    <p class="intro">Wer {app.jahr} welchen Einzelplan verantwortet: Kabinett laut Bundesregierung, Partei aus Fraktion oder Kabinettsseite. Zuständigkeit für einen Einzelplan ist keine Entscheidung über eine einzelne Zahlung.</p>
    {#if !app.personIndex}
      <p class="muted">Lade Personen …</p>
    {:else if !mitglieder.length}
      <p class="muted">Für {app.jahr} ist keine Leitung mit belegtem Zeitraum erfasst.</p>
    {:else}
      {#snippet liste(items: typeof mitglieder)}
        <ul>
          {#each items as m (m.id)}
            <li>
              <Avatar name={m.name} size={40} id={`p:${m.id}`} />
              <div class="text">
                <button class="link" onclick={() => void app.openAkte(m.id)}>{m.name}</button>
                <small>{m.amt}{#if m.epl && !LEITUNG.test(m.amt)} · {ressort(m.epl)}{/if} {#if m.partei}<Partei name={parteiKurz(m.partei)} />{/if}</small>
              </div>
              <div class="knoepfe">
                {#if m.epl}<button class="chip" onclick={() => app.zeigeImFluss([m.epl!])}>Zuständigkeiten</button>{/if}
                <button class="chip hell" onclick={() => void app.openAkte(m.id)}>Akte</button>
              </div>
            </li>
          {/each}
        </ul>
      {/snippet}
      {@render liste(spitze)}
      {#if weitere.length}
        <h3>Staatsministerinnen, Staatsminister und Parlamentarische Staatssekretäre</h3>
        {@render liste(weitere)}
      {/if}
    {/if}
  {:else}
    <Personen {app} />
  {/if}
</div>

<style>
  .pv { font-size: 12px; }
  .reiter { display: inline-flex; gap: 4px; background: var(--nav-bg); border-radius: 10px; padding: 3px; margin-bottom: 10px; }
  .reiter button { background: none; border: 0; color: var(--header); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; opacity: .75; }
  .reiter button.on { background: var(--nav-on); color: var(--nav-on-fg); opacity: 1; }
  .intro { margin: 0 0 10px; color: var(--muted); }
  h3 { margin: 14px 0 6px; font-size: 12px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  li { display: grid; grid-template-columns: 40px 1fr auto; gap: 10px; align-items: center; background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 8px 10px; }
  .text { display: flex; flex-direction: column; min-width: 0; gap: 2px; }
  .text small { color: var(--muted); display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
  .link { background: none; border: 0; padding: 0; font: inherit; font-weight: 700; color: var(--header); cursor: pointer; text-align: left; font-size: 13px; }
  .link:hover { text-decoration: underline; }
  .knoepfe { display: flex; gap: 6px; flex-wrap: wrap; justify-content: flex-end; }
  .chip { font-size: 11px; padding: 5px 10px; border-radius: 999px; border: 0; background: var(--nav-on); color: var(--nav-on-fg); cursor: pointer; white-space: nowrap; }
  .chip.hell { background: var(--chip-blau); color: var(--header); }
  .muted { color: var(--muted); }
</style>
