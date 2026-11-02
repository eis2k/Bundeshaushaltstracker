<script lang="ts">
  /** „Geldquelle (Bund) → Empfänger → Titel“ (Spec §4.11): drei Spalten aus den Haushaltstiteln des Empfängers; ohne Titel die Geber laut
   *  Lobbyregister (gestrichelt, Untergrenzen). Beide Quellen erscheinen nie im selben Bild. */
  import { sankey, sankeyJustify, sankeyLinkHorizontal, type SankeyLink, type SankeyNode } from "d3-sankey";
  import { Landmark } from "lucide-svelte";
  import type { EmpfaengerSeite } from "../model/empfaenger";
  import { fmtEuro } from "../model/format";
  import Avatar from "./Avatar.svelte";

  let { seite, jahr, stand, onEpl, onTitel, height = 260 }: { seite: EmpfaengerSeite; jahr: number; stand: "soll" | "ist"; onEpl: (epl: string) => void; onTitel: (id: string) => void; height?: number } = $props();
  type N = { id: string; label: string; wert: number; art: "quelle" | "mitte" | "titel" | "rest"; quelle: "haushalt" | "lobby" };
  type L = { source: string; target: string; value: number };

  let width = $state(640);
  /** Jahr mit Werten: das gewählte, sonst das letzte mit Werten. */
  const datenJahr = $derived.by(() => {
    const jahre = [...new Set(seite.haushalt.titel.flatMap((t) => Object.keys(t.werte).map(Number)))].sort((a, b) => a - b);
    return jahre.includes(jahr) ? jahr : (jahre.at(-1) ?? null);
  });
  function wertVon(t: EmpfaengerSeite["haushalt"]["titel"][number]): number {
    const w = datenJahr === null ? undefined : t.werte[String(datenJahr)];
    if (!w) return 0;
    return Math.max(0, stand === "ist" ? (w.ist ?? w.soll) : w.soll);
  }
  const modell = $derived.by(() => {
    const nodes: N[] = [];
    const links: L[] = [];
    const titel = seite.haushalt.titel.map((t) => ({ t, wert: wertVon(t) })).filter((x) => x.wert > 0).sort((a, b) => b.wert - a.wert);
    if (titel.length) {
      const jeEpl = new Map<string, { label: string; wert: number }>();
      for (const { t, wert } of titel) { const e = jeEpl.get(t.epl) ?? { label: t.epl_text || `Einzelplan ${t.epl}`, wert: 0 }; e.wert += wert; jeEpl.set(t.epl, e); }
      for (const [epl, e] of [...jeEpl.entries()].sort((a, b) => b[1].wert - a[1].wert)) { nodes.push({ id: `epl:${epl}`, label: e.label, wert: e.wert, art: "quelle", quelle: "haushalt" }); links.push({ source: `epl:${epl}`, target: "mitte", value: e.wert }); }
      const gesamt = titel.reduce((s, x) => s + x.wert, 0);
      nodes.push({ id: "mitte", label: seite.name, wert: gesamt, art: "mitte", quelle: "haushalt" });
      titel.slice(0, 4).forEach(({ t, wert }) => { nodes.push({ id: `titel:${t.id}`, label: t.text, wert, art: "titel", quelle: "haushalt" }); links.push({ source: "mitte", target: `titel:${t.id}`, value: wert }); });
      const rest = titel.slice(4).reduce((s, x) => s + x.wert, 0);
      if (rest > 0) { nodes.push({ id: "rest", label: `Weitere Titel (${titel.length - 4})`, wert: rest, art: "rest", quelle: "haushalt" }); links.push({ source: "mitte", target: "rest", value: rest }); }
      return { nodes, links, quelle: "haushalt" as const, gesamt, jahr: datenJahr };
    }
    const geber = new Map<string, { label: string; wert: number; epl: string | null }>();
    for (const z of seite.lobby_zuwendungen) { const k = z.epl ?? z.geber; const g = geber.get(k) ?? { label: z.geber, wert: 0, epl: z.epl }; g.wert += z.von; geber.set(k, g); }
    const liste = [...geber.entries()].sort((a, b) => b[1].wert - a[1].wert);
    for (const [k, g] of liste) { nodes.push({ id: `geber:${k}`, label: g.label, wert: g.wert, art: "quelle", quelle: "lobby" }); links.push({ source: `geber:${k}`, target: "mitte", value: g.wert }); }
    const gesamt = liste.reduce((s, [, g]) => s + g.wert, 0);
    if (gesamt > 0) nodes.push({ id: "mitte", label: seite.name, wert: gesamt, art: "mitte", quelle: "lobby" });
    return { nodes, links, quelle: "lobby" as const, gesamt, jahr: null };
  });
  const graph = $derived.by(() => {
    if (!modell.nodes.length) return null;
    const gen = sankey<N, L>().nodeId((d) => d.id).nodeWidth(12).nodePadding(12).nodeAlign(sankeyJustify).extent([[8, 24], [Math.max(320, width) - 8, height - 8]]);
    return gen({ nodes: modell.nodes.map((n) => ({ ...n })), links: modell.links.map((l) => ({ ...l })) });
  });
  const pfad = sankeyLinkHorizontal();
  function klick(n: SankeyNode<N, L>) {
    if (n.art === "quelle" && n.id.startsWith("epl:")) onEpl(n.id.slice(4));
    else if (n.art === "titel") onTitel(n.id.slice(6));
  }
  function anteil(n: SankeyNode<N, L>): string { return modell.gesamt > 0 && n.art !== "mitte" ? ` (${(Math.round((n.wert / modell.gesamt) * 1000) / 10).toLocaleString("de-DE")} %)` : ""; }
  function kurz(s: string, max: number): string { return s.length > max ? s.slice(0, max - 1) + "…" : s; }
