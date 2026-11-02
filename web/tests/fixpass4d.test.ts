import { describe, expect, test } from "vitest";
import { entwicklungIndex, herkunftVerwendung } from "../src/lib/model/dashboard";
import { ministerien, ministerienTabelle } from "../src/lib/model/ministerien";
import type { PersonIndex } from "../src/lib/model/personen";
import { quellenTabelle } from "../src/lib/model/quellen";
import { ringFarben } from "../src/lib/model/bereiche";
import type { YearData } from "../src/lib/model/types";
import type { Zeitreihe } from "../src/lib/model/zeitreihe";
import { fixtureYear } from "./fixtures";

describe("Fix-Pass 4d", () => {
  test("C1: Tabellenänderung nominal Soll gegen Soll, auch wenn die Ansicht Ist oder Preise zeigt", () => {
    const ansichtIst: YearData = { ...fixtureYear, rows: fixtureYear.rows.map((r) => ({ ...r, soll: r.ist ?? r.soll })) };
    const liste = ministerien(ansichtIst, "ist", false, 2025, 2025, null, null);
    const vorjahr: YearData = { ...fixtureYear, jahr: 2024, rows: fixtureYear.rows.map((r) => ({ ...r, soll: Math.round(r.soll * 0.8) })) };
    const t = ministerienTabelle(liste, fixtureYear, vorjahr, false);
    expect(t.find((x) => x.epl === "11")?.veraenderung).toBe(25);   // 700 gegen 560, nicht das Ist (690) gegen 560
  });
  test("I3: Steuer-Modelle erscheinen als eigener Posten der Herkunft, Anteile 100", () => {
    const h = herkunftVerwendung(fixtureYear, false, {}, 100);
    const modell = h.herkunft.find((p) => p.id === "modell")!;
    expect(modell.wert).toBe(100);
    expect(modell.label).toContain("Modell");
    expect(Math.abs(h.herkunft.reduce((s, x) => s + x.anteil, 0) - 100)).toBeLessThan(0.2);
    expect(h.herkunft.reduce((s, x) => s + x.wert, 0)).toBeCloseTo(h.verwendung.reduce((s, x) => s + x.wert, 0), 3);
    expect(herkunftVerwendung(fixtureYear, false, {}).herkunft.some((p) => p.id === "modell")).toBe(false);
  });
  test("I4: Sozialkassen-Zeile mit Jahren des Haushalts, Sondervermögen in der Haushaltszeile", () => {
    const t = quellenTabelle({ index: { jahre: [2015, 2026], ist_bis: 2025, sv_jahre: [2015, 2023, 2026], summen: {}, erzeugt: "2026-11-02T00:00:00+00:00" }, empfaenger: null, personen: null, vpi: null, steuern: 0, texte: null });
    const sk = t.find((z) => z.quelle.startsWith("Sozialkassen"))!;
    expect(sk.zeitraum).toBe("2015–2026");
    expect(sk.quelle).toMatch(/DRV/);
    expect(sk.datei).toBe("/data/sozialkassen/2026.json");
    expect(t[0].inhalt).toContain("Sondervermögen");
  });
  test("I5: Ringfarben ohne Doppelungen", () => {
    const f = ringFarben(["12", "60", "06", "30", "14", "32", null]);
    expect(new Set(f).size).toBe(7);
  });
  test("I6: amtierende undatierte Person vor der ausgeschiedenen datierten", () => {
    const personen: PersonIndex = { stand: "", modus: "relevant", eintraege: [
      { id: "alt", name: "Alt A", funktion_kurz: "", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesministerin", seit: "2021-12-08", bis: "2025-05-06" }] },
      { id: "neu", name: "Neu N", funktion_kurz: "", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["regierung"], epl_leitung: [{ epl: "11", amt: "Bundesminister", seit: null, bis: null }] },
    ] };
    const e11 = ministerien(fixtureYear, "soll", false, 2025, 2025, personen, null).find((x) => x.epl === "11")!;
    expect(e11.leitung.map((l) => l.id)).toEqual(["neu", "alt"]);
  });
  test("M1: Stand der Erklärtexte aus den Texten, Steuer-Modelle ohne eigenen Stand", () => {
    const t = quellenTabelle({ index: null, empfaenger: null, personen: null, vpi: null, steuern: 3, texte: { a: { text: "", quelle: [], stand: "2026-11-01" }, b: { text: "", quelle: [], stand: "2026-10-01" } } });
    expect(t.find((z) => z.quelle === "Erklärtexte")?.stand).toBe("2026-11-01");
    expect(t.find((z) => /Steuer-Modelle/.test(z.quelle))?.stand).toBeNull();
  });
  test("M4: Ist nicht mit Soll gemischt, auch bei Investitionen", () => {
    const z: Zeitreihe = { jahre: [2015, 2016], kap: {}, epl: { "11": { text: "A", art: "A", soll: [60, 66], ist: [60, null] } },
      titel: { "12-1201-74101": { text: "Bau", epl: "12", kap: "1201", art: "A", soll: [10, 11], ist: [10, null] } } };
    const e = entwicklungIndex(z, "ist");
    expect(e[1].gesamt).toBeNull();
    expect(e[1].investitionen).toBeNull();
  });
});
