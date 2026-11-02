<script lang="ts">
  /** Geldflüsse & Profiteure (Spec §4.11): Reiter, linke Kennzahlenkarten, Fluss in der Mitte, rechts Politische Verantwortung und Regler. */
  import { onMount } from "svelte";
  import { TrendingUp, Wallet } from "lucide-svelte";
  import { kennzahlen } from "../model/dashboard";
  import { fmtEuro } from "../model/format";
  import { anzahlEmpfaenger, topEmpfaenger, verantwortung } from "../model/profiteure";
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
  const reiter = $derived([
    { id: "gesamt", label: "Gesamtübersicht", on: app.topf === "bund" && app.focus.length === 0 },
    { id: "ministerien", label: "Nach Ministerien", on: app.topf === "bund" && app.focus.length > 0 },
    { id: "empfaenger", label: "Nach Empfängern", on: false },
    { id: "zeit", label: "Zeitvergleich", on: false },
  ]);
  function waehle(id: string) {
    if (id === "gesamt") { app.setTopf("bund"); app.setFocus([]); app.setSelected(null); }
    else if (id === "ministerien") { const epl = v?.epl; if (epl) app.zeigeImFluss([epl]); }
    else if (id === "empfaenger") app.openEmpfaengerListe();
    else app.setView("gewachsen");
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
    <h3>Geldfluss – Vom Steuerzahler zum Empfänger</h3>
    <Fluss {data} scenario={app.scenario} factors={app.factors} focus={app.focus} selected={app.selected}
           topf={app.topf} sozialkassen={app.viewSozialkassen} modelle={app.aktiveSteuern.je}
           empfaengerByTitel={app.empfaengerByTitel} empfaengerSpalte={spalte} empfaengerGesamt={spalteGesamt} empfaengerJahr={letztesJahr}
           onEmpfaenger={(id) => void app.openEmpfaenger(id)} onNetz={(epl) => void app.openNetz(`m:${epl}`)} onEmpfaengerListe={(epl) => app.openEmpfaengerListe({ epl })}
           onFocus={(p) => app.setFocus(p)} onSelect={(id) => app.setSelected(id)} onTopf={(t) => app.setTopf(t)} />
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
  h3 { margin: 0 0 8px; font-size: 14px; color: var(--header); }
  @media (max-width: 1200px) { .seite { grid-template-columns: minmax(0, 1fr) 300px; } .links { grid-column: 1 / -1; display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); } }
  @media (max-width: 900px) { .seite { grid-template-columns: 1fr; } .links { grid-template-columns: 1fr; } }
</style>
