import { describe, expect, test } from "vitest";
import { EINTRAEGE, aktiverEintrag, titelFuer, unteransichten } from "../src/lib/model/navigation";

describe("navigation (GUI v3)", () => {
  test("neun Einträge in der Reihenfolge des Dashboard-Entwurfs", () => {
    expect(EINTRAEGE.map((e) => e.id)).toEqual(["dashboard", "haushalt", "geldfluesse", "ministerien", "empfaenger", "simulator", "zeitvergleich", "politik", "verflechtungen"]);
    expect(EINTRAEGE.every((e) => typeof e.icon === "string" && e.icon.length > 0)).toBe(true);
  });
  test("aktiver Eintrag folgt der Ansicht", () => {
    expect(aktiverEintrag("fluss")).toBe("geldfluesse");
    expect(aktiverEintrag("karte")).toBe("haushalt");
    expect(aktiverEintrag("saeulen")).toBe("haushalt");
    expect(aktiverEintrag("simulator")).toBe("simulator");
    expect(aktiverEintrag("personen")).toBe("politik");
    expect(aktiverEintrag("politik")).toBe("politik");
    expect(aktiverEintrag("netz")).toBe("verflechtungen");
    expect(aktiverEintrag("gewachsen")).toBe("zeitvergleich");
    expect(aktiverEintrag("dashboard")).toBe("dashboard");
    expect(aktiverEintrag("ministerien")).toBe("ministerien");
    expect(aktiverEintrag("empfaenger")).toBe("empfaenger");
  });
  test("Unteransichten und Titel", () => {
    expect(unteransichten("haushalt").map((u) => u.view)).toEqual(["karte", "saeulen"]);
    expect(unteransichten("geldfluesse")).toEqual([]);
    expect(unteransichten("politik")).toEqual([]);
    expect(titelFuer("fluss").titel).toBe("Geldflüsse & Profiteure");
    expect(titelFuer("fluss").untertitel).toContain("woher die Gelder kommen");
    expect(titelFuer("simulator").titel).toBe("Haushaltssimulator");
    expect(titelFuer("dashboard").titel).toBe("Dashboard");
  });
});
