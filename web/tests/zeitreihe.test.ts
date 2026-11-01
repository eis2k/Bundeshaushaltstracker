import { describe, expect, test } from "vitest";
import { deflate, rankGrowth, type Zeitreihe } from "../src/lib/model/zeitreihe";

const z: Zeitreihe = {
  jahre: [2015, 2020, 2025],
  titel: {
    "11-1102-63681": { text: "Zuschuss Rentenversicherung", epl: "11", kap: "1102", art: "A", sv: false, soll: [800, 900, 1000], ist: [790, 880, null] },
    "17-1710-68404": { text: "Zuwendungen an Verbände", epl: "17", kap: "1710", art: "A", sv: false, soll: [100, 200, 400], ist: [100, 190, null] },
    "14-1403-42301": { text: "Bezüge Soldaten", epl: "14", kap: "1403", art: "A", sv: false, soll: [300, 320, 330], ist: [300, 320, null] },
    "60-6002-68309": { text: "Strompreisentlastung", epl: "60", kap: "6002", art: "A", sv: false, soll: [null, null, 172], ist: [null, null, null] },
    "12-1202-83101": { text: "Eigenkapital Bahn", epl: "12", kap: "1202", art: "A", sv: false, soll: [50, 60, 20], ist: [50, 60, null] },
    "60-6001-01101": { text: "Lohnsteuer", epl: "60", kap: "6001", art: "E", sv: false, soll: [500, 600, 700], ist: [500, 600, null] },
    "60-6092-89310": { text: "KTF Förderung", epl: "60", kap: "6092", art: "A", sv: true, soll: [10, 20, 30], ist: [null, null, null] },
  },
  kap: { "11-1102": { text: "Rentenversicherung", epl: "11", art: "A", soll: [800, 900, 1000], ist: [790, 880, null] } },
  epl: { "11": { text: "Arbeit und Soziales", art: "A", soll: [800, 900, 1000], ist: [790, 880, null] } },
};
const vpi = { 2015: 90, 2020: 100, 2025: 120 };
const base = { von: 2015, bis: 2025, ebene: "titel" as const, stand: "soll" as const, sort: "pct" as const, filter: "alle" as const, real: false };

describe("rankGrowth", () => {
  test("ranks Ausgabentitel by percent growth, 'neu' when start is 0 or missing", () => {
    const rows = rankGrowth(z, base);
    expect(rows.map((r) => r.id)).toEqual(["17-1710-68404", "11-1102-63681", "14-1403-42301", "12-1202-83101", "60-6002-68309"]);
    const neu = rows[4];
    expect(neu.pct).toBeNull();
    expect(neu.neu).toBe(true);
    expect(rows[0].pct).toBeCloseTo(3, 5);           // 100 → 400 = +300 %
    expect(rows[0].abs).toBe(300);
    expect(rows[0].verlauf).toEqual([100, 200, 400]);
    expect(rows.find((r) => r.id === "60-6001-01101")).toBeUndefined();  // Einnahmen nicht in der Ausgaben-Rangliste
    expect(rows.find((r) => r.id === "60-6092-89310")).toBeUndefined();  // Anlagen ohne includeSv nicht
  });

  test("sort by absolute growth", () => {
    const rows = rankGrowth(z, { ...base, sort: "abs" });
    expect(rows.map((r) => r.id).slice(0, 2)).toEqual(["17-1710-68404", "11-1102-63681"]);
  });

  test("filters: zuwendungen, personal, geschrumpft, neu", () => {
    expect(rankGrowth(z, { ...base, filter: "zuwendungen" }).map((r) => r.id).sort()).toEqual(["11-1102-63681", "17-1710-68404", "60-6002-68309"]);
    expect(rankGrowth(z, { ...base, filter: "personal" }).map((r) => r.id)).toEqual(["14-1403-42301"]);
    expect(rankGrowth(z, { ...base, filter: "geschrumpft" }).map((r) => r.id)).toEqual(["12-1202-83101"]);
    expect(rankGrowth(z, { ...base, filter: "neu" }).map((r) => r.id)).toEqual(["60-6002-68309"]);
  });

  test("zuwendungen filter keeps Gruppen 6xx und 8xx Zuschüsse only", () => {
    const ids = rankGrowth(z, { ...base, filter: "zuwendungen", sort: "abs" }).map((r) => r.id);
    expect(ids).toContain("17-1710-68404");   // 684
    expect(ids).toContain("11-1102-63681");   // 636
    expect(ids).toContain("60-6002-68309");   // 683
    expect(ids).not.toContain("14-1403-42301");
    expect(ids).not.toContain("12-1202-83101"); // 831 Beteiligungen sind keine Zuwendung
  });

  test("stand ist uses Ist values and stops at the last year with Ist", () => {
    const rows = rankGrowth(z, { ...base, stand: "ist", bis: 2020 });
    const r = rows.find((r) => r.id === "11-1102-63681")!;
    expect(r.von).toBe(790);
    expect(r.bis).toBe(880);
  });

  test("real growth deflates to prices of the end year", () => {
    const rows = rankGrowth(z, { ...base, real: true, vpi });
    const r = rows.find((r) => r.id === "11-1102-63681")!;
    expect(r.von).toBeCloseTo(800 * 120 / 90, 5);
    expect(r.bis).toBe(1000);
    expect(deflate(800, 2015, 2025, vpi)).toBeCloseTo(1066.6667, 3);
  });

  test("ebene kap and epl use the aggregated series", () => {
    expect(rankGrowth(z, { ...base, ebene: "kap" })[0].id).toBe("11-1102");
    expect(rankGrowth(z, { ...base, ebene: "epl" })[0].text).toBe("Arbeit und Soziales");
  });

  test("min drops rows whose start and end are both below the threshold", () => {
    const ids = rankGrowth(z, { ...base, min: 100 }).map((r) => r.id);
    expect(ids).not.toContain("12-1202-83101");   // 50 → 20
    expect(ids).toContain("60-6002-68309");       // neu, 172 ≥ 100
    expect(ids).toContain("17-1710-68404");
  });

  test("min drops rows whose start and end are both below the threshold", () => {
    const ids = rankGrowth(z, { ...base, min: 100 }).map((r) => r.id);
    expect(ids).not.toContain("12-1202-83101");   // 50 → 20
    expect(ids).toContain("60-6002-68309");       // neu, 172 ≥ 100
    expect(ids).toContain("17-1710-68404");
  });

  test("includeSv adds Anlagen", () => {
    expect(rankGrowth(z, { ...base, includeSv: true }).find((r) => r.id === "60-6092-89310")).toBeTruthy();
  });
});
