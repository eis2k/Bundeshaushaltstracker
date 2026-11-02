<script lang="ts">
  /** Geldflüsse & Profiteure (Spec §4.11): Reiter, linke Kennzahlenkarten, Fluss in der Mitte, rechts Politische Verantwortung und Regler. */
  import { onMount } from "svelte";
  import { TrendingUp, Wallet } from "lucide-svelte";
  import { kennzahlen } from "../model/dashboard";
  import { fmtEuro } from "../model/format";
  import { anzahlEmpfaenger, topEmpfaenger, verantwortung } from "../model/profiteure";
  import { ausgabenNachEinzelplan, ringFarben } from "../model/bereiche";
  import Ring from "../ui/Ring.svelte";
  import type { AppState } from "../state.svelte";
  import HerkunftVerwendung from "../ui/HerkunftVerwendung.svelte";
  import Kennzahl from "../ui/Kennzahl.svelte";
  import Panel from "../ui/Panel.svelte";
  import Verantwortung from "../ui/Verantwortung.svelte";
  import Fluss from "./Fluss.svelte";

  let { app }: { app: AppState } = $props();
  onMount(() => { void app.ensureEmpfaenger(); void app.ensurePersonen(); });
  $effect(() => { app.jahr; void app.ensureVorjahr(); });

  const data = $derived(app.viewData!);
  const extraBund = $derived(app.aktiveSteuern.bund);
  const k = $derived(kennzahlen(data, app.vorjahrData, app.scenario.includeSv, app.factors, app.empfaengerIndex, app.personIndex, app.data ?? data, extraBund));
  const fokusEpl = $derived(app.topf === "bund" && app.focus.length ? app.focus[0] : null);
  const letztesJahr = $derived(app.index?.jahre.at(-1) ?? app.jahr);
  const v = $derived(verantwortung(fokusEpl, app.jahr, letztesJahr, data, app.scenario.includeSv, app.personIndex));
  const top = $derived(topEmpfaenger(v?.epl ?? null, app.jahr, app.empfaengerIndex));
  /** Empfänger-Spalte nur im letzten Jahr des Index: die Haushaltsbeträge der Empfänger liegen je Einzelplan nur für dieses Jahr vor (Review I2). */
  const spalte = $derived(fokusEpl && app.jahr === letztesJahr ? topEmpfaenger(fokusEpl, app.jahr, app.empfaengerIndex, 6) : []);
  const spalteGesamt = $derived(fokusEpl && app.jahr === letztesJahr ? anzahlEmpfaenger(fokusEpl, app.empfaengerIndex) : 0);
  /** Reiter „Nach Bereichen“ (Spec §4.12): Ring der Ausgaben je Einzelplan statt des Sankeys; lokal, nicht im Link. */
  let bereiche = $state(false);
  const teile = $derived.by(() => {
    const b = ausgabenNachEinzelplan(data, app.scenario.includeSv, app.factors, 8);
    const farben = ringFarben(b.map((x) => x.epl));
    return b.map((x, i) => ({ id: x.epl, label: x.label, wert: x.wert, anteil: x.anteil, farbe: farben[i] }));
  });
  // Fokuswechsel von außen (Verantwortung, Suche, Links) beendet die Bereichsansicht
  $effect(() => { app.focus; app.topf; bereiche = false; });
  const reiter = $derived([
    { id: "gesamt", label: "Gesamtübersicht", on: !bereiche && app.topf === "bund" && app.focus.length === 0 },
    { id: "ministerien", label: "Nach Ministerien", on: !bereiche && app.topf === "bund" && app.focus.length > 0 },
    { id: "bereiche", label: "Nach Bereichen", on: bereiche },
    { id: "empfaenger", label: "Nach Empfängern", on: false },
    { id: "zeit", label: "Zeitvergleich", on: false },
  ]);
  function waehle(id: string) {
    bereiche = id === "bereiche";
    if (id === "gesamt") { app.setTopf("bund"); app.setFocus([]); app.setSelected(null); }
    else if (id === "ministerien") { const epl = v?.epl; if (epl) app.zeigeImFluss([epl]); }
    else if (id === "empfaenger") app.openEmpfaengerListe();
    else if (id === "zeit") app.setView("gewachsen");
  }
  function bereichKlick(epl: string | null) {
    if (!epl) return;
    bereiche = false;
    app.zeigeImFluss([epl]);
  }
</script>

