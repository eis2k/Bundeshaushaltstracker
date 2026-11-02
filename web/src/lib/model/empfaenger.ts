/** Empfänger von Bundesmitteln (Spec §4.6a): Index, Seite und reine Hilfsfunktionen für Liste und Seite. */

import { fmtEuro } from "./format";

export type EmpfaengerArt = "unternehmen" | "verein_stiftung" | "forschung" | "oeffentlich" | "kirche_wohlfahrt" | "sonstige";

export const EMPFAENGER_ART_LABELS: Record<EmpfaengerArt, string> = {
  unternehmen: "Unternehmen",
  verein_stiftung: "Vereine und Stiftungen",
  forschung: "Forschung",
  oeffentlich: "Öffentliche Einrichtungen",
  kirche_wohlfahrt: "Kirche und Wohlfahrt",
  sonstige: "Sonstige",
};

export interface EmpfaengerIndexEintrag {
  id: string;
  name: string;
  art: EmpfaengerArt;
  rechtsform: string;
  sitz: string;
  lobby_untergrenze_bund: number;
  haushalt_soll_letztes_jahr: number;
  foerderkatalog_summe: number;
  n_personen: number;
  n_verbindungen: number;
  lobbyregister: string | null;
  epls: string[];
}

export interface EmpfaengerIndex {
  stand: string;
  mit_personen: boolean;
  eintraege: EmpfaengerIndexEintrag[];
  /** Titel-Id → Empfänger, für Fluss und Panel. */
  titel: Record<string, { id: string; name: string }>;
}

export interface Quelle { kurz: string; url: string | null; abgerufen?: string; stand?: string; etikett?: string; version?: number }

export interface TitelEintrag { id: string; text: string; epl: string; epl_text: string; werte: Record<string, { soll: number; ist: number | null }> }
export interface LobbyZuwendung { geber: string; epl: string | null; von: number; bis: number; zweck: string; geschaeftsjahr: string }
export interface FoerderProjekt { fkz: string; ressort: string; epl: string | null; thema: string; von: string; bis: string; summe: number; foerderart: string }
export interface Regierungsfunktion { art: string; funktion: string; stelle: string; beendet: boolean; ende: string | null }
export interface PersonEintrag { name: string; funktion: string; rolle: "gesetzlicher_vertreter" | "interessenvertreter"; regierungsfunktion: Regierungsfunktion | null; quelle: Quelle; akte_id?: string | null; akte_sichtbar?: boolean }
export interface Verbindung {
  typ: "abgeordneter_funktion" | "regierungsfunktion" | "manuell" | string;
  person: string;
  funktion_person: string;
  funktion_beim_empfaenger: string;
  kategorie: string;
  abgleich: "exakt" | "geprueft" | "eigenangabe" | string;
  satz: string;
  ausschuesse: string[];
  geld_aus: string[];
  quellen: Quelle[];
  stand: string;
}
export interface Jahresabschluss {
  url: string | null;
  geschaeftsjahr: string;
  kennzahlen: Record<string, number | null> | null;
  seite: number | null;
  pruefer: string | null;
  hinweis: string | null;
  erfasst: string | null;
}
export interface Pflichtangaben {
  finanzierungsquellen: string[];
  spenden: { von: number; bis: number } | null;
  mitgliedsbeitraege: { von: number; bis: number } | null;
  lobbyausgaben: { von: number; bis: number } | null;
  geschaeftsjahr: string | null;
  jahresabschluss: Jahresabschluss | null;
}

export interface EmpfaengerSeite {
  id: string;
  name: string;
  art: EmpfaengerArt;
  rechtsform: string;
  sitz: string;
  website: string | null;
  stand: string;
  geprueft: boolean;
  lobbyregister: { nummer: string; eintrag_id: number; version: number; stand: string; url: string; pdf_url: string | null } | null;
  haushalt: { titel: TitelEintrag[] };
  lobby_zuwendungen: LobbyZuwendung[];
  lobby_untergrenze_bund: number;
  foerderkatalog: FoerderProjekt[];
  /** Der CSV-Export des Förderkatalogs liefert höchstens 100 Projekte. */
  foerderkatalog_auszug?: boolean;
  personen: PersonEintrag[];
  verbindungen: Verbindung[];
  pflichtangaben: Pflichtangaben | null;
  quellen: Quelle[];
}

export type EmpfaengerSort = "bund" | "haushalt" | "name" | "verbindungen";

const UMLAUTE: Record<string, string> = { ä: "ae", ö: "oe", ü: "ue", ß: "ss" };

