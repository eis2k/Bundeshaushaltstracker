<script lang="ts">
  /** Karte „Politische Verantwortung“ (Spec §4.11): Leitung des fokussierten Einzelplans, Haushalt, Anteil, Top-Empfänger je Quelle. */
  import { ChevronRight, Info } from "lucide-svelte";
  import { fmtEuro } from "../model/format";
  import type { TopEmpfaenger, Verantwortung } from "../model/profiteure";
  import Avatar from "./Avatar.svelte";
  import Partei from "./Partei.svelte";
  import { parteiKurz } from "../model/verantwortung";
  import { chef as chefVon, vorgaenger } from "../model/ministerien";

  let { v, top, jahr, empfaengerJahr, onAkte, onEmpfaenger, onFokus }: {
    v: Verantwortung | null; top: TopEmpfaenger[]; jahr: number; empfaengerJahr: number | null;
    onAkte: (id: string) => void; onEmpfaenger: (id: string) => void; onFokus: (epl: string) => void;
  } = $props();
  const chef = $derived(v ? chefVon(v.leitung) : null);
  const zuvor = $derived(v ? vorgaenger(v.leitung, chef) : []);
  const rolle = $derived(chef ? (/kanzler/i.test(chef.amt) ? "Kanzler/in" : /chef/i.test(chef.amt) ? "Chef/in" : /in$/.test(chef.amt.split(" ")[0]) ? "Ministerin" : /minister/i.test(chef.amt) ? "Minister" : chef.amt) : "");
  /** Kürzel wie „BMAS“: Bundesministerium → BM, dann Anfangsbuchstaben der Sachworte. */
  function kuerzel(name: string): string {
    const rest = name.replace(/\(.*?\)/g, "").replace(/^Bundesministerium\s+(für|der|des)\s+/i, "");
    const praefix = /^Bundesministerium/i.test(name) ? "BM" : "";
    const k = rest.split(/[\s-]+/).filter((w) => w && !/^(für|und|der|die|des|dem|den|im)$/i.test(w)).map((w) => w[0]).join("").toUpperCase();
    return (praefix + k).slice(0, 6);
  }
</script>

<section class="karte" aria-label="Politische Verantwortung">
  <h3>Politische Verantwortung <span class="info" title="Zuständigkeit für einen Einzelplan laut Bundesregierung. Sie ist keine persönliche Entscheidung über eine einzelne Zahlung."><Info size={14} /></span></h3>
  {#if v}
    <div class="kopf">
      {#if chef}<Avatar name={chef.name} size={64} />{:else}<Avatar name={v.name} art="organisation" size={64} />{/if}
      <div class="text">
        <b>{v.name}</b>
        {#if chef}
          <span class="zeile">{rolle}: <button class="link" onclick={() => onAkte(chef.id)}>{chef.name}</button> <Partei name={chef.partei ? parteiKurz(chef.partei) : null} /></span>
        {:else}
          <span class="zeile muted">{v.hinweis}</span>
        {/if}
        {#each zuvor as z (z.id)}<span class="zeile muted">zuvor: <button class="link" onclick={() => onAkte(z.id)}>{z.name}</button>{#if z.bis} (bis {z.bis}){/if}</span>{/each}
        <span class="zeile">Haushalt: <b class="tabular">{fmtEuro(v.haushalt)}</b></span>
        <span class="zeile">Anteil: <b class="tabular">{v.anteil.toLocaleString("de-DE")} %</b></span>
      </div>
      <button class="pfeil" title="Einzelplan im Fluss fokussieren" aria-label="Einzelplan im Fluss fokussieren" onclick={() => onFokus(v.epl)}><ChevronRight size={18} /></button>
    </div>
    {#if chef && v.hinweis}<p class="muted small">{v.hinweis}</p>{/if}
    <h4>Top-Empfänger ({kuerzel(v.name)})</h4>
    {#if top.length}
      <ul>
        {#each top as e (e.id)}
          <li>
            <Avatar name={e.name} art="organisation" size={28} />
            <button class="link name" onclick={() => onEmpfaenger(e.id)}>{e.name}</button>
            <span class="betrag"><b class="tabular">{fmtEuro(e.wert)}</b><small>{e.quelle === "haushalt" ? `Soll ${empfaengerJahr ?? ""}` : "Lobbyregister, Untergrenze"}</small></span>
          </li>
        {/each}
      </ul>
      <p class="muted small">Haushaltsbeträge aus Titeln, deren Zweckbestimmung den Empfänger nennt; Lobbyregister-Beträge sind Eigenangaben der Organisation. Beide werden nicht addiert.</p>
    {:else}
      <p class="muted small">Für diesen Einzelplan ist noch kein Empfänger mit Seite zugeordnet ({jahr}).</p>
    {/if}
  {:else}
    <p class="muted small">Kein Einzelplan mit Ausgaben im Jahr {jahr}.</p>
  {/if}
</section>

<style>
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; font-size: 12px; }
  h3 { margin: 0 0 10px; font-size: 14px; color: var(--header); display: flex; align-items: center; gap: 6px; }
  .info { color: var(--muted); display: inline-flex; }
  h4 { margin: 14px 0 8px; font-size: 13px; color: var(--header); }
  .kopf { display: grid; grid-template-columns: auto 1fr auto; gap: 10px; align-items: start; }
  .text { display: flex; flex-direction: column; gap: 3px; min-width: 0; }
  .text > b { color: var(--header); font-size: 13px; }
  .zeile { color: var(--fg); display: flex; flex-wrap: wrap; gap: 4px; align-items: center; }
  .zeile b { color: var(--header); }
  .link { background: none; border: 0; padding: 0; font: inherit; color: var(--header); cursor: pointer; text-align: left; }
  .link:hover { text-decoration: underline; }
  .pfeil { background: none; border: 0; color: var(--muted); cursor: pointer; padding: 4px; border-radius: 8px; }
  .pfeil:hover { background: var(--bg); color: var(--header); }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  li { display: grid; grid-template-columns: 28px 1fr auto; gap: 8px; align-items: center; }
  .name { font-weight: 600; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .betrag { display: flex; flex-direction: column; align-items: flex-end; }
  .betrag b { color: var(--header); }
  .betrag small { color: var(--muted); font-size: 10px; }
  .muted { color: var(--muted); } .small { font-size: 11px; margin: 8px 0 0; }
</style>
