<script lang="ts">
  import { EMPFAENGER_ART_LABELS, fmtSpanne, geldAus, issueUrl, titelZeitreihe, type EmpfaengerSeite } from "../model/empfaenger";
  import { fmtEuro } from "../model/format";
  import type { AppState } from "../state.svelte";

  let { app, seite }: { app: AppState; seite: EmpfaengerSeite } = $props();

  const mitPersonen = $derived(app.empfaengerIndex?.mit_personen ?? true);
  const geber = $derived(geldAus(seite));
  const reihe = $derived(titelZeitreihe(seite, app.stand));
  const reiheMax = $derived(Math.max(1, ...reihe.map((r) => r.wert)));
  const jahre = $derived([...new Set(seite.haushalt.titel.flatMap((t) => Object.keys(t.werte)))].sort());
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
  function etikett(v: { abgleich: string }): string {
    return v.abgleich === "exakt" ? "automatisch abgeglichen" : v.abgleich === "geprueft" ? "von Hand geprüft" : "Eigenangabe im Lobbyregister";
  }
  function titelOeffnen(id: string) {
    const [epl, kap] = id.split("-");
    app.setTopf("bund");
    app.setFocus([epl, `${epl}-${kap}`, id]);
    app.setSelected(id);
    app.setView("fluss");
  }
</script>

