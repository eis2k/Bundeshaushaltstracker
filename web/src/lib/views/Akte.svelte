<script lang="ts">
  import { fmtEuro, fmtEuroCent } from "../model/format";
  import { FUNKTION_LABELS, bezuegeNachPosten, issueUrlAkte, zeitlinieJahre, type Akte } from "../model/personen";
  import type { AppState } from "../state.svelte";

  let { app, akte }: { app: AppState; akte: Akte } = $props();

  const jahre = $derived(zeitlinieJahre(akte));
  const maxLobby = $derived(Math.max(1, ...jahre.map((j) => j.lobby)));
  const maxHaushalt = $derived(Math.max(1, ...jahre.map((j) => j.haushalt)));
  const maxSpenden = $derived(Math.max(1, ...jahre.map((j) => j.spenden)));
  const angabenNachKategorie = $derived.by(() => {
    const m = new Map<string, typeof akte.angaben>();
    for (const a of akte.angaben) m.set(a.kategorie, [...(m.get(a.kategorie) ?? []), a]);
    return [...m.entries()];
  });
  const grund = $derived(akte.grund_sichtbar === "amt" ? "öffentliches Amt" : akte.grund_sichtbar === "verbindung" ? "belegte Verbindung zur Entscheidungsseite" : akte.grund_sichtbar === "freigabe" ? "von einem Prüfer freigeschaltet" : akte.grund_sichtbar === "alle" ? "vollständige Fassung (alle Akten)" : "");
  const bezuege = $derived(akte.bezuege ? bezuegeNachPosten(akte.bezuege) : []);
  function zeitraum(von: string | null, bis: string | null, monate: number | null): string {
    if (!von) return "Zeitraum nicht belegt";
    return `${von} – ${bis ?? ""}${monate != null ? ` (${monate} Monate)` : ""}`;
  }
  function host(u: string | null): string {
    if (!u) return "";
    try { return new URL(u).hostname.replace("www.", ""); } catch { return u; }
  }
</script>

