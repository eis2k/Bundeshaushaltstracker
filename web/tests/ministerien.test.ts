import { describe, expect, test } from "vitest";
import { ministerien } from "../src/lib/model/ministerien";
import type { PersonIndex } from "../src/lib/model/personen";
import { includeRow } from "../src/lib/model/tree";
import type { YearData } from "../src/lib/model/types";
import { fixtureYear } from "./fixtures";

const personen: PersonIndex = { stand: "2026-11-02", modus: "relevant", eintraege: [
  { id: "c-d", name: "C D", funktion_kurz: "Mitglied des Bundestages", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb", "regierung"], epl_leitung: [{ epl: "11", amt: "Parlamentarische Staatssekretärin", seit: "2025-05-06", bis: null }] },
  { id: "a-b", name: "A B", funktion_kurz: "Bundesministerin für Arbeit und Soziales", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesministerin für Arbeit und Soziales", seit: "2025-05-06", bis: null }] },
  { id: "g-h", name: "G H", funktion_kurz: "Bundesminister für Arbeit und Soziales", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesminister für Arbeit und Soziales", seit: "2021-12-08", bis: "2025-05-06" }] },
  { id: "i-j", name: "I J", funktion_kurz: "Bundesminister der Verteidigung", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "14", amt: "Bundesminister der Verteidigung", seit: null, bis: null }] },
  { id: "e-f", name: "E F", funktion_kurz: "Vorstand", amt: false, sichtbar: false, n_organisationen: 1, shard: "ab", arten: ["gesetzlicher_vertreter"], epl_leitung: [] },
] };
const empfaenger = { stand: "2026-11-01", mit_personen: true, titel: {}, eintraege: [
  { id: "x", name: "X", art: "verein", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 0, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11", "14"] },
  { id: "y", name: "Y", art: "verein", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 0, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11"] },
] };
const daten: YearData = { ...fixtureYear, rows: [...fixtureYear.rows,
  { ...fixtureYear.rows[0], id: "11-1190-99901", kap: "1190", titel: "99901", soll: 100, ist: null, sv: true, text: "Sondervermögen" },
  { ...fixtureYear.rows[0], id: "11-1191-99902", kap: "1191", titel: "99902", soll: 50, ist: null, sv: false, transfer: true, text: "Zuführung an Sondervermögen" }] };

describe("ministerien", () => {
  test("Ausgaben wie im Fluss (Sondervermögen und Transfers nach includeRow), sortiert", () => {
    const m = ministerien(daten, "soll", false, 2025, 2025, personen, empfaenger as never);
    const e11 = m.find((x) => x.epl === "11")!;
    expect(e11.ausgaben).toBe(daten.rows.filter((r) => r.epl === "11" && r.art === "A" && includeRow(r, false)).reduce((s, r) => s + r.soll, 0));
    const mitSv = ministerien(daten, "soll", true, 2025, 2025, personen, empfaenger as never).find((x) => x.epl === "11")!;
    expect(mitSv.ausgaben).toBe(daten.rows.filter((r) => r.epl === "11" && r.art === "A" && includeRow(r, true)).reduce((s, r) => s + r.soll, 0));
    expect(m.map((x) => x.ausgaben)).toEqual([...m.map((x) => x.ausgaben)].sort((a, b) => b - a));
    expect(e11.empfaenger).toBe(2);
  });
  test("Leitung nur im Zeitraum des Amtes, Ministerin vor Staatssekretärin, mit Amt", () => {
    const e11 = ministerien(daten, "soll", false, 2025, 2025, personen, empfaenger as never).find((x) => x.epl === "11")!;
    expect(e11.leitung.map((l) => l.id)).toEqual(["a-b", "g-h", "c-d"]);   // Übergabejahr: Vorgänger bis 6.5. und Nachfolgerin ab 6.5. gehören beide zu 2025
    expect(e11.leitung[0].amt).toBe("Bundesministerin für Arbeit und Soziales");
    const alt = ministerien(daten, "soll", false, 2023, 2025, personen, empfaenger as never).find((x) => x.epl === "11")!;
    expect(alt.leitung.map((l) => l.id)).toEqual(["g-h"]);
    const frueh = ministerien(daten, "soll", false, 2019, 2025, personen, empfaenger as never).find((x) => x.epl === "11")!;
    expect(frueh.leitung).toEqual([]);
    expect(frueh.leitungHinweis).toBe("Leitung für 2019 nicht erfasst");
  });
  test("ohne belegtes Ernennungsdatum nur im aktuellen Jahr, mit Hinweis", () => {
    const heute = ministerien(daten, "soll", false, 2025, 2025, personen, empfaenger as never).find((x) => x.epl === "14")!;
    expect(heute.leitung.map((l) => l.id)).toEqual(["i-j"]);
    expect(heute.leitungHinweis).toBe("Ernennungsdatum nicht belegt; Stand des Kabinettsabrufs");
    const alt = ministerien(daten, "soll", false, 2024, 2025, personen, empfaenger as never).find((x) => x.epl === "14")!;
    expect(alt.leitung).toEqual([]);
  });
});
