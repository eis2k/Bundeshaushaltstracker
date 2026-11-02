<script lang="ts">
  /** Empfänger-Detailseite „Wer profitiert? – <Name>“ (Spec §4.11): Profilkarte links, Reiter, Übersicht mit Fluss, „Auf einen Blick“ und Karten. */
  import { onMount } from "svelte";
  import { BarChart3, Building2, FileText, Landmark, Scale, Share2, Users, Waypoints } from "lucide-svelte";
  import { EMPFAENGER_ART_LABELS, aufEinenBlick, fmtSpanne, geldAus, issueUrl, summeSeit, titelZeitreihe, zuwendungenJahr, type EmpfaengerSeite } from "../model/empfaenger";
  import { fmtEuro } from "../model/format";
  import { verantwortung } from "../model/profiteure";
  import type { AppState } from "../state.svelte";
  import Avatar from "../ui/Avatar.svelte";
  import EmpfaengerFluss from "../ui/EmpfaengerFluss.svelte";
  import Partei from "../ui/Partei.svelte";

  let { app, seite }: { app: AppState; seite: EmpfaengerSeite } = $props();
  onMount(() => { void app.ensurePersonen(); });

  type Reiter = "uebersicht" | "geldfluesse" | "verbindungen" | "personen" | "zeitverlauf" | "quellen";
  let reiter = $state<Reiter>("uebersicht");
  $effect(() => { seite.id; reiter = "uebersicht"; });
  const REITER: { id: Reiter; label: string }[] = [
    { id: "uebersicht", label: "Übersicht" }, { id: "geldfluesse", label: "Geldflüsse" }, { id: "verbindungen", label: "Verbindungen" },
    { id: "personen", label: "Personen" }, { id: "zeitverlauf", label: "Zeitverlauf" }, { id: "quellen", label: "Quellen" },
  ];

  const mitPersonen = $derived(app.empfaengerIndex?.mit_personen ?? true);
  const geber = $derived(geldAus(seite));
  const reihe = $derived(titelZeitreihe(seite, app.stand));
  const reiheMax = $derived(Math.max(1, ...reihe.map((r) => r.wert)));
  const jahre = $derived([...new Set(seite.haushalt.titel.flatMap((t) => Object.keys(t.werte)))].sort());
  const zj = $derived(zuwendungenJahr(seite, app.jahr, app.stand));
  const veraenderung = $derived(zj.vorjahr && zj.vorjahr > 0 ? Math.round(((zj.wert - zj.vorjahr) / zj.vorjahr) * 1000) / 10 : null);
  const seit2015 = $derived(summeSeit(seite, 2015, "soll"));
  const blick = $derived(aufEinenBlick(seite));
  const letztesJahr = $derived(app.index?.jahre.at(-1) ?? app.jahr);
  const zustaendigEpl = $derived(blick.eplHaushalt ?? blick.eplLobby);
  const v = $derived(zustaendigEpl && app.viewData ? verantwortung(zustaendigEpl, app.jahr, letztesJahr, app.viewData, app.scenario.includeSv, app.personIndex) : null);
  const LEITUNG = /^(bundeskanzler|bundesminister|chef)/i;
  const chef = $derived(v ? (v.leitung.find((l) => LEITUNG.test(l.amt)) ?? v.leitung[0] ?? null) : null);
  const mitAkte = $derived(seite.personen.filter((p) => p.akte_id && p.akte_sichtbar));
  const ja = $derived(seite.pflichtangaben?.jahresabschluss ?? null);
  const kz = $derived(ja?.kennzahlen ?? null);
  const kzLabels: Record<string, string> = {
    ertraege_gesamt: "Erträge gesamt", oeffentliche_hand: "davon Zuschüsse der öffentlichen Hand", spenden: "davon Spenden",
    personalaufwand: "Personalaufwand", projektfoerderung: "Projekt- und Betroffenenförderung", weitergeleitete_mittel: "Weitergeleitete Mittel", jahresergebnis: "Jahresergebnis",
  };
  function quote(z: number | null | undefined, n: number | null | undefined): string {
    if (!z || !n) return "";
    return ` (${Math.round((z / n) * 100)} % der Erträge, Rechnung)`;
  }
  function host(u: string | null): string {
    if (!u) return "";
    try { return new URL(u).hostname.replace("www.", ""); } catch { return u; }
  }
  function etikett(x: { abgleich: string }): string {
    return x.abgleich === "exakt" ? "automatisch abgeglichen" : x.abgleich === "geprueft" ? "von Hand geprüft" : "Eigenangabe im Lobbyregister";
  }
  function titelOeffnen(id: string) {
    const [epl, kap] = id.split("-");
    app.zeigeImFluss([epl, `${epl}-${kap}`, id], id);
  }
  function eplName(epl: string): string { return app.viewData?.epl[epl] ?? `Einzelplan ${epl}`; }
  function partei(p: { akte_id?: string | null }): string | null { return (p.akte_id ? app.personIndex?.eintraege.find((e) => e.id === p.akte_id)?.partei : null) ?? null; }
