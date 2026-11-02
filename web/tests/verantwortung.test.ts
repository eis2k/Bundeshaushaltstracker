import { describe, expect, test } from "vitest";
import type { PersonIndex } from "../src/lib/model/personen";
import { kabinett, parteiKurz } from "../src/lib/model/verantwortung";

const personen: PersonIndex = { stand: "", modus: "relevant", eintraege: [
  { id: "a-b", name: "A B", funktion_kurz: "Mitglied des Bundestages, SPD", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb", "regierung"], epl_leitung: [{ epl: "11", amt: "Bundesministerin für Arbeit und Soziales", seit: "2025-05-06", bis: null }] },
  { id: "c-d", name: "C D", funktion_kurz: "Bundesministerin für Wirtschaft und Energie, Bundesministerium für Wirtschaft und Energie", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "09", amt: "Bundesministerin für Wirtschaft und Energie", seit: "2025-05-06", bis: null }], partei: "CDU" },
  { id: "e-f", name: "E F", funktion_kurz: "Mitglied des Bundestages, CDU/CSU", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb", "regierung"], epl_leitung: [{ epl: "11", amt: "Parlamentarischer Staatssekretär", seit: "2025-05-06", bis: null }] },
  { id: "g-h", name: "G H", funktion_kurz: "Mitglied des Bundestages, Bündnis 90/Die Grünen", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb", "regierung"], epl_leitung: [{ epl: "11", amt: "Bundesminister für Arbeit und Soziales", seit: "2021-12-08", bis: "2024-12-31" }] },
  { id: "i-j", name: "I J", funktion_kurz: "Mitglied des Bundestages, SPD", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb"], epl_leitung: [] },
] };

describe("verantwortung", () => {
  test("kabinett: nur Leitungen im Jahr, Kanzler/Minister vor Staatssekretären, Partei aus Fraktion oder Index", () => {
    const k = kabinett(personen, 2025, 2025);
    expect(k.map((x) => x.id)).toEqual(["c-d", "a-b", "e-f"]); // Rang, dann Einzelplan-Nummer
    expect(k[1]).toMatchObject({ epl: "11", partei: "SPD", amt: "Bundesministerin für Arbeit und Soziales" });
    expect(k[0].partei).toBe("CDU");
    expect(k[2].partei).toBe("CDU/CSU");
  });
  test("kabinett: Vorgänger im früheren Jahr, leerer Index", () => {
    expect(kabinett(personen, 2023, 2025).map((x) => x.id)).toEqual(["g-h"]);
    expect(kabinett(null, 2025, 2025)).toEqual([]);
  });
  test("parteiKurz", () => {
    expect(parteiKurz("Bündnis 90/Die Grünen")).toBe("Grüne");
    expect(parteiKurz("CDU/CSU")).toBe("CDU/CSU");
    expect(parteiKurz("SPD")).toBe("SPD");
  });
});
