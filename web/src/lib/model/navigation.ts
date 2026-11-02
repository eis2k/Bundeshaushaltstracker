/** Hauptnavigation nach den GUI-v2-Mockups (Spec §4.10): sechs Einträge, Unteransichten als Reiter im Inhalt. */

import type { ViewId } from "./types";

export type EintragId = "geldfluesse" | "ministerien" | "empfaenger" | "verbindungen" | "zeitvergleich" | "simulator";

export interface NavEintrag {
  id: EintragId;
  label: string;
  kurz: string;
  untertitel: string;
  /** Titel der Seite in der Kopfzeile (Mockup), sonst `label`. */
  titel?: string;
  view: ViewId;
  /** Simulator: öffnet den Geldfluss mit Seitenpanel; flüchtiges Kennzeichen, nicht im Link. */
  gestalten?: boolean;
  symbol: string;
}

export const EINTRAEGE: NavEintrag[] = [
  { id: "geldfluesse", label: "Geldflüsse", kurz: "Fluss", titel: "Geldflüsse & Empfänger", untertitel: "Steuern → Ressorts → Titel → Empfänger", view: "fluss", symbol: "⇄" },
  { id: "ministerien", label: "Ministerien", kurz: "Ministerien", titel: "Ministerium & Haushaltstitel", untertitel: "Verantwortung und Zahlungen nachvollziehen", view: "ministerien", symbol: "▦" },
  { id: "empfaenger", label: "Empfänger", kurz: "Empfänger", titel: "Empfänger & Verbindungen", untertitel: "Geld · öffentliche Funktionen · belegte Beziehungen", view: "empfaenger", symbol: "◎" },
  { id: "verbindungen", label: "Verbindungen", kurz: "Netz", titel: "Verbindungen", untertitel: "Belegte Personen- und Organisationsbeziehungen", view: "personen", symbol: "⋈" },
  { id: "zeitvergleich", label: "Zeitvergleich", kurz: "Zeit", titel: "Geldflüsse im Zeitvergleich", untertitel: "Wer erhält wann wie viel?", view: "gewachsen", symbol: "↗" },
  { id: "simulator", label: "Simulator", kurz: "Simulator", titel: "Haushaltssimulator", untertitel: "Haushaltsänderungen nachvollziehbar modellieren", view: "fluss", gestalten: true, symbol: "⚙" },
];

export function aktiverEintrag(view: ViewId, gestalten: boolean): EintragId {
  if (view === "fluss" && gestalten) return "simulator";
  if (view === "fluss" || view === "karte" || view === "saeulen") return "geldfluesse";
  if (view === "personen" || view === "netz") return "verbindungen";
  if (view === "gewachsen") return "zeitvergleich";
  if (view === "ministerien") return "ministerien";
  return "empfaenger";
}

export function unteransichten(eintrag: EintragId): { view: ViewId; label: string }[] {
  if (eintrag === "geldfluesse" || eintrag === "simulator") return [{ view: "fluss", label: "Fluss" }, { view: "karte", label: "Karte" }, { view: "saeulen", label: "Säulen" }];
  if (eintrag === "verbindungen") return [{ view: "personen", label: "Personen" }, { view: "netz", label: "Netz" }];
  return [];
}

export function titelFuer(view: ViewId, gestalten: boolean): { titel: string; untertitel: string } {
  const e = EINTRAEGE.find((x) => x.id === aktiverEintrag(view, gestalten)) ?? EINTRAEGE[0];
  return { titel: e.titel ?? e.label, untertitel: e.untertitel };
}
