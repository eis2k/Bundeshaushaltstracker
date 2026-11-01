/** Steuer-Szenarien (Konzept §4.8a): Modelle mit offenen Annahmen, Aufkommen gesamt und Bund-Anteil. */

export type ModellArt = "satz_mal_basis" | "satzaenderung" | "basis_mal_faktor";

export interface Annahme {
  id: string;
  text: string;
  wert: number;
  min: number;
  max: number;
  schritt: number;
  einheit: string;
  quelle: string;
}

export interface Ereignis {
  datum: string;
  titel: string;
  text: string;
  akteure: string;
  quelle: string;
}

export interface SteuerSzenario {
  id: string;
  name: string;
  kurz: string;
  status: "erhoben" | "ausgesetzt" | "nie_eingefuehrt";
  empfaenger: "bund" | "laender" | "gemeinsam";
  bund_anteil: number;
  bund_anteil_quelle: string;
  beschreibung: string;
  modell: {
    art: ModellArt;
    basis: { wert: number; text: string; jahr: number; quelle: string };
    satz_alt?: number;
    annahmen: Annahme[];
  };
  geschichte: Ereignis[];
}

/** Aktive Szenarien mit Annahmewerten (fehlende Werte = Standard aus der Definition). */
export type AktiveSteuern = Record<string, Record<string, number>>;

export function defaultWerte(s: SteuerSzenario): Record<string, number> {
  return Object.fromEntries(s.modell.annahmen.map((a) => [a.id, a.wert]));
}

function wert(s: SteuerSzenario, werte: Record<string, number>, id: string): number {
  const a = s.modell.annahmen.find((x) => x.id === id);
  if (!a) return 0;
  const v = werte[id] ?? a.wert;
  if (!Number.isFinite(v)) return a.wert;
  return Math.min(a.max, Math.max(a.min, v));
}

/** Aufkommen eines Szenarios in Euro (gesamt und Bund-Anteil); nie negativ. */
export function aufkommen(s: SteuerSzenario, werte: Record<string, number>): { gesamt: number; bund: number } {
  const m = s.modell;
  let gesamt = 0;
  if (m.art === "satz_mal_basis") {
    gesamt = m.basis.wert * wert(s, werte, "satz") * (1 - wert(s, werte, "ausweich"));
  } else if (m.art === "satzaenderung") {
    gesamt = m.basis.wert * (wert(s, werte, "satz_neu") - (m.satz_alt ?? 0)) * 100;
  } else if (m.art === "basis_mal_faktor") {
    gesamt = m.basis.wert * (wert(s, werte, "faktor") - 1);
  }
  gesamt = Math.max(0, Math.round(gesamt));
  return { gesamt, bund: Math.round(gesamt * s.bund_anteil) };
}

export interface SteuerErgebnis {
  gesamt: number;
  bund: number;
  je: { id: string; kurz: string; gesamt: number; bund: number; empfaenger: SteuerSzenario["empfaenger"] }[];
}

export function steuerEinnahmen(szenarien: SteuerSzenario[], aktiv: AktiveSteuern | undefined): SteuerErgebnis {
  const je: SteuerErgebnis["je"] = [];
  let gesamt = 0, bund = 0;
  for (const [id, werte] of Object.entries(aktiv ?? {})) {
    const s = szenarien.find((x) => x.id === id);
    if (!s) continue;
    const a = aufkommen(s, werte);
    je.push({ id, kurz: s.kurz, gesamt: a.gesamt, bund: a.bund, empfaenger: s.empfaenger });
    gesamt += a.gesamt;
    bund += a.bund;
  }
  return { gesamt, bund, je };
}
