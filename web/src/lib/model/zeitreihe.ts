import type { NodeId } from "./types";

export interface Series {
  text: string;
  epl?: string;
  kap?: string;
  art: "E" | "A";
  sv?: boolean;
  soll: (number | null)[];
  ist: (number | null)[];
}

export interface Zeitreihe {
  jahre: number[];
  titel: Record<NodeId, Series>;
  kap: Record<NodeId, Series>;
  epl: Record<NodeId, Series>;
}

export type Vpi = Record<number, number>;
export type Ebene = "epl" | "kap" | "titel";
export type GrowthFilter = "alle" | "zuwendungen" | "personal" | "geschrumpft" | "neu";

export interface GrowthOpts {
  von: number;
  bis: number;
  ebene: Ebene;
  stand: "soll" | "ist";
  sort: "pct" | "abs";
  filter: GrowthFilter;
  real: boolean;
  vpi?: Vpi;
  includeSv?: boolean;
  /** Mindestbetrag in Euro: Zeilen, deren Start- und Endwert beide darunter liegen, entfallen. */
  min?: number;
}

export interface GrowthRow {
  id: NodeId;
  text: string;
  epl?: string;
  von: number;
  bis: number;
  abs: number;
  /** Zuwachs in Anteilen (0,25 = +25 %); null, wenn der Startwert 0 oder unbekannt ist. */
  pct: number | null;
  neu: boolean;
  verlauf: (number | null)[];
  hinweis?: string;
}

/** Rechnet einen Betrag aus dem Jahr `from` in Preise des Jahres `to` um. */
export function deflate(value: number, from: number, to: number, vpi: Vpi): number {
  const a = vpi[from], b = vpi[to];
  if (!a || !b) return value;
  return (value * b) / a;
}

function isZuwendung(titel: string): boolean {
  const g = Number.parseInt(titel.slice(0, 2), 10);
  return (g >= 63 && g <= 69) || g === 88 || g === 89;
}

export function rankGrowth(z: Zeitreihe, opts: GrowthOpts): GrowthRow[] {
  const iVon = z.jahre.indexOf(opts.von);
  const iBis = z.jahre.indexOf(opts.bis);
  if (iVon < 0 || iBis < 0) return [];
  const source = opts.ebene === "titel" ? z.titel : opts.ebene === "kap" ? z.kap : z.epl;
  const rows: GrowthRow[] = [];
  for (const [id, s] of Object.entries(source)) {
    if (s.art !== "A") continue;
    if (s.sv && !opts.includeSv) continue;
    const titel = opts.ebene === "titel" ? id.split("-")[2] : "";
    if (opts.ebene === "titel") {
      if (opts.filter === "zuwendungen" && !isZuwendung(titel)) continue;
      if (opts.filter === "personal" && titel[0] !== "4") continue;
    } else if (opts.filter === "zuwendungen" || opts.filter === "personal") {
      continue;
    }
    const series = opts.stand === "ist" ? s.ist : s.soll;
    const scaled = series.map((v, i) => (v === null ? null : opts.real && opts.vpi ? deflate(v, z.jahre[i], opts.bis, opts.vpi) : v));
    const vonRaw = scaled[iVon];
    const bisRaw = scaled[iBis];
    if (vonRaw === null && bisRaw === null) continue;
    const von = vonRaw ?? 0;
    const bis = bisRaw ?? 0;
    if (von === 0 && bis === 0) continue;
    const neu = von <= 0 && bis > 0;
    // Mindestbetrag: Endwert immer, Startwert nur wenn vorhanden (sonst "neu"-Zeilen verschwinden)
    if (opts.min && (Math.abs(bis) < opts.min || (!neu && Math.abs(von) < opts.min))) continue;
    const pct = von > 0 ? (bis - von) / von : null;
    const abs = bis - von;
    if (opts.filter === "geschrumpft" && !(abs < 0)) continue;
    if (opts.filter === "neu" && !neu) continue;
    rows.push({ id, text: s.text, epl: s.epl ?? (opts.ebene === "epl" ? id : undefined), von, bis, abs, pct, neu, verlauf: scaled.slice(Math.min(iVon, iBis), Math.max(iVon, iBis) + 1) });
  }
  if (opts.sort === "abs") rows.sort((a, b) => b.abs - a.abs);
  else rows.sort((a, b) => {
    // Prozent sortierbar zuerst; "neu" (kein Startwert) dahinter, nach Betrag
    if (a.neu !== b.neu) return a.neu ? 1 : -1;
    if (a.neu && b.neu) return b.abs - a.abs;
    return (b.pct ?? -Infinity) - (a.pct ?? -Infinity);
  });
  return rows;
}