<article class="akte">
  <button class="back" onclick={() => app.openPersonenListe()}>‹ Alle Personen</button>
  <header>
    <div class="path">Akte · sichtbar wegen: {grund}</div>
    <h2>{akte.name}</h2>
    <ul class="funktionen">
      {#each akte.funktionen as f}
        <li>
          <span class="tag">{FUNKTION_LABELS[f.art] ?? f.art}</span>
          <b>{f.text}</b>{#if f.organisation && f.art !== "mdb"} bei {#if f.organisation_id}<button class="link" onclick={() => void app.openEmpfaenger(f.organisation_id!)}>{f.organisation}</button>{:else}{f.organisation}{/if}{/if}
          {#if f.seit} · seit {f.seit}{#if f.seit_hinweis} <span class="muted" title={f.seit_hinweis}>(laut Biografie)</span>{/if}{/if}{#if f.bis} · bis {f.bis}{/if}
          <small class="muted">Quelle: <a href={f.quelle.url ?? "#"} target="_blank" rel="noopener">{f.quelle.kurz}</a>{#if f.quelle.etikett} · {f.quelle.etikett}{/if} · Stand {f.stand}</small>
          {#if f.ausschuesse?.length}<small class="muted">Ausschüsse und Gremien: {f.ausschuesse.join("; ")}</small>{/if}
        </li>
      {/each}
    </ul>
    {#if akte.gleichnamig.length}
      <div class="note">Gleicher Name, nicht zusammengeführt: Es gibt {akte.gleichnamig.length} weitere Akte{akte.gleichnamig.length === 1 ? "" : "n"} mit diesem Namen aus anderen Quellen. Ohne Beleg gelten sie als verschiedene Personen.
        {#each akte.gleichnamig as g}<button class="link" onclick={() => void app.openAkte(g)}>{g}</button> {/each}</div>
    {/if}
    <button class="netz" onclick={() => void app.openNetz(`p:${akte.id}`)}>Umfeld zeigen</button>
  </header>

  <section class="block">
    <h3>Organisationen und ihr Geld vom Bund</h3>
    {#if akte.organisationen.length === 0}
      <p class="muted">Keine Organisation mit Bundesmitteln, bei der diese Person laut Lobbyregister einen Posten hat.</p>
    {:else}
      <div class="scroll">
        <table>
          <thead><tr><th>Organisation</th><th>Posten</th><th class="num">Bund laut Lobbyregister<small>Untergrenze</small></th><th class="num">Haushaltstitel<small>Soll, letztes Jahr</small></th><th class="num">Förderkatalog</th></tr></thead>
          <tbody>
            {#each akte.organisationen as o (o.id)}
              <tr>
                <td><button class="link" onclick={() => void app.openEmpfaenger(o.id)}>{o.name}</button>{#if o.geld_aus?.length}<small class="muted">Geld von: {o.geld_aus.slice(0, 3).join("; ")}{o.geld_aus.length > 3 ? " …" : ""}</small>{/if}</td>
                <td>{o.funktion}<small class="muted">Stand {o.stand}</small></td>
                <td class="num tabular">{o.lobby_untergrenze_bund ? `ab ${fmtEuro(o.lobby_untergrenze_bund)}` : "–"}</td>
                <td class="num tabular">{o.haushalt_soll_letztes_jahr ? fmtEuro(o.haushalt_soll_letztes_jahr) : "–"}</td>
                <td class="num tabular">{o.foerderkatalog_summe ? fmtEuro(o.foerderkatalog_summe) : "–"}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
      <p class="muted small">Drei Quellen, nicht addiert. Das Geld fließt an die Organisation, nicht an die Person.</p>
    {/if}
  </section>

  {#if akte.angaben.length}
    <section class="block">
      <h3>Veröffentlichungspflichtige Angaben <span class="tag">bundestag.de · Selbstauskunft</span></h3>
      {#each angabenNachKategorie as [kategorie, liste]}
        <h4>{kategorie}</h4>
        <ul class="angaben">
          {#each liste as a}
            <li>{a.organisation}{#if a.ort}, {a.ort}{/if}{#if a.funktion}: {a.funktion}{/if}</li>
          {/each}
        </ul>
      {/each}
      <p class="muted small">Wörtlich nach den Angaben nach §§ 45 ff. Abgeordnetengesetz, Stand {akte.angaben[0].stand}. <a href={akte.angaben[0].quelle.url ?? "#"} target="_blank" rel="noopener">Quelle</a></p>
    </section>
  {/if}

  <section class="block">
    <h3>Parteispenden der verbundenen Organisationen <span class="tag">bundestag.de · amtlich</span></h3>
    {#if akte.spenden.length === 0}
      <p class="muted">Keine veröffentlichungspflichtige Parteispende (über 35.000 €, davor 50.000 €) einer Organisation, bei der diese Person einen Posten hat.</p>
    {:else}
      <table>
        <thead><tr><th>Organisation</th><th>Partei</th><th class="num">Betrag</th><th>Eingang</th><th>Fundstelle</th></tr></thead>
        <tbody>
          {#each akte.spenden as s}
            <tr><td>{s.organisation}</td><td>{s.partei}</td><td class="num tabular">{fmtEuro(s.betrag)}</td><td class="tabular">{s.eingang}</td><td>{#if s.drucksache_url}<a href={s.drucksache_url} target="_blank" rel="noopener">{s.drucksache}</a>{:else}{s.drucksache}{/if}</td></tr>
          {/each}
        </tbody>
      </table>
      <p class="muted small">Die Spende stammt von der Organisation, nicht von der Person.</p>
    {/if}
  </section>

  {#if akte.bezuege}
    <section class="block bezuege">
      <h3>Bezüge aus dem Amt</h3>
      {#each bezuege as g (g.posten)}
        <h4>{g.posten}</h4>
        <div class="scroll">
          <table>
            <thead><tr><th>Komponente</th><th class="num">monatlich</th><th>Zeitraum</th><th class="num">Summe</th><th>Quelle</th></tr></thead>
            <tbody>
              {#each g.zeilen as z}
                <tr>
                  <td>{z.komponente}{#if z.empfaenger === "dritte"} <span class="tag">an Dritte</span>{/if}<small class="muted">{z.rechtsgrundlage}</small></td>
                  <td class="num tabular">{z.monatlich != null ? fmtEuroCent(z.monatlich) : "–"}</td>
                  <td class="tabular">{zeitraum(z.zeitraum_von, z.zeitraum_bis, z.monate)}</td>
                  <td class="num tabular">{z.summe != null ? fmtEuroCent(z.summe) : "–"}</td>
                  <td>{#if z.quelle.url}<a href={z.quelle.url} target="_blank" rel="noopener" title={z.quelle.fundstelle ?? ""}>{z.quelle.kurz}</a>{:else}{z.quelle.kurz}{/if}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {/each}
      <p class="summe"><b>Gesetzlicher Anspruch der Person</b> (gerechnet aus den Monatsbeträgen, keine Auszahlungsbestätigung): <span class="tabular">{fmtEuroCent(akte.bezuege.summe_person)}</span></p>
      <p class="summe"><b>Höchstbeträge für Mitarbeiter und Sachleistungen</b> (nicht je Person abgerechnet): <span class="tabular">{fmtEuroCent(akte.bezuege.summe_aufwand)}</span></p>
      {#if akte.bezuege.hinweise.length}<ul class="muted small hinweise">{#each akte.bezuege.hinweise as h}<li>{h}</li>{/each}</ul>{/if}
      {#if akte.bezuege.nicht_bezifferbar.length}
        <h4>Nicht bezifferbar</h4>
        <ul class="muted small hinweise">{#each akte.bezuege.nicht_bezifferbar as n}<li>{n}</li>{/each}</ul>
      {/if}
      <p class="muted small">Gesetzlich festgelegte Beträge, keine Einzelabrechnung. Was die Person tatsächlich erhält, kann durch Kürzungen (§ 14, § 12 Abs. 6, § 29 AbgG) abweichen.</p>
    </section>
  {/if}

  <section class="block">
    <h3>Zeitlinie</h3>
    {#if jahre.length === 0}
      <p class="muted">Keine datierten Einträge.</p>
    {:else}
      <svg class="zl" viewBox={`0 0 ${jahre.length * 64} 90`} role="img" aria-label="Zeitlinie: Geld an verbundene Organisationen je Jahr und Quelle, Posten als Punkte">
        {#each jahre as j, i}
          {#if j.lobby}<rect x={i * 64 + 6} y={70 - (j.lobby / maxLobby) * 50} width="14" height={(j.lobby / maxLobby) * 50} fill="var(--steuern)" opacity="0.8" />{/if}
          {#if j.haushalt}<rect x={i * 64 + 22} y={70 - (j.haushalt / maxHaushalt) * 50} width="14" height={(j.haushalt / maxHaushalt) * 50} fill="var(--header)" opacity="0.6" />{/if}
          {#if j.spenden}<rect x={i * 64 + 40} y={70 - (j.spenden / maxSpenden) * 50} width="8" height={(j.spenden / maxSpenden) * 50} fill="var(--muted)" />{/if}
          {#each j.posten as _, k}<circle cx={i * 64 + 26} cy={76 + k * 4} r="2.5" fill="var(--header)" />{/each}
          <text x={i * 64 + 26} y="88" text-anchor="middle" font-size="8">{j.jahr}</text>
          <title>{j.jahr}: {[j.lobby ? `Lobbyregister ab ${fmtEuro(j.lobby)}` : "", j.haushalt ? `Haushalt Soll ${fmtEuro(j.haushalt)}` : "", j.spenden ? `Spenden ${fmtEuro(j.spenden)}` : ""].filter(Boolean).join(" · ") || "kein Geld-Eintrag"}{j.posten.length ? `; ${j.posten.join("; ")}` : ""}</title>
        {/each}
      </svg>
      <ul class="zlliste">
        {#each akte.zeitlinie as z}<li><span class="tabular">{z.jahr}</span> <span class="tag">{z.art}</span> {z.text}</li>{/each}
      </ul>
      <p class="muted small">Balken je Jahr, von links: Lobbyregister-Untergrenzen, Haushalts-Soll, Spenden (schmal). Jede Reihe hat ihren eigenen Maßstab; die Quellen werden nicht addiert. Punkte: Posten mit Stand-Datum.</p>
    {/if}
  </section>

  <section class="block">
    <h3>Quellen und Stand</h3>
    <ul class="quellen">
      {#each akte.quellen as q}<li><a href={q.url ?? "#"} target="_blank" rel="noopener">{q.kurz}</a>{#if q.etikett} · {q.etikett}{/if}{#if q.stand} · Stand {q.stand}{/if} <span class="muted">({host(q.url)})</span></li>{/each}
    </ul>
    <p class="muted small">Akte erzeugt am {akte.stand}. Alle Angaben stammen aus amtlichen Veröffentlichungen oder Selbstauskünften der Genannten; rechtlich verbindlich sind die Originale.</p>
    <a class="melden" href={issueUrlAkte(akte)} target="_blank" rel="noopener">Fehler melden / Beleg einreichen</a>
    <a class="melden second" href="https://github.com/eis2k/Bundeshaushaltstracker/blob/main/CONTRIBUTING.md" target="_blank" rel="noopener">Korrektur vorschlagen (Pull Request)</a>
  </section>
</article>

<style>
  .akte { font-size: 12px; max-width: 980px; }
  .back { background: none; border: 0; color: var(--header); cursor: pointer; font: inherit; font-size: 12px; padding: 0; margin-bottom: 6px; }
  .path { color: var(--muted); font-size: 11px; }
  h2 { margin: 2px 0 6px; font-size: 18px; }
  h3 { margin: 0 0 6px; font-size: 13px; }
  h4 { margin: 8px 0 2px; font-size: 12px; }
  .funktionen { list-style: none; padding: 0; margin: 0 0 8px; }
  .funktionen li { padding: 4px 0; }
  .funktionen small { display: block; }
  .tag { display: inline-block; font-size: 10px; background: var(--bg); border-radius: 999px; padding: 1px 8px; margin-right: 4px; color: var(--muted); font-weight: 400; }
  .note { background: var(--bg); border-left: 3px solid var(--accent); border-radius: 6px; padding: 6px 10px; margin: 6px 0; }
  .netz { font: inherit; font-size: 12px; background: var(--header); color: #fff; border: 0; border-radius: 8px; padding: 6px 12px; cursor: pointer; }
  .block { background: var(--panel); border: 1px solid var(--border); border-radius: 10px; padding: 10px 12px; margin-top: 10px; }
  table { width: 100%; border-collapse: collapse; }
  th { text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: .05em; color: var(--muted); padding: 5px 6px; border-bottom: 1px solid var(--border); vertical-align: bottom; }
  th small { display: block; text-transform: none; letter-spacing: 0; font-weight: 400; }
  td { padding: 5px 6px; border-bottom: 1px solid #f0f0f2; vertical-align: top; }
  td small { display: block; font-size: 10px; }
  .num { text-align: right; white-space: nowrap; }
  .scroll { overflow-x: auto; }
  .link { background: none; border: 0; color: var(--header); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; }
  .angaben { margin: 0 0 4px 16px; padding: 0; }
  .zl { width: 100%; max-width: 760px; height: 90px; display: block; }
  .zlliste { list-style: none; padding: 0; margin: 6px 0 0; max-height: 220px; overflow-y: auto; }
  .zlliste li { padding: 2px 0; border-top: 1px solid #f0f0f2; }
  .quellen { padding-left: 16px; margin: 0; }
  .melden { display: inline-block; margin-top: 8px; margin-right: 8px; font-size: 12px; background: var(--header); color: #fff; border-radius: 8px; padding: 6px 12px; text-decoration: none; }
  .melden.second { background: var(--bg); color: var(--fg); border: 1px solid var(--border); }
  .muted { color: var(--muted); }
  .small { font-size: 11px; }
  .bezuege h4 { margin: 10px 0 4px; font-size: 13px; }
  .summe { margin: 8px 0 2px; }
  .hinweise { padding-left: 18px; margin: 6px 0; }
  .hinweise li { margin: 2px 0; }
</style>
