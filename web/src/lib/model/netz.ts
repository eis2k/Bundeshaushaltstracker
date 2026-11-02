/** Netz (Spec §4.7a): vorberechnetes Umfeld je Knoten, Darstellungsregeln. */

import type { Quelle } from "./empfaenger";

export type KnotenArt = "person" | "organisation" | "ministerium" | "partei";
export type KantenArt = "geld" | "posten" | "spende";

export interface NetzKnoten { id: string; art: KnotenArt | string; label: string; sichtbar: boolean; seite: string | null }
export interface NetzKante { von: string; nach: string; art: KantenArt | string; text: string; wert: number | null; quelle: Quelle; stand: string }
export interface Umfeld { start: string; knoten: NetzKnoten[]; kanten: NetzKante[]; weitere: number }

/** Pfad der Shard-Datei eines Knotens laut Netz-Index (knoten_id → shard), null wenn der Knoten keine Kanten hat. */
export function netzPfad(knotenId: string, index: Record<string, string>): string | null {
  const sh = index[knotenId];
  return sh ? `netz/${sh}.json` : null;
}

/** Drei Kantenarten, eine Farbe: Geld durchgezogen, Posten gestrichelt, Spende gepunktet. */
export function kantenStil(art: KantenArt | string): { dasharray: string; width: number } {
  if (art === "geld") return { dasharray: "", width: 2 };
  if (art === "posten") return { dasharray: "6 4", width: 1.5 };
  return { dasharray: "2 3", width: 1.5 };
}

export function legende(): { art: KantenArt; label: string }[] {
  return [
    { art: "geld", label: "Geld (Ministerium → Organisation)" },
    { art: "posten", label: "Posten (Person – Organisation oder Ministerium)" },
    { art: "spende", label: "Spende (Organisation → Partei)" },
  ];
}

export const KNOTEN_LABELS: Record<string, string> = { person: "Person", organisation: "Organisation", ministerium: "Ministerium", partei: "Partei" };

/** Knoten-Id für den Start eines Umfelds. */
export const knotenId = {
  person: (id: string) => `p:${id}`,
  empfaenger: (id: string) => `e:${id}`,
  ministerium: (epl: string) => `m:${epl}`,
};
