<script lang="ts">
  /** Seite „Daten & Quellen“ (Spec §4.12, Kachel 09): Tabelle der Quellen mit Stand und Lizenz, bekannte Lücken, Lizenzen. */
  import { onMount } from "svelte";
  import { Database, Download, ExternalLink } from "lucide-svelte";
  import { loadVpiInfo } from "../model/load";
  import { LIZENZEN, LUECKEN, quellenTabelle } from "../model/quellen";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  let vpi = $state<{ quelle?: string; stand?: string } | null>(null);
  onMount(() => { void app.ensureEmpfaenger(); void app.ensurePersonen(); loadVpiInfo().then((v) => (vpi = v)).catch(() => (vpi = null)); });
  const zeilen = $derived(quellenTabelle({ index: app.index, empfaenger: app.empfaengerIndex, personen: app.personIndex, vpi, steuern: app.steuern.length }));
</script>

<div class="daten">
  <section class="karte">
    <h3><Database size={16} /> Verwendete Datensätze</h3>
    <div class="scroll">
      <table>
        <thead><tr><th>Quelle</th><th>Inhalt</th><th>Zeitraum</th><th>Stand</th><th>Lizenz</th><th>Links</th></tr></thead>
        <tbody>
          {#each zeilen as z (z.quelle)}
            <tr>
              <td><b>{z.quelle}</b></td>
              <td class="inhalt">{z.inhalt}</td>
              <td class="tabular">{z.zeitraum}</td>
              <td class="tabular">{z.stand ?? "–"}</td>
              <td class="lizenz">{z.lizenz}</td>
              <td class="links"><a href={z.url} target="_blank" rel="noopener" title="Quelle öffnen"><ExternalLink size={14} /> Quelle</a>{#if z.datei}<a href={z.datei} download title="Aufbereitete Datei (JSON)"><Download size={14} /> JSON</a>{/if}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    <p class="muted small">„Stand“ ist das Datum der Aufbereitung oder des Abrufs, wie es in den Daten steht; kein Datum heißt: nicht erfasst. Rechtlich verbindlich sind die amtlichen Dokumente.</p>
  </section>
  <div class="zwei">
    <section class="karte">
      <h3>Bekannte Lücken</h3>
      <ul>{#each LUECKEN as l}<li>{l}</li>{/each}</ul>
      <p class="muted small">Lücken werden benannt, nicht geschätzt. Belege und Korrekturen: <a href="https://github.com/eis2k/Bundeshaushaltstracker/issues" target="_blank" rel="noopener">Meldeformular auf GitHub</a>.</p>
    </section>
    <section class="karte">
      <h3>Lizenzen</h3>
      <table class="liz">
        <tbody>{#each LIZENZEN as l (l.was)}<tr><td>{l.was}</td><td><a href={l.url} target="_blank" rel="noopener">{l.lizenz}</a></td></tr>{/each}</tbody>
      </table>
      <p class="muted small">Alle aufbereiteten Dateien liegen unter <code>/data/</code> und im <a href="https://github.com/eis2k/Bundeshaushaltstracker" target="_blank" rel="noopener">Repository</a> (Pipeline, Pflegedateien, Build).</p>
    </section>
  </div>
</div>

<style>
  .daten { display: flex; flex-direction: column; gap: 12px; font-size: 12px; }
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; min-width: 0; }
  h3 { margin: 0 0 10px; font-size: 14px; color: var(--header); display: flex; align-items: center; gap: 6px; }
  .scroll { overflow-x: auto; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 6px; border-bottom: 1px solid var(--border); }
  td { padding: 7px 6px; border-bottom: 1px solid var(--border); vertical-align: top; }
  td b { color: var(--header); }
  .inhalt { color: var(--fg); min-width: 220px; }
  .lizenz { color: var(--muted); white-space: nowrap; }
  .links { white-space: nowrap; }
  .links a { display: inline-flex; align-items: center; gap: 4px; margin-right: 10px; color: var(--accent); text-decoration: none; }
  .links a:hover { text-decoration: underline; }
  .zwei { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
  ul { margin: 0; padding-left: 18px; display: flex; flex-direction: column; gap: 6px; }
  .liz td:first-child { color: var(--fg); }
  code { font-size: 11px; background: var(--bg); padding: 1px 4px; border-radius: 4px; }
  .muted { color: var(--muted); } .small { font-size: 11px; margin: 10px 0 0; }
  @media (max-width: 800px) { .zwei { grid-template-columns: 1fr; } }
</style>
