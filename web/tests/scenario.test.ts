import { describe, expect, test } from "vitest";
import { balance, childFactorsOverridden, effectiveFactor, effectiveValue, rowFactor, setFactor } from "../src/lib/model/scenario";
import type { Scenario } from "../src/lib/model/types";
import { fixtureYear, KREDITE, SUM_A_KERN, SUM_E_OHNE_KREDITE } from "./fixtures";

const empty: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };
const rowById = (id: string) => fixtureYear.rows.find((r) => r.id === id)!;

describe("effectiveFactor", () => {
  test("titel override beats kapitel beats einzelplan", () => {
    const f = { "11": 0.8, "11-1102": 0.6, "11-1102-63681": 0.5 };
    expect(effectiveFactor("11-1102-63681", f)).toBe(0.5);
    expect(effectiveFactor("11-1102-63682", f)).toBe(0.6);
    expect(effectiveFactor("11-1101-68101", f)).toBe(0.8);
    expect(effectiveFactor("14-1401-55101", f)).toBe(1);
  });

  test("revenue rows resolve titel, then tax group, then all taxes", () => {
    expect(rowFactor(rowById("60-6001-01101"), { "E:steuern": 1.1 })).toBe(1.1);
    expect(rowFactor(rowById("60-6001-01101"), { "E:steuern": 1.1, "E:steuern:011": 1.3 })).toBe(1.3);
    expect(rowFactor(rowById("60-6001-01101"), { "E:steuern:011": 1.3, "60-6001-01101": 0.9 })).toBe(0.9);
    expect(rowFactor(rowById("14-1401-11901"), { "E:steuern": 1.1 })).toBe(1);
    expect(rowFactor(rowById("14-1401-11901"), { "E:sonstige": 2 })).toBe(2);
  });
});

describe("balance", () => {
  test("excludes Kredite from revenue and keeps negative rows", () => {
    const b = balance(fixtureYear, {}, false);
    expect(b.einnahmen).toBe(SUM_E_OHNE_KREDITE);
    expect(b.ausgaben).toBe(SUM_A_KERN);
    expect(b.neueSchulden).toBe(SUM_A_KERN - SUM_E_OHNE_KREDITE);
    expect(b.neueSchulden).toBe(KREDITE);
    expect(b.delta).toBe(0);
  });

  test("includeSv adds Anlagen to both sides", () => {
    const b = balance(fixtureYear, {}, true);
    expect(b.ausgaben).toBe(SUM_A_KERN + 80);
    expect(b.einnahmen).toBe(SUM_E_OHNE_KREDITE + 80);
  });

  test("halving a titel reduces ausgaben by half its soll and improves delta", () => {
    const s = setFactor(empty, "11-1102-63681", 0.5);
    const b = balance(fixtureYear, s.factors, false);
    expect(b.ausgabenOriginal - b.ausgaben).toBe(200);
    expect(b.delta).toBe(200);
    expect(b.neueSchulden).toBe(KREDITE - 200);
  });

  test("factor on a titel with soll 0 is harmless", () => {
    const s = setFactor(empty, "11-1101-68199", 3);
    const b = balance(fixtureYear, s.factors, false);
    expect(b.ausgaben).toBe(SUM_A_KERN);
    expect(Number.isNaN(effectiveValue(rowById("11-1101-68199"), s.factors))).toBe(false);
  });

  test("raising a tax group raises revenue", () => {
    const b = balance(fixtureYear, { "E:steuern:011": 1.5 }, false);
    expect(b.einnahmen).toBe(SUM_E_OHNE_KREDITE + 150);
  });
});

describe("setFactor", () => {
  test("is pure and removes the key when factor is 1", () => {
    const s1 = setFactor(empty, "14", 2);
    expect(empty.factors).toEqual({});
    expect(s1.factors).toEqual({ "14": 2 });
    const s2 = setFactor(s1, "14", 1);
    expect(s2.factors).toEqual({});
  });

  test("childFactorsOverridden lists explicit descendants", () => {
    const f = { "11": 0.8, "11-1102": 0.6, "11-1102-63681": 0.5, "14": 2 };
    expect(childFactorsOverridden("11", f).sort()).toEqual(["11-1102", "11-1102-63681"]);
    expect(childFactorsOverridden("11-1102", f)).toEqual(["11-1102-63681"]);
    expect(childFactorsOverridden("14", f)).toEqual([]);
  });
});

describe("Schnitt-Faktoren (Review 9)", () => {
  test("ka:/ea: factors apply to matching rows below user titel/kap/epl factors", () => {
    expect(rowFactor(rowById("14-1401-55101"), { "ka:sach": 0.5 })).toBe(0.5);
    expect(rowFactor(rowById("11-1102-63681"), { "ka:sach": 0.5 })).toBe(1);
    expect(rowFactor(rowById("11-1102-63681"), { "ea:sozialversicherung": 0.8 })).toBe(0.8);
    expect(rowFactor(rowById("11-1102-63681"), { "ea:sozialversicherung": 0.8, "11": 1.2 })).toBe(1.2);
    expect(balance(fixtureYear, { "ka:zuweisungen": 0.5 }, false).ausgaben).toBe(950 - 350);
  });
});

describe("Transfers bei Nebenhaushalten (Review 11)", () => {
  test("rows flagged transfer are skipped when includeSv is on, counted when off", () => {
    const data = { ...fixtureYear, rows: [
      ...fixtureYear.rows,
      { id: "60-6002-63401", art: "A" as const, epl: "60", kap: "6002", titel: "63401", text: "Zuweisung an das Sondervermögen", fkt: "000", flex: null, tgr: null, soll: 30, ist: null, sv: false, transfer: true },
      { id: "60-6098-23101", art: "E" as const, epl: "60", kap: "6098", titel: "23101", text: "Zuweisung aus dem Bundeshaushalt", fkt: "000", flex: null, tgr: null, soll: 30, ist: null, sv: true, transfer: true },
    ] };
    expect(balance(data, {}, false).ausgaben).toBe(SUM_A_KERN + 30);
    expect(balance(data, {}, true).ausgaben).toBe(SUM_A_KERN + 80);          // Kern-Zuweisung entfällt, SV-Ausgaben 80 dazu
    expect(balance(data, {}, true).einnahmen).toBe(SUM_E_OHNE_KREDITE + 80); // SV-Einnahme aus dem Bund entfällt
  });
});
