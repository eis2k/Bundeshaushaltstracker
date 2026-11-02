/** Personen-Akten (Spec §4.7a): Index, Akte und reine Hilfsfunktionen. */

import { suchNorm, type Quelle } from "./empfaenger";

export interface PersonIndexEintrag {
  id: string;
  name: string;
  funktion_kurz: string;
  amt: boolean;
  sichtbar: boolean;
  n_organisationen: number;
  shard: string;
  /** Funktionsarten der Akte (mdb, regierung, gesetzlicher_vertreter, …); zusammengeführte Akten tragen mehrere. */
  arten: string[];
}

export interface PersonIndex { stand: string; modus: "relevant" | "alle" | string; eintraege: PersonIndexEintrag[] }

export interface Funktion {
  art: "mdb" | "regierung" | "gesetzlicher_vertreter" | "interessenvertreter" | "fruehere_regierungsfunktion" | string;
  text: string;
  organisation_id: string | null;
  organisation: string;
  epl: string | null;
  seit: string | null;
  bis: string | null;
  stand: string;
  quelle: Quelle;
  ausschuesse: string[];
  amt?: string | null;
  aemter?: string[];
  seit_hinweis?: string | null;
  seit_quelle?: string | null;
}

export interface AkteOrganisation {
  id: string; name: string; funktion: string; rolle: string; stand: string;
  lobby_untergrenze_bund?: number; haushalt_soll_letztes_jahr?: number; foerderkatalog_summe?: number; geld_aus?: string[];
}

export interface AkteAngabe { kategorie: string; organisation: string; ort: string; funktion: string; stand: string; quelle: Quelle }
export interface AkteSpende { organisation_id: string; organisation: string; partei: string; betrag: number; eingang: string; veroeffentlicht?: string; drucksache: string; drucksache_url: string | null; quelle: Quelle }
export interface ZeitlinieEintrag { jahr: number; art: "geld" | "posten" | "spende" | string; quelle?: "lobbyregister" | "haushalt" | string; organisation_id: string | null; text: string; wert?: number }

/** Stufe 3d: eine Zeile „Bezüge aus dem Amt“; summe null = Zeitraum nicht belegt. */
export interface BezugZeile { posten: string; komponente: string; rechtsgrundlage: string; monatlich: number | null; zeitraum_von: string | null; zeitraum_bis: string | null; monate: number | null; summe: number | null; empfaenger: "person" | "dritte" | string; quelle: { kurz: string; url: string | null; fundstelle?: string } }
export interface Bezuege { zeilen: BezugZeile[]; summe_person: number; summe_aufwand: number; hinweise: string[]; nicht_bezifferbar: string[]; wp_beginn: string }

export interface Akte {
  id: string;
  name: string;
  sichtbar: boolean;
  grund_sichtbar: "amt" | "verbindung" | "freigabe" | "alle" | null | string;
  gleichnamig: string[];
  quellen_ids: string[];
  amt: boolean;
  verbindung: boolean;
  freigabe: boolean;
  funktionen: Funktion[];
  angaben: AkteAngabe[];
  organisationen: AkteOrganisation[];
  spenden: AkteSpende[];
  zeitlinie: ZeitlinieEintrag[];
  quellen: Quelle[];
  stand: string;
  bezuege?: Bezuege | null;
}

/** Zeilen je Posten in der Reihenfolge des ersten Auftretens. */
export function bezuegeNachPosten(b: Bezuege): { posten: string; zeilen: BezugZeile[] }[] {
  const out: { posten: string; zeilen: BezugZeile[] }[] = [];
  for (const z of b.zeilen) {
    const g = out.find((x) => x.posten === z.posten);
    if (g) g.zeilen.push(z);
    else out.push({ posten: z.posten, zeilen: [z] });
  }
  return out;
}

export type PersonFilter = "alle" | "abgeordnete" | "regierung" | "vertreter";

export const FUNKTION_LABELS: Record<string, string> = {
  mdb: "Mitglied des Bundestages",
  regierung: "Bundesregierung",
  gesetzlicher_vertreter: "Gesetzliche Vertretung",
  interessenvertreter: "Interessenvertretung laut Lobbyregister",
  fruehere_regierungsfunktion: "Frühere öffentliche Funktion",
  regierungsfunktion: "Öffentliche Funktion laut Lobbyregister",
};

/** „bei <Organisation>“ nur, wenn die Organisation nicht schon im Text steht und es kein Mandat oder Regierungsamt ist. */
export function zeigeBei(f: { art: string; text: string; organisation: string }): boolean {
  if (!f.organisation || f.art === "mdb" || f.art === "regierung") return false;
  return !f.text.toLowerCase().includes(f.organisation.toLowerCase());
}

function passtFilter(e: PersonIndexEintrag, f: PersonFilter): boolean {
  const arten = e.arten ?? [];
  if (f === "alle") return true;
  if (f === "abgeordnete") return arten.includes("mdb");
  if (f === "regierung") return arten.includes("regierung");
  return !e.amt;
}

export function filterePersonen(index: PersonIndex, q: string, filter: PersonFilter, nurSichtbar = true): PersonIndexEintrag[] {
  const nq = suchNorm(q);
  const rows = index.eintraege.filter((e) => (!nurSichtbar || e.sichtbar) && passtFilter(e, filter) && (!nq || suchNorm(e.name).includes(nq)));
  return [...rows].sort((a, b) => Number(b.amt) - Number(a.amt) || a.name.localeCompare(b.name, "de"));
}

/** Geld je Jahr getrennt nach Quelle (Lobbyregister-Untergrenzen, Haushalts-Soll) und Spenden; Quellen werden nie addiert (§4.6a). */
export interface ZeitlinieJahr { jahr: number; lobby: number; haushalt: number; spenden: number; posten: string[] }

export function zeitlinieJahre(akte: Akte): ZeitlinieJahr[] {
  const m = new Map<number, ZeitlinieJahr>();
  for (const z of akte.zeitlinie) {
    const j = m.get(z.jahr) ?? { jahr: z.jahr, lobby: 0, haushalt: 0, spenden: 0, posten: [] };
    if (z.art === "geld" && z.quelle === "haushalt") j.haushalt += z.wert ?? 0;
    else if (z.art === "geld") j.lobby += z.wert ?? 0;
    else if (z.art === "spende") j.spenden += z.wert ?? 0;
    else j.posten.push(z.text);
    m.set(z.jahr, j);
  }
  return [...m.values()].sort((a, b) => a.jahr - b.jahr);
}

export function issueUrlAkte(akte: Akte): string {
  const title = `Akte: ${akte.name} – Korrektur oder Beleg`;
  const body = [`Akten-Id: ${akte.id}`, `Name: ${akte.name}`, `Stand der Akte: ${akte.stand}`, "", "Was ist falsch oder fehlt?", "", "Beleg (URL einer amtlichen Quelle, Datum):", ""].join("\n");
  return `https://github.com/eis2k/Bundeshaushaltstracker/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}&labels=${encodeURIComponent("personen,beleg")}`;
}
