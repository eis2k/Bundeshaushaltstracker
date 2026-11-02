import { describe, expect, test } from "vitest";
import { entwicklungIndex, herkunftVerwendung, kennzahlen } from "../src/lib/model/dashboard";
import { balance } from "../src/lib/model/scenario";
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

describe("kennzahlen: Veränderung zum Vorjahr (Review I4)", () => {
  test("ohne Faktoren, aus den Rohdaten, auch wenn die Ansicht Faktoren trägt", () => {
    const mit = kennzahlen(fixtureYear, year2019, false, { "11": 1.5 }, empf, personen);
    const ohne = kennzahlen(fixtureYear, year2019, false, {}, empf, personen);
    expect(mit.haushalt).toBeGreaterThan(ohne.haushalt);
    expect(mit.veraenderung).toBe(ohne.veraenderung);
  });
  test("Rohdaten der Ansicht können getrennt übergeben werden (Ist- oder Preisansicht)", () => {
    const ansicht = { ...fixtureYear, rows: fixtureYear.rows.map((r) => ({ ...r, soll: r.soll * 2 })) };
    const k = kennzahlen(ansicht, year2019, false, {}, empf, personen, fixtureYear);
    expect(k.haushalt).toBe(2 * kennzahlen(fixtureYear, year2019, false, {}, empf, personen).haushalt);
    expect(k.veraenderung).toBe(kennzahlen(fixtureYear, year2019, false, {}, empf, personen).veraenderung);
  });
});

describe("Stufe 4d: Dashboard-Grundlagen", () => {
  const z: Zeitreihe = { jahre: [2015, 2016, 2017], kap: {}, epl: {
    "11": { text: "A", art: "A", soll: [60, 66, 72.6], ist: [60, 66, 72.6] },
  }, titel: {
    "11-1101-68101": { text: "Bürgergeld", epl: "11", kap: "1101", art: "A", soll: [50, 55, 60], ist: [50, null, 60] },
    "12-1201-74101": { text: "Bau", epl: "12", kap: "1201", art: "A", soll: [10, 11, 12.1], ist: [10, 11, 12] },
    "12-1201-89101": { text: "Investitionszuschuss", epl: "12", kap: "1201", art: "A", soll: [10, 11, 12.1], ist: [10, 11, 12] },
    "60-6001-01101": { text: "Lohnsteuer", epl: "60", kap: "6001", art: "E", soll: [100, 100, 100], ist: [100, 100, 100] },
  } };
  test("entwicklungIndex: Investitionen aus Hauptgruppen 7 und 8 als Index", () => {
    const e = entwicklungIndex(z, "soll");
    expect(e.map((x) => x.investitionen)).toEqual([100, 110, 121]);
  });
  test("entwicklungIndex: Ist nicht mit Soll gemischt", () => {
    const e = entwicklungIndex(z, "ist");
    expect(e[1].investitionen).toBe(110);
    expect(e[0].gesamt).toBe(100);
  });
  test("kennzahlen: Einnahmen und Haushalt wie der Seitenkopf inklusive Steuer-Modelle", () => {
    const ohne = kennzahlen(fixtureYear, null, false, {}, null, null);
    const mit = kennzahlen(fixtureYear, null, false, {}, null, null, fixtureYear, 100);
    expect(mit.einnahmen).toBe(ohne.einnahmen + 100);
  });
  test("herkunftVerwendung: Kredite aus der Bilanz des Szenarios", () => {
    const h = herkunftVerwendung(fixtureYear, false, { "11": 0.5 });
    const kredit = h.herkunft.find((p) => p.id === "E:kredite")!;
    expect(kredit.wert).toBeCloseTo(balance(fixtureYear, { "11": 0.5 }, false).neueSchulden, 3);
    expect(Math.abs(h.herkunft.reduce((s, x) => s + x.anteil, 0) - 100)).toBeLessThan(0.2);
  });
});
