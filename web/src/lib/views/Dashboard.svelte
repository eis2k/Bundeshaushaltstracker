<script lang="ts">
  import { Building2, Coins, Landmark, Receipt, Search, Share2, SlidersHorizontal, Users, Wallet } from "lucide-svelte";
  import { onMount } from "svelte";
  import { entwicklungIndex, herkunftVerwendung, kennzahlen } from "../model/dashboard";
  import { fmtEuro, fmtPct } from "../model/format";
  import { ministerien } from "../model/ministerien";
  import { effectiveFactor } from "../model/scenario";
  import type { AppState } from "../state.svelte";
  import Avatar from "../ui/Avatar.svelte";
  import Kennzahl from "../ui/Kennzahl.svelte";
  import MiniFluss from "../ui/MiniFluss.svelte";
  import HerkunftVerwendung from "../ui/HerkunftVerwendung.svelte";

  let { app }: { app: AppState } = $props();
  onMount(() => { void app.ensureEmpfaenger(); void app.ensurePersonen(); void app.ensureZeitreihe(); });
  $effect(() => { app.jahr; void app.ensureVorjahr(); });

  const data = $derived(app.viewData!);
  const k = $derived(kennzahlen(data, app.vorjahrData, app.scenario.includeSv, app.factors, app.empfaengerIndex, app.personIndex));
  const hv = $derived(herkunftVerwendung(data, app.scenario.includeSv, app.factors));
  const entwicklung = $derived(app.zeitreihe ? entwicklungIndex(app.zeitreihe, app.stand).filter((e) => e.gesamt != null) : []);
  const mins = $derived(ministerien(data, app.stand, app.scenario.includeSv, app.jahr, app.index?.jahre.at(-1) ?? app.jahr, app.personIndex, app.empfaengerIndex));
  const groesstes = $derived(mins.find((m) => m.epl !== "60" && m.epl !== "32") ?? mins[0]);
  const LEITUNG = /^(bundeskanzler|bundesminister|chef)/i;
  const chef = $derived(groesstes ? (groesstes.leitung.find((l) => LEITUNG.test(l.amt)) ?? groesstes.leitung[0]) : undefined);

  const topEmpfaenger = $derived([...(app.empfaengerIndex?.eintraege ?? [])].sort((a, b) => b.haushalt_soll_letztes_jahr - a.haushalt_soll_letztes_jahr).slice(0, 5));
  const kabinett = $derived(mins.flatMap((m) => m.leitung.map((l) => ({ ...l, epl: m.epl, ressort: m.name }))).filter((l) => LEITUNG.test(l.amt)).slice(0, 5));
  const simulatorEpls = ["14", "30", "11"];
  const summeEntwicklung = $derived(hv.verwendung.reduce((s, x) => s + x.wert, 0));

  function linie(werte: { jahr: number; gesamt: number | null }[]): string {
    const vals = werte.map((w) => w.gesamt ?? 0);
    const min = Math.min(...vals, 100), max = Math.max(...vals, 100);
    const w = 320, h = 120;
    return vals.map((v, i) => `${(i / Math.max(1, vals.length - 1)) * w},${h - ((v - min) / Math.max(1, max - min)) * (h - 10) - 5}`).join(" ");
  }
</script>

