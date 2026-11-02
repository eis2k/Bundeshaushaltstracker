<script lang="ts">
  /** Ministerien (Spec §4.11): Detailkarte des gewählten Einzelplans mit Reitern Geldflüsse | Empfänger | Verantwortung | Entwicklung, darunter alle Einzelpläne als Karten. */
  import { onMount } from "svelte";
  import { fmtEuro } from "../model/format";
  import { ministerien, type Ministerium } from "../model/ministerien";
  import { topEmpfaenger } from "../model/profiteure";
  import { parteiKurz } from "../model/verantwortung";
  import type { AppState } from "../state.svelte";
  import Avatar from "../ui/Avatar.svelte";
  import Partei from "../ui/Partei.svelte";
  import Fluss from "./Fluss.svelte";

  let { app }: { app: AppState } = $props();
  onMount(() => { void app.ensurePersonen(); void app.ensureEmpfaenger(); void app.ensureZeitreihe(); });

  const liste = $derived(app.viewData ? ministerien(app.viewData, app.stand, app.scenario.includeSv, app.jahr, app.index?.jahre.at(-1) ?? app.jahr, app.personIndex, app.empfaengerIndex) : []);
  const summe = $derived(liste.reduce((s, m) => s + m.ausgaben, 0));
  /** Gewählter Einzelplan; Vorgabe: das größte Ministerium (ohne Allgemeine Finanzverwaltung und Bundesschuld). */
  let gewaehlt = $state<string | null>(null);
  const m: Ministerium | undefined = $derived(liste.find((x) => x.epl === gewaehlt) ?? liste.find((x) => x.epl !== "60" && x.epl !== "32") ?? liste[0]);
  type Reiter = "geldfluesse" | "empfaenger" | "verantwortung" | "entwicklung";
  let reiter = $state<Reiter>("geldfluesse");
  const REITER: { id: Reiter; label: string }[] = [{ id: "geldfluesse", label: "Geldflüsse" }, { id: "empfaenger", label: "Empfänger" }, { id: "verantwortung", label: "Verantwortung" }, { id: "entwicklung", label: "Entwicklung" }];
  const LEITUNG = /^(bundeskanzler|bundesminister|chef)/i;
  const chef = $derived(m ? (m.leitung.find((l) => LEITUNG.test(l.amt)) ?? m.leitung[0] ?? null) : null);
  const anteil = $derived(m && summe ? Math.round((m.ausgaben / summe) * 1000) / 10 : 0);
  const letztesJahr = $derived(app.index?.jahre.at(-1) ?? app.jahr);
  const top = $derived(m ? topEmpfaenger(m.epl, app.jahr, app.empfaengerIndex, 5) : []);
  /** Fokus für den eingebetteten Fluss: Einzelplan, Kapitel und Titel bleiben hier lokal. */
  let fokus = $state<string[]>([]);
  let gewaehltKnoten = $state<string | null>(null);
  $effect(() => { if (m) { fokus = [m.epl]; gewaehltKnoten = m.epl; } });
  const entwicklung = $derived.by(() => {
    if (!m || !app.zeitreihe) return [];
    const s = app.zeitreihe.epl[m.epl];
    if (!s) return [];
    return app.zeitreihe.jahre.map((jahr, i) => ({ jahr, wert: app.stand === "ist" ? (s.ist[i] ?? s.soll[i]) : s.soll[i] })).filter((x): x is { jahr: number; wert: number } => x.wert != null);
  });
  const veraenderung = $derived(entwicklung.length > 1 && entwicklung[0].wert > 0 ? Math.round(((entwicklung[entwicklung.length - 1].wert - entwicklung[0].wert) / entwicklung[0].wert) * 1000) / 10 : null);
  function linie(w: { wert: number }[]): string {
    const vals = w.map((x) => x.wert);
    const min = Math.min(...vals), max = Math.max(...vals);
    return vals.map((v, i) => `${(i / Math.max(1, vals.length - 1)) * 320},${115 - ((v - min) / Math.max(1, max - min)) * 100}`).join(" ");
  }
  function rolle(amt: string): string { return /kanzler/i.test(amt) ? "Kanzler/in" : /^chef/i.test(amt) ? "Chef/in des Kanzleramts" : /^bundesministerin/i.test(amt) ? "Ministerin" : /^bundesminister/i.test(amt) ? "Minister" : amt; }
