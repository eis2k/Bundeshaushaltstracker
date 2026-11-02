<script lang="ts">
  import { onMount } from "svelte";
  import { filterePersonen, type PersonFilter } from "../model/personen";
  import type { AppState } from "../state.svelte";
  import { parteiKurz, parteiVon } from "../model/verantwortung";
  import Avatar from "../ui/Avatar.svelte";
  import Partei from "../ui/Partei.svelte";

  let { app }: { app: AppState } = $props();

  let q = $state("");
  let filter = $state<PersonFilter>("alle");
  let limit = $state(100);

  onMount(() => { void app.ensurePersonen(); });

  const index = $derived(app.personIndex);
  const rows = $derived(index ? filterePersonen(index, q, filter, true) : []);
  const shown = $derived(rows.slice(0, limit));
  const versteckt = $derived(index ? index.eintraege.filter((e) => !e.sichtbar).length : 0);
  const filters: { id: PersonFilter; label: string }[] = [
    { id: "alle", label: "Alle" },
    { id: "abgeordnete", label: "Abgeordnete" },
    { id: "regierung", label: "Bundesregierung" },
    { id: "vertreter", label: "Vertreter von Empfängern" },
  ];
</script>

<div class="personen">
  <h2>Personen</h2>
  <p class="intro">Menschen in öffentlicher Funktion: Abgeordnete, Mitglieder der Bundesregierung sowie Vorstände, Geschäftsführungen und Interessenvertreter von Organisationen, die Bundesmittel erhalten. Jede Angabe trägt Quelle und Datum.</p>

  {#if app.akteFehlt === "nicht freigeschaltet"}
    <div class="note">Diese Akte ist nicht freigeschaltet. Öffentlich sind Akten von Personen mit öffentlichem Amt, mit belegter Verbindung zur Entscheidungsseite oder nach Prüfung eines Belegs. Der Name steht weiter auf der Seite der Organisation; eine Freischaltung kann mit Beleg per Pull Request vorgeschlagen werden.</div>
  {:else if app.akteFehlt === "unbekannt"}
    <div class="note warn">Eine Akte mit dieser Kennung gibt es nicht (mehr).</div>
  {/if}

  <div class="controls">
    <input type="search" placeholder="Person suchen …" aria-label="Person suchen" bind:value={q} />
  </div>
  <div class="chips" role="group" aria-label="Funktion">
    {#each filters as f}
      <button class="chip" class:on={filter === f.id} aria-pressed={filter === f.id} onclick={() => (filter = f.id)}>{f.label}</button>
    {/each}
  </div>

  {#if !index}
    <div class="muted">Lade Personen …</div>
  {:else if !index.eintraege.length}
    <div class="muted">Noch keine Personen-Daten im Build.</div>
  {:else}
    <div class="total">{rows.length} Akten sichtbar · Stand {index.stand}{#if versteckt} · {versteckt} weitere Personen stehen nur auf den Seiten ihrer Organisationen (Relevanzregel){/if}</div>
    <table>
      <thead><tr><th>Name</th><th>Funktion</th><th class="num">Organisationen</th></tr></thead>
      <tbody>
        {#each shown as e (e.id)}
          <tr>
            <td class="name"><Avatar name={e.name} size={28} /><a href={`#v1;j=${app.jahr};a=personen;pe=${e.id}`} onclick={(ev) => { ev.preventDefault(); void app.openAkte(e.id); }}>{e.name}</a></td>
            <td>{e.funktion_kurz.replace(/^(Mitglied des Bundestages(?: bis [^,]+)?), .+$/, "$1")} {#if parteiVon(e)}<Partei name={parteiKurz(parteiVon(e)!)} />{/if}</td>
            <td class="num tabular">{e.n_organisationen || "–"}</td>
          </tr>
        {/each}
      </tbody>
    </table>
    {#if rows.length > shown.length}
      <button class="more" onclick={() => (limit += 100)}>Mehr anzeigen ({rows.length - shown.length} weitere)</button>
    {/if}
    <p class="small muted">Quellen: Lobbyregister des Deutschen Bundestags (Eigenangaben), Biografien auf bundestag.de (Selbstauskünfte), bundesregierung.de, Parteispenden-Veröffentlichungen des Bundestagspräsidenten. Korrekturen und Belege: Pull Request oder Issue im Repository.</p>
  {/if}
</div>

<style>
  .personen { font-size: 12px; }
  h2 { margin: 0 0 4px; font-size: 16px; }
  .intro { margin: 0 0 10px; color: var(--muted); }
  .note { background: var(--bg); border-left: 3px solid var(--accent); border-radius: 6px; padding: 6px 10px; margin-bottom: 8px; }
  .note.warn { border-left-color: var(--bad); }
  .controls { display: flex; gap: 12px; align-items: center; flex-wrap: wrap; margin-bottom: 8px; }
  input[type="search"] { font: inherit; font-size: 12px; padding: 5px 8px; border: 1px solid var(--border); border-radius: 6px; min-width: 220px; flex: 1; }
  .chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 10px; }
  .chip { font-size: 11px; padding: 5px 10px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); cursor: pointer; color: var(--fg); }
  .chip.on { background: var(--nav-on); color: var(--nav-on-fg); border-color: var(--nav-on); }
  .total { background: var(--bg); border-radius: 8px; padding: 6px 10px; margin-bottom: 10px; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 6px; border-bottom: 1px solid var(--border); }
  td { padding: 6px; border-bottom: 1px solid var(--border); }
  td.name { display: flex; align-items: center; gap: 8px; }
  td a { color: var(--header); font-weight: 700; text-decoration: none; }
  td a:hover { text-decoration: underline; }
  .num { text-align: right; white-space: nowrap; }
  .more { margin-top: 10px; font-size: 12px; background: var(--bg); border: 1px solid var(--border); border-radius: 8px; padding: 6px 12px; cursor: pointer; color: var(--fg); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; margin-top: 10px; }
</style>
