import { describe, expect, test } from "vitest";
import { empfaengerArt, groupBy, kostenart } from "../src/lib/model/schnitte";
import { fixtureYear, SUM_A_KERN } from "./fixtures";

describe("kostenart", () => {
  test("maps Hauptgruppen to Kostenarten, Zinsen separately", () => {
    expect(kostenart("42301")).toBe("personal");
    expect(kostenart("52901")).toBe("sach");
    expect(kostenart("57501")).toBe("zinsen");
    expect(kostenart("56101")).toBe("zinsen");
    expect(kostenart("63681")).toBe("zuweisungen");
    expect(kostenart("71101")).toBe("bau");
    expect(kostenart("83101")).toBe("investitionen");
    expect(kostenart("97201")).toBe("finanzierung");
  });
});

describe("empfaengerArt", () => {
  test("derives recipient type from the Gruppierung", () => {
    expect(empfaengerArt("63681")).toBe("sozialversicherung");
    expect(empfaengerArt("61301")).toBe("laender_gemeinden");
    expect(empfaengerArt("88201")).toBe("laender_gemeinden");
    expect(empfaengerArt("68201")).toBe("unternehmen");
    expect(empfaengerArt("89201")).toBe("unternehmen");
    expect(empfaengerArt("68401")).toBe("vereine_inland");
    expect(empfaengerArt("68501")).toBe("vereine_inland");
    expect(empfaengerArt("89401")).toBe("vereine_inland");
    expect(empfaengerArt("68701")).toBe("ausland");
    expect(empfaengerArt("89601")).toBe("ausland");
    expect(empfaengerArt("42301")).toBe("bund_selbst");
    expect(empfaengerArt("52901")).toBe("bund_selbst");
    expect(empfaengerArt("57501")).toBe("glaeubiger");
    expect(empfaengerArt("68101")).toBe("privatpersonen");
  });
});

describe("groupBy", () => {
  test("kostenart tree sums to total Ausgaben and labels groups", () => {
    const t = groupBy(fixtureYear, "kostenart", false);
    expect(t.roots.reduce((s, r) => s + r.soll, 0)).toBe(SUM_A_KERN);
    const zuw = t.roots.find((r) => r.id === "ka:zuweisungen")!;
    expect(zuw.label).toBe("Zuweisungen und Zuschüsse");
    expect(zuw.soll).toBe(400 + 100 + 200);
    expect(zuw.children.map((c) => c.id).sort()).toEqual(["11-1101-68101", "11-1101-68199", "11-1102-63681", "11-1102-63682"]);
    expect(t.byId.get("ka:finanzierung")!.soll).toBe(-50);
  });

  test("empfaengerart tree puts the Rentenzuschuss under Sozialversicherung", () => {
    const t = groupBy(fixtureYear, "empfaengerart", false);
    expect(t.roots.reduce((s, r) => s + r.soll, 0)).toBe(SUM_A_KERN);
    const sv = t.roots.find((r) => r.id === "ea:sozialversicherung")!;
    expect(sv.children.map((c) => c.id).sort()).toEqual(["11-1102-63681", "11-1102-63682"]);
    expect(t.roots.find((r) => r.id === "ea:privatpersonen")!.soll).toBe(200);
  });

  test("ressort schnitt equals buildTree", () => {
    const t = groupBy(fixtureYear, "ressort", false);
    expect(t.roots.map((r) => r.id).sort()).toEqual(["11", "14", "60"]);
  });

  test("includeSv adds Anlagen rows", () => {
    expect(groupBy(fixtureYear, "kostenart", true).roots.reduce((s, r) => s + r.soll, 0)).toBe(SUM_A_KERN + 80);
  });
});
