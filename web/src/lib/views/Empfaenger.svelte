<script lang="ts">
  import { onMount } from "svelte";
  import { EMPFAENGER_ART_LABELS, filtereEmpfaenger, type EmpfaengerArt, type EmpfaengerSort } from "../model/empfaenger";
  import { fmtEuro } from "../model/format";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();

  let q = $state("");
  let art = $state<EmpfaengerArt | "alle">("alle");
  let sort = $state<EmpfaengerSort>("bund");
  let limit = $state(100);

  onMount(() => { void app.ensureEmpfaenger(); });

  const index = $derived(app.empfaengerIndex);
  const letztesJahr = $derived(app.index ? app.index.jahre[app.index.jahre.length - 1] : app.jahr);
  const rows = $derived(index ? filtereEmpfaenger(index, q, art, sort, app.empfaengerFilterEpl) : []);
  const shown = $derived(rows.slice(0, limit));
  const arten: (EmpfaengerArt | "alle")[] = ["alle", "unternehmen", "verein_stiftung", "forschung", "oeffentlich", "kirche_wohlfahrt", "sonstige"];
  const sorts: { id: EmpfaengerSort; label: string }[] = [
    { id: "bund", label: "Bund laut Lobbyregister" },
    { id: "haushalt", label: "Haushaltstitel" },
    { id: "verbindungen", label: "Verbindungen" },
    { id: "name", label: "Name" },
  ];
  const eplName = $derived(app.empfaengerFilterEpl ? (app.data?.epl[app.empfaengerFilterEpl] ?? `Einzelplan ${app.empfaengerFilterEpl}`) : null);
</script>

<div class="empf">
  <h2>Empfänger von Bundesmitteln</h2>
  <p class="intro">Organisationen, die laut Lobbyregister Geld vom Bund erhalten oder die ein Haushaltstitel namentlich nennt. Drei Geldspalten aus drei Quellen; sie werden nicht addiert.</p>

  {#if app.empfaengerFehlt}
    <div class="note warn">Einen Empfänger mit der Kennung „{app.empfaengerFehlt}“ gibt es nicht (mehr). Unten die vollständige Liste.</div>
  {/if}
  {#if eplName}
    <div class="note">Gefiltert: Empfänger, die laut Lobbyregister oder Haushalt Geld aus „{eplName}“ erhalten (ohne Titelzuordnung). <button class="link" onclick={() => app.openEmpfaengerListe()}>Filter aufheben</button></div>
  {/if}

  <div class="controls">
    <input type="search" placeholder="Empfänger suchen …" aria-label="Empfänger suchen" bind:value={q} />
    <label>Sortierung
      <select bind:value={sort}>{#each sorts as s}<option value={s.id}>{s.label}</option>{/each}</select>
    </label>
  </div>
  <div class="chips" role="group" aria-label="Art des Empfängers">
    {#each arten as a}
      <button class="chip" class:on={art === a} aria-pressed={art === a} onclick={() => (art = a)}>{a === "alle" ? "Alle" : EMPFAENGER_ART_LABELS[a]}</button>
    {/each}
  </div>

  {#if !index}
    <div class="muted">Lade Empfänger …</div>
  {:else if !index.eintraege.length}
    <div class="muted">Noch keine Empfänger-Daten im Build.</div>
  {:else}
    <div class="total">{rows.length} Empfänger · Stand {index.stand}{#if !index.mit_personen} · Personenangaben in dieser Fassung nicht veröffentlicht{/if}</div>
    <table>
      <thead>
        <tr>
          <th>Empfänger</th>
          <th class="num">Bund laut Lobbyregister<small>Untergrenze, Eigenangabe</small></th>
          <th class="num">Haushaltstitel {letztesJahr}<small>Soll, namentlich genannt</small></th>
          <th class="num">Förderkatalog<small>Projektsummen</small></th>
          <th class="num">Verbindungen<small>belegt</small></th>
        </tr>
      </thead>
      <tbody>
        {#each shown as e (e.id)}
          <tr onclick={() => void app.openEmpfaenger(e.id)} tabindex="0" onkeydown={(ev) => (ev.key === "Enter" || ev.key === " ") && void app.openEmpfaenger(e.id)}>
            <td><b>{e.name}</b><small class="muted">{[e.rechtsform, e.sitz].filter(Boolean).join(" · ")}{#if e.lobbyregister} · {e.lobbyregister}{/if}</small></td>
            <td class="num tabular">{e.lobby_untergrenze_bund > 0 ? `ab ${fmtEuro(e.lobby_untergrenze_bund)}` : "–"}</td>
            <td class="num tabular">{e.haushalt_soll_letztes_jahr > 0 ? fmtEuro(e.haushalt_soll_letztes_jahr) : "–"}</td>
            <td class="num tabular">{e.foerderkatalog_summe > 0 ? fmtEuro(e.foerderkatalog_summe) : "–"}</td>
            <td class="num tabular">{e.n_verbindungen > 0 ? e.n_verbindungen : "–"}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if rows.length > shown.length}
      <button class="more" onclick={() => (limit += 100)}>Mehr anzeigen ({rows.length - shown.length} weitere)</button>
    {/if}
    <p class="small muted">Quellen: Lobbyregister des Deutschen Bundestags (Eigenangaben der Registrierten, Beträge in Spannen), bundeshaushalt.de (Titel, deren Zweckbestimmung den Empfänger nennt), Förderkatalog des Bundes (Projektförderung von sechs Ressorts). Jede Seite nennt ihre Quellen mit Datum.</p>
  {/if}
</div>

<style>
  .empf { font-size: 12px; }
  h2 { margin: 0 0 4px; font-size: 16px; }
  .intro { margin: 0 0 10px; color: var(--muted); }
  .note { background: var(--bg); border-left: 3px solid var(--accent); border-radius: 6px; padding: 6px 10px; margin-bottom: 8px; }
  .note.warn { border-left-color: var(--bad); }
  .link { background: none; border: 0; color: var(--header); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; }
  .controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
  .controls label { display: flex; gap: 4px; align-items: center; color: var(--muted); }
  input[type="search"] { font: inherit; font-size: 12px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; min-width: 220px; flex: 1; }
  select { font: inherit; font-size: 12px; padding: 3px 6px; border: 1px solid var(--border); border-radius: 6px; background: #fff; color: var(--fg); }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
  .chip { font-size: 11px; padding: 5px 10px; border-radius: 999px; border: 1px solid #d1d1d6; background: #fff; cursor: pointer; color: var(--fg); }
  .chip.on { background: var(--header); color: #fff; border-color: var(--header); }
  .total { background: var(--bg); border-radius: 8px; padding: 6px 10px; margin-bottom: 10px; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 6px; border-bottom: 1px solid var(--border); vertical-align: bottom; }
  th small { display: block; text-transform: none; letter-spacing: 0; font-weight: 400; }
  td { padding: 7px 6px; border-bottom: 1px solid #f0f0f2; vertical-align: middle; }
  td small { display: block; font-size: 10px; font-weight: 400; }
  tbody tr { cursor: pointer; }
  tbody tr:hover, tbody tr:focus { background: #fafafa; outline: none; }
  .num { text-align: right; white-space: nowrap; }
  .more { margin-top: 10px; font-size: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; cursor: pointer; color: var(--fg); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; margin-top: 10px; }
  @media (max-width: 720px) { th:nth-child(4), td:nth-child(4) { display: none; } td { padding: 5px 4px; } }
</style>
