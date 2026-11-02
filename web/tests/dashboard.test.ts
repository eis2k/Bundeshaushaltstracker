import { describe, expect, test } from "vitest";
import { entwicklungIndex, herkunftVerwendung, kennzahlen } from "../src/lib/model/dashboard";
import type { EmpfaengerIndex } from "../src/lib/model/empfaenger";
import type { PersonIndex } from "../src/lib/model/personen";
import type { YearData } from "../src/lib/model/types";
import type { Zeitreihe } from "../src/lib/model/zeitreihe";
import { fixtureYear } from "./fixtures";

const year2019: YearData = { ...fixtureYear, jahr: 2019, rows: fixtureYear.rows.map((r) => ({ ...r, soll: Math.round(r.soll * 0.8) })) };
const empf = { stand: "", mit_personen: true, titel: {}, eintraege: [{ id: "a", name: "A", art: "verein", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 1, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11"] }] } as unknown as EmpfaengerIndex;
const personen: PersonIndex = { stand: "", modus: "relevant", eintraege: [
  { id: "p", name: "P", funktion_kurz: "MdB", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb"] },
  { id: "q", name: "Q", funktion_kurz: "Vorstand", amt: false, sichtbar: false, n_organisationen: 1, shard: "aa", arten: ["gesetzlicher_vertreter"] },
] };

describe("dashboard", () => {
  test("kennzahlen: Haushalt, Veränderung zum Vorjahr, Zahlen der Register", () => {
    const k = kennzahlen(fixtureYear, year2019, false, {}, empf, personen);
    expect(k.haushalt).toBe(950);
    expect(k.veraenderung).toBeCloseTo((950 - 760) / 760 * 100, 1);
    expect(k.empfaengerMitSeite).toBe(1);
    expect(k.aktenSichtbar).toBe(1);
    expect(kennzahlen(fixtureYear, null, false, {}, null, null).veraenderung).toBeNull();
  });
  test("herkunftVerwendung: Anteile summieren sich zu 100", () => {
    const h = herkunftVerwendung(fixtureYear, false, {});
    const sh = h.herkunft.reduce((s, x) => s + x.anteil, 0);
    const sv = h.verwendung.reduce((s, x) => s + x.anteil, 0);
    expect(Math.abs(sh - 100)).toBeLessThan(0.11);
    expect(Math.abs(sv - 100)).toBeLessThan(0.11);
    expect(h.verwendung.map((x) => x.label)).toContain("Ministerien");
  });
  test("entwicklungIndex: erstes Jahr = 100", () => {
    const z: Zeitreihe = { jahre: [2015, 2016, 2017], titel: {}, kap: {}, epl: {
      "11": { text: "Arbeit", art: "A", soll: [60, 66, 72.6], ist: [null, null, null] },
      "14": { text: "Verteidigung", art: "A", soll: [40, 44, 48.4], ist: [null, null, null] },
      "60": { text: "Steuern", art: "E", soll: [500, 500, 500], ist: [null, null, null] } } };
    const e = entwicklungIndex(z, "soll");
    expect(e.map((x) => x.gesamt)).toEqual([100, 110, 121]);
    expect(e[0].jahr).toBe(2015);
  });
});
