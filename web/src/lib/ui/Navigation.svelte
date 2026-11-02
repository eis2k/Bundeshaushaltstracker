<script lang="ts">
  import { Building2, Landmark, LayoutDashboard, Menu, Share2, SlidersHorizontal, TrendingUp, Users, Wallet, Waypoints } from "lucide-svelte";
  import { EINTRAEGE, aktiverEintrag, type NavEintrag } from "../model/navigation";
  import type { AppState } from "../state.svelte";
  import type { IconComp } from "./icons";

  let { app }: { app: AppState } = $props();
  const aktiv = $derived(aktiverEintrag(app.view));
  const ICONS: Record<string, IconComp> = { LayoutDashboard, Wallet, Waypoints, Landmark, Building2, SlidersHorizontal, TrendingUp, Users, Share2 };
  let mehr = $state(false);
  const mobilEintraege = $derived(EINTRAEGE.filter((e) => e.mobil));
  const weitereEintraege = $derived(EINTRAEGE.filter((e) => !e.mobil));
  function waehle(e: NavEintrag) { app.waehle(e); mehr = false; }
</script>

<!-- Desktop: weiße Seitenleiste wie im Dashboard-Entwurf -->
<nav class="seite" aria-label="Hauptnavigation">
  <ul>
    {#each EINTRAEGE as e (e.id)}
      {@const Icon = ICONS[e.icon]}
      <li>
        <button class:on={aktiv === e.id} aria-current={aktiv === e.id ? "page" : undefined} onclick={() => waehle(e)} title={e.untertitel}>
          <Icon size={18} />{e.label}
        </button>
      </li>
    {/each}
  </ul>
  <div class="fuss">
    <a href="https://github.com/eis2k/Bundeshaushaltstracker" target="_blank" rel="noopener">Quellcode und Daten</a>
    <a href="/impressum.html">Impressum</a>
    <a href="/datenschutz.html">Datenschutz</a>
  </div>
</nav>

<!-- Mobil: untere Leiste mit fünf Einträgen und „Mehr“ -->
<nav class="unten" aria-label="Hauptnavigation">
  {#each mobilEintraege as e (e.id)}
    {@const Icon = ICONS[e.icon]}
    <button class:on={aktiv === e.id} aria-current={aktiv === e.id ? "page" : undefined} onclick={() => waehle(e)}><Icon size={18} /><span>{e.kurz}</span></button>
  {/each}
  <button class:on={mehr || weitereEintraege.some((e) => e.id === aktiv)} onclick={() => (mehr = !mehr)} aria-expanded={mehr}><Menu size={18} /><span>Mehr</span></button>
  {#if mehr}
    <div class="mehr">
      {#each weitereEintraege as e (e.id)}
        {@const Icon = ICONS[e.icon]}
        <button class:on={aktiv === e.id} onclick={() => waehle(e)}><Icon size={16} />{e.label}</button>
      {/each}
    </div>
  {/if}
</nav>

<style>
  .seite { background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius); padding: 10px; display: flex; flex-direction: column; gap: 10px; position: sticky; top: 72px; align-self: start; max-height: calc(100vh - 88px); }
  ul { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 4px; }
  .seite button { width: 100%; text-align: left; background: none; color: var(--fg); border: 0; border-radius: 10px; padding: 10px 12px; font-size: 14px; font-weight: 500; cursor: pointer; display: flex; align-items: center; gap: 10px; }
  .seite button:hover { background: var(--nav-bg); }
  .seite button.on { background: var(--nav-on); color: var(--nav-on-fg); font-weight: 600; }
  .fuss { margin-top: auto; padding: 8px 12px 4px; display: flex; flex-direction: column; gap: 3px; font-size: 11px; border-top: 1px solid var(--border); }
  .fuss a { color: var(--muted); text-decoration: none; }
  .fuss a:hover { color: var(--header); text-decoration: underline; }
  .unten { display: none; }
  @media (max-width: 900px) {
    .seite { display: none; }
    .unten { display: grid; grid-template-columns: repeat(6, 1fr); position: fixed; left: 0; right: 0; bottom: 0; background: var(--panel); border-top: 1px solid var(--border); padding: 6px 4px calc(6px + env(safe-area-inset-bottom)); z-index: 20; }
    .unten > button { background: none; border: 0; border-radius: 10px; color: var(--header); font-size: 10px; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 2px; cursor: pointer; }
    .unten > button.on { background: var(--nav-on); color: var(--nav-on-fg); }
    .mehr { position: absolute; left: 8px; right: 8px; bottom: calc(100% + 6px); background: var(--panel); border: 1px solid var(--border); border-radius: var(--radius-s); padding: 6px; display: flex; flex-direction: column; gap: 2px; box-shadow: 0 -8px 24px rgba(23, 60, 102, .12); }
    .mehr button { background: none; border: 0; border-radius: 8px; padding: 9px 10px; text-align: left; font: inherit; font-size: 13px; color: var(--fg); display: flex; align-items: center; gap: 8px; cursor: pointer; }
    .mehr button.on { background: var(--chip-blau); color: var(--header); }
  }
</style>
