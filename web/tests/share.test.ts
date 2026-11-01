import { describe, expect, test } from "vitest";
import { decodeScenario, encodeScenario } from "../src/lib/model/share";
import type { Scenario } from "../src/lib/model/types";
import { fixtureYear } from "./fixtures";

const base: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };

describe("encodeScenario", () => {
  test("empty state encodes to the minimal form", () => {
    expect(encodeScenario(base, "fluss", [])).toBe("v1;j=2025;a=fluss");
  });

  test("encodes focus, presets, factors as whole percent and sv flag", () => {
    const s: Scenario = { jahr: 2025, factors: { "11-1102-63681": 0.5, "14": 2, "E:steuern:011": 1.1 }, presets: ["rentenzuschuss_halbieren", "schwarze_null"], includeSv: true };
    expect(encodeScenario(s, "karte", ["11", "11-1102", "11-1102-63681"]))
      .toBe("v1;j=2025;a=karte;f=11/1102/63681;p=rentenzuschuss_halbieren,schwarze_null;o=11-1102-63681:50,14:200,E:steuern:011:110;sv=1");
  });

  test("schnitt is encoded only when not ressort and restored on decode", () => {
    expect(encodeScenario(base, "karte", [], "kostenart")).toBe("v1;j=2025;a=karte;sc=kostenart");
    expect(encodeScenario(base, "karte", [], "ressort")).toBe("v1;j=2025;a=karte");
    expect(decodeScenario("v1;j=2025;a=karte;sc=empfaengerart", fixtureYear).schnitt).toBe("empfaengerart");
    expect(decodeScenario("v1;j=2025;a=karte;sc=unsinn", fixtureYear).schnitt).toBe("ressort");
    expect(decodeScenario("v1;j=2025;a=karte", fixtureYear).schnitt).toBe("ressort");
  });

  test("topf is encoded only when not gesamt", () => {
    expect(encodeScenario(base, "fluss", [], "ressort", "bund")).toBe("v1;j=2025;a=fluss;t=bund");
    expect(encodeScenario(base, "fluss", [], "ressort", "gesamt")).toBe("v1;j=2025;a=fluss");
    expect(decodeScenario("v1;j=2025;a=fluss;t=grv", fixtureYear).topf).toBe("grv");
    expect(decodeScenario("v1;j=2025;a=fluss", fixtureYear).topf).toBe("gesamt");
    expect(decodeScenario("v1;j=2025;a=fluss;t=unsinn", fixtureYear).topf).toBe("gesamt");
  });

  test("factors of exactly 100 % are omitted", () => {
    expect(encodeScenario({ ...base, factors: { "14": 1 } }, "fluss", [])).toBe("v1;j=2025;a=fluss");
  });
});

describe("decodeScenario", () => {
  test("roundtrip restores everything", () => {
    const s: Scenario = { jahr: 2025, factors: { "11-1102-63681": 0.5, "14": 2, "E:steuern:011": 1.1 }, presets: ["a", "b"], includeSv: true };
    const hash = encodeScenario(s, "saeulen", ["11", "11-1102"]);
    const d = decodeScenario(hash, fixtureYear);
    expect(d.scenario).toEqual(s);
    expect(d.view).toBe("saeulen");
    expect(d.focus).toEqual(["11", "11-1102"]);
    expect(d.unknownIds).toEqual([]);
  });

  test("unknown ids are dropped and reported", () => {
    const d = decodeScenario("v1;j=2025;a=fluss;o=11-1102-63681:50,99-9999-99999:10,E:steuern:011:120", fixtureYear);
    expect(d.scenario.factors).toEqual({ "11-1102-63681": 0.5, "E:steuern:011": 1.2 });
    expect(d.unknownIds).toEqual(["99-9999-99999"]);
  });

  test("broken or foreign hashes yield the default state for the data's year", () => {
    const d = decodeScenario("irgendwas=kaputt", fixtureYear);
    expect(d.scenario).toEqual({ jahr: 2025, factors: {}, presets: [], includeSv: false });
    expect(d.view).toBe("fluss");
    expect(d.focus).toEqual([]);
    expect(decodeScenario("", fixtureYear).scenario.jahr).toBe(2025);
  });

  test("accepts a leading # and ignores an invalid view", () => {
    const d = decodeScenario("#v1;j=2019;a=unsinn;f=14", fixtureYear);
    expect(d.scenario.jahr).toBe(2019);
    expect(d.view).toBe("fluss");
    expect(d.focus).toEqual(["14"]);
  });
});
