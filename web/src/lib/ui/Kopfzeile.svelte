<script lang="ts">
  import { Landmark, Monitor, Moon, Sun } from "lucide-svelte";
  import { THEME_LABEL, naechstes } from "../model/theme";
  import type { AppState } from "../state.svelte";
  import Suche from "./Suche.svelte";

  let { app }: { app: AppState } = $props();

  let copied = $state(false);
  async function share() {
    const url = `${location.origin}${location.pathname}#${app.toHash()}`;
    try {
      await navigator.clipboard.writeText(url);
      copied = true;
      setTimeout(() => (copied = false), 2000);
    } catch {
      prompt("Link zum Kopieren:", url);
    }
  }
  const jahre = $derived(app.index?.jahre ?? []);
  const istBis = $derived(app.index?.ist_bis ?? 0);
  const modell = $derived(Object.keys(app.scenario.factors).length > 0 || app.scenario.presets.length > 0 || Object.keys(app.scenario.steuern ?? {}).length > 0);
</script>

<header class="top">
  <button class="marke" onclick={() => app.waehle({ id: "dashboard", label: "Dashboard", kurz: "Start", titel: "Dashboard", untertitel: "", view: "dashboard", icon: "LayoutDashboard" })} title="Zum Dashboard">
    <span class="adler"><Landmark size={22} /></span>
    <span class="wort"><b>Bundeshaushalts<span>tracker</span></b><small>Transparenz. Zahlen. Politik.</small></span>
  </button>
  <div class="rechts">
    <label class="jahr">
      <span class="sr-only">Haushaltsjahr</span>
      <select value={app.jahr} onchange={(e) => void app.setJahr(Number((e.target as HTMLSelectElement).value))}>
        {#each jahre as j}<option value={j}>{j}{j > istBis ? " (Entwurf)" : ""}</option>{/each}
      </select>
    </label>
    <Suche {app} />
    {#if modell}
      <button class="ghost" onclick={() => app.reset()} title="Alle Regler und Presets zurück auf Original">Zurücksetzen</button>
    {/if}
    <button class="ghost icon" onclick={() => app.setTheme(naechstes(app.theme))} title={`Darstellung: ${THEME_LABEL[app.theme]} (klicken zum Wechseln)`} aria-label={`Darstellung: ${THEME_LABEL[app.theme]}, wechseln`}>
      {#if app.theme === "hell"}<Sun size={16} />{:else if app.theme === "dunkel"}<Moon size={16} />{:else}<Monitor size={16} />{/if}
    </button>
    <button class="share" onclick={share}>{copied ? "Link kopiert" : "Teilen"}</button>
  </div>
</header>

<style>
  .top { display: flex; align-items: center; gap: 16px; padding: 10px 20px; background: var(--panel); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 25; }
  .marke { display: flex; align-items: center; gap: 10px; background: none; border: 0; padding: 0; cursor: pointer; text-align: left; color: var(--header); }
  .adler { width: 40px; height: 40px; border-radius: 12px; background: var(--nav-bg); display: inline-flex; align-items: center; justify-content: center; color: var(--header); }
  .wort { display: flex; flex-direction: column; line-height: 1.1; }
  .wort b { font-size: 17px; letter-spacing: -0.3px; }
  .wort b span { color: var(--accent); }
  .wort small { font-size: 11px; color: var(--muted); }
  .rechts { margin-left: auto; display: flex; align-items: center; gap: 10px; flex: 1; justify-content: flex-end; }
  .jahr select { font: inherit; font-size: 13px; padding: 8px 10px; border: 1px solid var(--border); border-radius: 10px; background: var(--panel); color: var(--header); font-weight: 600; }
  .share { background: var(--nav-on); color: var(--nav-on-fg); font-weight: 700; border: 0; border-radius: 10px; padding: 9px 14px; cursor: pointer; font-size: 13px; white-space: nowrap; }
  .ghost { background: var(--panel); border: 1px solid var(--border); color: var(--header); border-radius: 10px; padding: 8px 12px; cursor: pointer; font-size: 13px; white-space: nowrap; }
  .ghost.icon { padding: 8px; display: inline-flex; align-items: center; }
  .sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  @media (max-width: 900px) {
    .top { flex-wrap: wrap; gap: 8px; padding: 10px 12px; }
    .rechts { width: 100%; flex-wrap: wrap; }
    .wort small { display: none; }
  }
</style>
