import { describe, expect, test } from "vitest";
import { EINTRAEGE, aktiverEintrag, titelFuer, unteransichten } from "../src/lib/model/navigation";

describe("navigation", () => {
  test("sechs Einträge in Mockup-Reihenfolge", () => {
    expect(EINTRAEGE.map((e) => e.id)).toEqual(["geldfluesse", "ministerien", "empfaenger", "verbindungen", "zeitvergleich", "simulator"]);
  });
  test("aktiver Eintrag folgt der Ansicht; Simulator nur mit Kennzeichen", () => {
    expect(aktiverEintrag("fluss", false)).toBe("geldfluesse");
    expect(aktiverEintrag("karte", false)).toBe("geldfluesse");
    expect(aktiverEintrag("fluss", true)).toBe("simulator");
    expect(aktiverEintrag("netz", false)).toBe("verbindungen");
    expect(aktiverEintrag("gewachsen", false)).toBe("zeitvergleich");
    expect(aktiverEintrag("ministerien", false)).toBe("ministerien");
  });
  test("Unteransichten und Titel", () => {
    expect(unteransichten("geldfluesse").map((u) => u.view)).toEqual(["fluss", "karte", "saeulen"]);
    expect(unteransichten("verbindungen").map((u) => u.view)).toEqual(["personen", "netz"]);
    expect(unteransichten("empfaenger")).toEqual([]);
    expect(titelFuer("fluss", false).titel).toBe("Geldflüsse & Empfänger");
    expect(titelFuer("fluss", true).titel).toBe("Haushaltssimulator");
  });
});
