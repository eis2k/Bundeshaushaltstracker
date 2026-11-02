import { describe, expect, test } from "vitest";
import type { EmpfaengerIndex } from "../src/lib/model/empfaenger";
import type { PersonIndex } from "../src/lib/model/personen";
import { suche } from "../src/lib/model/suche";
import { fixtureYear } from "./fixtures";

const empf = { stand: "2026-11-01", mit_personen: true, titel: {}, eintraege: [
  { id: "drv", name: "Deutsche Rentenversicherung Bund", art: "oeffentlich", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 400, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11"] },
] } as unknown as EmpfaengerIndex;
const personen: PersonIndex = { stand: "2026-11-02", modus: "relevant", eintraege: [
  { id: "sanae-abdi", name: "Sanae Abdi", funktion_kurz: "Mitglied des Bundestages, SPD", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb"] },
  { id: "timo-reinfrank", name: "Timo Reinfrank", funktion_kurz: "Vorstand", amt: false, sichtbar: false, n_organisationen: 1, shard: "bb", arten: ["gesetzlicher_vertreter"] },
] };

describe("suche", () => {
  test("findet Einzelpläne, Empfänger und sichtbare Akten in dieser Reihenfolge", () => {
    const t = suche("arbeit", fixtureYear, empf, personen);
    expect(t[0]).toMatchObject({ art: "ministerium", id: "11" });
    expect(suche("renten", fixtureYear, empf, personen).find((x) => x.art === "empfaenger")?.id).toBe("drv");
    expect(suche("abdi", fixtureYear, empf, personen)).toEqual([{ art: "person", id: "sanae-abdi", label: "Sanae Abdi", neben: "Mitglied des Bundestages, SPD" }]);
    expect(suche("reinfrank", fixtureYear, empf, personen)).toEqual([]);   // nicht freigeschaltete Akte erscheint nicht
    expect(suche("11", fixtureYear, empf, personen)[0]).toMatchObject({ art: "ministerium", id: "11" });
  });
  test("leere Anfrage und Obergrenze", () => {
    expect(suche("", fixtureYear, empf, personen)).toEqual([]);
    expect(suche("e", fixtureYear, empf, personen, 2).length).toBeLessThanOrEqual(2);
  });
});
