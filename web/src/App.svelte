<script lang="ts">
  import { onMount } from "svelte";
  import { loadGesetzFrei, loadIndex, loadKonkordanz, loadPresets, loadSozialkassen, loadSteuern, loadTexte, loadVpi, loadYear, loadZeitreihe } from "./lib/model/load";
  import { AppState } from "./lib/state.svelte";
  import Jahresleiste from "./lib/ui/Jahresleiste.svelte";
  import Kopfzeile from "./lib/ui/Kopfzeile.svelte";
  import Panel from "./lib/ui/Panel.svelte";
  import Presets from "./lib/ui/Presets.svelte";
  import Fluss from "./lib/views/Fluss.svelte";
  import Karte from "./lib/views/Karte.svelte";
  import Saeulen from "./lib/views/Saeulen.svelte";
  import Gewachsen from "./lib/views/Gewachsen.svelte";
  import Schnittwechsel from "./lib/ui/Schnittwechsel.svelte";

  const app = new AppState({ loadIndex, loadYear, loadPresets, loadGesetzFrei, loadZeitreihe, loadVpi, loadSozialkassen, loadTexte, loadKonkordanz, loadSteuern });
  let ready = $state(false);

  onMount(() => {
    void app.init(location.hash).then(() => (ready = true));
    // Ein von außen geänderter Hash (geteilter Link in derselben Seite) lädt den Zustand neu.
    const onHash = () => { if (location.hash.slice(1) !== app.toHash()) void app.init(location.hash); };
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  });

  $effect(() => {
    if (!ready) return;
    const hash = app.toHash();
    if (location.hash.slice(1) !== hash) history.replaceState(null, "", `#${hash}`);
  });
</script>

<div class="app">
  <Kopfzeile {app} />
  <Jahresleiste {app} />
  <Presets {app} />
  <main>
    <section class="view" aria-busy={app.loading}>
      {#if app.error}
        <div class="error">Daten konnten nicht geladen werden: {app.error}</div>
      {:else if !app.viewData}
        <div class="loading">Lade Haushalt …</div>
      {:else if app.view === "fluss"}
        <Fluss data={app.viewData} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected}
               topf={app.topf} sozialkassen={app.viewSozialkassen} modelle={app.aktiveSteuern.je}
               onFocus={(p) => app.setFocus(p)} onSelect={(id) => app.setSelected(id)} onTopf={(t) => app.setTopf(t)} />
      {:else if app.view === "karte"}
        <Schnittwechsel {app} />
        <Karte data={app.viewData} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected} schnitt={app.schnitt}
               onFocus={(p) => app.setFocus(p)} onSelect={(id) => app.setSelected(id)} />
      {:else if app.view === "saeulen"}
        <Schnittwechsel {app} />
        <Saeulen data={app.viewData} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected} schnitt={app.schnitt}
                 onFocus={(p) => app.setFocus(p)} onSelect={(id) => app.setSelected(id)} />
      {:else if app.view === "gewachsen"}
        <Gewachsen {app} />
      {:else}
        <div class="soon">Diese Ansicht ist noch im Aufbau.</div>
      {/if}
    </section>
    <Panel {app} />
  </main>
  <footer>
    <span>Daten: <a href="https://www.bundeshaushalt.de" target="_blank" rel="noopener">bundeshaushalt.de</a> (Bundesministerium der Finanzen){#if app.index}, Stand der Aufbereitung {app.index.erzeugt.slice(0, 10)}{/if}. Rechtlich verbindlich sind die amtlichen Dokumente.</span>
    <span><a href="https://github.com/eis2k/Bundeshaushaltstracker" target="_blank" rel="noopener">Quellcode und Daten auf GitHub</a> · <a href="/impressum.html">Impressum</a> · <a href="/datenschutz.html">Datenschutz</a></span>
  </footer>
</div>

<style>
  .app { min-height: 100vh; display: flex; flex-direction: column; }
  main { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 16px; padding: 16px; flex: 1; align-items: start; }
  .view { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px; min-height: 420px; }
  .view[aria-busy="true"] { opacity: .7; }
  .loading, .soon, .error { color: var(--muted); padding: 40px; text-align: center; }
  .error { color: var(--bad); }
  footer { display: flex; justify-content: space-between; gap: 12px; padding: 10px 16px 16px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }
  @media (max-width: 900px) {
    main { grid-template-columns: 1fr; }
  }
</style>