</script>

<div class="ef" bind:clientWidth={width}>
  {#if graph}
    <div class="kopf"><span>Geldquelle (Bund){modell.quelle === "lobby" ? " · laut Lobbyregister" : ""}</span><span>{modell.quelle === "haushalt" ? `Titel (Verwendung) · ${stand === "ist" ? "Ist" : "Soll"} ${modell.jahr}` : ""}</span></div>
    <svg {width} {height} role="img" aria-label="Geldfluss vom Bund zum Empfänger">
      {#each graph.links as l}
        <path d={pfad(l as SankeyLink<N, L>) ?? ""} fill="none" stroke={modell.quelle === "lobby" ? "var(--muted)" : "var(--nav-on)"} stroke-opacity="0.2" stroke-width={Math.max(1.5, l.width ?? 1)} stroke-dasharray={modell.quelle === "lobby" ? "6 4" : undefined} />
      {/each}
      {#each graph.nodes as n}
        {@const x0 = n.x0 ?? 0}{@const x1 = n.x1 ?? 0}{@const y0 = n.y0 ?? 0}{@const y1 = n.y1 ?? 0}
        <g class="knoten" class:klickbar={n.art === "titel" || (n.art === "quelle" && n.id.startsWith("epl:"))} role="button" tabindex="0" onclick={() => klick(n)} onkeydown={(e) => e.key === "Enter" && klick(n)}>
          <rect x={x0} y={y0} width={x1 - x0} height={Math.max(2, y1 - y0)} rx="4" fill={n.art === "mitte" ? "var(--header)" : n.art === "rest" ? "#9fb3c8" : modell.quelle === "lobby" ? "var(--muted)" : "var(--nav-on)"} />
          {#if n.art === "quelle"}
            <foreignObject x={x1 + 6} y={(y0 + y1) / 2 - 11} width="22" height="22"><span class="kachel"><Landmark size={13} /></span></foreignObject>
            <text x={x1 + 32} y={(y0 + y1) / 2} dy="-0.15em">{kurz(n.label, 34)}<tspan x={x1 + 32} dy="1.2em" class="betrag">{modell.quelle === "lobby" ? "ab " : ""}{fmtEuro(n.wert)}{anteil(n)}</tspan></text>
          {:else if n.art === "mitte"}
            <foreignObject x={(x0 + x1) / 2 - 16} y={y0 - 2 - 36} width="32" height="34"><Avatar name={n.label} art="organisation" size={30} /></foreignObject>
            <text x={(x0 + x1) / 2} y={y1 + 14} text-anchor="middle" class="mitte">{kurz(n.label, 40)}<tspan x={(x0 + x1) / 2} dy="1.2em" class="betrag">{modell.quelle === "lobby" ? "ab " : ""}{fmtEuro(n.wert)}</tspan></text>
          {:else}
            <text x={x0 - 6} y={(y0 + y1) / 2} dy="-0.15em" text-anchor="end">{kurz(n.label, 36)}<tspan x={x0 - 6} dy="1.2em" class="betrag">{fmtEuro(n.wert)}{anteil(n)}</tspan></text>
          {/if}
          <title>{n.label}: {fmtEuro(n.wert)}{modell.quelle === "lobby" ? " (Untergrenze laut Lobbyregister, Eigenangabe)" : ""}</title>
        </g>
      {/each}
    </svg>
    {#if modell.quelle === "lobby"}<p class="hinweis">Kein Haushaltstitel nennt den Empfänger; gezeigt werden die Zuwendungen des Bundes laut Lobbyregister (Eigenangabe, untere Spannengrenze).</p>{/if}
  {:else}
    <p class="hinweis">Weder ein Haushaltstitel noch das Lobbyregister nennt Zahlungen des Bundes an diesen Empfänger.</p>
  {/if}
</div>

<style>
  .ef { width: 100%; }
  .kopf { display: flex; justify-content: space-between; font-size: 12px; font-weight: 700; color: var(--header); margin-bottom: 2px; }
  svg { display: block; width: 100%; overflow: visible; }
  .knoten.klickbar { cursor: pointer; }
  .knoten:focus-visible rect { outline: 2px solid var(--accent); }
  text { font-size: 11px; fill: var(--fg); font-weight: 600; }
  text.mitte { font-weight: 700; }
  .betrag { font-weight: 400; fill: var(--muted); font-size: 10.5px; }
  .kachel { width: 22px; height: 22px; border-radius: 6px; background: var(--chip-blau); color: var(--nav-on); display: inline-flex; align-items: center; justify-content: center; }
  .hinweis { font-size: 11px; color: var(--muted); margin: 6px 0 0; }
</style>
