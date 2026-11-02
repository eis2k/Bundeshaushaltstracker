import { expect, test } from "vitest";
import { fmtDatum, fmtEuro, fmtPct } from "../src/lib/model/format";

test("fmtEuro picks Mrd, Mio or Euro and uses German formatting", () => {
  expect(fmtEuro(48_207_871_000)).toBe("48,2 Mrd €");
  expect(fmtEuro(2_000_000)).toBe("2,0 Mio €");
  expect(fmtEuro(1_234)).toBe("1.234 €");
  expect(fmtEuro(0)).toBe("0 €");
  expect(fmtEuro(-60_900_000_000)).toBe("−60,9 Mrd €");
  expect(fmtEuro(999_999_999)).toBe("1.000,0 Mio €");
});

test("fmtPct renders factors as whole percent", () => {
  expect(fmtPct(0.5)).toBe("50 %");
  expect(fmtPct(1)).toBe("100 %");
  expect(fmtPct(1.5)).toBe("150 %");
  expect(fmtPct(0.333)).toBe("33 %");
});


test("fmtDatum schreibt ISO-Daten deutsch und lässt anderes unverändert", () => {
  expect(fmtDatum("2025-03-25")).toBe("25.3.2025");
  expect(fmtDatum("2026-11-02")).toBe("2.11.2026");
  expect(fmtDatum("2026-11")).toBe("2026-11");
  expect(fmtDatum(null)).toBe("");
});
