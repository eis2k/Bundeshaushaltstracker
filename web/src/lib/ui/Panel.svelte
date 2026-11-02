<script lang="ts">
  import { fmtDelta, fmtEuro, fmtPct } from "../model/format";
  import { gesetzStatus } from "../model/presets";
  import { childFactorsOverridden, effectiveFactor, effectiveValue, rowFactor } from "../model/scenario";
  import { buildTree, revenueGroups } from "../model/tree";
  import { groupBy } from "../model/schnitte";
  import type { BudgetRow, NodeId, TreeNode } from "../model/types";
  import type { AppState } from "../state.svelte";
  import SteuerPanel from "./SteuerPanel.svelte";

  let { app }: { app: AppState } = $props();

  interface Info {
    id: NodeId;
    kind: "epl" | "kap" | "titel" | "einnahmen";
    label: string;
    path: string[];
    rows: BudgetRow[];
    original: number;
    effective: number;
    parentOriginal: number;
    parentLabel: string;
    factor: number;
    userFactor: number | null;
    row?: BudgetRow;
  }

  function rowsOf(n: TreeNode): BudgetRow[] {
    return n.row ? [n.row] : n.children.flatMap(rowsOf);
  }

  const info = $derived.by<Info | null>(() => {
    const data = app.viewData;
    const id = app.selected;
    if (!data || !id) return null;
    const factors = app.factors;
    const total = app.balance?.ausgabenOriginal ?? 0;
    if (id.startsWith("E:")) {
      const g = revenueGroups(data, app.scenario.includeSv).find((g) => g.id === id);
      if (!g) return null;
      const effective = g.rows.reduce((s, r) => s + effectiveValue(r, factors), 0);
      const f = g.rows.length ? rowFactor(g.rows[0], factors) : 1;
      return { id, kind: "einnahmen", label: g.label, path: ["Einnahmen"], rows: g.rows, original: g.soll, effective,
               parentOriginal: app.balance?.einnahmenOriginal ?? 0, parentLabel: "aller Einnahmen", factor: f,
               userFactor: app.scenario.factors[id] ?? null };
    }
    if (id.includes(":")) {
      const g = groupBy(data, id.startsWith("ka:") ? "kostenart" : "empfaengerart", app.scenario.includeSv).byId.get(id);
      if (!g) return null;
      const rows = rowsOf(g);
      const effective = rows.reduce((s, r) => s + effectiveValue(r, factors), 0);
      return { id, kind: "epl", label: g.label, path: [id.startsWith("ka:") ? "Kostenart" : "Empfänger-Art"], rows, original: g.soll, effective,
               parentOriginal: total, parentLabel: "aller Ausgaben", factor: effectiveFactor(id, factors), userFactor: app.scenario.factors[id] ?? null };
    }
    const tree = buildTree(data, app.scenario.includeSv);
    const node = tree.byId.get(id);
    if (!node) return null;
    const rows = rowsOf(node);
    const effective = rows.reduce((s, r) => s + effectiveValue(r, factors), 0);
    const parts = id.split("-");
    const path: string[] = [];
    let parentOriginal = total, parentLabel = "aller Ausgaben";
    if (parts.length >= 1) path.push(data.epl[parts[0]] ?? `Einzelplan ${parts[0]}`);
    if (parts.length >= 2) {
      path.push(data.kap[parts[1]] ?? `Kapitel ${parts[1]}`);
      const epl = tree.byId.get(parts[0]);
      if (epl) { parentOriginal = epl.soll; parentLabel = `der Ausgaben von „${epl.label}“`; }
    }
    if (parts.length === 3) {
      const kap = tree.byId.get(`${parts[0]}-${parts[1]}`);
      if (kap) { parentOriginal = kap.soll; parentLabel = `des Kapitels „${kap.label}“`; }
    }
    return { id, kind: node.kind, label: node.label, path, rows, original: node.soll, effective, parentOriginal, parentLabel,
             factor: effectiveFactor(id, factors), userFactor: app.scenario.factors[id] ?? null, row: node.row };
  });

  const gesetz = $derived(info && info.kind !== "einnahmen" ? gesetzStatus(info.id, app.gesetz) : null);
  const overridden = $derived(info ? childFactorsOverridden(info.id, app.scenario.factors) : []);
  const delta = $derived(info ? info.effective - info.original : 0);
  const share = $derived(info && info.parentOriginal > 0 ? Math.abs(delta) / info.parentOriginal : 0);
  const quelle = $derived(app.stand === "ist" ? app.data?.quelle.ist : app.data?.quelle.soll);
  const steuer = $derived(app.selected?.startsWith("x:") ? app.steuern.find((s) => s.id === app.selected!.slice(2)) ?? null : null);

  /** Ausgewählter Knoten einer Sozialkasse (topf:grv, posten:grv:renten, beitraege:grv, defizit:grv, ruecklage:grv). */
  const kasse = $derived.by(() => {
    const id = app.selected;
    const sk = app.viewSozialkassen;
    const t = app.toepfe;
    if (!id || !sk || !t) return null;
    const m = id.match(/^(topf|posten|beitraege|sonstige|defizit|ruecklage):([a-z]+)(?::(.+))?$/);
    if (!m || m[2] === "bund") return null;
    const data = sk.toepfe[m[2]];
    const topf = t.toepfe.find((x) => x.id === m[2]);
    if (!data || !topf) return null;
    const posten = m[1] === "posten" ? data.ausgaben.find((p) => p.id === m[3]) ?? null : null;
    const q = data.quelle;
    const quelle = typeof q === "string" ? { kurz: q, dokument: null, url: null } : q;
    return { kind: m[1], data, topf, posten, quelle };
  });
  const erklaerung = $derived(info ? app.texte[info.id] ?? null : null);

  let betrag = $state("");
  function applyBetrag() {
    if (!info || info.original <= 0) return;
    const v = Number.parseFloat(betrag.replace(",", "."));
    if (!Number.isFinite(v)) return;
    app.setFactor(info.id, (v * 1e6) / info.original);
    betrag = "";
  }
  function slide(e: Event) {
    if (!info) return;
    app.setFactor(info.id, Number((e.target as HTMLInputElement).value) / 100);
  }
