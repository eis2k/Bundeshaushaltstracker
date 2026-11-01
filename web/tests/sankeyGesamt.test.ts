import { describe, expect, test } from "vitest";
import { buildGesamtSankey } from "../src/lib/views/sankeyGesamt";
import type { SozialkassenYear } from "../src/lib/model/toepfe";
import type { Scenario } from "../src/lib/model/types";
import { fixtureYear, KREDITE, SUM_A_KERN } from "./fixtures";

const sk: SozialkassenYear = {
  jahr: 2025,
  toepfe: {
    grv: {
      name: "Gesetzliche Rentenversicherung", kurz: "Rentenkasse", farbe: "beitraege", geschaetzt: false, quelle: "DRV",
      bundesmittel: [{ titel: "11-1102-63681", text: "Zuschuss" }, { titel: "11-1102-63682", text: "Zuschuss Ost" }],
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
const base: Scenario = { jahr: 2025, factors: {}, presets: [], includeSv: false };
const opts = { maxPerColumn: 3 };

function sumLinks(s: ReturnType<typeof buildGesamtSankey>, pred: (l: { source: string; target: string }) => boolean) {
  return s.links.filter(pred).reduce((a, l) => a + l.value, 0);
}

describe("buildGesamtSankey", () => {
  test("has four columns: inflows, Bund, Kassen plus Bund-Verwendung, Kassen-Verwendung", () => {
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    expect(s.nodes.filter((n) => n.column === 1).map((n) => n.id)).toEqual(["topf:bund"]);
    expect(s.nodes.filter((n) => n.kind === "topf" && n.column === 2).map((n) => n.id).sort()).toEqual(["topf:gkv", "topf:grv"]);
    expect(Math.max(...s.nodes.map((n) => n.column))).toBe(3);
    expect(s.nodes.filter((n) => n.id.startsWith("posten:")).every((n) => n.column === 3)).toBe(true);
  });

  test("Beiträge feed their Topf directly; Bundesmittel are one Querband Bund → Kasse", () => {
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    expect(s.nodes.find((n) => n.id === "beitraege:grv")!.effective).toBe(1000);
    expect(sumLinks(s, (l) => l.source === "beitraege:grv" && l.target === "topf:grv")).toBe(1000);
    const quer = s.links.find((l) => l.source === "topf:bund" && l.target === "topf:grv")!;
    expect(quer.value).toBe(500);
    expect(quer.colorKey).toBe("steuern");
    expect(s.nodes.find((n) => n.id === "bundesmittel:grv")).toBeUndefined();
    expect(s.nodes.find((n) => n.id === "zuschuesse:bund")).toBeUndefined();
  });

  test("Kassen are balanced; the Bund's outflows exceed its inflows exactly by the Minderausgaben", () => {
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    for (const id of ["topf:grv", "topf:gkv"]) {
      expect(sumLinks(s, (l) => l.target === id)).toBe(sumLinks(s, (l) => l.source === id));
    }
    expect(sumLinks(s, (l) => l.source === "topf:bund") - sumLinks(s, (l) => l.target === "topf:bund")).toBe(50);
    // Bund: Epl-Bänder ohne die verknüpften Titel plus Querband = positive Ausgaben
    expect(sumLinks(s, (l) => l.source === "topf:bund")).toBe(SUM_A_KERN + 50);
  });

  test("uses the same saldo as buildToepfe", () => {
    const factors = { "11-1102-63681": 0.5 };
    const s = buildGesamtSankey(fixtureYear, sk, { ...base, factors }, factors, opts);
    const defizit = s.nodes.find((n) => n.id === "defizit:grv")!;
    expect(defizit.effective).toBe(200);
    expect(defizit.changed).toBe(true);     // Original-Saldo war 0
    const s0 = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    expect(s0.nodes.find((n) => n.id === "ruecklage:gkv")!.changed).toBe(false);
  });

  test("a Topf deficit becomes a dashed 'Defizit' inflow, a surplus a 'Rücklage' outflow", () => {
    const halved = buildGesamtSankey(fixtureYear, sk, { ...base, factors: { "11-1102-63681": 0.5 } }, { "11-1102-63681": 0.5 }, opts);
    const defizit = halved.nodes.find((n) => n.id === "defizit:grv")!;
    expect(defizit.effective).toBe(200);
    expect(defizit.kind).toBe("kredit");
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    expect(s.nodes.find((n) => n.id === "ruecklage:gkv")!.effective).toBe(10);
    expect(s.nodes.find((n) => n.id === "defizit:grv")).toBeUndefined();
  });

  test("Bund Kredite node carries neueSchulden", () => {
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, opts);
    expect(s.nodes.find((n) => n.id === "E:kredite")!.effective).toBe(KREDITE);
  });

  test("single-Topf view shows only that fund", () => {
    const s = buildGesamtSankey(fixtureYear, sk, base, {}, { ...opts, only: "grv" });
    expect(s.nodes.filter((n) => n.column === 1).map((n) => n.id)).toEqual(["topf:grv"]);
    expect(s.nodes.filter((n) => n.column === 2).map((n) => n.id).sort()).toEqual(["posten:grv:kvdr", "posten:grv:renten"]);
  });
});
