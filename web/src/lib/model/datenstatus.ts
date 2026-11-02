/** Datenstatus-Leiste (Spec §4.10): nennt je Ansicht das wirklich verwendete Jahr, Quellen, Stand und Preisstand. */

import type { ViewId } from "./types";

export interface DatenstatusEingabe {
  view: ViewId;
  /** Empfänger: geöffnete Seite (alle Jahre) statt Liste (Soll des letzten Jahres). */
  seite: boolean;
  jahr: number;
  stand: "soll" | "ist";
  real: boolean;
  bezugsjahr: number;
  erzeugt: string | null;
  modell: boolean;
  empfaengerStand: string | null;
  personenStand: string | null;
  letztesJahr: number | null;
}

export interface Datenstatus {
  jahr: string;
  quellen: string[];
  stand: string | null;
  preise: string;
  modell: boolean;
  jahresleiste: boolean;
}

const HAUSHALT: ViewId[] = ["fluss", "karte", "saeulen", "gewachsen", "ministerien"];

export function datenstatus(e: DatenstatusEingabe): Datenstatus {
  const preise = e.real ? `in Preisen von ${e.bezugsjahr}` : "nominal";
  if (HAUSHALT.includes(e.view)) {
    return {
      jahr: `${e.jahr} ${e.stand === "ist" ? "Ist" : "Soll"}`,
      quellen: e.stand === "ist" ? ["bundeshaushalt.de", "Haushaltsrechnung"] : ["bundeshaushalt.de"],
      stand: e.erzeugt,
      preise,
      modell: e.modell,
      jahresleiste: true,
    };
  }
  const soll = e.letztesJahr ? `Soll ${e.letztesJahr}` : "";
  if (e.view === "empfaenger") {
    return { jahr: e.seite ? "alle Jahre, Soll und Ist je Titel" : soll, quellen: ["Lobbyregister", "Förderkatalog", "bundestag.de"], stand: e.empfaengerStand, preise, modell: e.modell, jahresleiste: false };
  }
  return { jahr: e.view === "netz" ? "" : soll, quellen: ["Lobbyregister", "bundestag.de", "bundesregierung.de"], stand: e.personenStand, preise, modell: e.modell, jahresleiste: false };
}
