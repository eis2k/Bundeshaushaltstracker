<script lang="ts">
  import { onMount } from "svelte";
  import { loadEmpfaenger, loadEmpfaengerIndex, loadGesetzFrei, loadIndex, loadKonkordanz, loadNetzIndex, loadNetzShard, loadPersonIndex, loadPersonShard, loadPresets, loadSozialkassen, loadSteuern, loadTexte, loadVpi, loadYear, loadZeitreihe } from "./lib/model/load";
  import { AppState } from "./lib/state.svelte";
  import Datenstatus from "./lib/ui/Datenstatus.svelte";
  import Kopfzeile from "./lib/ui/Kopfzeile.svelte";
  import Navigation from "./lib/ui/Navigation.svelte";
  import Panel from "./lib/ui/Panel.svelte";
  import Pfad from "./lib/ui/Pfad.svelte";
  import Presets from "./lib/ui/Presets.svelte";
  import Seitenkopf from "./lib/ui/Seitenkopf.svelte";
  import Unteransichten from "./lib/ui/Unteransichten.svelte";
  import Fluss from "./lib/views/Fluss.svelte";
  import Karte from "./lib/views/Karte.svelte";
  import Saeulen from "./lib/views/Saeulen.svelte";
  import Gewachsen from "./lib/views/Gewachsen.svelte";
  import Empfaenger from "./lib/views/Empfaenger.svelte";
  import EmpfaengerSeite from "./lib/views/EmpfaengerSeite.svelte";
  import Personen from "./lib/views/Personen.svelte";
  import Akte from "./lib/views/Akte.svelte";
  import Netz from "./lib/views/Netz.svelte";
  import Ministerien from "./lib/views/Ministerien.svelte";
  import Dashboard from "./lib/views/Dashboard.svelte";
  import Schnittwechsel from "./lib/ui/Schnittwechsel.svelte";

  const app = new AppState({ loadIndex, loadYear, loadPresets, loadGesetzFrei, loadZeitreihe, loadVpi, loadSozialkassen, loadTexte, loadKonkordanz, loadSteuern, loadEmpfaengerIndex, loadEmpfaenger, loadPersonIndex, loadPersonShard, loadNetzIndex, loadNetzShard });
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

  const haushalt = $derived(app.view === "fluss" || app.view === "karte" || app.view === "saeulen" || app.view === "gewachsen");
  const mitPanel = $derived(haushalt || app.view === "simulator");
</script>

