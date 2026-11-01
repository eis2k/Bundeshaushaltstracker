import { balance, effectiveValue } from "./scenario";
import type { NodeId, YearData } from "./types";

export interface Posten { id: string; text: string; betrag: number }

export interface TopfData {
  name: string;
  kurz: string;
  farbe: string;
  geschaetzt: boolean;
  quelle: string | null;
  hinweis?: string | null;
  bundesmittel: { titel: NodeId; text: string }[];
  einnahmen: Posten[];
  ausgaben: Posten[];
}

export interface SozialkassenYear {
  jahr: number;
  toepfe: Record<string, TopfData>;
  querfluesse: { von: string; nach: string; id: string; text: string; quelle?: string | null }[];
}

export interface Topf {
  id: string;
  name: string;
  kurz: string;
  geschaetzt: boolean;
  quelle: string | null;
  hinweis?: string | null;
  einnahmen: number;
  einnahmenOriginal: number;
  ausgaben: number;
  /** Summe der verknüpften Bund-Titel nach Faktor (Euro). */
  bundesmittel: number;
  bundesmittelOriginal: number;
  saldo: number;
  saldoOriginal: number;
  einnahmenListe: Posten[];
  ausgabenListe: Posten[];
}

export interface ToepfeResult {
  toepfe: Topf[];
  bundAusgaben: number;
  /** Bund + alle Töpfe, Bundesmittel und Querflüsse nur einmal gezählt. */
  gesamtAusgaben: number;
  /** Beiträge aller Sozialkassen (ohne Bundesmittel). */
  beitraege: number;
  querfluesse: { von: string; nach: string; id: string; text: string; betrag: number }[];
}

export function buildToepfe(bund: YearData, sk: SozialkassenYear, factors: Record<NodeId, number>, includeSv: boolean): ToepfeResult {
  const rowById = new Map(bund.rows.map((r) => [r.id, r]));
  const toepfe: Topf[] = [];
  let beitraege = 0, bundesmittelSum = 0, toepfeAusgaben = 0;
  for (const [id, t] of Object.entries(sk.toepfe)) {
    let bmOriginal = 0, bm = 0;
    for (const b of t.bundesmittel) {
      const row = rowById.get(b.titel);
      if (!row) continue;
      bmOriginal += row.soll;
      bm += effectiveValue(row, factors);
    }
    const einnahmenOriginal = t.einnahmen.reduce((s, e) => s + e.betrag, 0);
    const einnahmen = einnahmenOriginal - bmOriginal + bm;
    const ausgaben = t.ausgaben.reduce((s, e) => s + e.betrag, 0);
    beitraege += t.einnahmen.filter((e) => e.id === "beitraege").reduce((s, e) => s + e.betrag, 0);
    bundesmittelSum += bm;
    toepfeAusgaben += ausgaben;
    toepfe.push({
      id, name: t.name, kurz: t.kurz, geschaetzt: t.geschaetzt, quelle: t.quelle, hinweis: t.hinweis,
      einnahmen, einnahmenOriginal, ausgaben, bundesmittel: bm, bundesmittelOriginal: bmOriginal,
      saldo: einnahmen - ausgaben, saldoOriginal: einnahmenOriginal - ausgaben,
      einnahmenListe: t.einnahmen, ausgabenListe: t.ausgaben,
    });
  }
  const querfluesse = sk.querfluesse.map((q) => {
    const von = sk.toepfe[q.von];
    const betrag = von?.ausgaben.find((a) => a.id === q.id)?.betrag ?? 0;
    return { von: q.von, nach: q.nach, id: q.id, text: q.text, betrag };
  });
  const bundAusgaben = balance(bund, factors, includeSv).ausgaben;
  const gesamtAusgaben = bundAusgaben + toepfeAusgaben - bundesmittelSum - querfluesse.reduce((s, q) => s + q.betrag, 0);
  return { toepfe, bundAusgaben, gesamtAusgaben, beitraege, querfluesse };
}
