<script lang="ts">
  import { EINTRAEGE, aktiverEintrag } from "../model/navigation";
  import type { AppState } from "../state.svelte";

  let { app }: { app: AppState } = $props();
  const aktiv = $derived(aktiverEintrag(app.view, app.gestalten));
</script>

<!-- Desktop: Seitenleiste wie im Mockup -->
<nav class="seite" aria-label="Hauptnavigation">
  <div class="marke">
    <div class="wort">Bundeshaushalts<span>tracker</span></div>
    <div class="unter">Transparenz · Zahlen · Belege</div>
  </div>
  <ul>
    {#each EINTRAEGE as e (e.id)}
      <li>
        <button class:on={aktiv === e.id} aria-current={aktiv === e.id ? "page" : undefined} onclick={() => app.waehle(e)} title={e.untertitel}>
          <span class="symbol" aria-hidden="true">{e.symbol}</span>{e.label}
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

<!-- Mobil: untere Leiste mit denselben sechs Einträgen -->
<nav class="unten" aria-label="Hauptnavigation">
  {#each EINTRAEGE as e (e.id)}
    <button class:on={aktiv === e.id} aria-current={aktiv === e.id ? "page" : undefined} onclick={() => app.waehle(e)}>
      <span class="symbol" aria-hidden="true">{e.symbol}</span><span class="kurz">{e.kurz}</span>
    </button>
  {/each}
</nav>

<style>
  .seite { background: var(--nav-bg); padding: 22px 15px; display: flex; flex-direction: column; gap: 14px; min-height: 100vh; position: sticky; top: 0; align-self: start; }
  .marke .wort { font-size: 21px; font-weight: 800; color: var(--header); letter-spacing: -0.3px; line-height: 1.1; }
  .marke .wort span { color: var(--accent); }
  .marke .unter { font-size: 13px; color: var(--muted); margin-top: 4px; }
  ul { list-style: none; margin: 8px 0 0; padding: 0; display: flex; flex-direction: column; gap: 10px; }
  .seite button { width: 100%; text-align: left; background: var(--nav-item); color: var(--header); border: 0; border-radius: var(--radius-s); padding: 13px 14px; font-size: 15px; font-weight: 600; cursor: pointer; display: flex; align-items: center; gap: 10px; }
  .seite button:hover { background: var(--chip-blau); }
  .seite button.on { background: var(--nav-on); color: var(--nav-on-fg); }
  .symbol { width: 18px; display: inline-block; text-align: center; opacity: .85; }
  .fuss { margin-top: auto; display: flex; flex-direction: column; gap: 4px; font-size: 12px; }
  .fuss a { color: var(--muted); text-decoration: none; }
  .fuss a:hover { color: var(--header); text-decoration: underline; }
  .unten { display: none; }
  @media (max-width: 900px) {
    .seite { display: none; }
    .unten { display: grid; grid-template-columns: repeat(6, 1fr); position: fixed; left: 0; right: 0; bottom: 0; background: var(--nav-bg); border-top: 1px solid var(--border); padding: 6px 4px calc(6px + env(safe-area-inset-bottom)); z-index: 20; }
    .unten button { background: none; border: 0; border-radius: 10px; color: var(--header); font-size: 10px; display: flex; flex-direction: column; align-items: center; gap: 2px; padding: 6px 2px; cursor: pointer; }
    .unten button .symbol { font-size: 16px; width: auto; }
    .unten button.on { background: var(--nav-on); color: var(--nav-on-fg); }
  }
</style>
