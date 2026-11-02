<script lang="ts">
  import type { IconComp } from "./icons";
  /** Kennzahlenkarte mit farbiger Symbolkachel wie in den Entwürfen. */
  let { label, wert, neben = "", ton = "blau", icon: Icon, nebenTon = "" }: { label: string; wert: string; neben?: string; ton?: "blau" | "gruen" | "orange" | "rot" | "violett"; icon: IconComp; nebenTon?: "" | "gut" | "schlecht" } = $props();
</script>

<div class="kennzahl">
  <span class="kachel {ton}"><Icon size={20} /></span>
  <div class="text">
    <small>{label}</small>
    <b class="tabular">{wert}</b>
    {#if neben}<span class="neben" class:gut={nebenTon === "gut"} class:schlecht={nebenTon === "schlecht"}>{neben}</span>{/if}
  </div>
</div>

<style>
  .kennzahl { display: flex; align-items: center; gap: 12px; background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 12px 14px; min-width: 0; }
  .kachel { width: 42px; height: 42px; border-radius: 12px; display: inline-flex; align-items: center; justify-content: center; color: var(--header); flex: none; }
  .kachel.blau { background: var(--chip-blau); color: var(--nav-on); }
  .kachel.gruen { background: var(--chip-gruen); color: var(--gruen-fg); }
  .kachel.orange { background: var(--chip-orange); color: var(--orange-fg); }
  .kachel.rot { background: var(--bad-bg); color: var(--bad); }
  .kachel.violett { background: var(--violett-bg); color: var(--violett-fg); }
  .text { display: flex; flex-direction: column; line-height: 1.15; min-width: 0; }
  .text small { font-size: 11px; color: var(--muted); }
  .text b { font-size: 17px; color: var(--header); }
  .neben { font-size: 11px; color: var(--muted); }
  .neben.gut { color: var(--good); }
  .neben.schlecht { color: var(--bad); }
</style>
