import { describe, expect, test } from "vitest";
import { ausgabenNachEinzelplan } from "../src/lib/model/bereiche";
import { fixtureYear } from "./fixtures";

describe("ausgabenNachEinzelplan (Ring „Nach Bereichen“)", () => {
  test("die größten Einzelpläne einzeln, Anteile summieren sich zu 100", () => {
    const t = ausgabenNachEinzelplan(fixtureYear, false, {}, 2);
    expect(t.map((x) => x.epl)).toEqual(["11", "14"]);
    expect(t.map((x) => x.wert)).toEqual([700, 300]);
    expect(t.map((x) => x.anteil)).toEqual([70, 30]);
    expect(t[0].label).toBe(fixtureYear.epl["11"]);
  });
  test("Rest als „Weitere Einzelpläne“, Faktoren wirken", () => {
    const t = ausgabenNachEinzelplan(fixtureYear, false, { "14": 2 }, 1);
    expect(t.map((x) => x.epl)).toEqual(["11", null]);
    expect(t[1].label).toBe("Weitere Einzelpläne");
    expect(t[1].wert).toBe(600);
    expect(Math.abs(t.reduce((s, x) => s + x.anteil, 0) - 100)).toBeLessThan(0.2);
  });
});