<div class="dashboard">
  <div class="kennzahlen">
    <Kennzahl label={`Bundeshaushalt ${app.jahr}`} wert={fmtEuro(k.haushalt)} neben={k.veraenderung == null ? "" : `${k.veraenderung > 0 ? "+" : ""}${k.veraenderung.toLocaleString("de-DE")} % ggü. ${app.jahr - 1}`} nebenTon={k.veraenderung == null ? "" : k.veraenderung > 0 ? "schlecht" : "gut"} ton="blau" icon={Wallet} />
    <Kennzahl label="Einnahmen" wert={fmtEuro(k.einnahmen)} neben={`davon Steuern ${fmtEuro(k.steuern)}`} ton="gruen" icon={Coins} />
    <Kennzahl label="Empfänger mit Seite" wert={k.empfaengerMitSeite.toLocaleString("de-DE")} neben="Lobbyregister und geprüfte Zuordnungen" ton="violett" icon={Building2} />
    <Kennzahl label="Personen-Akten" wert={k.aktenSichtbar.toLocaleString("de-DE")} neben="öffentlich sichtbar" ton="orange" icon={Users} />
  </div>

  <div class="reihe">
    <section class="karte">
      <HerkunftVerwendung {data} includeSv={app.scenario.includeSv} factors={app.factors} />
    </section>
    <section class="karte breit">
      <h3>Geldflüsse im Überblick <small class="muted">Steuern → Bundeshaushalt → größte Einzelpläne · {app.stand === "ist" ? "Ist" : "Soll"} {app.jahr}</small></h3>
      <MiniFluss {app} {data} factors={app.factors} includeSv={app.scenario.includeSv} />
    </section>
    <section class="karte">
      <h3>Schnelleinstiege</h3>
      <div class="einstiege">
        <button onclick={() => app.setView("ministerien")}><Landmark size={16} />Ministerium analysieren</button>
        <button onclick={() => app.openEmpfaengerListe()}><Building2 size={16} />Empfänger recherchieren</button>
        <button onclick={() => app.setView("politik")}><Users size={16} />Person suchen</button>
        <button onclick={() => app.waehleUnteransicht("netz")}><Share2 size={16} />Verflechtungen zeigen</button>
        <button onclick={() => app.setView("simulator")}><SlidersHorizontal size={16} />Haushalt verändern</button>
      </div>
      <h3>Aktuelle Entwicklung <small class="muted">Gesamtausgaben, Index {entwicklung[0]?.jahr ?? ""} = 100</small></h3>
      {#if entwicklung.length > 1}
        <svg viewBox="0 0 320 130" class="linie" role="img" aria-label="Entwicklung der Gesamtausgaben als Index">
          <polyline points={linie(entwicklung)} fill="none" stroke="var(--nav-on)" stroke-width="2.5" />
          {#each entwicklung as e, i}<circle cx={(i / Math.max(1, entwicklung.length - 1)) * 320} cy={linie(entwicklung).split(" ")[i].split(",")[1]} r="3" fill="var(--nav-on)"><title>{e.jahr}: {e.gesamt?.toLocaleString("de-DE")}</title></circle>{/each}
        </svg>
        <div class="achse"><span>{entwicklung[0].jahr}</span><span>{entwicklung[entwicklung.length - 1].jahr}: {entwicklung[entwicklung.length - 1].gesamt?.toLocaleString("de-DE")}</span></div>
        <p class="muted small">Quelle: bundeshaushalt.de, Einzelpläne ohne Sondervermögen; Investitionen als eigene Reihe folgen.</p>
      {:else}
        <p class="muted small">Zeitreihe wird geladen …</p>
      {/if}
    </section>
  </div>

  <div class="reihe teaser">
    <section class="karte">
      <h3><Building2 size={16} /> Empfänger & Zuwendungen</h3>
      <table>
        <thead><tr><th>Empfänger</th><th class="num">Soll {app.index?.jahre.at(-1) ?? ""}</th></tr></thead>
        <tbody>
          {#each topEmpfaenger as e (e.id)}
            <tr><td><button class="link zeile" onclick={() => void app.openEmpfaenger(e.id)}><Avatar name={e.name} art="organisation" size={24} />{e.name}</button></td><td class="num tabular">{fmtEuro(e.haushalt_soll_letztes_jahr)}</td></tr>
          {/each}
        </tbody>
      </table>
      <button class="mehr" onclick={() => app.openEmpfaengerListe()}>Alle Empfänger</button>
    </section>
    <section class="karte">
      <h3><Landmark size={16} /> Ministerium – Detailansicht</h3>
      {#if groesstes}
        <div class="minister">
          {#if chef}<Avatar name={chef.name} size={44} />{:else}<Avatar name={groesstes.name} art="organisation" size={44} />{/if}
          <div><b>{groesstes.name}</b><small class="muted">{chef ? `${chef.amt}: ${chef.name}` : groesstes.leitungHinweis}</small><small>Haushalt {app.jahr}: <b class="tabular">{fmtEuro(groesstes.ausgaben)}</b> · {(summeEntwicklung ? Math.round((groesstes.ausgaben / summeEntwicklung) * 1000) / 10 : 0).toLocaleString("de-DE")} % der Ausgaben</small></div>
        </div>
        <button class="mehr" onclick={() => app.setView("ministerien")}>Alle Ministerien</button>
      {/if}
    </section>
    <section class="karte">
      <h3><Users size={16} /> Politik & Verantwortung</h3>
      <ul class="personen">
        {#each kabinett as p (p.id)}
          <li><Avatar name={p.name} size={28} /><div><button class="link" onclick={() => void app.openAkte(p.id)}>{p.name}</button><small class="muted">{p.amt}</small></div><button class="chip" onclick={() => app.zeigeImFluss([p.epl])}>Zuständigkeiten</button></li>
        {/each}
        {#if !kabinett.length}<li class="muted small">Leitung für {app.jahr} nicht erfasst.</li>{/if}
      </ul>
      <button class="mehr" onclick={() => app.setView("politik")}>Alle Personen</button>
    </section>
    <section class="karte">
      <h3><SlidersHorizontal size={16} /> Haushaltssimulator</h3>
      {#each simulatorEpls as epl}
        {@const f = effectiveFactor(epl, app.factors)}
        <label class="regler"><span>{data.epl[epl] ?? `Einzelplan ${epl}`}</span>
          <input type="range" min="0.5" max="1.5" step="0.05" value={f} oninput={(e) => app.setFactor(epl, Number((e.target as HTMLInputElement).value))} aria-label={`Faktor ${data.epl[epl] ?? epl}`} />
          <b class="tabular" class:gut={f < 1} class:schlecht={f > 1}>{f === 1 ? "±0 %" : `${f > 1 ? "+" : "−"}${fmtPct(Math.abs(f - 1))}`}</b></label>
      {/each}
      <button class="mehr" onclick={() => app.setView("simulator")}>Zum Simulator</button>
    </section>
  </div>
</div>

<style>
  .dashboard { display: flex; flex-direction: column; gap: 14px; }
  .kennzahlen { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
  .reihe { display: grid; grid-template-columns: 1fr 2fr 1fr; gap: 12px; align-items: start; }
  .reihe.teaser { grid-template-columns: repeat(4, minmax(0, 1fr)); }
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; min-width: 0; }
  h3 { margin: 0 0 10px; font-size: 14px; color: var(--header); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  h3 small { font-weight: 400; font-size: 11px; }
  .einstiege { display: flex; flex-direction: column; gap: 6px; margin-bottom: 14px; }
  .einstiege button { display: flex; align-items: center; gap: 8px; background: var(--bg); border: 1px solid var(--border); border-radius: 10px; padding: 8px 10px; font: inherit; font-size: 12px; color: var(--header); cursor: pointer; text-align: left; }
  .einstiege button:hover { background: var(--chip-blau); }
  .linie { width: 100%; height: auto; }
  .achse { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }
  table { width: 100%; border-collapse: collapse; font-size: 12px; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 4px 0; }
  td { padding: 5px 0; border-top: 1px solid var(--border); }
  .num { text-align: right; }
  .link { background: none; border: 0; color: var(--header); font: inherit; cursor: pointer; padding: 0; text-align: left; }
  .link.zeile { display: inline-flex; align-items: center; gap: 8px; }
  .mehr { margin-top: 10px; width: 100%; background: var(--chip-blau); color: var(--header); border: 0; border-radius: 10px; padding: 8px; font: inherit; font-size: 12px; font-weight: 600; cursor: pointer; }
  .minister { display: flex; gap: 10px; align-items: center; }
  .minister div { display: flex; flex-direction: column; gap: 2px; font-size: 12px; }
  .minister b { color: var(--header); }
  .personen { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .personen li { display: grid; grid-template-columns: 28px 1fr auto; gap: 8px; align-items: center; font-size: 12px; }
  .personen li div { display: flex; flex-direction: column; min-width: 0; }
  .personen .link { font-weight: 600; }
  .chip { font-size: 11px; padding: 4px 8px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); color: var(--header); cursor: pointer; white-space: nowrap; }
  .regler { display: grid; grid-template-columns: 1fr auto; gap: 2px 8px; font-size: 12px; margin-bottom: 8px; }
  .regler span { grid-column: 1 / 3; color: var(--fg); }
  .regler input { width: 100%; accent-color: var(--nav-on); }
  .regler b { min-width: 48px; text-align: right; color: var(--muted); }
  .regler b.gut { color: var(--good); } .regler b.schlecht { color: var(--bad); }
  .muted { color: var(--muted); } .small { font-size: 11px; }
  @media (max-width: 1200px) { .kennzahlen, .reihe.teaser { grid-template-columns: repeat(2, minmax(0, 1fr)); } .reihe { grid-template-columns: 1fr; } }
  @media (max-width: 700px) { .kennzahlen, .reihe.teaser { grid-template-columns: 1fr; } }
</style>
