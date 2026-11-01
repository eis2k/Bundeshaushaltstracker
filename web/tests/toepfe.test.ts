import { describe, expect, test } from "vitest";
import { buildToepfe, type SozialkassenYear } from "../src/lib/model/toepfe";
import { fixtureYear } from "./fixtures";

const sk: SozialkassenYear = {
  jahr: 2025,
  toepfe: {
    grv: {
      name: "Gesetzliche Rentenversicherung", kurz: "Rentenkasse", farbe: "beitraege", geschaetzt: false, quelle: "DRV",
      bundesmittel: [{ titel: "11-1102-63681", text: "Zuschuss" }, { titel: "11-1102-63682", text: "Zuschuss Ost" }, { titel: "99-9999-99999", text: "gibt es nicht" }],
      einnahmen: [{ id: "beitraege", text: "Beiträge", betrag: 1000 }, { id: "bund", text: "Bundesmittel", betrag: 500 }],
      ausgaben: [{ id: "renten", text: "Renten", betrag: 1400 }, { id: "kvdr", text: "KVdR", betrag: 100 }],
    },
    gkv: {
      name: "GKV", kurz: "Krankenkassen", farbe: "beitraege", geschaetzt: true, quelle: "KJ1",
      bundesmittel: [],
      einnahmen: [{ id: "beitraege", text: "Beiträge", betrag: 800 }],
      ausgaben: [{ id: "leistungen", text: "Leistungen", betrag: 790 }],
    },
  },
  querfluesse: [{ von: "grv", nach: "gkv", id: "kvdr", text: "KVdR" }],
};

describe("buildToepfe", () => {
  test("bundesmittel follow the Bund factors; unknown titles are ignored", () => {
    const base = buildToepfe(fixtureYear, sk, {}, false);
    const grv = base.toepfe.find((t) => t.id === "grv")!;
    expect(grv.bundesmittel).toBe(400 + 100);          // Soll der verknüpften Bund-Titel
    expect(grv.einnahmen).toBe(1000 + 500);              // Tabellenwert statt Bundeswert im Original
    expect(grv.saldo).toBe(1500 - 1500);
    const halved = buildToepfe(fixtureYear, sk, { "11-1102-63681": 0.5 }, false);
    const g2 = halved.toepfe.find((t) => t.id === "grv")!;
    expect(g2.bundesmittel).toBe(200 + 100);
    expect(g2.einnahmen).toBe(1500 - 200);              // Einnahmen sinken um die gestrichenen Bundesmittel
    expect(g2.saldo).toBe(-200);
    expect(g2.saldoOriginal).toBe(0);
  });

  test("querfluesse are counted once in the total", () => {
    const r = buildToepfe(fixtureYear, sk, {}, false);
    const toepfeAusgaben = 1500 + 790;
    const bundAusgaben = 950;
    const bundesmittel = 500;   // Bund → GRV
    const kvdr = 100;           // GRV → GKV
    expect(r.gesamtAusgaben).toBe(bundAusgaben + toepfeAusgaben - bundesmittel - kvdr);
    expect(r.querfluesse.map((q) => q.betrag)).toEqual([100]);
  });

  test("beitraege total excludes Bundesmittel", () => {
    const r = buildToepfe(fixtureYear, sk, {}, false);
    expect(r.beitraege).toBe(1000 + 800);
  });

  test("topf flagged geschaetzt is passed through", () => {
    const r = buildToepfe(fixtureYear, sk, {}, false);
    expect(r.toepfe.find((t) => t.id === "gkv")!.geschaetzt).toBe(true);
  });
});

describe("Saldo-Formel und reale Preise (Review 3)", () => {
  test("topfEinnahmen is the single formula used for saldo", () => {
    const r = buildToepfe(fixtureYear, sk, { "11-1102-63681": 0.5 }, false);
    const grv = r.toepfe.find((t) => t.id === "grv")!;
    expect(grv.einnahmen).toBe(1500 - 200);
    expect(grv.saldo).toBe(grv.einnahmen - grv.ausgaben);
  });
});