<div class="geldfluesse">
<div class="reiter" role="tablist" aria-label="Geldflüsse">
  {#each reiter as r (r.id)}
    <button role="tab" aria-selected={r.on} class:on={r.on} onclick={() => waehle(r.id)}>{r.label}</button>
  {/each}
</div>

<div class="seite">
  <aside class="links">
    <Kennzahl label={`Bundeshaushalt ${app.jahr}`} wert={fmtEuro(k.haushalt)} neben={k.veraenderung == null ? "" : `${k.veraenderung > 0 ? "+" : ""}${k.veraenderung.toLocaleString("de-DE")} % ggü. ${app.jahr - 1}`} ton="blau" icon={k.veraenderung != null && k.veraenderung > 0 ? TrendingUp : Wallet} />
    <HerkunftVerwendung {data} includeSv={app.scenario.includeSv} factors={app.factors} {extraBund} max={4} getrennt />
  </aside>
  <section class="mitte" aria-busy={app.loading}>
    {#if bereiche}
    <h3>Ausgaben nach Bereichen <small class="muted">{app.stand === "ist" ? "Ist" : "Soll"} {app.jahr}, Einzelpläne, mit deinen Reglern</small></h3>
    <div class="ring">
      <Ring {teile} mitte={{ wert: fmtEuro(app.balance?.ausgaben ?? 0), label: "Gesamthaushalt" }} onKlick={bereichKlick} />
      <ul class="teile">
        {#each teile as t (t.id ?? "rest")}
          <li><i style="background:{t.farbe}"></i>{#if t.id}<button class="link" onclick={() => bereichKlick(t.id)}>{t.label}</button>{:else}<span>{t.label}</span>{/if}<b class="tabular">{fmtEuro(t.wert)}</b><small class="tabular">{t.anteil.toLocaleString("de-DE")} %</small></li>
        {/each}
      </ul>
    </div>
    <p class="muted small">Klick auf einen Bereich fokussiert den Einzelplan im Geldfluss. Anteile an den Ausgaben des Bundes (ohne Sondervermögen, sofern nicht eingeblendet).</p>
    {:else}
    <h3>Geldfluss – Vom Steuerzahler zum Empfänger</h3>
    <Fluss {data} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected}
           topf={app.topf} sozialkassen={app.viewSozialkassen} modelle={app.aktiveSteuern.je}
           empfaengerByTitel={app.empfaengerByTitel} empfaengerSpalte={spalte} empfaengerGesamt={spalteGesamt} empfaengerJahr={letztesJahr}
           onEmpfaenger={(id) => void app.openEmpfaenger(id)} onNetz={(epl) => void app.openNetz(`m:${epl}`)} onEmpfaengerListe={(epl) => app.openEmpfaengerListe({ epl })}
           onFocus={(p) => app.setFocus(p)} onSelect={(id) => app.setSelected(id)} onTopf={(t) => app.setTopf(t)} />
    {/if}
  </section>
  <aside class="rechts">
    <Verantwortung {v} {top} jahr={app.jahr} empfaengerJahr={letztesJahr}
                   onAkte={(id) => void app.openAkte(id)} onEmpfaenger={(id) => void app.openEmpfaenger(id)} onFokus={(epl) => app.zeigeImFluss([epl])} />
    <Panel {app} />
  </aside>
</div>
</div>

<style>
  .geldfluesse { min-width: 0; }
  .reiter { display: inline-flex; gap: 4px; background: var(--nav-bg); border-radius: 10px; padding: 3px; margin-bottom: 10px; flex-wrap: wrap; }
  .reiter button { background: none; border: 0; color: var(--header); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 13px; font-weight: 600; opacity: .75; }
  .reiter button.on { background: var(--nav-on); color: var(--nav-on-fg); opacity: 1; }
  .seite { display: grid; grid-template-columns: 220px minmax(0, 1fr) 280px; gap: 12px; align-items: start; }
  .links, .rechts { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
  .mitte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; min-width: 0; }
  .mitte[aria-busy="true"] { opacity: .7; }
  h3 { margin: 0 0 8px; font-size: 14px; color: var(--header); display: flex; gap: 8px; align-items: baseline; flex-wrap: wrap; }
  h3 small { font-weight: 400; font-size: 11px; }
  .ring { display: grid; grid-template-columns: minmax(160px, 240px) minmax(0, 1fr); gap: 18px; align-items: center; }
  .ring :global(svg) { width: 100%; height: auto; }
  .teile { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
  .teile li { display: grid; grid-template-columns: 12px 1fr auto auto; gap: 8px; align-items: center; }
  .teile i { width: 12px; height: 12px; border-radius: 4px; display: inline-block; }
  .teile b { color: var(--header); }
  .teile small { color: var(--muted); min-width: 44px; text-align: right; }
  .link { background: none; border: 0; padding: 0; font: inherit; color: var(--header); cursor: pointer; text-align: left; }
  .link:hover { text-decoration: underline; }
  .muted { color: var(--muted); } .small { font-size: 11px; margin: 8px 0 0; }
  @media (max-width: 640px) { .ring { grid-template-columns: 1fr; justify-items: center; } }
  @media (max-width: 1200px) { .seite { grid-template-columns: minmax(0, 1fr) 300px; } .links { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  @media (max-width: 900px) { .seite { grid-template-columns: 1fr; } .links { grid-template-columns: 1fr; } }
</style>
