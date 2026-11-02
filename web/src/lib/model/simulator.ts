/** Haushaltssimulator (Spec §4.11): Bereiche aus Einzelplan-Gruppen, Bereichsfaktor und Ergebniskarte. Reine Rechnung auf den Faktoren, keine Prognose. */

import { effectiveFactor, type Factors } from "./scenario";
import type { Balance } from "./types";

export interface Bereich { id: string; label: string; epls: string[]; icon: string }

/** Reglerkarten wie im Entwurf; die Zuordnung ist die Einzelplan-Nummer des Ressorts. */
export const BEREICHE: Bereich[] = [
  { id: "verteidigung", label: "Verteidigung", epls: ["14"], icon: "Shield" },
  { id: "bildung", label: "Bildung & Forschung", epls: ["30"], icon: "GraduationCap" },
  { id: "soziales", label: "Soziales", epls: ["11"], icon: "HeartHandshake" },
  { id: "verkehr", label: "Verkehr & Infrastruktur", epls: ["12"], icon: "TrainFront" },
  { id: "klima", label: "Klima & Umwelt", epls: ["16"], icon: "Leaf" },
  { id: "gesundheit", label: "Gesundheit", epls: ["15"], icon: "Stethoscope" },
  { id: "inneres", label: "Inneres", epls: ["06"], icon: "ShieldCheck" },
  { id: "entwicklung", label: "Entwicklung", epls: ["23"], icon: "Globe" },
];

/** Faktor des Bereichs: der gemeinsame Faktor, wenn alle Einzelpläne gleich stehen, sonst der Mittelwert. */
export function bereichFaktor(bereich: Bereich, factors: Factors): number {
  const f = bereich.epls.map((epl) => effectiveFactor(epl, factors));
  if (!f.length) return 1;
  return f.reduce((s, x) => s + x, 0) / f.length;
}

export interface Ergebnis { gesamtvolumen: number; veraenderung: number; neuverschuldung: number; defizitquote: number }

/** Ergebniskarte: Volumen, Veränderung gegen das Original, Neuverschuldung und Defizitquote = max(0, Neuverschuldung) / Ausgaben. */
export function ergebnis(b: Balance): Ergebnis {
  return {
    gesamtvolumen: b.ausgaben,
    veraenderung: b.ausgaben - b.ausgabenOriginal,
    neuverschuldung: b.neueSchulden,
    defizitquote: b.ausgaben > 0 ? Math.max(0, b.neueSchulden) / b.ausgaben : 0,
  };
}
