import { describe, expect, test } from "vitest";
import { applyPresets, expandTarget, gesetzStatus } from "../src/lib/model/presets";
import { balance } from "../src/lib/model/scenario";
import type { GesetzFreiMap, Preset, Scenario } from "../src/lib/model/types";
import { fixtureYear } from "./fixtures";

const presets: Preset[] = [
  { id: "rente_halb", name: "Rente halb", beschreibung: "", regeln: [
    { ziel: "11-1102-63681", faktor: 0.5 }, { ziel: "11-1102-63682", faktor: 0.5 }, { ziel: "11-1102-63683", faktor: 0.5 }] },
  { id: "hg5_null", name: "Sachausgaben streichen", beschreibung: "", regeln: [{ ziel: "HG:5", faktor: 0 }] },
  { id: "g681", name: "Gruppe 681", beschreibung: "", regeln: [{ ziel: "G:681", faktor: 1.5 }] },
  { id: "schwarze_null", name: "Schwarze Null", beschreibung: "", regeln: [{ bedingung: "schwarze_null" }] },
];
const gesetz: GesetzFreiMap = {
  "11-1102-63681": { status: "gesetz", grundlage: "§ 213 SGB VI", quelle: "https://x" },
  "32": { status: "gesetz", grundlage: "Kreditverträge", quelle: "https://x" },
};
const base: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };

describe("expandTarget", () => {
  test("HG and G targets expand to titel ids, plain ids pass through", () => {
    expect(expandTarget("HG:5", fixtureYear)).toEqual(["14-1401-55101"]);
    expect(expandTarget("G:681", fixtureYear).sort()).toEqual(["11-1101-68101", "11-1101-68199"]);
    expect(expandTarget("11-1102", fixtureYear).sort()).toEqual(["11-1102-63681", "11-1102-63682"]);  // Kapitel → Titel
    expect(expandTarget("E:steuern:011", fixtureYear)).toEqual(["E:steuern:011"]);
  });
});

describe("gesetzStatus", () => {
  test("resolves titel then parents, default ungeprüft", () => {
    expect(gesetzStatus("11-1102-63681", gesetz)?.status).toBe("gesetz");
    expect(gesetzStatus("32-3205-57501", gesetz)?.grundlage).toBe("Kreditverträge");
    expect(gesetzStatus("14-1401-55101", gesetz)).toBeNull();
  });
});

describe("applyPresets", () => {
  test("a preset sets its targets", () => {
    const { factors } = applyPresets(fixtureYear, { ...base, presets: ["rente_halb"] }, presets, gesetz);
    expect(factors["11-1102-63681"]).toBe(0.5);
    expect(factors["11-1102-63682"]).toBe(0.5);
    expect(factors["11-1102-63683"]).toBe(0.5);
  });

  test("HG target expands to the matching titel", () => {
    const { factors } = applyPresets(fixtureYear, { ...base, presets: ["hg5_null"] }, presets, gesetz);
    expect(factors["14-1401-55101"]).toBe(0);
    expect(balance(fixtureYear, factors, false).ausgaben).toBe(950 - 300);
  });

  test("user factor beats preset", () => {
    const s = { ...base, presets: ["rente_halb"], factors: { "11-1102-63681": 0.8 } };
    const { factors } = applyPresets(fixtureYear, s, presets, gesetz);
    expect(factors["11-1102-63681"]).toBe(0.8);
    expect(factors["11-1102-63682"]).toBe(0.5);
  });

  test("unknown preset ids are ignored", () => {
    const { factors, solver } = applyPresets(fixtureYear, { ...base, presets: ["gibt_es_nicht"] }, presets, gesetz);
    expect(factors).toEqual({});
    expect(solver).toBeNull();
  });

  test("schwarze_null cuts free titel proportionally until balanced, keeps gesetz titel", () => {
    const { factors, solver } = applyPresets(fixtureYear, { ...base, presets: ["schwarze_null"] }, presets, gesetz);
    const b = balance(fixtureYear, factors, false);
    expect(Math.abs(b.neueSchulden)).toBeLessThanOrEqual(3);
    expect(factors["11-1102-63681"]).toBeUndefined();  // gesetz: unverändert
    expect(solver).not.toBeNull();
    expect(solver!.erreichbar).toBe(true);
    // frei: 63682 (100) + 68101 (200) + 68199 (0) + 55101 (300) + 97201 (−50) = 550; Lücke 250
    expect(solver!.faktor).toBeCloseTo(300 / 550, 3);
    expect(solver!.gekuerzt).toBeGreaterThanOrEqual(247);
    expect(solver!.gekuerzt).toBeLessThanOrEqual(253);
  });

  test("schwarze_null leaves individually set titel alone", () => {
    const s = { ...base, presets: ["schwarze_null"], factors: { "14-1401-55101": 1.2 } };
    const { factors } = applyPresets(fixtureYear, s, presets, gesetz);
    expect(factors["14-1401-55101"]).toBe(1.2);
  });

  test("schwarze_null reports unreachable when fixed spending exceeds revenue", () => {
    const s = { ...base, presets: ["schwarze_null"], factors: { "E:steuern": 0.5 } };
    const { factors, solver } = applyPresets(fixtureYear, s, presets, gesetz);
    expect(solver!.erreichbar).toBe(false);
    expect(solver!.faktor).toBe(0);
    expect(balance(fixtureYear, factors, false).ausgaben).toBe(400); // nur der gesetzliche Titel bleibt
  });
});

describe("Vorrang über Ebenen (Review 8)", () => {
  test("a user factor on an Einzelplan beats preset titel factors underneath it", () => {
    const hgPreset: Preset[] = [{ id: "hg5", name: "", beschreibung: "", regeln: [{ ziel: "HG:5", faktor: 0.9 }] }];
    const s = { ...base, presets: ["hg5"], factors: { "14": 1.5 } };
    const { factors } = applyPresets(fixtureYear, s, hgPreset, gesetz);
    expect(factors["14-1401-55101"]).toBeUndefined();   // Preset-Eintrag unter dem Nutzer-Einzelplan entfernt
    expect(factors["14"]).toBe(1.5);
    expect(balance(fixtureYear, factors, false).ausgaben).toBe(950 + 150);
  });

  test("later presets win over earlier ones on the same titel; Einzelplan presets expand to titel", () => {
    const ps: Preset[] = [
      { id: "vert2", name: "", beschreibung: "", regeln: [{ ziel: "14", faktor: 2 }] },
      { id: "hg5", name: "", beschreibung: "", regeln: [{ ziel: "HG:5", faktor: 0.9 }] },
    ];
    const a = applyPresets(fixtureYear, { ...base, presets: ["vert2", "hg5"] }, ps, gesetz).factors;
    expect(a["14-1401-55101"]).toBe(0.9);
    const b = applyPresets(fixtureYear, { ...base, presets: ["hg5", "vert2"] }, ps, gesetz).factors;
    expect(b["14-1401-55101"]).toBe(2);
    expect(b["14"]).toBeUndefined();
  });
});
