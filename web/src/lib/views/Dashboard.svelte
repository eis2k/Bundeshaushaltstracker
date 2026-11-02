<script lang="ts">
  import { Building2, Coins, Landmark, Receipt, Search, Share2, SlidersHorizontal, Users, Wallet } from "lucide-svelte";
  import { onMount } from "svelte";
  import { entwicklungIndex, kennzahlen } from "../model/dashboard";
  import { fmtEuro, fmtPct } from "../model/format";
  import { chef as chefVon, ministerien } from "../model/ministerien";
  import { kabinett as kabinettDes, parteiKurz } from "../model/verantwortung";
  import Partei from "../ui/Partei.svelte";
  import { effectiveFactor, effectiveValue } from "../model/scenario";
  import { includeRow } from "../model/tree";
  import type { AppState } from "../state.svelte";
  import Avatar from "../ui/Avatar.svelte";
  import Kennzahl from "../ui/Kennzahl.svelte";
  import MiniFluss from "../ui/MiniFluss.svelte";
  import HerkunftVerwendung from "../ui/HerkunftVerwendung.svelte";

  let { app }: { app: AppState } = $props();
  onMount(() => { void app.ensureEmpfaenger(); void app.ensurePersonen(); void app.ensureZeitreihe(); });
  $effect(() => { app.jahr; void app.ensureVorjahr(); });

  const data = $derived(app.viewData!);
  const extraBund = $derived(app.aktiveSteuern.bund);
  const k = $derived(kennzahlen(data, app.vorjahrData, app.scenario.includeSv, app.factors, app.empfaengerIndex, app.personIndex, app.data ?? data, extraBund));
  const entwicklung = $derived(app.zeitreihe ? entwicklungIndex(app.zeitreihe, app.stand).filter((e) => e.gesamt != null) : []);
  const mins = $derived(ministerien(data, app.stand, app.scenario.includeSv, app.jahr, app.index?.jahre.at(-1) ?? app.jahr, app.personIndex, app.empfaengerIndex));
  const groesstes = $derived(mins.find((m) => m.epl !== "60" && m.epl !== "32") ?? mins[0]);
  const LEITUNG = /^(bundeskanzler|bundesminister|chef)/i;
  const chef = $derived(groesstes ? chefVon(groesstes.leitung) : null);

  const topEmpfaenger = $derived([...(app.empfaengerIndex?.eintraege ?? [])].sort((a, b) => b.haushalt_soll_letztes_jahr - a.haushalt_soll_letztes_jahr).slice(0, 5));
  const kabinett = $derived(kabinettDes(app.personIndex, app.jahr, app.index?.jahre.at(-1) ?? app.jahr).filter((m) => LEITUNG.test(m.amt)).slice(0, 5));
  const simulatorEpls = ["14", "30", "11"];
  /** Anteil des größten Einzelplans mit denselben Faktoren wie die Summe (Review M8). */
  const groesstesEffektiv = $derived(groesstes ? data.rows.filter((r) => r.art === "A" && r.epl === groesstes.epl && includeRow(r, app.scenario.includeSv)).reduce((s, r) => s + effectiveValue(r, app.factors), 0) : 0);
  const groesstesAnteil = $derived(app.balance && app.balance.ausgaben > 0 ? Math.round((groesstesEffektiv / app.balance.ausgaben) * 1000) / 10 : 0);

  /** Gemeinsame Skala für beide Linien; fehlende Werte unterbrechen die Linie nicht (werden übersprungen). */
  const skala = $derived.by(() => {
    const vals = entwicklung.flatMap((e) => [e.gesamt, e.investitionen]).filter((v): v is number => v != null);
    return { min: Math.min(...vals, 100), max: Math.max(...vals, 100) };
  });
  function punkt(i: number, v: number): string {
    const w = 320, h = 120;
    return `${(i / Math.max(1, entwicklung.length - 1)) * w},${h - ((v - skala.min) / Math.max(1, skala.max - skala.min)) * (h - 10) - 5}`;
  }
  function linie(key: "gesamt" | "investitionen"): string {
    return entwicklung.map((e, i) => (e[key] != null ? punkt(i, e[key]!) : null)).filter((p): p is string => p !== null).join(" ");
  }
  const hatInvestitionen = $derived(entwicklung.some((e) => e.investitionen != null));
</script>

