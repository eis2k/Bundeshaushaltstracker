import { describe, expect, test } from "vitest";
import { aufkommen, defaultWerte, normalisiere, steuerEinnahmen, type SteuerSzenario } from "../src/lib/model/steuern";
import { balance } from "../src/lib/model/scenario";
import { fixtureYear, KREDITE, SUM_E_OHNE_KREDITE } from "./fixtures";

const vermoegen: SteuerSzenario = {
  id: "vermoegensteuer", name: "Vermögensteuer", kurz: "Vermögensteuer", status: "ausgesetzt", empfaenger: "laender",
  bund_anteil: 0, bund_anteil_quelle: "https://x", beschreibung: "",
  modell: {
    art: "satz_mal_basis",
    basis: { wert: 4_200_000_000_000, text: "Basis", jahr: 2024, quelle: "https://x" },
    annahmen: [
      { id: "satz", text: "Satz", wert: 0.01, min: 0, max: 0.03, schritt: 0.0025, einheit: "%", quelle: "https://x" },
      { id: "ausweich", text: "Ausweich", wert: 0.3, min: 0, max: 0.6, schritt: 0.05, einheit: "%", quelle: "https://x" },
    ],
  },
  geschichte: [],
};
const spitze: SteuerSzenario = {
  id: "spitzensteuersatz", name: "Spitzensatz", kurz: "Spitzensatz", status: "erhoben", empfaenger: "gemeinsam",
  bund_anteil: 0.425, bund_anteil_quelle: "https://x", beschreibung: "",
  modell: {
    art: "satzaenderung",
    basis: { wert: 4_667_000_000, text: "je Punkt", jahr: 2025, quelle: "https://x" },
    satz_alt: 0.42,
    annahmen: [{ id: "satz_neu", text: "neu", wert: 0.45, min: 0.42, max: 0.53, schritt: 0.01, einheit: "%", quelle: "https://x" }],
  },
  geschichte: [],
};
const erbe: SteuerSzenario = {
  id: "erbschaftsteuer", name: "Erbschaft", kurz: "Erbschaft", status: "erhoben", empfaenger: "laender",
  bund_anteil: 0, bund_anteil_quelle: "https://x", beschreibung: "",
  modell: { art: "basis_mal_faktor", basis: { wert: 13_300_000_000, text: "", jahr: 2024, quelle: "https://x" },
            annahmen: [{ id: "faktor", text: "", wert: 1, min: 1, max: 2.5, schritt: 0.1, einheit: "×", quelle: "https://x" }] },
  geschichte: [],
};

describe("aufkommen", () => {
  test("satz_mal_basis: Vermögensteuer 1 % auf 4,2 Bio mit 30 % Ausweich = 29,4 Mrd, Bund 0", () => {
    const a = aufkommen(vermoegen, defaultWerte(vermoegen));
    expect(a.gesamt).toBe(29_400_000_000);
    expect(a.bund).toBe(0);
  });

  test("satzaenderung: +3 Punkte × 4,667 Mrd = 14 Mrd, Bund 42,5 %", () => {
    const a = aufkommen(spitze, { satz_neu: 0.45 });
    expect(a.gesamt).toBeCloseTo(14_001_000_000, -6);
    expect(a.bund).toBeCloseTo(14_001_000_000 * 0.425, -6);
  });

  test("basis_mal_faktor: Faktor 1 ergibt 0, Faktor 1,5 ergibt die Hälfte der Basis", () => {
    expect(aufkommen(erbe, { faktor: 1 }).gesamt).toBe(0);
    expect(aufkommen(erbe, { faktor: 1.5 }).gesamt).toBe(6_650_000_000);
  });

  test("values are clamped to min/max and the result is never negative", () => {
    expect(aufkommen(vermoegen, { satz: -1, ausweich: 5 }).gesamt).toBe(0);
    expect(aufkommen(vermoegen, { satz: 9, ausweich: 0 }).gesamt).toBe(4_200_000_000_000 * 0.03);
    expect(aufkommen(spitze, { satz_neu: 0.1 }).gesamt).toBe(0);  // unter satz_alt → auf min begrenzt → 0
  });
});

describe("steuerEinnahmen", () => {
  test("sums active scenarios and reports each", () => {
    const r = steuerEinnahmen([vermoegen, spitze, erbe], { vermoegensteuer: {}, spitzensteuersatz: { satz_neu: 0.45 } });
    expect(r.je.map((x) => x.id)).toEqual(["vermoegensteuer", "spitzensteuersatz"]);
    expect(r.gesamt).toBeCloseTo(29_400_000_000 + 14_001_000_000, -6);
    expect(r.bund).toBeCloseTo(14_001_000_000 * 0.425, -6);
  });

  test("unknown scenario ids are ignored", () => {
    expect(steuerEinnahmen([vermoegen], { gibt_es_nicht: {} }).je).toEqual([]);
  });
});

describe("balance with extra Bund revenue", () => {
  test("extraBund lowers neueSchulden and raises delta", () => {
    const b = balance(fixtureYear, {}, false, 100);
    expect(b.einnahmen).toBe(SUM_E_OHNE_KREDITE + 100);
    expect(b.neueSchulden).toBe(KREDITE - 100);
    expect(b.delta).toBe(100);
    expect(b.einnahmenOriginal).toBe(SUM_E_OHNE_KREDITE);
  });
});

describe("normalisiere", () => {
  test("drops unknown scenarios and keys, clamps values to min/max", () => {
    const r = normalisiere([vermoegen, spitze], {
      vermoegensteuer: { satz: 5, ausweich: 0.3, foo: 1 },
      gibt_es_nicht: { x: 1 },
      spitzensteuersatz: { satz_neu: 0.1 },
    });
    expect(r).toEqual({ vermoegensteuer: { satz: 0.03, ausweich: 0.3 }, spitzensteuersatz: { satz_neu: 0.42 } });
  });
});
