import { describe, expect, test } from "vitest";
import { aktuellesGlied, pfad, type Glied, type GliedEingabe } from "../src/lib/model/pfad";

const leer: GliedEingabe = { view: "fluss", topf: "bund", focus: [], selected: null, eplNamen: {}, titelNamen: {}, topfNamen: { gesamt: "Gesamtfluss", bund: "Bund" }, empfaengerId: null, empfaengerName: null, empfaengerFilterEpl: null, akteId: null, akteName: null, netzStart: null, netzLabel: null };

describe("aktuellesGlied", () => {
  test("im Haushalt nennt Topf, Einzelplan und Titel", () => {
    const g = aktuellesGlied({ ...leer, focus: ["11"], selected: "11-1102-63681", eplNamen: { "11": "Arbeit und Soziales" }, titelNamen: { "11-1102-63681": "Zuschuss Rente" } });
    expect(g.label).toBe("Bund › Einzelplan 11 Arbeit und Soziales › Zuschuss Rente");
    expect(g.ziel).toEqual({ art: "haushalt", view: "fluss", topf: "bund", focus: ["11"] });
  });
  test("Gesamtfluss ohne Fokus, Empfänger, Akte, Netz", () => {
    expect(aktuellesGlied({ ...leer, topf: "gesamt" }).label).toBe("Gesamtfluss");
    expect(aktuellesGlied({ ...leer, view: "empfaenger", empfaengerFilterEpl: "11" }).label).toBe("Empfänger (Einzelplan 11)");
    expect(aktuellesGlied({ ...leer, view: "empfaenger", empfaengerId: "aas", empfaengerName: "Amadeu Antonio Stiftung" })).toEqual({ label: "Empfänger: Amadeu Antonio Stiftung", ziel: { art: "empfaenger", id: "aas" } });
    expect(aktuellesGlied({ ...leer, view: "personen" }).ziel).toEqual({ art: "personenliste" });
    expect(aktuellesGlied({ ...leer, view: "personen", akteId: "sanae-abdi", akteName: "Sanae Abdi" }).label).toBe("Akte: Sanae Abdi");
    expect(aktuellesGlied({ ...leer, view: "netz", netzStart: "p:sanae-abdi", netzLabel: "Sanae Abdi" })).toEqual({ label: "Umfeld: Sanae Abdi", ziel: { art: "netz", knoten: "p:sanae-abdi" } });
  });
});

describe("pfad", () => {
  test("kürzt auf die letzten sechs Glieder", () => {
    const g = (n: number): Glied => ({ label: `G${n}`, ziel: { art: "personenliste" } });
    expect(pfad([1, 2, 3, 4, 5, 6, 7].map(g), g(8)).map((x) => x.label)).toEqual(["G3", "G4", "G5", "G6", "G7", "G8"]);
  });
});