<div class="dashboard">
  <div class="kennzahlen">
    <Kennzahl label={`Bundeshaushalt ${app.jahr}`} wert={fmtEuro(k.haushalt)} neben={k.veraenderung == null ? "" : `${k.veraenderung > 0 ? "+" : ""}${k.veraenderung.toLocaleString("de-DE")} % ggü. ${app.jahr - 1}`} ton="blau" icon={Wallet} />
    <Kennzahl label="Einnahmen" wert={fmtEuro(k.einnahmen)} neben={`davon Steuern ${fmtEuro(k.steuern)}`} ton="gruen" icon={Coins} />
    <Kennzahl label="Empfänger mit Seite" wert={k.empfaengerMitSeite.toLocaleString("de-DE")} neben="Lobbyregister und geprüfte Zuordnungen" ton="violett" icon={Building2} />
    <Kennzahl label="Personen-Akten" wert={k.aktenSichtbar.toLocaleString("de-DE")} neben="öffentlich sichtbar" ton="orange" icon={Users} />
  </div>

  <div class="reihe">
    <section class="karte">
      <HerkunftVerwendung {data} includeSv={app.scenario.includeSv} factors={app.factors} {extraBund} />
    </section>
    <section class="karte breit">
      <h3>Geldflüsse im Überblick <small class="muted">Steuern → Bundeshaushalt → größte Einzelpläne · {app.stand === "ist" ? "Ist" : "Soll"} {app.jahr}</small></h3>
      <MiniFluss {app} {data} factors={app.factors} includeSv={app.scenario.includeSv} {extraBund} />
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
      <h3>Aktuelle Entwicklung <small class="muted">Gesamtausgaben und Investitionen, Index {entwicklung[0]?.jahr ?? ""} = 100</small></h3>
      {#if entwicklung.length > 1}
        <svg viewBox="0 0 320 130" class="linie" role="img" aria-label="Entwicklung der Gesamtausgaben und der Investitionen als Index">
          {#if hatInvestitionen}<polyline points={linie("investitionen")} fill="none" stroke="var(--beitraege)" stroke-width="2" stroke-dasharray="5 3" />{/if}
          <polyline points={linie("gesamt")} fill="none" stroke="var(--nav-on)" stroke-width="2.5" />
          {#each entwicklung as e, i}
            {#if e.gesamt != null}<circle cx={punkt(i, e.gesamt).split(",")[0]} cy={punkt(i, e.gesamt).split(",")[1]} r="3" fill="var(--nav-on)"><title>{e.jahr}: Gesamtausgaben {e.gesamt.toLocaleString("de-DE")}</title></circle>{/if}
            {#if e.investitionen != null}<circle cx={punkt(i, e.investitionen).split(",")[0]} cy={punkt(i, e.investitionen).split(",")[1]} r="2.5" fill="var(--beitraege)"><title>{e.jahr}: Investitionen {e.investitionen.toLocaleString("de-DE")}</title></circle>{/if}
          {/each}
        </svg>
        <div class="achse"><span>{entwicklung[0].jahr}</span><span>{entwicklung[entwicklung.length - 1].jahr}: {entwicklung[entwicklung.length - 1].gesamt?.toLocaleString("de-DE")}{#if entwicklung[entwicklung.length - 1].investitionen != null}&nbsp;· Investitionen {entwicklung[entwicklung.length - 1].investitionen?.toLocaleString("de-DE")}{/if}</span></div>
        <div class="legende"><span><i style="background:var(--nav-on)"></i> Gesamtausgaben</span>{#if hatInvestitionen}<span><i class="dash" style="border-color:var(--beitraege)"></i> Investitionen (Hauptgruppen 7, 8)</span>{/if}</div>
        <p class="muted small">Quelle: bundeshaushalt.de, {app.stand === "ist" ? "Ist" : "Soll"}, Einzelpläne ohne Sondervermögen; Investitionen = Baumaßnahmen und sonstige Investitionen nach Gruppierungsplan.</p>
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
            <tr><td><button class="link zeile" onclick={() => void app.openEmpfaenger(e.id)}><Avatar name={e.name} art="organisation" size={24} id={`o:${e.id}`} />{e.name}</button></td><td class="num tabular">{fmtEuro(e.haushalt_soll_letztes_jahr)}</td></tr>
          {/each}
        </tbody>
      </table>
      <button class="mehr" onclick={() => app.openEmpfaengerListe()}>Alle Empfänger</button>
    </section>
    <section class="karte">
      <h3><Landmark size={16} /> Ministerium – Detailansicht</h3>
      {#if groesstes}
        <div class="minister">
          {#if chef}<Avatar name={chef.name} size={44} id={`p:${chef.id}`} />{:else}<Avatar name={groesstes.name} art="organisation" size={44} />{/if}
          <div><b>{groesstes.name}</b><small class="muted">{chef ? `${chef.amt}: ${chef.name}` : groesstes.leitungHinweis}</small><small>Haushalt {app.jahr}: <b class="tabular">{fmtEuro(groesstesEffektiv)}</b> · {groesstesAnteil.toLocaleString("de-DE")} % der Ausgaben</small></div>
        </div>
        <button class="mehr" onclick={() => app.setView("ministerien")}>Alle Ministerien</button>
      {/if}
    </section>
    <section class="karte">
      <h3><Users size={16} /> Politik & Verantwortung</h3>
      <ul class="personen">
        {#each kabinett as p (p.id)}
          <li><Avatar name={p.name} size={28} id={`p:${p.id}`} /><div><button class="link" onclick={() => void app.openAkte(p.id)}>{p.name}</button><small class="muted">{p.amt} {#if p.partei}<Partei name={parteiKurz(p.partei)} />{/if}</small></div>{#if p.epl}<button class="chip" onclick={() => app.zeigeImFluss([p.epl!])}>Zuständigkeiten</button>{/if}</li>
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
          <b class="tabular">{f === 1 ? "±0 %" : `${f > 1 ? "+" : "−"}${fmtPct(Math.abs(f - 1))}`}</b></label>
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
  .legende { display: flex; gap: 12px; font-size: 11px; color: var(--muted); margin-top: 4px; flex-wrap: wrap; }
  .legende i { display: inline-block; width: 14px; height: 3px; vertical-align: middle; margin-right: 4px; border-radius: 2px; }
  .legende i.dash { background: none; border-top: 2px dashed; height: 0; }
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
  .muted { color: var(--muted); } .small { font-size: 11px; }
  @media (max-width: 1200px) { .kennzahlen, .reihe.teaser { grid-template-columns: repeat(2, minmax(0, 1fr)); } .reihe { grid-template-columns: 1fr; } }
  @media (max-width: 700px) { .kennzahlen, .reihe.teaser { grid-template-columns: 1fr; } }
</style>