<article class="seite">
  <div class="top"><button class="back" onclick={() => app.openEmpfaengerListe()}>‹ Alle Empfänger</button><button class="netz" onclick={() => void app.openNetz(`e:${seite.id}`)}>Umfeld zeigen</button></div>
  <header>
    <div class="path">Empfänger · {EMPFAENGER_ART_LABELS[seite.art] ?? seite.art}</div>
    <h2>{seite.name}</h2>
    <div class="meta">
      {#if seite.rechtsform}<span>{seite.rechtsform}</span>{/if}
      {#if seite.sitz}<span>{seite.sitz}</span>{/if}
      {#if seite.lobbyregister}<span>Lobbyregister <a href={seite.lobbyregister.url} target="_blank" rel="noopener">{seite.lobbyregister.nummer}</a> (Version {seite.lobbyregister.version}, Stand {seite.lobbyregister.stand})</span>{/if}
      {#if seite.website}<span><a href={seite.website.startsWith("http") ? seite.website : `https://${seite.website}`} target="_blank" rel="noopener">{seite.website.replace(/^https?:\/\//, "")}</a></span>{/if}
    </div>
  </header>

  <section class="block verb">
    <h3>Belegte Verbindungen</h3>
    {#if !mitPersonen}
      <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
    {:else if seite.verbindungen.length === 0}
      <p class="muted">In den ausgewerteten Quellen (bundestag.de, Lobbyregister, bestätigte Belege) keine belegte Verbindung, Stand {seite.stand}.</p>
    {:else}
      {#each seite.verbindungen as v}
        <div class="v">
          <p class="satz">{v.satz}</p>
          <p class="src"><span class="tag">{etikett(v)}</span>
            {#each v.quellen as q}<a href={q.url} target="_blank" rel="noopener">{q.kurz}{#if q.etikett} · {q.etikett}{/if}{#if q.stand} (Stand {q.stand}){/if}</a> {/each}
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

  <section class="block">
    <h3>Geld vom Bund</h3>
    <p class="muted small">Drei Quellen, drei Blickwinkel auf dasselbe Geld. Die Beträge werden nicht addiert.</p>

    <h4>Haushaltstitel <span class="tag">bundeshaushalt.de · {app.stand === "ist" ? "Ist" : "Soll"}</span></h4>
    {#if seite.haushalt.titel.length === 0}
      <p class="muted">Kein Haushaltstitel nennt diesen Empfänger namentlich. Zuwendungen laufen dann über Sammeltitel; wer genau was erhält, veröffentlicht der Bund nicht titelgenau.</p>
    {:else}
      {#if reihe.length > 1}
        <svg class="balken" viewBox={`0 0 ${reihe.length * 34} 60`} role="img" aria-label="Summe der Titel je Jahr">
          {#each reihe as r, i}
            <rect x={i * 34 + 4} y={56 - (r.wert / reiheMax) * 44} width="26" height={(r.wert / reiheMax) * 44} fill="var(--steuern)" />
            <text x={i * 34 + 17} y="59" text-anchor="middle" font-size="7">{String(r.jahr).slice(2)}</text>
            <title>{r.jahr}: {fmtEuro(r.wert)}</title>
          {/each}
        </svg>
      {/if}
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
            <tr>
              <td>{z.geber}{#if z.epl}<small class="muted">Einzelplan {z.epl}</small>{/if}</td>
              <td class="num tabular">{fmtSpanne(z.von, z.bis)}</td>
              <td class="zweck">{z.zweck}</td>
            </tr>
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
                <td>{p.ressort}</td>
                <td class="zweck">{p.thema}</td>
                <td class="tabular">{p.von.slice(0, 4)}–{p.bis.slice(0, 4)}</td>
                <td class="num tabular">{fmtEuro(p.summe)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      {#if seite.foerderkatalog.length > 50}<p class="muted small">{seite.foerderkatalog.length - 50} weitere Projekte im Förderkatalog.</p>{/if}
      {#if seite.foerderkatalog_auszug}<p class="muted small">Auszug: Der Export des Förderkatalogs liefert höchstens 100 Projekte je Suche; die Summe ist eine Untergrenze.</p>{/if}
    {/if}
  </section>

  <section class="block">
    <h3>Wer steht dahinter</h3>
    {#if !mitPersonen}
      <p class="muted">Personenangaben sind in dieser Fassung nicht veröffentlicht.</p>
    {:else if seite.personen.length === 0}
      <p class="muted">Keine Angaben zu gesetzlichen Vertretern in den ausgewerteten Quellen.</p>
    {:else}
      <ul class="personen">
        {#each seite.personen as p}
          <li>{#if p.akte_id && p.akte_sichtbar}<button class="link" onclick={() => void app.openAkte(p.akte_id!)}><b>{p.name}</b></button>{:else}<b>{p.name}</b>{#if p.akte_id === null || p.akte_sichtbar === false} <span class="tag">Akte nicht freigeschaltet</span>{/if}{/if} · {p.funktion || (p.rolle === "interessenvertreter" ? "Interessenvertretung" : "gesetzliche Vertretung")}
            {#if p.rolle === "interessenvertreter"}<span class="tag">Interessenvertreter laut Lobbyregister</span>{/if}
            {#if p.regierungsfunktion}<span class="tag">frühere öffentliche Funktion: {p.regierungsfunktion.funktion}{#if p.regierungsfunktion.stelle}, {p.regierungsfunktion.stelle}{/if}{#if p.regierungsfunktion.ende} bis {p.regierungsfunktion.ende}{/if}</span>{/if}
            <small class="muted">Quelle: <a href={p.quelle.url ?? "#"} target="_blank" rel="noopener">{p.quelle.kurz}</a>, Stand {p.quelle.stand}</small>
          </li>
        {/each}
      </ul>
    {/if}
  </section>

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
</article>

<style>
  .seite { font-size: 12px; max-width: 980px; }
  .back { background: none; border: 0; color: var(--header); cursor: pointer; font: inherit; font-size: 12px; padding: 0; margin-bottom: 6px; }
  .top { display: flex; justify-content: space-between; align-items: center; gap: 8px; }
  .netz { font: inherit; font-size: 12px; background: var(--header); color: #fff; border: 0; border-radius: 8px; padding: 5px 10px; cursor: pointer; }
  .path { color: var(--muted); font-size: 11px; }
  h2 { margin: 2px 0 4px; font-size: 18px; }
  h3 { margin: 0 0 6px; font-size: 13px; }
  h4 { margin: 12px 0 4px; font-size: 12px; }
  .meta { display: flex; gap: 12px; flex-wrap: wrap; color: var(--muted); }
  .block { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-top: 10px; }
  .block.verb { border-left: 4px solid var(--header); }
  .v { padding: 6px 0; border-top: 1px solid var(--border); }
  .v:first-of-type { border-top: 0; }
  .satz { margin: 0; font-size: 13px; }
  .src { margin: 2px 0 0; font-size: 11px; color: var(--muted); }
  .tag { display: inline-block; font-size: 10px; background: var(--bg); border-radius: 999px; padding: 1px 8px; margin-left: 4px; color: var(--muted); font-weight: 400; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 5px 6px; border-bottom: 1px solid var(--border); }
  td { padding: 5px 6px; border-bottom: 1px solid #f0f0f2; vertical-align: top; }
  td small { display: block; font-size: 10px; }
  .num { text-align: right; white-space: nowrap; }
  .zweck { color: var(--muted); font-size: 11px; }
  .sum td { font-weight: 700; border-top: 2px solid var(--border); }
  .scroll { overflow-x: auto; }
  .balken { width: 100%; max-width: 480px; height: 60px; display: block; margin: 4px 0; }
  .link { background: none; border: 0; color: var(--header); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; }
  .personen { list-style: none; padding: 0; margin: 0; }
  .personen li { padding: 5px 0; border-top: 1px solid var(--border); }
  .personen li:first-child { border-top: 0; }
  .personen small { display: block; }
  dl { display: grid; grid-template-columns: max-content 1fr; gap: 4px 12px; margin: 0; }
  dt { color: var(--muted); }
  dd { margin: 0; }
  .quellen { padding-left: 16px; margin: 0; }
  .melden { display: inline-block; margin-top: 8px; margin-right: 8px; font-size: 12px; background: var(--header); color: #fff; border-radius: 8px; padding: 6px 12px; text-decoration: none; }
  .melden.second { background: var(--bg); color: var(--fg); border: 1px solid var(--border); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; }
  @media (max-width: 720px) { dl { grid-template-columns: 1fr; } .zweck { display: none; } }
</style>