</script>

<div class="ministerien">
  {#if m}
    <article class="detail">
      <header>
        {#if chef}<Avatar name={chef.name} size={64} />{:else}<Avatar name={m.name} art="organisation" size={64} />{/if}
        <div class="kopf">
          <span class="epl">Einzelplan {m.epl}</span>
          <h3>{m.name}</h3>
          {#if chef}
            <span class="zeile">{rolle(chef.amt)}: <button class="link" onclick={() => void app.openAkte(chef.id)}>{chef.name}</button> {#if chef.partei}<Partei name={parteiKurz(chef.partei)} />{/if}</span>
          {:else}
            <span class="zeile muted">{m.leitungHinweis}</span>
          {/if}
          <span class="zeile">Haushalt {app.jahr} ({app.stand === "ist" ? "Ist" : "Soll"}): <b class="tabular">{fmtEuro(m.ausgaben)}</b> · Anteil am Gesamthaushalt: <b class="tabular">{anteil.toLocaleString("de-DE")} %</b></span>
        </div>
      </header>
      <div class="reiter" role="tablist" aria-label="Abschnitte der Ministeriumskarte">
        {#each REITER as r (r.id)}<button role="tab" aria-selected={reiter === r.id} class:on={reiter === r.id} onclick={() => (reiter = r.id)}>{r.label}</button>{/each}
      </div>
      {#if reiter === "geldfluesse"}
        {#if app.viewData}
          <Fluss data={app.viewData} scenario={app.scenario} factors={app.factors} focus={fokus} selected={gewaehltKnoten} topf="bund"
                 empfaengerByTitel={app.empfaengerByTitel} empfaengerSpalte={top} empfaengerJahr={letztesJahr}
                 onEmpfaenger={(id) => void app.openEmpfaenger(id)} onNetz={(epl) => void app.openNetz(`m:${epl}`)}
                 onFocus={(p) => (fokus = p.length ? p : [m!.epl])} onSelect={(id) => (gewaehltKnoten = id)} />
        {/if}
        <button class="chip" onclick={() => app.zeigeImFluss(fokus, gewaehltKnoten)}>Im Geldfluss öffnen</button>
      {:else if reiter === "empfaenger"}
        {#if top.length}
          <ul class="empf">
            {#each top as e (e.id)}
              <li><Avatar name={e.name} art="organisation" size={30} /><button class="link" onclick={() => void app.openEmpfaenger(e.id)}>{e.name}</button><span class="betrag"><b class="tabular">{fmtEuro(e.wert)}</b><small>{e.quelle === "haushalt" ? `Soll ${letztesJahr}` : "Lobbyregister, Untergrenze"}</small></span></li>
            {/each}
          </ul>
          <p class="muted small">Haushaltsbeträge aus Titeln, deren Zweckbestimmung den Empfänger nennt; Lobbyregister-Beträge sind Eigenangaben. Nicht addiert.</p>
        {:else}
          <p class="muted">Für diesen Einzelplan ist noch kein Empfänger mit Seite zugeordnet.</p>
        {/if}
        <button class="chip" onclick={() => app.openEmpfaengerListe({ epl: m!.epl })} disabled={!m.empfaenger}>{m.empfaenger} Empfänger mit Seite</button>
      {:else if reiter === "verantwortung"}
        {#if m.leitung.length}
          <ul class="leitung">
            {#each m.leitung as l (l.id)}
              <li><Avatar name={l.name} size={36} /><div><button class="link" onclick={() => void app.openAkte(l.id)}>{l.name}</button> {#if l.partei}<Partei name={parteiKurz(l.partei)} />{/if}<small class="muted">{l.amt}{#if l.seit} · seit {l.seit}{/if}{#if l.bis} · bis {l.bis}{/if}</small></div><button class="chip hell" onclick={() => void app.openAkte(l.id)}>Akte</button></li>
            {/each}
          </ul>
        {/if}
        {#if m.leitungHinweis}<p class="muted small">{m.leitungHinweis}</p>{/if}
        <p class="muted small">Leitung laut Bundesregierung und bundestag.de; Zeiträume nur mit Beleg. Zuständigkeit für einen Einzelplan ist keine Entscheidung über eine einzelne Zahlung.</p>
      {:else}
        {#if entwicklung.length > 1}
          <div class="entw">
            <span class="delta" class:gut={(veraenderung ?? 0) < 0} class:schlecht={(veraenderung ?? 0) > 0}>{veraenderung != null ? `${veraenderung > 0 ? "+" : ""}${veraenderung.toLocaleString("de-DE")} % seit ${entwicklung[0].jahr}` : ""}</span>
            <svg viewBox="0 0 320 125" class="linie" role="img" aria-label="Entwicklung der Ausgaben des Einzelplans">
              <polyline points={linie(entwicklung)} fill="none" stroke="var(--nav-on)" stroke-width="2.5" />
              {#each entwicklung as e, i}<circle cx={(i / Math.max(1, entwicklung.length - 1)) * 320} cy={linie(entwicklung).split(" ")[i].split(",")[1]} r="3" fill="var(--nav-on)"><title>{e.jahr}: {fmtEuro(e.wert)}</title></circle>{/each}
            </svg>
            <div class="achse"><span>{entwicklung[0].jahr}: {fmtEuro(entwicklung[0].wert)}</span><span>{entwicklung[entwicklung.length - 1].jahr}: {fmtEuro(entwicklung[entwicklung.length - 1].wert)}</span></div>
            <p class="muted small">{app.stand === "ist" ? "Ist" : "Soll"} je Jahr aus der Zeitreihe (bundeshaushalt.de), nominal; Ressortzuschnitte ändern sich zwischen Wahlperioden.</p>
          </div>
        {:else}
          <p class="muted">{app.zeitreihe ? "Keine Zeitreihe für diesen Einzelplan." : "Zeitreihe wird geladen …"}</p>
        {/if}
        <button class="chip" onclick={() => app.setView("gewachsen")}>Zum Zeitvergleich</button>
      {/if}
    </article>
  {/if}

  <p class="intro muted">Alle Einzelpläne {app.jahr} ({app.stand === "ist" ? "Ist" : "Soll"}, gezählt wie im Geldfluss). Klick wählt die Detailkarte oben.</p>
  <div class="karten">
    {#each liste as x (x.epl)}
      {@const leit = x.leitung.find((l) => LEITUNG.test(l.amt)) ?? x.leitung[0]}
      <button class="karte" class:on={m?.epl === x.epl} onclick={() => { gewaehlt = x.epl; reiter = "geldfluesse"; }} aria-pressed={m?.epl === x.epl}>
        <div class="kz">
          {#if leit}<Avatar name={leit.name} size={34} />{:else}<Avatar name={x.name} art="organisation" size={34} />{/if}
          <div class="kt"><span class="epl">Einzelplan {x.epl}</span><b>{x.name}</b><small class="muted">{leit ? `${leit.name}${leit.partei ? ` (${parteiKurz(leit.partei)})` : ""}` : x.leitungHinweis}</small></div>
        </div>
        <div class="zahl"><b class="tabular">{fmtEuro(x.ausgaben)}</b><small class="muted">{summe ? (Math.round((x.ausgaben / summe) * 1000) / 10).toLocaleString("de-DE") : 0} %</small></div>
        <div class="balken" aria-hidden="true"><span style="width:{summe ? (x.ausgaben / summe) * 100 : 0}%"></span></div>
      </button>
    {/each}
  </div>
</div>

<style>
  .ministerien { font-size: 13px; display: flex; flex-direction: column; gap: 12px; }
  .detail { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; display: flex; flex-direction: column; gap: 10px; }
  header { display: flex; gap: 12px; align-items: flex-start; }
  .kopf { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .epl { font-size: 10px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  h3 { margin: 0; font-size: 16px; color: var(--header); line-height: 1.25; }
  .zeile { font-size: 12px; color: var(--fg); display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
  .zeile b { color: var(--header); }
  .link { background: none; border: 0; padding: 0; font: inherit; color: var(--header); cursor: pointer; text-align: left; font-weight: 600; }
  .link:hover { text-decoration: underline; }
  .reiter { display: inline-flex; gap: 2px; background: var(--nav-bg); border-radius: 10px; padding: 3px; align-self: flex-start; flex-wrap: wrap; }
  .reiter button { background: none; border: 0; color: var(--header); padding: 5px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; opacity: .75; }
  .reiter button.on { background: var(--nav-on); color: var(--nav-on-fg); opacity: 1; }
  .chip { align-self: flex-start; font-size: 12px; padding: 6px 12px; border-radius: 999px; border: 0; background: var(--nav-on); color: var(--nav-on-fg); cursor: pointer; }
  .chip.hell { background: var(--chip-blau); color: var(--header); font-size: 11px; padding: 4px 10px; }
  .chip:disabled { opacity: .5; cursor: default; }
  .empf, .leitung { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; font-size: 12px; }
  .empf li { display: grid; grid-template-columns: 30px 1fr auto; gap: 8px; align-items: center; }
  .leitung li { display: grid; grid-template-columns: 36px 1fr auto; gap: 8px; align-items: center; }
  .leitung li div { display: flex; flex-direction: column; min-width: 0; }
  .leitung small { display: block; }
  .betrag { display: flex; flex-direction: column; align-items: flex-end; }
  .betrag b { color: var(--header); }
  .betrag small { color: var(--muted); font-size: 10px; }
  .entw { display: flex; flex-direction: column; gap: 4px; max-width: 560px; }
  .delta { align-self: flex-start; font-size: 12px; font-weight: 700; padding: 2px 8px; border-radius: 999px; background: var(--bg); color: var(--muted); }
  .delta.gut { color: var(--good); background: var(--chip-gruen); } .delta.schlecht { color: var(--bad); background: #fee2e2; }
  .linie { width: 100%; height: auto; }
  .achse { display: flex; justify-content: space-between; font-size: 11px; color: var(--muted); }
  .intro { margin: 0; font-size: 12px; }
  .karten { display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 10px; }
  .karte { text-align: left; font: inherit; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; display: flex; flex-direction: column; gap: 8px; cursor: pointer; }
  .karte:hover { border-color: var(--nav-on); }
  .karte.on { border-color: var(--nav-on); box-shadow: 0 0 0 2px var(--chip-blau); }
  .kz { display: flex; gap: 10px; align-items: center; }
  .kt { display: flex; flex-direction: column; min-width: 0; gap: 1px; }
  .kt b { font-size: 13px; color: var(--header); line-height: 1.2; }
  .kt small { font-size: 11px; }
  .zahl { display: flex; align-items: baseline; gap: 8px; }
  .zahl b { font-size: 16px; color: var(--header); }
  .balken { height: 6px; background: var(--nav-bg); border-radius: 999px; overflow: hidden; }
  .balken span { display: block; height: 100%; background: var(--nav-on); border-radius: 999px; }
  .muted { color: var(--muted); }
  .small { font-size: 11px; margin: 4px 0 0; }
</style>
