import type { BudgetRow, YearData } from "../src/lib/model/types";

function row(p: Partial<BudgetRow> & Pick<BudgetRow, "epl" | "kap" | "titel" | "art" | "soll">): BudgetRow {
  return {
    id: `${p.epl}-${p.kap}-${p.titel}`,
    text: p.text ?? `Titel ${p.titel}`,
    fkt: p.fkt ?? "000",
    flex: p.flex ?? null,
    tgr: p.tgr ?? null,
    ist: p.ist ?? null,
    sv: p.sv ?? false,
    ...p,
  };
}

/** Kleiner, vollständig nachrechenbarer Jahreshaushalt (Beträge in Euro). */
export const fixtureYear: YearData = {
  jahr: 2025,
  stand: "soll",
  quelle: { soll: { dokument: "Fixture", url: "https://example.invalid", abgerufen: "2026-11-01" }, ist: null, hinweise: [] },
  epl: { "11": "Arbeit und Soziales", "14": "Verteidigung", "32": "Bundesschuld", "60": "Allgemeine Finanzverwaltung" },
  kap: { "1101": "Grundsicherung", "1102": "Rentenversicherung", "1401": "Bundeswehr", "3201": "Kreditaufnahme", "6001": "Steuern", "6092": "KTF" },
  rows: [
    // Ausgaben
    row({ epl: "11", kap: "1102", titel: "63681", art: "A", soll: 400, text: "Zuschuss Rentenversicherung", ist: 390 }),
    row({ epl: "11", kap: "1102", titel: "63682", art: "A", soll: 100, text: "Zuschuss Ost" }),
    row({ epl: "11", kap: "1101", titel: "68101", art: "A", soll: 200, text: "Bürgergeld" }),
    row({ epl: "11", kap: "1101", titel: "68199", art: "A", soll: 0, text: "Leertitel" }),
    row({ epl: "14", kap: "1401", titel: "55101", art: "A", soll: 300, text: "Militärische Beschaffungen" }),
    row({ epl: "60", kap: "6001", titel: "97201", art: "A", soll: -50, text: "Globale Minderausgabe" }),
    row({ epl: "60", kap: "6092", titel: "89310", art: "A", soll: 80, text: "KTF Förderung", sv: true }),
    // Einnahmen (ohne Kredite 700, Kredite 250 → Ausgaben Kern 950)
    row({ epl: "60", kap: "6001", titel: "01101", art: "E", soll: 300, text: "Lohnsteuer" }),
    row({ epl: "60", kap: "6001", titel: "01501", art: "E", soll: 250, text: "Umsatzsteuer" }),
    row({ epl: "60", kap: "6001", titel: "03103", art: "E", soll: 50, text: "Energiesteuer" }),
    row({ epl: "60", kap: "6001", titel: "04901", art: "E", soll: 40, text: "Sonstige Steuer" }),
    row({ epl: "14", kap: "1401", titel: "11901", art: "E", soll: 60, text: "Verwaltungseinnahmen" }),
    row({ epl: "32", kap: "3201", titel: "32511", art: "E", soll: 250, text: "Einnahmen aus Krediten vom Kreditmarkt" }),
    row({ epl: "60", kap: "6092", titel: "33401", art: "E", soll: 80, text: "KTF Zuweisung", sv: true }),
  ],
};

export const SUM_A_KERN = 400 + 100 + 200 + 0 + 300 - 50; // 950
export const SUM_E_OHNE_KREDITE = 300 + 250 + 50 + 40 + 60; // 700
export const KREDITE = 250;
