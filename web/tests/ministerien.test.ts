import { describe, expect, test } from "vitest";
import { ministerien } from "../src/lib/model/ministerien";
import type { PersonIndex } from "../src/lib/model/personen";
import { fixtureYear } from "./fixtures";

const personen: PersonIndex = { stand: "2026-11-02", modus: "relevant", eintraege: [
  { id: "a-b", name: "A B", funktion_kurz: "Bundesministerin für Arbeit und Soziales", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: ["11"] },
  { id: "c-d", name: "C D", funktion_kurz: "Mitglied des Bundestages", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb", "regierung"], epl_leitung: ["11"] },
  { id: "e-f", name: "E F", funktion_kurz: "Vorstand", amt: false, sichtbar: false, n_organisationen: 1, shard: "ab", arten: ["gesetzlicher_vertreter"], epl_leitung: [] },
] };
const empfaenger = { stand: "2026-11-01", mit_personen: true, titel: {}, eintraege: [
  { id: "x", name: "X", art: "verein", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 0, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11", "14"] },
  { id: "y", name: "Y", art: "verein", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 0, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11"] },
] };

describe("ministerien", () => {
  test("je Einzelplan Name, Ausgaben, Leitung und Zahl der Empfänger, nach Ausgaben sortiert", () => {
    const m = ministerien(fixtureYear, "soll", personen, empfaenger as never);
    const e11 = m.find((x) => x.epl === "11")!;
    expect(e11.name).toBe("Arbeit und Soziales");
    expect(e11.ausgaben).toBe(fixtureYear.rows.filter((r) => r.epl === "11" && r.art === "A").reduce((s, r) => s + r.soll, 0));
    expect(e11.leitung.map((l) => l.id)).toEqual(["a-b", "c-d"]);
    expect(e11.empfaenger).toBe(2);
    expect(m.find((x) => x.epl === "14")!.empfaenger).toBe(1);
    expect(m.find((x) => x.epl === "14")!.leitung).toEqual([]);
    expect(m.map((x) => x.ausgaben)).toEqual([...m.map((x) => x.ausgaben)].sort((a, b) => b - a));
  });
  test("Ist-Modus nutzt Ist-Werte, wo vorhanden", () => {
    const m = ministerien(fixtureYear, "ist", personen, empfaenger as never);
    const e11 = m.find((x) => x.epl === "11")!;
    expect(e11.ausgaben).toBe(fixtureYear.rows.filter((r) => r.epl === "11" && r.art === "A").reduce((s, r) => s + (r.ist ?? r.soll), 0));
  });
});
