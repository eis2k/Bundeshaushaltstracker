import { describe, expect, test } from "vitest";
import { buildTree, revenueGroups } from "../src/lib/model/tree";
import { fixtureYear, KREDITE, SUM_A_KERN } from "./fixtures";

describe("buildTree", () => {
  test("builds Einzelplan → Kapitel → Titel for Ausgaben only", () => {
    const t = buildTree(fixtureYear, false);
    expect(t.roots.map((r) => r.id).sort()).toEqual(["11", "14", "60"]);
    const epl11 = t.roots.find((r) => r.id === "11")!;
    expect(epl11.label).toBe("Arbeit und Soziales");
    expect(epl11.kind).toBe("epl");
    expect(epl11.soll).toBe(700);
    expect(epl11.children.map((k) => k.id).sort()).toEqual(["11-1101", "11-1102"]);
    const kap1102 = epl11.children.find((k) => k.id === "11-1102")!;
    expect(kap1102.label).toBe("Rentenversicherung");
    expect(kap1102.children.map((c) => c.id)).toEqual(["11-1102-63681", "11-1102-63682"]);
    expect(kap1102.children[0].kind).toBe("titel");
    expect(kap1102.children[0].row?.text).toBe("Zuschuss Rentenversicherung");
    expect(kap1102.ist).toBe(390);
  });

  test("total of roots equals Kern-Ausgaben and negative rows stay", () => {
    const t = buildTree(fixtureYear, false);
    expect(t.roots.reduce((s, r) => s + r.soll, 0)).toBe(SUM_A_KERN);
    expect(t.byId.get("60-6001-97201")?.soll).toBe(-50);
  });

  test("includeSv adds Anlagen-Kapitel flagged sv", () => {
    const without = buildTree(fixtureYear, false);
    expect(without.byId.has("60-6092")).toBe(false);
    const withSv = buildTree(fixtureYear, true);
    const kap = withSv.byId.get("60-6092")!;
    expect(kap.sv).toBe(true);
    expect(kap.soll).toBe(80);
  });
});

describe("revenueGroups", () => {
  test("groups taxes by Gruppierung, separates Sonstige and Kredite", () => {
    const g = revenueGroups(fixtureYear, false);
    const byId = Object.fromEntries(g.map((x) => [x.id, x]));
    expect(byId["E:steuern:011"].label).toBe("Lohnsteuer");
    expect(byId["E:steuern:011"].soll).toBe(300);
    expect(byId["E:steuern:015"].label).toBe("Umsatzsteuer");
    expect(byId["E:steuern:031"].label).toBe("Energiesteuer");
    expect(byId["E:steuern:rest"].soll).toBe(40);
    expect(byId["E:sonstige"].soll).toBe(60);
    expect(byId["E:kredite"].soll).toBe(KREDITE);
    expect(byId["E:kredite"].isKredit).toBe(true);
    expect(g.filter((x) => !x.isKredit).reduce((s, x) => s + x.soll, 0)).toBe(700);
  });

  test("includeSv adds Anlagen revenue to Sonstige", () => {
    const g = revenueGroups(fixtureYear, true);
    expect(g.find((x) => x.id === "E:sonstige")!.soll).toBe(60 + 80);
  });
});