<div class="app">
  <Kopfzeile {app} />
  <div class="raster">
    <Navigation {app} />
    <div class="rechts">
      <Seitenkopf {app} />
      <Datenstatus {app} />
      <Pfad {app} />
      {#if haushalt}
        <Presets {app} />
      {/if}
      <main class:breit={!mitPanel}>
        <section class="view" aria-busy={app.loading}>
          <Unteransichten {app} />
          {#if app.error}
            <div class="error">Daten konnten nicht geladen werden: {app.error}</div>
          {:else if !app.viewData}
            <div class="loading">Lade Haushalt …</div>
          {:else if app.view === "dashboard"}
            <Dashboard {app} />
          {:else if app.view === "fluss"}
            <Fluss data={app.viewData} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected}
                   topf={app.topf} sozialkassen={app.viewSozialkassen} modelle={app.aktiveSteuern.je}
                   empfaengerByTitel={app.empfaengerByTitel} onEmpfaenger={(id) => void app.openEmpfaenger(id)}
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
          {:else if app.view === "ministerien"}
            <Ministerien {app} />
          {:else if app.view === "simulator"}
            <div class="soon">Haushaltssimulator: Diese Ansicht entsteht gerade. Die Regler stehen rechts im Seitenpanel und auf den Haushaltsansichten.</div>
          {:else if app.view === "politik"}
            <Personen {app} />
          {:else if app.view === "empfaenger"}
            {#if app.empfaengerSeite}
              <EmpfaengerSeite {app} seite={app.empfaengerSeite} />
            {:else}
              <Empfaenger {app} />
            {/if}
          {:else if app.view === "personen"}
            {#if app.akte}
              <Akte {app} akte={app.akte} />
            {:else}
              <Personen {app} />
            {/if}
          {:else if app.view === "netz"}
            {#if app.netz}
              <Netz {app} umfeld={app.netz} />
            {:else}
              <div class="soon">{app.netzFehlt ? `Für „${app.netzFehlt}“ gibt es kein Umfeld: Der Knoten hat keine Kanten oder keine freigeschaltete Seite.` : app.netzLeer ? "Kein Knoten gewählt. Ein Umfeld öffnet sich von einer Akte oder einer Empfänger-Seite aus („Umfeld zeigen“)." : "Lade Umfeld …"} <button class="link" onclick={() => app.openPersonenListe()}>Zu den Personen</button></div>
            {/if}
          {:else}
            <div class="soon">Diese Ansicht ist noch im Aufbau.</div>
          {/if}
        </section>
        {#if app.view === "personen" || app.view === "politik" || app.view === "netz"}
          <aside class="panel hint">
            <b>Personen und Netz</b>
            <p>Akten zeigen nur, was amtlich veröffentlicht ist oder die Person selbst angegeben hat: Mandat, Amt, Posten, veröffentlichungspflichtige Angaben, Parteispenden ihrer Organisationen. Jede Zeile trägt Quelle und Datum.</p>
            <p>Öffentlich sind Akten von Personen mit öffentlichem Amt, mit belegter Verbindung oder nach Prüfung eines Belegs. Gleiche Namen werden nur mit Beleg zusammengeführt.</p>
            <p>Das Netz zeigt Geld (Ministerium → Organisation), Posten und Parteispenden zwei Schritte weit; Ministerien und Parteien werden nicht weiter ausgebreitet. Es ist eine Landkarte belegter Beziehungen, kein Urteil.</p>
            <p>Bezüge aus dem Amt sind die gesetzlich festgelegten Monatsbeträge mit Fundstelle; was nicht je Person veröffentlicht wird, steht als Lücke dabei.</p>
          </aside>
        {:else if app.view === "empfaenger"}
          <aside class="panel hint">
            <b>Empfänger-Seiten</b>
            <p>Belege aus Lobbyregister, Bundeshaushalt, Förderkatalog und bundestag.de. Eigenangaben sind als solche gekennzeichnet; Beträge aus verschiedenen Quellen werden nicht addiert.</p>
            <p>Verbindungen zwischen Entscheidern und Empfängern erscheinen nur mit Fundstelle und nur bei exakt gleichem Organisationsnamen oder nach menschlicher Prüfung.</p>
            <p>Fehlt ein Beleg oder stimmt etwas nicht: Auf jeder Seite gibt es „Fehler melden / Beleg einreichen“.</p>
          </aside>
        {:else if app.view === "ministerien"}
          <aside class="panel hint">
            <b>Ministerien</b>
            <p>Je Einzelplan: Leitung laut Bundesregierung, Ausgaben des Jahres und Empfänger mit Seite. Zuständigkeit für einen Einzelplan ist keine persönliche Entscheidung über eine einzelne Zahlung.</p>
          </aside>
        {:else if app.view === "dashboard"}
          <aside class="panel hint">
            <b>Dashboard</b>
            <p>Alle Zahlen stammen aus dem Bundeshaushalt (bundeshaushalt.de) und den amtlichen Registern; Modellrechnungen sind als solche gekennzeichnet.</p>
          </aside>
        {:else}
          <Panel {app} />
        {/if}
      </main>
      <footer>
        <span>Daten: <a href="https://www.bundeshaushalt.de" target="_blank" rel="noopener">bundeshaushalt.de</a> (Bundesministerium der Finanzen){#if app.index}, Stand der Aufbereitung {app.index.erzeugt.slice(0, 10)}{/if}. Rechtlich verbindlich sind die amtlichen Dokumente.</span>
        <span class="mobil-links"><a href="https://github.com/eis2k/Bundeshaushaltstracker" target="_blank" rel="noopener">Quellcode und Daten auf GitHub</a> · <a href="/impressum.html">Impressum</a> · <a href="/datenschutz.html">Datenschutz</a></span>
      </footer>
    </div>
  </div>
</div>

<style>
  .app { min-height: 100vh; background: var(--bg); display: flex; flex-direction: column; }
  .raster { display: grid; grid-template-columns: 250px minmax(0, 1fr); gap: 16px; padding: 14px 20px 0; flex: 1; align-items: start; }
  .rechts { display: flex; flex-direction: column; min-width: 0; gap: 8px; }
  .panel.hint { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; font-size: 12px; color: var(--muted); }
  .panel.hint b { color: var(--header); }
  .panel.hint p { margin: 6px 0; }
  .link { background: none; border: 0; color: var(--accent); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; }
  main { display: grid; grid-template-columns: minmax(0, 1fr) 300px; gap: 16px; align-items: start; }
  .view { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; min-height: 420px; }
  .view[aria-busy="true"] { opacity: .7; }
  .loading, .soon, .error { color: var(--muted); padding: 40px; text-align: center; }
  .error { color: var(--bad); }
  footer { display: flex; justify-content: space-between; gap: 12px; padding: 6px 0 16px; font-size: 11px; color: var(--muted); flex-wrap: wrap; }
  .mobil-links { display: none; }
  @media (max-width: 900px) {
    .raster { grid-template-columns: 1fr; padding: 10px 12px 0; }
    .rechts { padding-bottom: calc(76px + env(safe-area-inset-bottom)); }
    main { grid-template-columns: 1fr; }
    .mobil-links { display: inline; }
  }
</style>
