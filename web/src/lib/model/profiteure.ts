/** Geldflüsse & Profiteure (Spec §4.11): größte Empfänger eines Einzelplans je Quelle und die Karte „Politische Verantwortung“. Beträge werden nie über Quellen addiert. */

import type { EmpfaengerIndex } from "./empfaenger";
import { ministerien, type Leitung } from "./ministerien";
import type { PersonIndex } from "./personen";
import type { YearData } from "./types";

export type EmpfaengerQuelle = "haushalt" | "lobbyregister";

export interface TopEmpfaenger { id: string; name: string; wert: number; quelle: EmpfaengerQuelle }

/** Empfänger mit Seite, die dem Einzelplan zugeordnet sind (null = alle): Haushalts-Soll des letzten Jahres vor Lobbyregister-Untergrenze, je Quelle absteigend. */
export function topEmpfaenger(epl: string | null, _jahr: number, index: EmpfaengerIndex | null, max = 6): TopEmpfaenger[] {
  const alle = (index?.eintraege ?? []).filter((e) => epl === null || (e.epls ?? []).includes(epl));
  const haushalt = alle.filter((e) => e.haushalt_soll_letztes_jahr > 0).map((e) => ({ id: e.id, name: e.name, wert: e.haushalt_soll_letztes_jahr, quelle: "haushalt" as const }));
  const lobby = alle.filter((e) => e.haushalt_soll_letztes_jahr <= 0 && e.lobby_untergrenze_bund > 0).map((e) => ({ id: e.id, name: e.name, wert: e.lobby_untergrenze_bund, quelle: "lobbyregister" as const }));
  haushalt.sort((a, b) => b.wert - a.wert);
  lobby.sort((a, b) => b.wert - a.wert);
  return [...haushalt, ...lobby].slice(0, max);
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
