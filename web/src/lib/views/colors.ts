/** Farben: Steuern blau, Beiträge lila, Kredite rot, Ausgaben je Einzelplan; keine Verdachtsfarben. */
const EPL_PALETTE = [
  "#dc2626", "#f97316", "#eab308", "#84cc16", "#14b8a6", "#06b6d4", "#0ea5e9", "#8b5cf6",
  "#a855f7", "#6366f1", "#ec4899", "#f43f5e", "#22c55e", "#0891b2", "#7c3aed", "#d946ef",
  "#65a30d", "#ca8a04", "#ea580c", "#b91c1c", "#0d9488", "#4f46e5", "#c026d3", "#15803d",
];

const FIXED: Record<string, string> = {
  steuern: "#2563eb",
  sonstige: "#64748b",
  beitraege: "#7c3aed",
  kredit: "#dc2626",
  minder: "#9ca3af",
  topf: "#101828",
  rest: "#94a3b8",
};

const eplIndex = new Map<string, number>();

export function colorFor(key: string): string {
  if (FIXED[key]) return FIXED[key];
  if (!eplIndex.has(key)) {
    const n = Number.parseInt(key, 10);
    eplIndex.set(key, Number.isFinite(n) ? n % EPL_PALETTE.length : eplIndex.size % EPL_PALETTE.length);
  }
  return EPL_PALETTE[eplIndex.get(key)!];
}

export const CHANGED_STROKE = "#facc15";
export const GHOST_STROKE = "#dc2626";