</script>

<article class="seite">
  <div class="top"><button class="back" onclick={() => app.openEmpfaengerListe()}>‹ Zurück zur Übersicht</button></div>
  <div class="raster">
    <aside class="profil">
      <div class="kopf">
        <Avatar name={seite.name} art="organisation" size={52} />
        <div><b>{seite.name}</b><small>{EMPFAENGER_ART_LABELS[seite.art] ?? seite.art}{#if seite.rechtsform} · {seite.rechtsform}{/if}</small>
          {#if seite.haushalt.titel.length}<span class="chip gruen">Öffentliche Mittel</span>{:else if seite.lobbyregister}<span class="chip">Lobbyregister</span>{/if}</div>
      </div>
      <ul class="kennzahlen">
        <li><span class="kachel blau"><Landmark size={15} /></span><div><small>Zuwendungen {app.jahr} ({app.stand === "ist" ? "Ist" : "Soll"})</small><b class="tabular">{seite.haushalt.titel.length ? fmtEuro(zj.wert) : "–"}</b></div>{#if veraenderung !== null}<span class="delta" class:gut={veraenderung < 0} class:schlecht={veraenderung > 0}>{veraenderung > 0 ? "+" : ""}{veraenderung.toLocaleString("de-DE")} %</span>{/if}</li>
        <li><span class="kachel blau"><FileText size={15} /></span><div><small>Haushaltstitel</small><b class="tabular">{seite.haushalt.titel.length}</b></div></li>
        <li><span class="kachel blau"><BarChart3 size={15} /></span><div><small>Seit 2015 (Soll, Titel)</small><b class="tabular">{seite.haushalt.titel.length ? fmtEuro(seit2015) : "–"}</b></div></li>
        {#if seite.lobby_untergrenze_bund > 0}<li><span class="kachel"><Scale size={15} /></span><div><small>Lobbyregister, Bund</small><b class="tabular">ab {fmtEuro(seite.lobby_untergrenze_bund)}</b></div></li>{/if}
      </ul>
      <button class="knopf" onclick={() => (reiter = "geldfluesse")}>Alle Zahlungen</button>
      <button class="knopf hell" onclick={() => void app.openNetz(`e:${seite.id}`)}><Share2 size={14} /> Umfeld zeigen</button>
      <div class="meta">
        {#if seite.sitz}<span>{seite.sitz}</span>{/if}
        {#if seite.lobbyregister}<span>Lobbyregister <a href={seite.lobbyregister.url} target="_blank" rel="noopener">{seite.lobbyregister.nummer}</a></span>{/if}
        {#if seite.website}<span><a href={seite.website.startsWith("http") ? seite.website : `https://${seite.website}`} target="_blank" rel="noopener">{seite.website.replace(/^https?:\/\//, "")}</a></span>{/if}
      </div>
    </aside>

    <div class="inhalt">
      <header>
        <h2>Wer profitiert? – {seite.name}</h2>
        <p class="unter">Geldflüsse, Verantwortliche und belegte Verbindungen im Überblick.</p>
      </header>
      <div class="reiter" role="tablist" aria-label="Abschnitte der Empfänger-Seite">
        {#each REITER as r (r.id)}<button role="tab" aria-selected={reiter === r.id} class:on={reiter === r.id} onclick={() => (reiter = r.id)}>{r.label}</button>{/each}
      </div>

      {#if reiter === "uebersicht"}
        <div class="oben">
          <section class="block">
            <EmpfaengerFluss {seite} jahr={app.jahr} stand={app.stand} onEpl={(epl) => app.zeigeImFluss([epl])} onTitel={titelOeffnen} />
          </section>
          <section class="block blick">
            <h3>Auf einen Blick</h3>
            <ul>
              {#if blick.eplHaushalt}
                <li><span class="kachel blau"><Landmark size={15} /></span><div><small>Zuständiges Ministerium (Haushaltstitel)</small><button class="link" onclick={() => app.zeigeImFluss([blick.eplHaushalt!])}>{eplName(blick.eplHaushalt)}</button></div></li>
              {/if}
              {#if blick.eplLobby && blick.eplLobby !== blick.eplHaushalt}
                <li><span class="kachel"><Scale size={15} /></span><div><small>Geldgeber laut Lobbyregister</small><button class="link" onclick={() => app.zeigeImFluss([blick.eplLobby!])}>{eplName(blick.eplLobby)}</button></div></li>
              {/if}
              {#if v}
                <li>{#if chef}<Avatar name={chef.name} size={30} />{:else}<span class="kachel"><Users size={15} /></span>{/if}<div><small>Politische Verantwortung {app.jahr}</small>{#if chef}<button class="link" onclick={() => void app.openAkte(chef.id)}>{chef.amt.split(" ")[0]}: {chef.name}</button> <Partei name={chef.partei ?? null} />{:else}<span class="muted">{v.hinweis}</span>{/if}</div></li>
              {/if}
              {#if blick.vertretung}
                <li><Avatar name={blick.vertretung.name} size={30} /><div><small>{blick.vertretung.funktion || "Gesetzliche Vertretung"} (laut Lobbyregister)</small><button class="link" onclick={() => void app.openAkte(blick.vertretung!.akte_id!)}>{blick.vertretung.name}</button></div></li>
              {/if}
              {#if !blick.eplHaushalt && !blick.eplLobby && !blick.vertretung}<li class="muted">Keine Zuordnung in den ausgewerteten Quellen.</li>{/if}
            </ul>
            <p class="muted small">Zuständigkeit für einen Einzelplan ist keine persönliche Entscheidung über eine einzelne Zahlung.</p>
          </section>
        </div>

        <div class="karten">
          <section class="block">
            <h3><Share2 size={15} /> Verbindungsanalyse – Netzwerk</h3>
            {#if !mitPersonen}
              <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
            {:else}
              <div class="netzvorschau">
                <Avatar name={seite.name} art="organisation" size={40} />
                {#each mitAkte.slice(0, 4) as p}<Avatar name={p.name} size={32} />{/each}
                {#if geber.length}<span class="kachel blau" title={geber.join(", ")}><Landmark size={15} /></span>{/if}
              </div>
              <p class="muted small">{mitAkte.length} {mitAkte.length === 1 ? "Person" : "Personen"} mit Akte, {seite.verbindungen.length} belegte {seite.verbindungen.length === 1 ? "Verbindung" : "Verbindungen"}{#if geber.length}, Geld von {geber.length} {geber.length === 1 ? "Stelle" : "Stellen"} des Bundes{/if}.</p>
              <button class="knopf" onclick={() => void app.openNetz(`e:${seite.id}`)}>Umfeld zeigen</button>
            {/if}
          </section>
          <section class="block">
            <h3><Users size={15} /> Personen & Funktionen</h3>
            {#if !mitPersonen}
              <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
            {:else if seite.personen.length === 0}
              <p class="muted">Keine Angaben zu gesetzlichen Vertretern in den ausgewerteten Quellen.</p>
            {:else}
              <ul class="pliste">
                {#each seite.personen.slice(0, 4) as p}
                  <li><Avatar name={p.name} size={30} /><div><b>{p.name}</b> <Partei name={partei(p)} /><small class="muted">{p.funktion || (p.rolle === "interessenvertreter" ? "Interessenvertretung" : "gesetzliche Vertretung")}{#if p.regierungsfunktion} · {p.regierungsfunktion.funktion}{/if}</small></div>
                    {#if p.akte_id && p.akte_sichtbar}<button class="chip knopfchip" onclick={() => void app.openAkte(p.akte_id!)}>Akte</button>{/if}</li>
                {/each}
              </ul>
              <button class="knopf hell" onclick={() => (reiter = "personen")}>Alle beteiligten Personen anzeigen</button>
            {/if}
          </section>
          <section class="block">
            <h3><BarChart3 size={15} /> Zeitverlauf der Zahlungen</h3>
            {#if reihe.length > 1}
              <svg class="balken" viewBox={`0 0 ${reihe.length * 34} 70`} role="img" aria-label="Summe der Titel je Jahr">
                {#each reihe as r, i}
                  <rect x={i * 34 + 4} y={56 - (r.wert / reiheMax) * 44} width="26" height={(r.wert / reiheMax) * 44} rx="3" fill={r.jahr === app.jahr ? "var(--nav-on)" : "#9cc3ee"}><title>{r.jahr}: {fmtEuro(r.wert)}</title></rect>
                  <text x={i * 34 + 17} y="66" text-anchor="middle" font-size="8">{String(r.jahr).slice(2)}</text>
                {/each}
              </svg>
              <p class="muted small">Summe der Haushaltstitel je Jahr ({app.stand === "ist" ? "Ist" : "Soll"}), bundeshaushalt.de.</p>
            {:else if reihe.length === 1}
              <p class="muted">Nur ein Jahr mit Werten: {reihe[0].jahr}, {fmtEuro(reihe[0].wert)}.</p>
            {:else}
              <p class="muted">Kein Haushaltstitel nennt diesen Empfänger namentlich.</p>
            {/if}
            <button class="knopf hell" onclick={() => (reiter = "zeitverlauf")}>Tabelle je Jahr</button>
          </section>
        </div>

        <div class="karten zwei">
          <section class="block">
            <h3><Landmark size={15} /> Politische Verbindungen</h3>
            <ul class="haken">
              <li><span class="tag">{seite.lobbyregister ? "ja" : "nein"}</span> Eintrag im Lobbyregister{#if seite.lobbyregister}: <a href={seite.lobbyregister.url} target="_blank" rel="noopener">{seite.lobbyregister.nummer}</a>{/if}</li>
              <li><span class="tag">{seite.lobby_zuwendungen.length}</span> Zuwendungen des Bundes laut Register{#if seite.lobby_untergrenze_bund > 0}, zusammen ab {fmtEuro(seite.lobby_untergrenze_bund)}{/if}</li>
              <li><span class="tag">{seite.parteispenden?.length ?? 0}</span> veröffentlichungspflichtige Parteispenden{#if seite.parteispenden?.length}: {[...new Set(seite.parteispenden.map((s) => s.partei))].join(", ")}{/if}</li>
              <li><span class="tag">{seite.verbindungen.length}</span> belegte Verbindungen zu Personen mit öffentlichem Amt</li>
            </ul>
            <button class="knopf hell" onclick={() => (reiter = "verbindungen")}>Details zu den Verbindungen</button>
          </section>
          <section class="block">
            <h3><FileText size={15} /> Quellen & Nachweise</h3>
            <ul class="qliste">
              {#each seite.quellen.slice(0, 5) as q}<li><a href={q.url ?? "#"} target="_blank" rel="noopener">{q.kurz}</a>{#if q.etikett} <span class="tag">{q.etikett}</span>{/if}<span class="muted"> {host(q.url)}</span></li>{/each}
            </ul>
            <button class="knopf hell" onclick={() => (reiter = "quellen")}>Alle Quellen anzeigen</button>
          </section>
        </div>

      {:else if reiter === "geldfluesse"}
        <section class="block">
          <h3>Geld vom Bund</h3>
          <p class="muted small">Drei Quellen, drei Blickwinkel auf dasselbe Geld. Die Beträge werden nicht addiert.</p>
          <h4>Haushaltstitel <span class="tag">bundeshaushalt.de · {app.stand === "ist" ? "Ist" : "Soll"}</span></h4>
          {#if seite.haushalt.titel.length === 0}
            <p class="muted">Kein Haushaltstitel nennt diesen Empfänger namentlich. Zuwendungen laufen dann über Sammeltitel; wer genau was erhält, veröffentlicht der Bund nicht titelgenau.</p>
          {:else}
            <div class="scroll">
              <table>
                <thead><tr><th>Titel</th>{#each jahre as j}<th class="num">{j}</th>{/each}</tr></thead>
                <tbody>
                  {#each seite.haushalt.titel as t (t.id)}
                    <tr>
                      <td><button class="link" onclick={() => titelOeffnen(t.id)}>{t.id}</button><small class="muted">{t.text} · {t.epl_text}</small></td>
                      {#each jahre as j}
                        {@const w = t.werte[j]}
                        <td class="num tabular">{w ? (app.stand === "ist" ? (w.ist === null ? "–" : fmtEuro(w.ist)) : fmtEuro(w.soll)) : "–"}</td>
                      {/each}
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
          {/if}
          <h4>Lobbyregister <span class="tag">Eigenangabe des Empfängers{#if seite.pflichtangaben?.geschaeftsjahr} · Geschäftsjahr {seite.pflichtangaben.geschaeftsjahr}{/if}</span></h4>
          {#if seite.lobby_zuwendungen.length === 0}
            <p class="muted">{seite.lobbyregister ? "Keine Zuwendungen des Bundes im Lobbyregister angegeben." : "Nicht im Lobbyregister eingetragen."}</p>
          {:else}
            <table>
              <thead><tr><th>Geldgeber</th><th class="num">Betrag (Spanne)</th><th>Zweck laut Eintrag</th></tr></thead>
              <tbody>
                {#each seite.lobby_zuwendungen as z}
                  <tr><td>{z.geber}{#if z.epl}<small class="muted">Einzelplan {z.epl}</small>{/if}</td><td class="num tabular">{fmtSpanne(z.von, z.bis)}</td><td class="zweck">{z.zweck}</td></tr>
                {/each}
                <tr class="sum"><td>Untergrenze zusammen</td><td class="num tabular">ab {fmtEuro(seite.lobby_untergrenze_bund)}</td><td class="muted">Summe der unteren Spannengrenzen; der tatsächliche Betrag liegt darüber.</td></tr>
              </tbody>
            </table>
          {/if}
          <h4>Förderkatalog des Bundes <span class="tag">Projektförderung BMFTR, BMWE, BMUKN, BMLEH, BMV, BMJV</span></h4>
          {#if seite.foerderkatalog.length === 0}
            <p class="muted">Keine Projekte unter diesem Namen im Förderkatalog.</p>
          {:else}
            <div class="scroll">
              <table>
                <thead><tr><th>Kennzeichen</th><th>Ressort</th><th>Thema</th><th>Laufzeit</th><th class="num">Bundesanteil</th></tr></thead>
                <tbody>
                  {#each seite.foerderkatalog.slice(0, 50) as p (p.fkz)}
                    <tr>
                      <td><a href={`https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=view&fkz=${encodeURIComponent(p.fkz)}`} target="_blank" rel="noopener">{p.fkz}</a></td>
                      <td>{p.ressort}</td><td class="zweck">{p.thema}</td><td class="tabular">{p.von.slice(0, 4)}–{p.bis.slice(0, 4)}</td><td class="num tabular">{fmtEuro(p.summe)}</td>
                    </tr>
                  {/each}
                </tbody>
              </table>
            </div>
            {#if seite.foerderkatalog.length > 50}<p class="muted small">{seite.foerderkatalog.length - 50} weitere Projekte im Förderkatalog.</p>{/if}
            {#if seite.foerderkatalog_auszug}<p class="muted small">Auszug: Der Export des Förderkatalogs liefert höchstens 100 Projekte je Suche; die Summe ist eine Untergrenze.</p>{/if}
          {/if}
        </section>

      {:else if reiter === "verbindungen"}
        <section class="block verb">
          <h3>Belegte Verbindungen</h3>
          {#if !mitPersonen}
            <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
          {:else if seite.verbindungen.length === 0}
            <p class="muted">In den ausgewerteten Quellen (bundestag.de, Lobbyregister, bestätigte Belege) keine belegte Verbindung, Stand {seite.stand}.</p>
          {:else}
            {#each seite.verbindungen as x}
              <div class="v">
                <p class="satz">{x.satz}</p>
                <p class="src"><span class="tag">{etikett(x)}</span>
                  {#each x.quellen as q}<a href={q.url} target="_blank" rel="noopener">{q.kurz}{#if q.etikett} · {q.etikett}{/if}{#if q.stand} (Stand {q.stand}){/if}</a> {/each}
                </p>
              </div>
            {/each}
            <p class="muted small">Tatsachen mit Fundstelle, keine Bewertung. Verbindungen werden nur bei exakt gleichem Organisationsnamen automatisch gezeigt; Ähnliches wartet auf eine menschliche Prüfung.</p>
          {/if}
        </section>
        {#if seite.parteispenden?.length}
          <section class="block">
            <h3>Parteispenden der Organisation</h3>
            <div class="scroll">
              <table>
                <thead><tr><th>Partei</th><th class="num">Betrag</th><th>Eingang</th><th>Veröffentlicht</th></tr></thead>
                <tbody>
                  {#each seite.parteispenden as sp}
                    <tr><td>{sp.partei}</td><td class="num tabular">{fmtEuro(sp.betrag)}</td><td class="tabular">{sp.eingang}</td>
                      <td><a href={sp.quelle.url ?? "#"} target="_blank" rel="noopener">{sp.drucksache || "bundestag.de"}</a>{#if sp.veroeffentlicht} · {sp.veroeffentlicht}{/if}</td></tr>
                  {/each}
                </tbody>
              </table>
            </div>
            <p class="muted small">Veröffentlichungspflichtige Spenden an Parteien (über 35.000 €, davor 50.000 €) laut bundestag.de, amtlich. Eine Spende belegt eine Zahlung, nicht mehr.</p>
          </section>
        {/if}

      {:else if reiter === "personen"}
        <section class="block">
          <h3>Wer steht dahinter</h3>
          {#if !mitPersonen}
            <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
          {:else if seite.personen.length === 0}
            <p class="muted">Keine Angaben zu gesetzlichen Vertretern in den ausgewerteten Quellen.</p>
          {:else}
            <ul class="personen">
              {#each seite.personen as p}
                <li><Avatar name={p.name} size={32} /><div>
                  {#if p.akte_id && p.akte_sichtbar}<button class="link" onclick={() => void app.openAkte(p.akte_id!)}><b>{p.name}</b></button>{:else}<b>{p.name}</b>{#if p.akte_id === null || p.akte_sichtbar === false} <span class="tag">Akte nicht freigeschaltet</span>{/if}{/if} <Partei name={partei(p)} /> · {p.funktion || (p.rolle === "interessenvertreter" ? "Interessenvertretung" : "gesetzliche Vertretung")}
                  {#if p.rolle === "interessenvertreter"}<span class="tag">Interessenvertreter laut Lobbyregister</span>{/if}
                  {#if p.regierungsfunktion}<span class="tag">{p.regierungsfunktion.beendet ? "frühere öffentliche Funktion" : "öffentliche Funktion, laufend"}: {p.regierungsfunktion.funktion}{#if p.regierungsfunktion.stelle}, {p.regierungsfunktion.stelle}{/if}{#if p.regierungsfunktion.beendet && p.regierungsfunktion.ende} bis {p.regierungsfunktion.ende}{/if}</span>{/if}
                  <small class="muted">Quelle: <a href={p.quelle.url ?? "#"} target="_blank" rel="noopener">{p.quelle.kurz}</a>, Stand {p.quelle.stand}</small>
                </div></li>
              {/each}
            </ul>
          {/if}
        </section>

      {:else if reiter === "zeitverlauf"}
        <section class="block">
          <h3>Zeitverlauf der Zahlungen <span class="tag">Haushaltstitel · {app.stand === "ist" ? "Ist" : "Soll"}</span></h3>
          {#if reihe.length === 0}
            <p class="muted">Kein Haushaltstitel nennt diesen Empfänger namentlich.</p>
          {:else}
            <table class="jahre">
              <thead><tr><th>Jahr</th><th class="num">Summe der Titel</th><th class="num">Veränderung</th></tr></thead>
              <tbody>
                {#each reihe as r, i}
                  {@const vj = i > 0 ? reihe[i - 1] : null}
                  <tr class:on={r.jahr === app.jahr}><td>{r.jahr}</td><td class="num tabular">{fmtEuro(r.wert)}</td><td class="num tabular">{vj && vj.wert > 0 && vj.jahr === r.jahr - 1 ? `${r.wert >= vj.wert ? "+" : ""}${(Math.round(((r.wert - vj.wert) / vj.wert) * 1000) / 10).toLocaleString("de-DE")} %` : "–"}</td></tr>
                {/each}
              </tbody>
            </table>
            <p class="muted small">Zuwendungen laut Lobbyregister und Förderkatalog stehen im Reiter Geldflüsse; sie werden nicht in diese Reihe gerechnet.</p>
          {/if}
        </section>

      {:else}
        <section class="block">
          <h3>Pflichtangaben des Empfängers</h3>
          {#if !seite.pflichtangaben}
            <p class="muted">Keine Pflichtangaben in den ausgewerteten Registern.</p>
          {:else}
            {@const pa = seite.pflichtangaben}
            <dl>
              {#if pa.finanzierungsquellen.length}<dt>Hauptfinanzierungsquellen</dt><dd>{pa.finanzierungsquellen.join(", ")}</dd>{/if}
              {#if pa.spenden}<dt>Spenden und Schenkungen{#if pa.geschaeftsjahr} {pa.geschaeftsjahr}{/if}</dt><dd class="tabular">{fmtSpanne(pa.spenden.von, pa.spenden.bis)}</dd>{/if}
              {#if pa.mitgliedsbeitraege && pa.mitgliedsbeitraege.bis > 0}<dt>Mitgliedsbeiträge</dt><dd class="tabular">{fmtSpanne(pa.mitgliedsbeitraege.von, pa.mitgliedsbeitraege.bis)}</dd>{/if}
              {#if pa.lobbyausgaben}<dt>Ausgaben für Interessenvertretung</dt><dd class="tabular">{fmtSpanne(pa.lobbyausgaben.von, pa.lobbyausgaben.bis)}</dd>{/if}
            </dl>
            <p class="muted small">Angaben nach dem Lobbyregistergesetz, vom Empfänger selbst gemeldet, in Spannen.</p>
            {#if ja}
              <h4>Jahresabschluss {ja.geschaeftsjahr} <span class="tag">Eigenangabe, veröffentlicht über das Lobbyregister</span></h4>
              <p><a href={ja.url ?? "#"} target="_blank" rel="noopener">Jahresabschluss als PDF</a>{#if ja.pruefer} · Prüfvermerk: {ja.pruefer}{/if}</p>
              {#if kz}
                <table>
                  <tbody>
                    {#each Object.entries(kzLabels) as [k, label]}
                      {#if kz[k] !== null && kz[k] !== undefined}
                        <tr><td>{label}</td><td class="num tabular">{fmtEuro(kz[k] ?? 0)}{k === "oeffentliche_hand" || k === "personalaufwand" || k === "spenden" ? quote(kz[k], kz.ertraege_gesamt) : ""}</td></tr>
                      {/if}
                    {/each}
                  </tbody>
                </table>
                <p class="muted small">Abgelesen aus Seite {ja.seite ?? "?"} des Dokuments{#if ja.erfasst} am {ja.erfasst}{/if}. {ja.hinweis ?? ""} Prozentangaben sind Rechnungen dieser Seite, keine Angaben des Empfängers.</p>
              {:else}
                <p class="muted small">Kennzahlen aus diesem Dokument sind noch nicht erfasst.</p>
              {/if}
            {/if}
          {/if}
        </section>
        <section class="block">
          <h3>Quellen und Stand</h3>
          <ul class="quellen">
            {#each seite.quellen as q}
              <li><a href={q.url ?? "#"} target="_blank" rel="noopener">{q.kurz}</a>{#if q.etikett} · {q.etikett}{/if}{#if q.stand} · Stand {q.stand}{/if}{#if q.abgerufen} · abgerufen {q.abgerufen}{/if} <span class="muted">({host(q.url)})</span></li>
            {/each}
          </ul>
          <p class="muted small">Seite erzeugt am {seite.stand}. Rechtlich verbindlich sind die amtlichen Dokumente.</p>
          <a class="melden" href={issueUrl(seite)} target="_blank" rel="noopener">Fehler melden / Beleg einreichen</a>
          <a class="melden second" href="https://fragdenstaat.de/anfrage-stellen/" target="_blank" rel="noopener">Anfrage nach dem Informationsfreiheitsgesetz stellen</a>
        </section>
      {/if}
    </div>
  </div>
</article>

<style>
  .seite { font-size: 12px; }
  .back { background: none; border: 0; color: var(--header); cursor: pointer; font: inherit; font-size: 12px; padding: 0; margin-bottom: 8px; }
  .raster { display: grid; grid-template-columns: 230px minmax(0, 1fr); gap: 14px; align-items: start; }
  .profil { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px; display: flex; flex-direction: column; gap: 10px; position: sticky; top: 10px; }
  .kopf { display: flex; gap: 10px; align-items: flex-start; }
  .kopf div { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .kopf b { font-size: 14px; color: var(--header); line-height: 1.2; }
  .kopf small { color: var(--muted); }
  .chip { display: inline-block; align-self: flex-start; font-size: 10px; padding: 1px 8px; border-radius: 999px; background: var(--bg); color: var(--muted); border: 1px solid var(--border); }
  .chip.gruen { background: var(--chip-gruen); color: #15803d; border-color: transparent; }
  .knopfchip { cursor: pointer; background: var(--chip-blau); color: var(--header); border-color: transparent; font: inherit; font-size: 10px; }
  .kennzahlen { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .kennzahlen li { display: grid; grid-template-columns: 26px 1fr auto; gap: 8px; align-items: center; background: var(--bg); border-radius: 10px; padding: 6px 8px; }
  .kennzahlen li div { display: flex; flex-direction: column; min-width: 0; }
  .kennzahlen small { color: var(--muted); font-size: 10px; }
  .kennzahlen b { color: var(--header); font-size: 13px; }
  .delta { font-size: 11px; font-weight: 600; padding: 1px 6px; border-radius: 999px; background: var(--bg); }
  .delta.gut { color: var(--good); background: var(--chip-gruen); } .delta.schlecht { color: var(--bad); background: #fee2e2; }
  .kachel { width: 26px; height: 26px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; background: var(--nav-bg); color: var(--header); flex: none; }
  .kachel.blau { background: var(--chip-blau); color: var(--nav-on); }
  .knopf { display: inline-flex; align-items: center; justify-content: center; gap: 6px; width: 100%; font: inherit; font-size: 12px; font-weight: 600; background: var(--nav-on); color: var(--nav-on-fg); border: 0; border-radius: 10px; padding: 8px 10px; cursor: pointer; margin-top: 6px; }
  .knopf.hell { background: var(--chip-blau); color: var(--header); }
  .meta { display: flex; flex-direction: column; gap: 3px; color: var(--muted); font-size: 11px; }
  .inhalt { min-width: 0; display: flex; flex-direction: column; gap: 10px; }
  header h2 { margin: 0; font-size: 20px; color: var(--header); }
  .unter { margin: 2px 0 0; color: var(--muted); }
  .reiter { display: inline-flex; gap: 2px; background: var(--nav-bg); border-radius: 10px; padding: 3px; flex-wrap: wrap; align-self: flex-start; }
  .reiter button { background: none; border: 0; color: var(--header); padding: 6px 12px; border-radius: 8px; cursor: pointer; font-size: 12px; font-weight: 600; opacity: .75; }
  .reiter button.on { background: var(--nav-on); color: var(--nav-on-fg); opacity: 1; }
  .oben { display: grid; grid-template-columns: minmax(0, 1fr) 260px; gap: 10px; align-items: start; }
  .karten { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; align-items: start; }
  .karten.zwei { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .block { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; min-width: 0; }
  .block.verb { border-left: 4px solid var(--header); }
  h3 { margin: 0 0 8px; font-size: 13px; color: var(--header); display: flex; align-items: center; gap: 6px; }
  h4 { margin: 12px 0 4px; font-size: 12px; }
  .blick ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 8px; }
  .blick li { display: grid; grid-template-columns: 30px 1fr; gap: 8px; align-items: center; }
  .blick li div { display: flex; flex-direction: column; min-width: 0; gap: 2px; }
  .blick small { color: var(--muted); font-size: 10px; }
  .netzvorschau { display: flex; gap: 6px; align-items: center; flex-wrap: wrap; margin-bottom: 6px; }
  .pliste { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .pliste li { display: grid; grid-template-columns: 30px 1fr auto; gap: 8px; align-items: center; }
  .pliste li div { display: flex; flex-direction: column; min-width: 0; }
  .pliste small { font-size: 10px; }
  .haken { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .qliste { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .v { padding: 6px 0; border-top: 1px solid var(--border); }
  .v:first-of-type { border-top: 0; }
  .satz { margin: 0; font-size: 13px; }
  .src { margin: 2px 0 0; font-size: 11px; color: var(--muted); }
  .tag { display: inline-block; font-size: 10px; background: var(--bg); border-radius: 999px; padding: 1px 8px; margin-left: 4px; color: var(--muted); font-weight: 400; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 5px 6px; border-bottom: 1px solid var(--border); }
  td { padding: 5px 6px; border-bottom: 1px solid var(--border); vertical-align: top; }
  td small { display: block; font-size: 10px; }
  tr.on td { background: var(--chip-blau); }
  .num { text-align: right; white-space: nowrap; }
  .zweck { color: var(--muted); font-size: 11px; }
  .sum td { font-weight: 700; border-top: 2px solid var(--border); }
  .scroll { overflow-x: auto; }
  .balken { width: 100%; height: 90px; display: block; margin: 4px 0; }
  .link { background: none; border: 0; color: var(--header); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; text-align: left; }
  .personen { list-style: none; padding: 0; margin: 0; }
  .personen li { padding: 6px 0; border-top: 1px solid var(--border); display: grid; grid-template-columns: 32px 1fr; gap: 8px; }
  .personen li:first-child { border-top: 0; }
  .personen small { display: block; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 0; }
  dt { color: var(--muted); }
  dd { margin: 0; }
  .quellen { padding-left: 16px; margin: 0; }
  .melden { display: inline-block; margin-top: 8px; margin-right: 8px; font-size: 12px; background: var(--nav-on); color: var(--nav-on-fg); border-radius: 8px; padding: 6px 12px; text-decoration: none; }
  .melden.second { background: var(--bg); color: var(--fg); border: 1px solid var(--border); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; }
  @media (max-width: 1100px) { .karten { grid-template-columns: 1fr 1fr; } .oben { grid-template-columns: 1fr; } }
  @media (max-width: 800px) { .raster { grid-template-columns: 1fr; } .profil { position: static; } .karten, .karten.zwei { grid-template-columns: 1fr; } dl { grid-template-columns: 1fr; } .zweck { display: none; } }
</style>
