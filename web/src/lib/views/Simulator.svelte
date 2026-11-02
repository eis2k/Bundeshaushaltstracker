<script lang="ts">
  /** Haushaltssimulator (Spec §4.11): Reglerkarten je Bereich, Ergebniskarte, Presets und Steuer-Modelle daneben, Szenario teilen. */
  import { Globe, GraduationCap, HeartHandshake, Leaf, Shield, ShieldCheck, Share2, SlidersHorizontal, Stethoscope, TrainFront, RotateCcw } from "lucide-svelte";
  import { fmtEuro, fmtPct } from "../model/format";
  import { BEREICHE, bereichFaktor, ergebnis } from "../model/simulator";
  import type { AppState } from "../state.svelte";
  import type { IconComp } from "../ui/icons";
  import Panel from "../ui/Panel.svelte";
  import Presets from "../ui/Presets.svelte";

  let { app }: { app: AppState } = $props();
  const ICONS: Record<string, IconComp> = { Shield, GraduationCap, HeartHandshake, TrainFront, Leaf, Stethoscope, ShieldCheck, Globe };
  const data = $derived(app.viewData!);
  const erg = $derived(app.balance ? ergebnis(app.balance) : null);
  const original = $derived(app.balance?.ausgabenOriginal ?? 0);
  const veraenderungPct = $derived(erg && original > 0 ? Math.round((erg.veraenderung / original) * 1000) / 10 : 0);
  function setze(epls: string[], faktor: number) { for (const epl of epls) app.setFactor(epl, faktor); }
  function prozent(f: number): string { return f === 1 ? "±0 %" : `${f > 1 ? "+" : "−"}${fmtPct(Math.abs(f - 1))}`; }
  function betrag(epls: string[]): number {
    let s = 0;
    for (const r of data.rows) if (r.art === "A" && epls.includes(r.epl) && (!r.sv || app.scenario.includeSv)) s += r.soll;
    return s;
  }
  let copied = $state(false);
  async function teilen() {
    const url = `${location.origin}${location.pathname}#${app.toHash()}`;
    try { await navigator.clipboard.writeText(url); copied = true; setTimeout(() => (copied = false), 2000); } catch { prompt("Link zum Kopieren:", url); }
  }
  const geaendert = $derived(Object.keys(app.scenario.factors).length > 0 || app.scenario.presets.length > 0 || !!app.scenario.steuern);
</script>

