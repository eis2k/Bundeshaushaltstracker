import { describe, expect, test } from "vitest";
import { datenstatus, type DatenstatusEingabe } from "../src/lib/model/datenstatus";

const basis: DatenstatusEingabe = { view: "fluss", seite: false, jahr: 2025, stand: "soll", real: false, bezugsjahr: 2025, erzeugt: "2026-11-01", modell: false, empfaengerStand: "2026-11-02", personenStand: "2026-11-02", letztesJahr: 2026 };

describe("datenstatus", () => {
  test("Haushaltsansicht: Jahr mit Soll, Quelle bundeshaushalt.de, Jahresleiste an", () => {
    expect(datenstatus(basis)).toEqual({ jahr: "2025 Soll", quellen: ["bundeshaushalt.de"], stand: "2026-11-01", preise: "nominal", modell: false, jahresleiste: true });
    expect(datenstatus({ ...basis, stand: "ist", view: "karte" }).quellen).toEqual(["bundeshaushalt.de", "Haushaltsrechnung"]);
    expect(datenstatus({ ...basis, stand: "ist" }).jahr).toBe("2025 Ist");
  });
  test("Empfänger: Liste nennt Soll des letzten Jahres, Seite alle Jahre; keine Jahresleiste", () => {
    const liste = datenstatus({ ...basis, view: "empfaenger" });
    expect(liste.jahr).toBe("Soll 2026");
    expect(liste.quellen).toEqual(["Lobbyregister", "Förderkatalog", "bundestag.de"]);
    expect(liste.stand).toBe("2026-11-02");
    expect(liste.jahresleiste).toBe(false);
    expect(datenstatus({ ...basis, view: "empfaenger", seite: true }).jahr).toBe("alle Jahre, Soll und Ist je Titel");
  });
  test("Personen und Netz", () => {
    const p = datenstatus({ ...basis, view: "personen" });
    expect(p.jahr).toBe("Soll 2026");
    expect(p.quellen).toEqual(["Lobbyregister", "bundestag.de", "bundesregierung.de"]);
    const n = datenstatus({ ...basis, view: "netz" });
    expect(n.jahr).toBe("");
    expect(n.jahresleiste).toBe(false);
    expect(n.stand).toBe("2026-11-02");
  });
  test("Preise und Modell werden durchgereicht", () => {
    expect(datenstatus({ ...basis, real: true, bezugsjahr: 2025 }).preise).toBe("in Preisen von 2025");
    expect(datenstatus({ ...basis, modell: true }).modell).toBe(true);
    expect(datenstatus({ ...basis, view: "ministerien" }).jahr).toBe("2025 Soll");
  });
});
