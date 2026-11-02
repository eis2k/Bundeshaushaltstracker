<script lang="ts">
  import { fmtEuro } from "../model/format";
  import { ministerien } from "../model/ministerien";
  import type { AppState } from "../state.svelte";
  import { onMount } from "svelte";

  let { app }: { app: AppState } = $props();
  const liste = $derived(app.viewData ? ministerien(app.viewData, app.stand, app.scenario.includeSv, app.jahr, app.index?.jahre.at(-1) ?? app.jahr, app.personIndex, app.empfaengerIndex) : []);
  const summe = $derived(liste.reduce((s, m) => s + m.ausgaben, 0));
  onMount(() => { void app.ensurePersonen(); void app.ensureEmpfaenger(); });
</script>

<div class="ministerien">
  <p class="intro muted">Je Einzelplan: Ausgaben {app.jahr} ({app.stand === "ist" ? "Ist" : "Soll"}, gezählt wie im Geldfluss), Leitung laut Bundesregierung für {app.jahr} und Empfänger mit eigener Seite. Zuständigkeit für einen Einzelplan ist keine Entscheidung über eine einzelne Zahlung.</p>
  <div class="karten">
    {#each liste as m (m.epl)}
      <article class="karte">
        <header>
          <span class="epl">Einzelplan {m.epl}</span>
          <h3>{m.name}</h3>
        </header>
        <div class="zahl"><b class="tabular">{fmtEuro(m.ausgaben)}</b><small class="muted">{summe ? Math.round((m.ausgaben / summe) * 1000) / 10 : 0} % der Ausgaben</small></div>
        <div class="balken" aria-hidden="true"><span style="width:{summe ? (m.ausgaben / summe) * 100 : 0}%"></span></div>
        <div class="leitung">
          {#each m.leitung as l (l.id)}
            <button class="person" onclick={() => void app.openAkte(l.id)} title={`${l.amt}${l.seit ? `, seit ${l.seit}` : ""}${l.bis ? `, bis ${l.bis}` : ""}`}>
              <span class="kreis" aria-hidden="true">{l.name.split(" ").filter((w) => !w.endsWith(".")).map((w) => w[0]).slice(0, 2).join("")}</span>
              <span class="pname">{l.name}<small>{l.amt}</small></span>
            </button>
          {/each}
          {#if m.leitungHinweis}<span class="muted hinweis">{m.leitungHinweis}</span>{/if}
        </div>
        <footer>
          <button class="chip" onclick={() => app.zeigeImFluss([m.epl])}>Im Geldfluss</button>
          <button class="chip" onclick={() => app.openEmpfaengerListe({ epl: m.epl })} disabled={!m.empfaenger}>{m.empfaenger} Empfänger</button>
        </footer>
      </article>
    {/each}
  </div>
</div>

<style>
  .ministerien { font-size: 13px; }
  .intro { margin: 0 0 12px; font-size: 12px; }
  .karten { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 14px; }
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; display: flex; flex-direction: column; gap: 8px; }
  .epl { font-size: 11px; color: var(--muted); text-transform: uppercase; letter-spacing: .05em; }
  h3 { margin: 2px 0 0; font-size: 15px; color: var(--header); line-height: 1.25; }
  .zahl { display: flex; align-items: baseline; gap: 8px; }
  .zahl b { font-size: 18px; color: var(--header); }
  .balken { height: 6px; background: var(--nav-bg); border-radius: 999px; overflow: hidden; }
  .balken span { display: block; height: 100%; background: var(--nav-on); border-radius: 999px; }
  .leitung { display: flex; flex-wrap: wrap; gap: 6px; min-height: 28px; }
  .person { display: inline-flex; align-items: center; gap: 6px; background: var(--chip-blau); color: var(--header); border: 0; border-radius: 999px; padding: 3px 10px 3px 3px; font: inherit; font-size: 12px; cursor: pointer; text-align: left; }
  .pname { display: flex; flex-direction: column; line-height: 1.1; }
  .pname small { font-size: 10px; color: var(--muted); }
  .hinweis { font-size: 11px; }
  .kreis { width: 22px; height: 22px; border-radius: 50%; background: var(--nav-on); color: var(--nav-on-fg); display: inline-flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; }
  footer { display: flex; gap: 6px; flex-wrap: wrap; margin-top: auto; }
  .chip { font-size: 12px; padding: 5px 10px; border-radius: 999px; border: 1px solid var(--border); background: var(--panel); color: var(--header); cursor: pointer; }
  .chip:hover:not(:disabled) { background: var(--chip-blau); }
  .chip:disabled { color: var(--muted); cursor: default; }
  .muted { color: var(--muted); }
</style>
