/** Recherchepfad (Spec §4.10): die tatsächliche Spur der Klicks im Inhalt plus das aktuelle Glied. Zeigt nie eine Beziehung, die nicht geklickt wurde. */

import type { NodeId, ViewId } from "./types";
import type { TopfId } from "./share";

export type Ziel =
  | { art: "haushalt"; view: ViewId; topf: TopfId; focus: NodeId[] }
  | { art: "empfaengerliste"; epl: string | null }
  | { art: "empfaenger"; id: string }
  | { art: "personenliste" }
  | { art: "akte"; id: string }
  | { art: "netz"; knoten: string }
  | { art: "ministerien" };

export interface Glied { label: string; ziel: Ziel }

export interface GliedEingabe {
  view: ViewId;
  topf: TopfId;
  focus: NodeId[];
  selected: NodeId | null;
  eplNamen: Record<string, string>;
  titelNamen: Record<string, string>;
  topfNamen: Record<string, string>;
  empfaengerId: string | null;
  empfaengerName: string | null;
  empfaengerFilterEpl: string | null;
  akteId: string | null;
  akteName: string | null;
  netzStart: string | null;
  netzLabel: string | null;
}

const HAUSHALT: ViewId[] = ["fluss", "karte", "saeulen", "gewachsen"];

export function aktuellesGlied(e: GliedEingabe): Glied {
  if (HAUSHALT.includes(e.view)) {
    const teile = [e.topfNamen[e.topf] ?? e.topf];
    // Nur benannte Glieder: Einzelplan (Nummer), Kapitel und Titel mit Namen; Kassen-, Posten- und Einnahmen-Ids ohne Namen bleiben weg
    for (const f of e.focus) {
      if (/^\d{2}$/.test(f)) teile.push(`Einzelplan ${f} ${e.eplNamen[f] ?? ""}`.trim());
      else if (e.titelNamen[f]) teile.push(e.titelNamen[f]);
    }
    if (e.selected && !e.focus.includes(e.selected) && e.titelNamen[e.selected]) teile.push(e.titelNamen[e.selected]);
    return { label: teile.join(" › "), ziel: { art: "haushalt", view: e.view, topf: e.topf, focus: [...e.focus] } };
  }
  if (e.view === "ministerien") return { label: "Ministerien", ziel: { art: "ministerien" } };
  if (e.view === "empfaenger") {
    if (e.empfaengerId) return { label: `Empfänger: ${e.empfaengerName ?? e.empfaengerId}`, ziel: { art: "empfaenger", id: e.empfaengerId } };
    return { label: e.empfaengerFilterEpl ? `Empfänger (Einzelplan ${e.empfaengerFilterEpl})` : "Empfänger", ziel: { art: "empfaengerliste", epl: e.empfaengerFilterEpl } };
  }
  if (e.view === "personen" || e.view === "politik") {
    if (e.akteId) return { label: `Akte: ${e.akteName ?? e.akteId}`, ziel: { art: "akte", id: e.akteId } };
    return { label: "Personen", ziel: { art: "personenliste" } };
  }
  if (e.netzStart) return { label: `Umfeld: ${e.netzLabel ?? e.netzStart}`, ziel: { art: "netz", knoten: e.netzStart } };
  return { label: "Netz", ziel: { art: "personenliste" } };
}

/** Spur plus aktuelles Glied, auf die letzten `max` Glieder gekürzt. */
export function pfad(spur: Glied[], aktuell: Glied, max = 6): Glied[] {
  const alle = [...spur, aktuell];
  return alle.slice(Math.max(0, alle.length - max));
}
