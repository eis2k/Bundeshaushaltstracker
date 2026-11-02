/** Geldflüsse & Profiteure (Spec §4.11): größte Empfänger eines Einzelplans je Quelle und die Karte „Politische Verantwortung“. Beträge werden nie über Quellen addiert. */

import type { EmpfaengerIndex } from "./empfaenger";
import { ministerien, type Leitung } from "./ministerien";
import type { PersonIndex } from "./personen";
import type { YearData } from "./types";

export type EmpfaengerQuelle = "haushalt" | "lobbyregister";

export interface TopEmpfaenger { id: string; name: string; wert: number; quelle: EmpfaengerQuelle }

/** Beträge eines Empfängers aus genau diesem Einzelplan (null = alle Einzelpläne), je Quelle getrennt; Förderkatalog-Ressorts sind keine Geldquelle. */
function betraege(e: EmpfaengerIndex["eintraege"][number], epl: string | null): { haushalt: number; lobby: number } {
  const summe = (m: Record<string, number> | undefined) => m ? Object.values(m).reduce((s, x) => s + x, 0) : 0;
  if (epl === null) return { haushalt: e.haushalt_je_epl ? summe(e.haushalt_je_epl) : e.haushalt_soll_letztes_jahr, lobby: e.lobby_je_epl ? summe(e.lobby_je_epl) : e.lobby_untergrenze_bund };
  return { haushalt: e.haushalt_je_epl?.[epl] ?? 0, lobby: e.lobby_je_epl?.[epl] ?? 0 };
}

/** Größte Empfänger mit Seite aus dem Einzelplan (null = alle): Haushalts-Soll des letzten Jahres aus Titeln des Einzelplans vor
 *  Lobbyregister-Untergrenze der Geber des Einzelplans, je Quelle absteigend, nie addiert (Review C2). `_jahr` bleibt für die Beschriftung des Aufrufers. */
export function topEmpfaenger(epl: string | null, _jahr: number, index: EmpfaengerIndex | null, max = 6): TopEmpfaenger[] {
  const haushalt: TopEmpfaenger[] = [];
  const lobby: TopEmpfaenger[] = [];
  for (const e of index?.eintraege ?? []) {
    const b = betraege(e, epl);
    if (b.haushalt > 0) haushalt.push({ id: e.id, name: e.name, wert: b.haushalt, quelle: "haushalt" });
    else if (b.lobby > 0) lobby.push({ id: e.id, name: e.name, wert: b.lobby, quelle: "lobbyregister" });
  }
  haushalt.sort((a, b) => b.wert - a.wert);
  lobby.sort((a, b) => b.wert - a.wert);
  return [...haushalt, ...lobby].slice(0, max);
}

/** Zahl aller Empfänger mit Betrag aus dem Einzelplan, für den Hinweis „weitere Empfänger“. */
export function anzahlEmpfaenger(epl: string | null, index: EmpfaengerIndex | null): number {
  return (index?.eintraege ?? []).filter((e) => { const b = betraege(e, epl); return b.haushalt > 0 || b.lobby > 0; }).length;
}

export interface Verantwortung { epl: string; name: string; haushalt: number; anteil: number; leitung: Leitung[]; hinweis: string | null }

/** Karte „Politische Verantwortung“: Leitung des Einzelplans im Jahr (über ministerien()), Haushalt und Anteil an den Ausgaben; ohne Einzelplan der größte. */
export function verantwortung(epl: string | null, jahr: number, aktuellesJahr: number, data: YearData, includeSv: boolean, personen: PersonIndex | null): Verantwortung | null {
  const alle = ministerien(data, "soll", includeSv, jahr, aktuellesJahr, personen, null);
  const gesamt = alle.reduce((s, m) => s + m.ausgaben, 0);
  const m = epl === null ? alle.find((x) => x.epl !== "60" && x.epl !== "32") ?? alle[0] : alle.find((x) => x.epl === epl);
  if (!m) return null;
  return { epl: m.epl, name: m.name, haushalt: m.ausgaben, anteil: gesamt ? Math.round((m.ausgaben / gesamt) * 1000) / 10 : 0, leitung: m.leitung, hinweis: m.leitungHinweis };
}
