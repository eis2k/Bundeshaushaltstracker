<script lang="ts">
  /** Listenkarten „Geldherkunft“ und „Geldverwendung“ (Spec §4.11), auf Dashboard und Geldflüssen. */
  import { Coins, Landmark } from "lucide-svelte";
  import { herkunftVerwendung, type Posten } from "../model/dashboard";
  import { fmtEuro } from "../model/format";
  import type { Factors } from "../model/scenario";
  import type { YearData } from "../model/types";

  let { data, includeSv, factors, extraBund = 0, max = 5, getrennt = false }: { data: YearData; includeSv: boolean; factors: Factors; extraBund?: number; max?: number; getrennt?: boolean } = $props();
  const hv = $derived(herkunftVerwendung(data, includeSv, factors, extraBund));
  function kompakt(liste: Posten[]): Posten[] {
    const top = liste.slice(0, max);
    const rest = liste.slice(max);
    if (!rest.length) return top;
    return [...top, { id: "rest", label: `Weitere (${rest.length})`, wert: rest.reduce((a, x) => a + x.wert, 0), anteil: Math.round(rest.reduce((a, x) => a + x.anteil, 0) * 10) / 10 }];
  }
</script>

{#snippet liste(posten: Posten[], ton: "gruen" | "blau")}
  <ul class="liste">
    {#each posten as p (p.id)}
      <li class:modell={p.id === "modell"}><span class="kachel {ton}">{#if ton === "gruen"}<Coins size={14} />{:else}<Landmark size={14} />{/if}</span><span class="l">{p.label}</span><b class="tabular">{fmtEuro(p.wert)}</b><small class="tabular">{p.anteil.toLocaleString("de-DE")} %</small></li>
    {/each}
  </ul>
{/snippet}

{#if getrennt}
  <section class="karte"><h3>Geldherkunft</h3>{@render liste(kompakt(hv.herkunft), "gruen")}</section>
  <section class="karte"><h3>Geldverwendung</h3>{@render liste(hv.verwendung, "blau")}</section>
{:else}
  <h3>Geldherkunft</h3>{@render liste(kompakt(hv.herkunft), "gruen")}
  <h3>Geldverwendung</h3>{@render liste(hv.verwendung, "blau")}
{/if}

<style>
  .karte { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 14px 16px; }
  h3 { margin: 0 0 10px; font-size: 14px; color: var(--header); }
  .liste { list-style: none; margin: 0 0 14px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
  .karte .liste { margin-bottom: 0; }
  .liste li { display: grid; grid-template-columns: 26px 1fr auto auto; gap: 8px; align-items: center; font-size: 12px; background: var(--bg); border-radius: 10px; padding: 6px 8px; }
  .liste b { color: var(--header); }
  .liste small { color: var(--muted); min-width: 44px; text-align: right; }
  .kachel { width: 26px; height: 26px; border-radius: 8px; display: inline-flex; align-items: center; justify-content: center; }
  .kachel.gruen { background: var(--chip-gruen); color: var(--gruen-fg); }
  .kachel.blau { background: var(--chip-blau); color: var(--nav-on); }
  .liste li.modell { border: 1px dashed var(--accent); background: transparent; }
</style>
