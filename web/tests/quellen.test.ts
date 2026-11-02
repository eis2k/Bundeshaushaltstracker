import { describe, expect, test } from "vitest";
import type { EmpfaengerIndex } from "../src/lib/model/empfaenger";
import type { PersonIndex } from "../src/lib/model/personen";
import { LIZENZEN, LUECKEN, quellenTabelle } from "../src/lib/model/quellen";
import type { Index } from "../src/lib/model/types";

const index: Index = { jahre: [2015, 2026], ist_bis: 2025, sv_jahre: [2022, 2026], summen: {}, erzeugt: "2026-11-02T00:33:23+00:00" };
const empf = { stand: "2026-11-01", mit_personen: true, titel: {}, eintraege: [] } as EmpfaengerIndex;
const pers: PersonIndex = { stand: "2026-11-02", modus: "relevant", eintraege: [] };

describe("quellenTabelle (Seite Daten & Quellen)", () => {
  test("Stände nur aus den Daten, Zeitraum aus dem Index", () => {
    const t = quellenTabelle({ index, empfaenger: empf, personen: pers, vpi: { stand: "2026-10-01" }, steuern: 4 });
    expect(t[0].quelle).toContain("bundeshaushalt.de");
    expect(t[0].zeitraum).toBe("2015–2026, Ist bis 2025");
    expect(t[0].stand).toBe("2026-11-02");
    expect(t.find((z) => z.quelle.startsWith("Lobbyregister"))?.stand).toBe("2026-11-01");
    expect(t.find((z) => z.quelle.startsWith("Sozialkassen"))?.zeitraum).toBe("2022–2026");
    expect(t.find((z) => /Verbraucherpreis/.test(z.quelle))?.stand).toBe("2026-10-01");
    expect(t.find((z) => /Steuer-Modelle/.test(z.quelle))?.inhalt).toContain("4");
    expect(t.find((z) => /Zeitreihe/.test(z.inhalt))?.datei).toBe("/data/zeitreihe.json");
  });
  test("ohne Daten keine erfundenen Stände", () => {
    const t = quellenTabelle({ index: null, empfaenger: null, personen: null, vpi: null, steuern: 0 });
    expect(t.length).toBeGreaterThan(5);
    expect(t.every((z) => z.stand === null)).toBe(true);
  });
  test("Lücken und Lizenzen sind feste Listen", () => {
    expect(LUECKEN.length).toBeGreaterThanOrEqual(4);
    expect(LIZENZEN.some((l) => l.lizenz === "MIT")).toBe(true);
  });
});
