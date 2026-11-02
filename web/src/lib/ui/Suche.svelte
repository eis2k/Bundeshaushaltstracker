<script lang="ts">
  import { Building2, Landmark, Search, User } from "lucide-svelte";
  import { suche, type Treffer } from "../model/suche";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  let q = $state("");
  let offen = $state(false);
  let aktiv = $state(0);
  const treffer = $derived(offen ? suche(q, app.data, app.empfaengerIndex, app.personIndex) : []);

  function fokus() {
    offen = true;
    void app.ensureEmpfaenger();
    void app.ensurePersonen();
  }
  function oeffne(t: Treffer) {
    if (t.art === "ministerium") app.zeigeImFluss([t.id]);
    else if (t.art === "empfaenger") void app.openEmpfaenger(t.id);
    else void app.openAkte(t.id);
    q = "";
    offen = false;
  }
  function taste(e: KeyboardEvent) {
    if (e.key === "ArrowDown") { aktiv = Math.min(aktiv + 1, treffer.length - 1); e.preventDefault(); }
    else if (e.key === "ArrowUp") { aktiv = Math.max(aktiv - 1, 0); e.preventDefault(); }
    else if (e.key === "Enter" && treffer[aktiv]) { oeffne(treffer[aktiv]); e.preventDefault(); }
    else if (e.key === "Escape") offen = false;
  }
</script>

<div class="suche" role="search">
  <Search size={16} class="lupe" aria-hidden="true" />
  <input type="search" placeholder="Suche nach Ministerium, Empfänger, Person …" bind:value={q} onfocus={fokus} oninput={() => { offen = true; aktiv = 0; }} onkeydown={taste}
         onblur={() => setTimeout(() => (offen = false), 150)} aria-label="Suche" role="combobox" aria-autocomplete="list" aria-expanded={offen && treffer.length > 0} aria-controls="suche-treffer" />
  {#if offen && treffer.length}
    <ul class="treffer" id="suche-treffer" role="listbox">
      {#each treffer as t, i (t.art + t.id)}
        <li role="option" aria-selected={i === aktiv}>
          <button class:aktiv={i === aktiv} onmousedown={(e) => e.preventDefault()} onclick={() => oeffne(t)}>
            <span class="art">{#if t.art === "ministerium"}<Landmark size={14} />{:else if t.art === "empfaenger"}<Building2 size={14} />{:else}<User size={14} />{/if}</span>
            <span class="label">{t.label}</span><small>{t.neben}</small>
          </button>
        </li>
      {/each}
    </ul>
  {/if}
</div>

<style>
  .suche { position: relative; display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 0 10px; min-width: 260px; flex: 1; max-width: 460px; }
  .suche :global(.lupe) { color: var(--muted); flex: none; }
  input { flex: 1; border: 0; background: none; padding: 9px 0; font: inherit; font-size: 13px; color: var(--fg); outline: none; min-width: 0; }
  input::placeholder { color: var(--muted); }
  .treffer { position: absolute; left: 0; right: 0; top: calc(100% + 6px); background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius-s); box-shadow: 0 10px 30px rgba(23, 60, 102, .12); list-style: none; margin: 0; padding: 6px; z-index: 30; }
  .treffer button { width: 100%; display: grid; grid-template-columns: 22px 1fr; column-gap: 8px; align-items: center; text-align: left; background: none; border: 0; border-radius: 8px; padding: 7px 8px; font: inherit; color: var(--fg); cursor: pointer; }
  .treffer button:hover, .treffer button.aktiv { background: var(--chip-blau); }
  .treffer .art { color: var(--muted); display: inline-flex; grid-row: span 2; }
  .treffer .label { font-size: 13px; font-weight: 600; color: var(--header); }
  .treffer small { color: var(--muted); font-size: 11px; }
</style>
