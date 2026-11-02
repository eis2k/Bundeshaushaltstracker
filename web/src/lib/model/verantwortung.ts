/** Politik & Verantwortung (Spec §4.11): Kabinett des Jahres aus dem Personen-Index, Partei als dezentes Etikett, keine Wertung. */

import type { PersonIndex, PersonIndexEintrag } from "./personen";

export interface Kabinettsmitglied { id: string; name: string; amt: string; epl: string | null; partei: string | null }

/** Rang wie in ministerien(): Kanzler, Minister/Kanzleramtschef, Staatsminister, Parlamentarische Staatssekretäre, Rest. */
function rang(amt: string): number {
  const a = amt.toLowerCase();
  if (a.startsWith("bundeskanzler")) return 0;
  if (a.startsWith("bundesminister") || a.startsWith("chef")) return 1;
  if (a.startsWith("staatsminister")) return 2;
  if (a.startsWith("parlamentarische")) return 3;
  return 4;
}

function imJahr(l: { seit: string | null; bis: string | null }, jahr: number): boolean {
  if (!l.seit) return false;
  const von = Number(l.seit.slice(0, 4));
  const bis = l.bis ? Number(l.bis.slice(0, 4)) : Infinity;
  return jahr >= von && jahr <= bis;
}

/** Partei eines Index-Eintrags: Feld `partei` (Pipeline) oder Fraktion aus „Mitglied des Bundestages[ bis …], <Fraktion>“. */
export function parteiVon(e: Pick<PersonIndexEintrag, "funktion_kurz" | "partei">): string | null {
  if (e.partei) return e.partei;
  const m = /^Mitglied des Bundestages(?: bis [^,]+)?, (.+)$/.exec(e.funktion_kurz ?? "");
  return m ? m[1].trim() : null;
}

/** Kurzform für Etiketten: „Bündnis 90/Die Grünen“ → „Grüne“; Fraktionsnamen sonst unverändert. */
export function parteiKurz(fraktion: string): string {
  const f = fraktion.trim();
  if (/gr[üu]ne/i.test(f)) return "Grüne";
  if (/^die linke$/i.test(f)) return "Linke";
  return f;
}

/** Regierungsmitglieder mit Einzelplan-Leitung im Jahr (wie ministerien()); ohne Datum nur im aktuellen Jahr. Sortiert nach Rang, Einzelplan, Name. */
export function kabinett(personen: PersonIndex | null, jahr: number, aktuellesJahr: number): Kabinettsmitglied[] {
  const out: Kabinettsmitglied[] = [];
  for (const p of personen?.eintraege ?? []) {
    if (!p.sichtbar || !p.arten?.includes("regierung")) continue;
    const leitungen = p.epl_leitung ?? [];
    let passend = leitungen.filter((l) => imJahr(l, jahr));
    if (!passend.length && jahr === aktuellesJahr) passend = leitungen.filter((l) => !l.seit);
    const l = [...passend].sort((a, b) => rang(a.amt) - rang(b.amt))[0];
    if (!l) continue;
    out.push({ id: p.id, name: p.name, amt: l.amt, epl: l.epl || null, partei: parteiVon(p) });
  }
  return out.sort((a, b) => rang(a.amt) - rang(b.amt) || (a.epl ?? "99").localeCompare(b.epl ?? "99") || a.name.localeCompare(b.name, "de"));
}
