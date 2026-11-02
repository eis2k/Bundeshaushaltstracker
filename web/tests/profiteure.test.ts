import { describe, expect, test } from "vitest";
import type { EmpfaengerIndex } from "../src/lib/model/empfaenger";
import type { PersonIndex } from "../src/lib/model/personen";
import { anzahlEmpfaenger, topEmpfaenger, verantwortung } from "../src/lib/model/profiteure";
import { fixtureYear } from "./fixtures";

const e = (id: string, name: string, epls: string[], haushalt: Record<string, number>, lobby: Record<string, number>) =>
  ({ id, name, art: "verein_stiftung", rechtsform: "", sitz: "", lobby_untergrenze_bund: Object.values(lobby).reduce((a, b) => a + b, 0), haushalt_soll_letztes_jahr: Object.values(haushalt).reduce((a, b) => a + b, 0),
     haushalt_je_epl: haushalt, lobby_je_epl: lobby, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls }) as EmpfaengerIndex["eintraege"][number];
const index: EmpfaengerIndex = { stand: "", mit_personen: true, titel: {}, eintraege: [
  e("drv", "Deutsche Rentenversicherung", ["11"], { "11": 500 }, {}),
  e("lobby", "Verband X", ["11", "12"], {}, { "11": 120, "12": 5 }),
  e("klein", "Verein Y", ["11"], { "11": 20 }, { "11": 900 }),
  e("bw", "Bundeswehr-Verband", ["14"], {}, { "14": 50 }),
  // Titel in Epl 04, im Förderkatalog unter Epl 30: zählt nur für 04 (Review C2)
  e("dw", "Deutsche Welle", ["04", "30"], { "04": 395 }, {}),
] };
const personen: PersonIndex = { stand: "", modus: "relevant", eintraege: [
  { id: "a-b", name: "A B", funktion_kurz: "Bundesministerin", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesministerin für Arbeit und Soziales", seit: "2025-05-06", bis: null }] },
  { id: "g-h", name: "G H", funktion_kurz: "Bundesminister", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesminister für Arbeit und Soziales", seit: "2021-12-08", bis: "2025-05-06" }] },
] };

describe("profiteure", () => {
  test("topEmpfaenger: nur Empfänger des Einzelplans, Haushalt vor Lobbyregister, Quelle gesetzt", () => {
    const t = topEmpfaenger("11", 2025, index);
    expect(t.map((x) => x.id)).toEqual(["drv", "klein", "lobby"]);
    expect(t[0]).toMatchObject({ wert: 500, quelle: "haushalt" });
    expect(t[2]).toMatchObject({ wert: 120, quelle: "lobbyregister" });
  });
  test("topEmpfaenger: Beträge je Einzelplan und Quelle, Förderkatalog-Einzelpläne zählen nicht (Review C2)", () => {
    expect(topEmpfaenger("12", 2025, index)).toEqual([{ id: "lobby", name: "Verband X", wert: 5, quelle: "lobbyregister" }]);
    expect(topEmpfaenger("30", 2025, index)).toEqual([]);
    expect(topEmpfaenger("04", 2025, index)).toEqual([{ id: "dw", name: "Deutsche Welle", wert: 395, quelle: "haushalt" }]);
    expect(topEmpfaenger(null, 2025, index, 2).map((x) => x.id)).toEqual(["drv", "dw"]);
  });
  test("anzahlEmpfaenger: alle mit Betrag aus dem Einzelplan (für „weitere Empfänger“)", () => {
    expect(anzahlEmpfaenger("11", index)).toBe(3);
    expect(anzahlEmpfaenger("30", index)).toBe(0);
  });
  test("topEmpfaenger: ohne Einzelplan alle, begrenzt durch max", () => {
    expect(topEmpfaenger(null, 2025, index, 2)).toHaveLength(2);
    expect(topEmpfaenger("11", 2025, null)).toEqual([]);
  });
  test("verantwortung: Leitung aus dem Zeitraum, Haushalt und Anteil", () => {
    const v = verantwortung("11", 2025, 2025, fixtureYear, false, personen)!;
    expect(v.epl).toBe("11");
    expect(v.leitung.map((l) => l.id)).toEqual(["a-b", "g-h"]); // beide im Jahr 2025 im Amt (Wechsel im Mai), Ministerin vor Vorgänger
    expect(v.haushalt).toBe(700);
    expect(v.anteil).toBeCloseTo((700 / 950) * 100, 1);
  });
  test("verantwortung: ohne Einzelplan der größte", () => {
    expect(verantwortung(null, 2025, 2025, fixtureYear, false, personen)?.epl).toBe("11");
    expect(verantwortung("99", 2025, 2025, fixtureYear, false, personen)).toBeNull();
  });
});
