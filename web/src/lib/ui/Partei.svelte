<script lang="ts">
  /** Partei-Etikett (Spec §4.11 „Parteien“): dezente Kennzeichnung, keine Wertung. Ohne Angabe nichts. */
  let { name }: { name: string | null } = $props();
  const FARBEN: Record<string, string> = {
    SPD: "#e3000f", CDU: "#1d1d1b", CSU: "#0a6ab6", "CDU/CSU": "#1d1d1b", "Bündnis 90/Die Grünen": "#46962b", GRÜNE: "#46962b", FDP: "#ffed00", "Die Linke": "#be3075", AfD: "#009ee0", BSW: "#7d254f", SSW: "#003c8f",
  };
  const farbe = $derived(name ? FARBEN[name] ?? "var(--muted)" : null);
  const hell = $derived(name === "FDP");
</script>

{#if name}
  <span class="partei" style="background:{farbe};color:{hell ? '#1d2a3a' : '#fff'}">{name}</span>
{/if}

<style>
  .partei { display: inline-block; font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 999px; line-height: 1.5; letter-spacing: .02em; }
</style>
