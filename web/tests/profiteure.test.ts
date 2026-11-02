import { describe, expect, test } from "vitest";
import type { EmpfaengerIndex } from "../src/lib/model/empfaenger";
import type { PersonIndex } from "../src/lib/model/personen";
import { topEmpfaenger, verantwortung } from "../src/lib/model/profiteure";
import type { Scenario } from "../src/lib/model/types";
import { buildSankey } from "../src/lib/views/sankeyData";
import { fixtureYear } from "./fixtures";

const e = (id: string, name: string, epls: string[], haushalt: number, lobby: number) =>
  ({ id, name, art: "verein_stiftung", rechtsform: "", sitz: "", lobby_untergrenze_bund: lobby, haushalt_soll_letztes_jahr: haushalt, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls }) as EmpfaengerIndex["eintraege"][number];
const index: EmpfaengerIndex = { stand: "", mit_personen: true, titel: {}, eintraege: [
  e("drv", "Deutsche Rentenversicherung", ["11"], 500, 0),
  e("lobby", "Verband X", ["11"], 0, 120),
  e("klein", "Verein Y", ["11"], 20, 900),
  e("bw", "Bundeswehr-Verband", ["14"], 0, 50),
] };
const personen: PersonIndex = { stand: "", modus: "relevant", eintraege: [
  { id: "a-b", name: "A B", funktion_kurz: "Bundesministerin", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesministerin für Arbeit und Soziales", seit: "2025-05-06", bis: null }] },
  { id: "g-h", name: "G H", funktion_kurz: "Bundesminister", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesminister für Arbeit und Soziales", seit: "2021-12-08", bis: "2025-05-06" }] },
] };

describe("profiteure", () => {
  test("topEmpfaenger: nur Empfänger des Einzelplans, Haushalt vor Lobbyregister, Quelle gesetzt", () => {
    const t = topEmpfaenger("11", 2025, index);
    expect(t.map((x) => x.id)).toEqual(["drv", "klein", "lobby"]);
    expect(t[0]).toMatchObject({ wert: 500, quelle: "haushalt" });
    expect(t[2]).toMatchObject({ wert: 120, quelle: "lobbyregister" });
  });
  test("topEmpfaenger: ohne Einzelplan alle, begrenzt durch max", () => {
    expect(topEmpfaenger(null, 2025, index, 2)).toHaveLength(2);
    expect(topEmpfaenger("11", 2025, null)).toEqual([]);
  });
  test("verantwortung: Leitung aus dem Zeitraum, Haushalt und Anteil", () => {
    const v = verantwortung("11", 2025, 2025, fixtureYear, false, personen)!;
    expect(v.epl).toBe("11");
    expect(v.leitung.map((l) => l.id)).toEqual(["a-b", "g-h"]); // beide im Jahr 2025 im Amt (Wechsel im Mai), Ministerin vor Vorgänger
    expect(v.haushalt).toBe(700);
    expect(v.anteil).toBeCloseTo((700 / 950) * 100, 1);
  });
  test("verantwortung: ohne Einzelplan der größte", () => {
    expect(verantwortung(null, 2025, 2025, fixtureYear, false, personen)?.epl).toBe("11");
    expect(verantwortung("99", 2025, 2025, fixtureYear, false, personen)).toBeNull();
  });
});

describe("buildSankey mit Empfänger-Spalte", () => {
  const base: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };
  test("Fokus auf Einzelplan hängt Empfänger-Knoten mit Kante vom Einzelplan an", () => {
    const spalte = [{ id: "drv", name: "Deutsche Rentenversicherung", wert: 500, quelle: "haushalt" }];
    const s = buildSankey(fixtureYear, base, {}, ["11"], { maxPerColumn: 3 }, spalte);
    const n = s.nodes.find((x) => x.id === "empfaenger:drv");
    expect(n?.kind).toBe("empfaenger");
    expect(s.links.some((l) => l.source === "11" && l.target === "empfaenger:drv" && l.value === 500)).toBe(true);
    expect(s.links.find((l) => l.target === "empfaenger:drv")?.quelle).toBe("haushalt");
  });
  test("ohne Fokus keine Empfänger-Spalte", () => {
    const s = buildSankey(fixtureYear, base, {}, [], { maxPerColumn: 3 }, [{ id: "drv", name: "DRV", wert: 500, quelle: "haushalt" }]);
    expect(s.nodes.some((x) => x.id === "empfaenger:drv")).toBe(false);
  });
});
