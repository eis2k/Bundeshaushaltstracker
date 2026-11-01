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

describe("Grenzen (Review 13)", () => {
  test("percent values are clamped to 0..1000 and ka:/ea: ids are known", () => {
    const d = decodeScenario("v1;j=2025;a=fluss;o=14:100000,11:-50,ka:personal:50", fixtureYear);
    expect(d.scenario.factors["14"]).toBe(10);
    expect(d.scenario.factors["11"]).toBe(0);
    expect(d.scenario.factors["ka:personal"]).toBe(0.5);
    expect(d.unknownIds).toEqual([]);
  });
});

describe("Steuer-Szenarien im Link (Stufe 1b)", () => {
  test("active scenarios with their assumptions roundtrip; unknown ones are reported", () => {
    const s: Scenario = { ...base, steuern: { vermoegensteuer: { satz: 0.01, ausweich: 0.3 }, spitzensteuersatz: { satz_neu: 0.45 } } };
    const h = encodeScenario(s, "fluss", []);
    expect(h).toBe("v1;j=2025;a=fluss;x=spitzensteuersatz:satz_neu=0.45,vermoegensteuer:ausweich=0.3:satz=0.01");
    const d = decodeScenario(h, fixtureYear, ["vermoegensteuer", "spitzensteuersatz"]);
    expect(d.scenario.steuern).toEqual(s.steuern);
    const u = decodeScenario("v1;j=2025;a=fluss;x=quatsch:a=1,vermoegensteuer:satz=0.02", fixtureYear, ["vermoegensteuer"]);
    expect(u.scenario.steuern).toEqual({ vermoegensteuer: { satz: 0.02 } });
    expect(u.unknownIds).toEqual(["x:quatsch"]);
    expect(encodeScenario(base, "fluss", [])).toBe("v1;j=2025;a=fluss");
  });
});