<div class="sim">
  <div class="links">
    <section class="karte regler">
      <h3><SlidersHorizontal size={16} /> Ausgaben verändern <small class="muted">Soll {app.jahr}, Faktor je Einzelplan; −50 % bis +50 % in 5-%-Schritten</small></h3>
      <div class="bereiche">
        {#each BEREICHE as b (b.id)}
          {@const Icon = ICONS[b.icon] ?? Shield}
          {@const f = bereichFaktor(b, app.factors)}
          <div class="bereich" class:aktiv={f !== 1}>
            <span class="kachel"><Icon size={16} /></span>
            <div class="text">
              <label for={`regler-${b.id}`}>{b.label}</label>
              <small class="muted">{b.epls.map((e) => data.epl[e] ?? `Einzelplan ${e}`).join(", ")} · {fmtEuro(betrag(b.epls))}</small>
              <input id={`regler-${b.id}`} type="range" min="0.5" max="1.5" step="0.05" value={f} oninput={(e) => setze(b.epls, Number((e.target as HTMLInputElement).value))} />
            </div>
            <b class="tabular" class:gut={f < 1} class:schlecht={f > 1}>{prozent(f)}</b>
          </div>
        {/each}
      </div>
      <p class="muted small">Die Regler setzen denselben Faktor wie das Seitenpanel und die Haushaltsansichten; gesetzlich gebundene Titel sind dort gekennzeichnet. Feinere Eingriffe (Kapitel, Titel) im Geldfluss.</p>
    </section>
    <section class="karte">
      <h3>Presets und Steuer-Modelle</h3>
      <Presets {app} />
      <Panel {app} />
    </section>
  </div>
  <aside class="rechts">
    <section class="karte ergebnis">
      <h3>Ergebnis deines Szenarios</h3>
      {#if erg}
        <dl>
          <dt>Gesamtvolumen</dt><dd class="tabular">{fmtEuro(erg.gesamtvolumen)}</dd>
          <dt>Veränderung</dt><dd class="tabular" class:gut={erg.veraenderung < 0} class:schlecht={erg.veraenderung > 0}>{erg.veraenderung === 0 ? "±0 €" : `${erg.veraenderung > 0 ? "+" : "−"}${fmtEuro(Math.abs(erg.veraenderung))}`} <small>({veraenderungPct > 0 ? "+" : ""}{veraenderungPct.toLocaleString("de-DE")} %)</small></dd>
          <dt>Neuverschuldung</dt><dd class="tabular" class:schlecht={erg.neuverschuldung > (app.balance?.neueSchuldenOriginal ?? 0)} class:gut={erg.neuverschuldung < (app.balance?.neueSchuldenOriginal ?? 0)}>{fmtEuro(erg.neuverschuldung)}<small> war {fmtEuro(app.balance?.neueSchuldenOriginal ?? 0)}</small></dd>
          <dt>Defizitquote</dt><dd class="tabular">{(Math.round(erg.defizitquote * 1000) / 10).toLocaleString("de-DE")} %<small> Neuverschuldung / Ausgaben</small></dd>
        </dl>
        <p class="muted small">Rechnung auf den Soll-Ansätzen {app.jahr}, keine Prognose; Einnahmen bleiben fest, außer über Steuer-Modelle. Soll und Annahmen sind getrennt ausgewiesen.</p>
      {:else}
        <p class="muted">Lade Haushalt …</p>
      {/if}
      <div class="knoepfe">
        <button class="knopf" onclick={teilen}><Share2 size={14} /> {copied ? "Link kopiert" : "Szenario teilen"}</button>
        <button class="knopf hell" onclick={() => app.reset()} disabled={!geaendert}><RotateCcw size={14} /> Zurücksetzen</button>
      </div>
    </section>
  </aside>
</div>

<style>
  .sim { display: grid; grid-template-columns: minmax(0, 1fr) 320px; gap: 12px; align-items: start; font-size: 12px; }
  .links, .rechts { display: flex; flex-direction: column; gap: 12px; min-width: 0; }
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }
  h3 { margin: 0 0 10px; font-size: 14px; color: var(--header); display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
  h3 small { font-weight: 400; font-size: 11px; }
  .bereiche { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
  .bereich { display: grid; grid-template-columns: 30px 1fr auto; gap: 10px; align-items: center; background: var(--bg); border-radius: 12px; padding: 10px 12px; border: 1px solid transparent; }
  .bereich.aktiv { border-color: var(--nav-on); }
  .kachel { width: 30px; height: 30px; border-radius: 9px; background: var(--chip-blau); color: var(--nav-on); display: inline-flex; align-items: center; justify-content: center; }
  .text { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  label { font-weight: 600; color: var(--header); }
  .text small { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 10px; }
  input[type="range"] { width: 100%; accent-color: var(--nav-on); margin-top: 4px; }
  .bereich b { min-width: 52px; text-align: right; color: var(--muted); }
  .gut { color: var(--good) !important; } .schlecht { color: var(--bad) !important; }
  .ergebnis dl { display: grid; grid-template-columns: 1fr auto; gap: 8px 12px; margin: 0; }
  .ergebnis dt { color: var(--muted); }
  .ergebnis dd { margin: 0; text-align: right; font-weight: 700; color: var(--header); }
  .ergebnis dd small { display: block; font-weight: 400; color: var(--muted); font-size: 10px; }
  .knoepfe { display: flex; flex-direction: column; gap: 6px; margin-top: 10px; }
  .knopf { display: inline-flex; align-items: center; justify-content: center; gap: 6px; font: inherit; font-size: 12px; font-weight: 600; background: var(--nav-on); color: var(--nav-on-fg); border: 0; border-radius: 10px; padding: 8px 10px; cursor: pointer; }
  .knopf.hell { background: var(--chip-blau); color: var(--header); }
  .knopf:disabled { opacity: .5; cursor: default; }
  .muted { color: var(--muted); } .small { font-size: 11px; margin: 10px 0 0; }
  @media (max-width: 1000px) { .sim { grid-template-columns: 1fr; } }
  @media (max-width: 640px) { .bereiche { grid-template-columns: 1fr; } }
</style>
