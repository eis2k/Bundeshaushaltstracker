import { describe, expect, test } from "vitest";
import { BEREICHE, bereichFaktor, ergebnis } from "../src/lib/model/simulator";
import type { Balance } from "../src/lib/model/types";

describe("simulator", () => {
  test("BEREICHE decken die acht Entwurfsbereiche mit Einzelplänen ab", () => {
    expect(BEREICHE.map((b) => b.epls[0])).toEqual(["14", "30", "11", "12", "16", "15", "06", "23"]);
    expect(BEREICHE.every((b) => b.label && b.icon)).toBe(true);
  });
  test("bereichFaktor: gleicher Faktor aller Einzelpläne, sonst Mittelwert, ohne Angabe 1", () => {
    const b = { id: "x", label: "X", epls: ["14", "30"], icon: "Shield" };
    expect(bereichFaktor(b, {})).toBe(1);
    expect(bereichFaktor(b, { "14": 1.1, "30": 1.1 })).toBeCloseTo(1.1);
    expect(bereichFaktor(b, { "14": 1.2 })).toBeCloseTo(1.1);
  });
  test("ergebnis: Volumen, Veränderung, Neuverschuldung und Defizitquote", () => {
    const bal: Balance = { ausgaben: 1100, einnahmen: 800, neueSchulden: 300, ausgabenOriginal: 1000, einnahmenOriginal: 800, neueSchuldenOriginal: 200, delta: 100, modellEinnahmen: 0 };
    expect(ergebnis(bal)).toEqual({ gesamtvolumen: 1100, veraenderung: 100, neuverschuldung: 300, defizitquote: 300 / 1100 });
    expect(ergebnis({ ...bal, neueSchulden: -50 }).defizitquote).toBe(0);
  });
});