</script>

<aside class="panel">
  {#if app.unknownIds.length}
    <div class="note warn">{app.unknownIds.length} Einstellung{app.unknownIds.length === 1 ? "" : "en"} betreffen Titel, die es {app.jahr} nicht gibt, und bleiben hier ohne Wirkung.</div>
  {/if}
  {#if steuer}
    <SteuerPanel {app} szenario={steuer} />
  {:else if kasse}
    <div class="path">Sozialkasse › {kasse.data.name}{#if kasse.posten} › {kasse.posten.text}{/if}</div>
    <h3>{kasse.posten ? kasse.posten.text : kasse.kind === "beitraege" ? `Beiträge ${kasse.data.kurz}` : kasse.kind === "defizit" ? `Defizit ${kasse.data.kurz}` : kasse.kind === "ruecklage" ? `Rücklage ${kasse.data.kurz}` : kasse.data.name}</h3>
    {#if kasse.posten}
      <div class="kv"><span>Betrag {app.jahr}</span><b class="tabular">{fmtEuro(kasse.posten.betrag)}</b></div>
      <div class="kv"><span>Anteil an den Ausgaben der Kasse</span><b class="tabular">{fmtPct(kasse.topf.ausgaben ? kasse.posten.betrag / kasse.topf.ausgaben : 0)}</b></div>
    {:else}
      <div class="kv"><span>Einnahmen</span><b class="tabular">{fmtEuro(kasse.topf.einnahmen)}{#if kasse.topf.einnahmen !== kasse.topf.einnahmenOriginal} <small class="muted">war {fmtEuro(kasse.topf.einnahmenOriginal)}</small>{/if}</b></div>
      <div class="kv"><span>davon Bundesmittel</span><b class="tabular">{fmtEuro(kasse.topf.bundesmittel)}</b></div>
      <div class="kv"><span>Ausgaben</span><b class="tabular">{fmtEuro(kasse.topf.ausgaben)}</b></div>
      <div class="kv"><span>{kasse.topf.saldo >= 0 ? "Rücklage (Überschuss)" : "Defizit"}</span><b class="tabular" class:bad={kasse.topf.saldo < 0} class:good={kasse.topf.saldo >= 0}>{fmtEuro(Math.abs(kasse.topf.saldo))}</b></div>
      <div class="box">
        <b>Einnahmen</b>
        {#each kasse.data.einnahmen as e}<p><span class="tabular">{fmtEuro(e.betrag)}</span> {e.text}{#if e.geprueft === false} <span class="tag">ungeprüft</span>{/if}</p>{/each}
        <b>Ausgaben</b>
        {#each kasse.data.ausgaben as e}<p><span class="tabular">{fmtEuro(e.betrag)}</span> {e.text}{#if e.geprueft === false} <span class="tag">ungeprüft</span>{/if}</p>{/each}
      </div>
    {/if}
    {#if kasse.data.geschaetzt}
      <div class="note warn">Geschätzt: {kasse.data.hinweis ?? "zwischen Stützjahren interpoliert"}. Amtliche Werte liegen für 2015, 2020, 2024 und 2025 vor.</div>
    {/if}
    {#if kasse.data.bundesmittel.length}
      <div class="note">Verknüpfte Titel im Bundeshaushalt: {kasse.data.bundesmittel.map((b) => `${b.titel} (${b.text})`).join(", ")}. Regler an diesen Titeln verändern die Einnahmen dieser Kasse.</div>
    {/if}
    <div class="src">
      Quelle: {#if kasse.quelle?.url}<a href={kasse.quelle.url} target="_blank" rel="noopener">{kasse.quelle.dokument ?? kasse.quelle.kurz}</a>{:else}{kasse.quelle?.kurz ?? "siehe data/manual/sozialkassen.yaml"}{/if}
      {#if kasse.data.hinweis && !kasse.data.geschaetzt}<br /><span class="muted">{kasse.data.hinweis}</span>{/if}
    </div>
  {:else if !info}
    <div class="empty">
      <b>Klick auf ein Band, einen Knoten oder eine Kachel.</b>
      <p>Dann siehst du hier, was es ist, was es kostet, woher die Zahl stammt, und kannst daran drehen.</p>
      <p class="muted">Haushaltsjahr {app.jahr}, {app.stand === "ist" ? "Ist (Haushaltsrechnung)" : "Soll (Haushaltsplan)"}. {app.data?.rows.length ?? 0} Titel geladen.</p>
    </div>
  {:else}
    <div class="path">{info.path.join(" › ")}{#if info.row} › Titel {info.row.titel.slice(0, 3)} {info.row.titel.slice(3)}{/if}</div>
    <h3>{info.label}</h3>
    <div class="kv"><span>Original</span><b class="tabular">{fmtEuro(info.original)}</b></div>
    <div class="kv"><span>Dein Wert</span><b class="tabular" class:changed={info.factor !== 1}>{fmtEuro(info.effective)}</b></div>
    {#if info.original > 0 || info.factor !== 1}
      <input class="slider" type="range" min="0" max="200" step="1" value={Math.round(info.factor * 100)} oninput={slide} aria-label="Anteil vom Original in Prozent" />
      <div class="scale"><span>0 %</span><span>{fmtPct(info.factor)}</span><span>200 %</span></div>
      <div class="quick">
        {#each [0, 0.5, 1, 1.5] as q}
          <button class:on={Math.abs(info.factor - q) < 0.005} onclick={() => app.setFactor(info!.id, q)}>{fmtPct(q)}</button>
        {/each}
        <span class="betrag">
          <input type="text" inputmode="decimal" placeholder="Mio €" bind:value={betrag} onkeydown={(e) => e.key === "Enter" && applyBetrag()} aria-label="Betrag in Millionen Euro" />
          <button onclick={applyBetrag}>setzen</button>
        </span>
      </div>
    {:else}
      <div class="note">{info.original < 0 ? "Absetzungstitel (negativer Ansatz, z. B. Globale Minderausgabe oder Disagio). Ein Regler ist hier nicht vorgesehen." : "Leertitel ohne Ansatz. Ein Regler hätte hier keine Wirkung."}</div>
    {/if}
    {#if overridden.length}
      <div class="note">{overridden.length} untergeordnete{overridden.length === 1 ? "r Posten ist" : " Posten sind"} einzeln gesetzt und folgen diesem Regler nicht.</div>
    {/if}
    {#if info.kind !== "einnahmen"}
      <div class="status">
        {#if gesetz}
          <span class="tag" class:gesetz={gesetz.status === "gesetz"} class:frei={gesetz.status === "frei"}>{gesetz.status === "gesetz" ? "Gesetz" : "frei"}</span>
          <span class="grund">{gesetz.grundlage} <a href={gesetz.quelle} target="_blank" rel="noopener">Quelle</a></span>
          {#if gesetz.status === "gesetz" && info.factor !== 1}<span class="muted">Dafür müsste ein Gesetz geändert werden.</span>{/if}
        {:else}
          <span class="tag">ungeprüft</span><span class="muted">Ob dieser Posten gesetzlich gebunden ist, wurde noch nicht erfasst.</span>
        {/if}
      </div>
    {/if}
    {#if info.row}
      {@const emp = app.empfaengerByTitel[info.id]}
      {#if emp}
        <div class="note"><b>Empfänger:</b> {emp.name} · <button class="link" onclick={() => void app.openEmpfaenger(emp.id)}>Empfänger-Seite öffnen</button></div>
      {:else if /^(6[3-9]|8[89])/.test(info.row.titel) && info.kind !== "einnahmen"}
        <div class="note">Empfänger nicht veröffentlicht: Dieser Titel nennt keinen Empfänger. <button class="link" onclick={() => app.openEmpfaengerListe({ epl: info!.row!.epl })}>Bekannte Empfänger dieses Ministeriums laut Lobbyregister</button> · <a href="https://fragdenstaat.de/anfrage-stellen/" target="_blank" rel="noopener">Anfrage nach dem Informationsfreiheitsgesetz stellen</a></div>
      {/if}
    {/if}
    <div class="box">
      <b>Was das ist</b>
      {#if erklaerung}
        <p>{erklaerung.text}</p>
        <p class="muted">Erklärtext, Stand {erklaerung.stand}; Belege: {#each erklaerung.quelle as q, i}{#if i > 0}, {/if}<a href={q} target="_blank" rel="noopener">{new URL(q).hostname.replace("www.", "")}</a>{/each}</p>
      {:else}
        <p>{#if info.row}{info.row.text}{:else}{info.kind === "epl" ? "Einzelplan" : info.kind === "kap" ? "Kapitel" : "Einnahmengruppe"} mit {info.rows.length} Titel{info.rows.length === 1 ? "" : "n"}.{/if}</p>
        <p class="muted">{info.row ? "Amtliche Zweckbestimmung; noch kein Erklärtext." : ""}</p>
      {/if}
      {#if info.factor !== 1}
        <b>Auswirkung deiner Änderung</b>
        <p><span class="tabular" class:good={info.kind === "einnahmen" ? delta > 0 : delta < 0} class:bad={info.kind === "einnahmen" ? delta < 0 : delta > 0}>{fmtDelta(delta)}</span>, das sind {fmtPct(share)} {info.parentLabel}. <span class="muted">(Rechnung, keine Prognose)</span></p>
      {/if}
    </div>
    <div class="src">
      Quelle: {#if quelle}<a href={quelle.url} target="_blank" rel="noopener">{quelle.dokument}</a>{#if quelle.abgerufen}, abgerufen {quelle.abgerufen.slice(0, 10)}{/if}{:else}bundeshaushalt.de{/if}
      {#if app.data?.quelle.hinweise.length}<br /><span class="muted">{app.data.quelle.hinweise.join(" · ")}</span>{/if}
    </div>
  {/if}
</aside>

<style>
  .panel { background: var(--panel); border: 1px solid var(--border); border-radius: 12px; padding: 14px; font-size: 12px; }
  .link { background: none; border: 0; color: var(--header); text-decoration: underline; cursor: pointer; font: inherit; padding: 0; }
  .empty b { font-size: 13px; }
  .empty p { margin: 6px 0 0; }
  .muted { color: var(--muted); }
  .path { color: var(--muted); font-size: 11px; margin-bottom: 4px; }
  h3 { margin: 0 0 8px; font-size: 14px; line-height: 1.3; }
  .kv { display: flex; justify-content: space-between; padding: 3px 0; }
  .kv b.changed { color: var(--bad); }
  .slider { width: 100%; margin: 10px 0 2px; accent-color: var(--header); }
  .scale { display: flex; justify-content: space-between; font-size: 10px; color: var(--muted); }
  .scale span:nth-child(2) { font-weight: 700; color: var(--fg); }
  .quick { display: flex; gap: 4px; flex-wrap: wrap; margin: 8px 0; align-items: center; }
  .quick button { font-size: 11px; padding: 4px 8px; border-radius: 999px; border: 1px solid #d1d1d6; background: #fff; cursor: pointer; color: var(--fg); }
  .quick button.on { background: var(--header); color: #fff; border-color: var(--header); }
  .betrag { display: flex; gap: 4px; margin-left: auto; }
  .betrag input { width: 70px; font-size: 11px; padding: 3px 6px; border: 1px solid #d1d1d6; border-radius: 6px; }
  .note { background: var(--bg); border-radius: 8px; padding: 6px 8px; margin: 6px 0; color: var(--muted); }
  .note.warn { background: #fef3c7; color: #92400e; }
  .status { display: flex; gap: 6px; align-items: baseline; flex-wrap: wrap; margin: 8px 0; }
  .tag { font-size: 10px; padding: 2px 6px; border-radius: 4px; background: #e5e7eb; color: #374151; font-weight: 700; }
  .tag.gesetz { background: #fee2e2; color: #991b1b; }
  .tag.frei { background: #dcfce7; color: #166534; }
  .box { background: var(--bg); border-left: 3px solid var(--accent); border-radius: 6px; padding: 8px 10px; margin-top: 8px; }
  .box p { margin: 2px 0 6px; }
  .good { color: var(--good); font-weight: 700; }
  .bad { color: var(--bad); font-weight: 700; }
  .src { font-size: 10px; color: var(--muted); margin-top: 10px; }
</style>
