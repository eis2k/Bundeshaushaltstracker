<script lang="ts">
  /** Platzhalter für Porträts und Logos (Spec §4.11): Initialen im Kreis bzw. Kürzel in der Kachel, bis Stufe 4b lizenzierte Bilder liefert. */
  let { name, art = "person", size = 36 }: { name: string; art?: "person" | "organisation"; size?: number } = $props();

  const TOENE = ["var(--chip-blau)", "var(--chip-gruen)", "var(--chip-orange)", "var(--nav-bg)"];
  const kuerzel = $derived.by(() => {
    const woerter = name.replace(/\(.*?\)/g, "").split(/[\s-]+/).filter((w) => w && !w.endsWith(".") && !/^(e\.V\.|GmbH|AG|gGmbH|mbH|KG|SE|und|der|die|das|für|von|zu|&)$/i.test(w));
    if (art === "person") return woerter.slice(0, 2).map((w) => w[0]).join("").toUpperCase() || "?";
    const grossbuchstaben = name.replace(/[^A-ZÄÖÜ]/g, "");
    if (grossbuchstaben.length >= 2 && grossbuchstaben.length <= 4 && name.length <= 8) return grossbuchstaben;
    return woerter.slice(0, 3).map((w) => w[0]).join("").toUpperCase() || "?";
  });
  const ton = $derived(TOENE[[...name].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7) % TOENE.length]);
</script>

<span class="avatar" class:org={art === "organisation"} style="width:{size}px;height:{size}px;font-size:{Math.max(9, Math.round(size * 0.34))}px;background:{ton}" aria-hidden="true" title={name}>{kuerzel}</span>

<style>
  .avatar { display: inline-flex; align-items: center; justify-content: center; border-radius: 50%; color: var(--header); font-weight: 700; letter-spacing: .02em; flex: none; border: 1px solid var(--border); }
  .avatar.org { border-radius: 8px; }
</style>