/** Suchnormalisierung: klein, Umlaute aufgelöst, nur Buchstaben und Ziffern. */
export function suchNorm(s: string): string {
  return s.toLowerCase().replace(/[äöüß]/g, (c) => UMLAUTE[c] ?? c).replace(/[^a-z0-9]+/g, " ").trim();
}

export function filtereEmpfaenger(index: EmpfaengerIndex, q: string, art: EmpfaengerArt | "alle", sort: EmpfaengerSort, epl?: string | null): EmpfaengerIndexEintrag[] {
  const nq = suchNorm(q);
  let rows = index.eintraege.filter((e) =>
    (art === "alle" || e.art === art) &&
    (!epl || e.epls.includes(epl)) &&
    (!nq || suchNorm(e.name).includes(nq)));
  const byBund = (a: EmpfaengerIndexEintrag, b: EmpfaengerIndexEintrag) =>
    b.lobby_untergrenze_bund - a.lobby_untergrenze_bund || b.haushalt_soll_letztes_jahr - a.haushalt_soll_letztes_jahr || a.name.localeCompare(b.name, "de");
  rows = [...rows];
  if (sort === "bund") rows.sort(byBund);
  else if (sort === "haushalt") rows.sort((a, b) => b.haushalt_soll_letztes_jahr - a.haushalt_soll_letztes_jahr || byBund(a, b));
  else if (sort === "verbindungen") rows.sort((a, b) => b.n_verbindungen - a.n_verbindungen || byBund(a, b));
  else rows.sort((a, b) => a.name.localeCompare(b.name, "de"));
  return rows;
}

const de1 = new Intl.NumberFormat("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const de2 = new Intl.NumberFormat("de-DE", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const deInt = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 });

/** Betragsspanne aus dem Lobbyregister: "1,04–1,05 Mio €", "580.001–590.000 €"; gleiche Grenzen → fmtEuro. */
export function fmtSpanne(von: number, bis: number): string {
  if (von === bis) return fmtEuro(von);
  const max = Math.max(Math.abs(von), Math.abs(bis));
  if (max >= 1e9) return `${de1.format(von / 1e9)}–${de1.format(bis / 1e9)} Mrd €`;
  if (max >= 1e6) return `${de2.format(von / 1e6)}–${de2.format(bis / 1e6)} Mio €`;
  return `${deInt.format(von)}–${deInt.format(bis)} €`;
}

/** Geldgeber des Bundes laut Lobbyregister, jeder einmal, nach Untergrenze absteigend. */
export function geldAus(seite: EmpfaengerSeite): string[] {
  const summe = new Map<string, number>();
  for (const z of seite.lobby_zuwendungen) summe.set(z.geber, (summe.get(z.geber) ?? 0) + z.von);
  return [...summe.entries()].sort((a, b) => b[1] - a[1]).map(([g]) => g);
}

/** Summe aller Haushaltstitel des Empfängers je Jahr; Jahre ohne Wert (z. B. fehlendes Ist) fallen weg. */
export function titelZeitreihe(seite: EmpfaengerSeite, stand: "soll" | "ist"): { jahr: number; wert: number }[] {
  const summe = new Map<number, number>();
  for (const t of seite.haushalt.titel) {
    for (const [j, w] of Object.entries(t.werte)) {
      const v = stand === "ist" ? w.ist : w.soll;
      if (v === null || v === undefined) continue;
      const jahr = Number(j);
      summe.set(jahr, (summe.get(jahr) ?? 0) + v);
    }
  }
  return [...summe.entries()].sort((a, b) => a[0] - b[0]).map(([jahr, wert]) => ({ jahr, wert }));
}

/** Vorausgefülltes Issue „Fehler melden / Beleg einreichen“ im öffentlichen Repository. */
export function issueUrl(seite: EmpfaengerSeite): string {
  const title = `Empfänger: ${seite.name} – Korrektur oder Beleg`;
  const body = [
    `Empfänger-Id: ${seite.id}`,
    `Name: ${seite.name}`,
    `Stand der Seite: ${seite.stand}`,
    "",
    "Was ist falsch oder fehlt?",
    "",
    "Beleg (URL einer amtlichen Quelle, Datum):",
    "",
  ].join("\n");
  return `https://github.com/eis2k/Bundeshaushaltstracker/issues/new?title=${encodeURIComponent(title)}&body=${encodeURIComponent(body)}&labels=${encodeURIComponent("empfaenger,beleg")}`;
}
