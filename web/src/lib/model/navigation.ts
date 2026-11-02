/** Hauptnavigation nach dem Dashboard-Entwurf (Spec §4.11): neun Einträge, Symbole aus Lucide, Unteransichten als Reiter im Inhalt. */

import type { ViewId } from "./types";

export type EintragId = "dashboard" | "haushalt" | "geldfluesse" | "ministerien" | "empfaenger" | "simulator" | "zeitvergleich" | "politik" | "verflechtungen" | "daten";

export interface NavEintrag {
  id: EintragId;
  label: string;
  kurz: string;
  titel: string;
  untertitel: string;
  view: ViewId;
  /** Lucide-Symbolname (Zuordnung in Navigation.svelte). */
  icon: string;
  /** Erscheint in der mobilen unteren Leiste. */
  mobil?: boolean;
}

export const EINTRAEGE: NavEintrag[] = [
  { id: "dashboard", label: "Dashboard", kurz: "Start", titel: "Dashboard", untertitel: "Bundeshaushalt auf einen Blick: Herkunft, Verwendung, Empfänger, Entwicklung.", view: "dashboard", icon: "LayoutDashboard", mobil: true },
  { id: "haushalt", label: "Haushalt", kurz: "Haushalt", titel: "Haushalt", untertitel: "Einzelpläne, Kapitel und Titel als Karte oder Säulen.", view: "karte", icon: "Wallet" },
  { id: "geldfluesse", label: "Geldflüsse & Profiteure", kurz: "Geldflüsse", titel: "Geldflüsse & Profiteure", untertitel: "Verfolge, woher die Gelder kommen, wohin sie fließen, wer davon profitiert und welche politischen Verantwortlichen dahinterstehen.", view: "fluss", icon: "Waypoints", mobil: true },
  { id: "ministerien", label: "Ministerien", kurz: "Ministerien", titel: "Ministerien", untertitel: "Haushalt, Entwicklung, Empfänger und Verantwortung je Einzelplan.", view: "ministerien", icon: "Landmark" },
  { id: "empfaenger", label: "Empfänger & Zuwendungen", kurz: "Empfänger", titel: "Empfänger & Zuwendungen", untertitel: "Alle Zahlungsempfänger mit Seite: Haushaltstitel, Lobbyregister, Förderkatalog, Verbindungen.", view: "empfaenger", icon: "Building2", mobil: true },
  { id: "simulator", label: "Haushaltssimulator", kurz: "Simulator", titel: "Haushaltssimulator", untertitel: "Ausgaben verändern und Auswirkungen sofort sehen. Modellrechnung, keine Prognose.", view: "simulator", icon: "SlidersHorizontal" },
  { id: "zeitvergleich", label: "Zeitvergleich", kurz: "Zeit", titel: "Zeitvergleich", untertitel: "Was ist seit 2015 gewachsen, was geschrumpft? Soll und Ist, nominal und in Preisen.", view: "gewachsen", icon: "TrendingUp" },
  { id: "politik", label: "Politik & Verantwortung", kurz: "Politik", titel: "Politik & Verantwortung", untertitel: "Welche Personen entscheiden über welche Gelder? Kabinett, Abgeordnete, Akten.", view: "politik", icon: "Users", mobil: true },
  { id: "verflechtungen", label: "Verflechtungen", kurz: "Netz", titel: "Verflechtungen", untertitel: "Belegte Beziehungen zwischen Ministerien, Organisationen, Personen und Parteien.", view: "netz", icon: "Share2", mobil: true },
  { id: "daten", label: "Daten & Quellen", kurz: "Daten", titel: "Daten & Quellen", untertitel: "Verwendete Datensätze, Stand, Lizenzen und bekannte Lücken.", view: "daten", icon: "Database" },
];

export function aktiverEintrag(view: ViewId): EintragId {
  switch (view) {
    case "fluss": return "geldfluesse";
    case "karte": case "saeulen": return "haushalt";
    case "personen": case "politik": return "politik";
    case "netz": return "verflechtungen";
    case "gewachsen": return "zeitvergleich";
    case "dashboard": return "dashboard";
    case "ministerien": return "ministerien";
    case "simulator": return "simulator";
    case "daten": return "daten";
    default: return "empfaenger";
  }
}

export function unteransichten(eintrag: EintragId): { view: ViewId; label: string }[] {
  if (eintrag === "haushalt") return [{ view: "karte", label: "Karte" }, { view: "saeulen", label: "Säulen" }];
  return [];
}

export function titelFuer(view: ViewId): { titel: string; untertitel: string } {
  const e = EINTRAEGE.find((x) => x.id === aktiverEintrag(view)) ?? EINTRAEGE[0];
  return { titel: e.titel, untertitel: e.untertitel };
}
