import { describe, expect, test } from "vitest";
import { buildSankey } from "../src/lib/views/sankeyData";
import type { Scenario } from "../src/lib/model/types";
import { fixtureYear, KREDITE, SUM_A_KERN } from "./fixtures";
import type { BudgetRow } from "../src/lib/model/types";

const base: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };
const opts = { maxPerColumn: 3 };

describe("buildSankey", () => {
  test("without focus shows revenue, Topf and Einzelpläne (3 columns)", () => {
    const s = buildSankey(fixtureYear, base, {}, [], opts);
    const cols = new Set(s.nodes.map((n) => n.column));
    expect([...cols].sort()).toEqual([0, 1, 2]);
    expect(s.nodes.find((n) => n.id === "topf:bund")).toBeTruthy();
    expect(s.nodes.filter((n) => n.column === 2).map((n) => n.id).sort()).toEqual(["11", "14"]); // Epl 60 hat nur die Minderausgabe, kein Band
  });

  test("links out of the Topf sum to Ausgaben minus Minderausgaben; Kredite node carries neueSchulden", () => {
    const s = buildSankey(fixtureYear, base, {}, [], opts);
    const out = s.links.filter((l) => l.source === "topf:bund").reduce((a, l) => a + l.value, 0);
    expect(s.minderausgaben).toBe(-50);
    expect(out).toBe(SUM_A_KERN + 50);
    const kredite = s.nodes.find((n) => n.id === "E:kredite")!;
    expect(kredite.effective).toBe(KREDITE);
    expect(kredite.isKredit).toBe(true);
    const revenueIn = s.links.filter((l) => l.target === "topf:bund").reduce((a, l) => a + l.value, 0);
    expect(revenueIn).toBe(SUM_A_KERN + 50); // Einnahmen + Kredite + Minderausgaben-Ausgleich = Ausgaben-Bänder
  });

  test("focus on Einzelplan adds Kapitel column, on Kapitel adds Titel column", () => {
    const s1 = buildSankey(fixtureYear, base, {}, ["11"], opts);
    expect(Math.max(...s1.nodes.map((n) => n.column))).toBe(3);
    expect(s1.nodes.filter((n) => n.column === 3).map((n) => n.id).sort()).toEqual(["11-1101", "11-1102"]);
    const s2 = buildSankey(fixtureYear, base, {}, ["11", "11-1102"], opts);
    expect(Math.max(...s2.nodes.map((n) => n.column))).toBe(5);
    expect(s2.nodes.filter((n) => n.column === 4).map((n) => n.id).sort()).toEqual(["11-1102-63681", "11-1102-63682"]);
    expect(s2.nodes.filter((n) => n.column === 5)[0].id).toBe("empfaenger:unbekannt");
  });

  test("non-focused nodes are marked dim", () => {
    const s = buildSankey(fixtureYear, base, {}, ["11"], opts);
    expect(s.nodes.find((n) => n.id === "14")!.dim).toBe(true);
    expect(s.nodes.find((n) => n.id === "11")!.dim).toBe(false);
  });

  test("ghost for halved titel equals half its soll, node marked changed", () => {
    const factors = { "11-1102-63681": 0.5 };
    const s = buildSankey(fixtureYear, base, factors, ["11", "11-1102"], opts);
    const g = s.ghosts.find((g) => g.id === "11-1102-63681")!;
    expect(g.diff).toBe(200);
    const n = s.nodes.find((n) => n.id === "11-1102-63681")!;
    expect(n.changed).toBe(true);
    expect(n.original).toBe(400);
    expect(n.effective).toBe(200);
    expect(s.nodes.find((n) => n.id === "11")!.changed).toBe(true);
  });

  test("titel with value 0 creates no link; 'Alle anderen' aggregates the rest", () => {
    const s = buildSankey(fixtureYear, base, {}, ["11", "11-1101"], opts);
    expect(s.links.find((l) => l.target === "11-1101-68199")).toBeUndefined();
    const s2 = buildSankey(fixtureYear, base, {}, [], { maxPerColumn: 1 });
    const rest = s2.nodes.find((n) => n.id === "rest:2")!;
    expect(rest.label).toBe("Alle anderen");
    expect(rest.effective).toBe(300); // Epl 14 (300) + Epl 60 (nur Minderausgabe, zählt nicht)
    const col2 = s2.nodes.filter((n) => n.column === 2);
    expect(col2.map((n) => n.id).sort()).toEqual(["11", "rest:2"]);
    expect(s2.links.find((l) => l.target === "rest:2")!.value).toBe(300);
  });

  test("revenue factor changes revenue node and Kredite node", () => {
    const s = buildSankey(fixtureYear, base, { "E:steuern:011": 1.5 }, [], opts);
    const lohn = s.nodes.find((n) => n.id === "E:steuern:011")!;
    expect(lohn.effective).toBe(450);
    expect(lohn.changed).toBe(true);
    expect(s.nodes.find((n) => n.id === "E:kredite")!.effective).toBe(KREDITE - 150);
  });
});

describe("negative revenue titles (EU-Eigenmittel, Länderanteile)", () => {
  const abzug: BudgetRow = { id: "60-6001-02202", art: "E", epl: "60", kap: "6001", titel: "02202", text: "BNE-Eigenmittel der EU", fkt: "000", flex: null, tgr: null, soll: -30, ist: null, sv: false };
  const withAbzug = { ...fixtureYear, rows: [...fixtureYear.rows, abzug] };
  test("appear as an outflow node 'abzuege' so the Topf stays balanced", () => {
    const s = buildSankey(withAbzug, base, {}, [], opts);
    const node = s.nodes.find((n) => n.id === "abzuege")!;
    expect(node.column).toBe(2);
    expect(node.effective).toBe(30);
    expect(s.links.find((l) => l.source === "topf:bund" && l.target === "abzuege")!.value).toBe(30);
    const into = s.links.filter((l) => l.target === "topf:bund").reduce((a, l) => a + l.value, 0);
    const out = s.links.filter((l) => l.source === "topf:bund").reduce((a, l) => a + l.value, 0);
    expect(into).toBe(out);
    expect(s.nodes.find((n) => n.id === "E:kredite")!.effective).toBe(KREDITE + 30);
  });
  test("no abzuege node when there are no negative revenue titles", () => {
    expect(buildSankey(fixtureYear, base, {}, [], opts).nodes.find((n) => n.id === "abzuege")).toBeUndefined();
  });
});
