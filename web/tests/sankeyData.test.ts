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

  test("links out of the Topf sum to the positive Ausgaben; Minderausgaben are reported, not drawn as a band", () => {
    const s = buildSankey(fixtureYear, base, {}, [], opts);
    const out = s.links.filter((l) => l.source === "topf:bund").reduce((a, l) => a + l.value, 0);
    expect(s.minderausgaben).toBe(-50);
    expect(s.absetzungen).toBe(0);
    expect(out).toBe(SUM_A_KERN + 50);
    expect(s.nodes.find((n) => n.id === "minderausgabe")).toBeUndefined();
    const kredite = s.nodes.find((n) => n.id === "E:kredite")!;
    expect(kredite.effective).toBe(KREDITE);
    expect(kredite.isKredit).toBe(true);
    const revenueIn = s.links.filter((l) => l.target === "topf:bund").reduce((a, l) => a + l.value, 0);
    expect(revenueIn).toBe(SUM_A_KERN); // Einnahmen + Kredite = Netto-Ausgaben; der Topf wird nach Abflüssen bemessen
  });

  test("negative Ausgabentitel outside Gruppe 97x count as Absetzungen, negative Einnahmen der Gruppe 37x as Mindereinnahmen", () => {
    const data = { ...fixtureYear, rows: [
      ...fixtureYear.rows,
      { id: "32-3205-57509", art: "A" as const, epl: "32", kap: "3205", titel: "57509", text: "Disagio", fkt: "000", flex: null, tgr: null, soll: -40, ist: null, sv: false },
      { id: "60-6002-37203", art: "E" as const, epl: "60", kap: "6002", titel: "37203", text: "Globale Mindereinnahme", fkt: "000", flex: null, tgr: null, soll: -25, ist: null, sv: false },
      { id: "60-6001-02202", art: "E" as const, epl: "60", kap: "6001", titel: "02202", text: "BNE-Eigenmittel", fkt: "000", flex: null, tgr: null, soll: -30, ist: null, sv: false },
    ] };
    const s = buildSankey(data, base, {}, [], opts);
    expect(s.minderausgaben).toBe(-50);
    expect(s.absetzungen).toBe(-40);
    expect(s.nodes.find((n) => n.id === "abzuege")!.effective).toBe(30);
    expect(s.nodes.find((n) => n.id === "mindereinnahmen")!.effective).toBe(25);
    expect(s.nodes.find((n) => n.id === "mindereinnahmen")!.column).toBe(2);
  });

  test("a node set to 0 % stays visible with a ghost of its original size", () => {
    const s = buildSankey(fixtureYear, base, { "14": 0 }, [], opts);
    const n = s.nodes.find((n) => n.id === "14")!;
    expect(n.effective).toBe(0);
    expect(n.changed).toBe(true);
    expect(s.ghosts.find((g) => g.id === "14")!.diff).toBe(300);
    expect(s.links.find((l) => l.target === "14")).toBeUndefined();
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
    expect(out - into).toBe(50);   // Differenz = Globale Minderausgaben, die nicht als Band gezeichnet werden
    expect(s.nodes.find((n) => n.id === "E:kredite")!.effective).toBe(KREDITE + 30);
  });
  test("no abzuege node when there are no negative revenue titles", () => {
    expect(buildSankey(fixtureYear, base, {}, [], opts).nodes.find((n) => n.id === "abzuege")).toBeUndefined();
  });
});

describe("Modell-Einnahmen aus Steuer-Szenarien (Stufe 1b)", () => {
  test("active scenarios appear as dashed inflow nodes with the Bund share as band; Länder taxes show a label-only node", () => {
    const modelle = [
      { id: "spitzensteuersatz", kurz: "Spitzensteuersatz", gesamt: 14_000_000_000, bund: 5_950_000_000, empfaenger: "gemeinsam" as const },
      { id: "vermoegensteuer", kurz: "Vermögensteuer", gesamt: 29_400_000_000, bund: 0, empfaenger: "laender" as const },
    ];
    const s = buildSankey(fixtureYear, base, {}, [], { ...opts, modelle });
    const sp = s.nodes.find((n) => n.id === "x:spitzensteuersatz")!;
    expect(sp.column).toBe(0);
    expect(sp.kind).toBe("modell");
    expect(sp.effective).toBe(5_950_000_000);
    expect(sp.netEffective).toBe(14_000_000_000);
    expect(s.links.find((l) => l.source === "x:spitzensteuersatz")!.value).toBe(5_950_000_000);
    const vm = s.nodes.find((n) => n.id === "x:vermoegensteuer")!;
    expect(vm.effective).toBe(0);
    expect(vm.netEffective).toBe(29_400_000_000);
    expect(s.links.find((l) => l.source === "x:vermoegensteuer")).toBeUndefined();
    // Knotenhöhe = Gesamtaufkommen (d3 fixedValue), Band = Bund-Anteil; der Rest des Knotens bleibt leer (Länder)
    expect(vm.fixedValue).toBe(29_400_000_000);
    expect(sp.fixedValue).toBe(14_000_000_000);
    expect(s.ghosts.find((g) => g.id === "x:vermoegensteuer")).toBeUndefined();
    // Kredite-Knoten sinkt um den Bund-Anteil
    expect(s.nodes.find((n) => n.id === "E:kredite")!.effective).toBe(KREDITE - 5_950_000_000);
  });
});
