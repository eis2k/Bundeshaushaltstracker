const de = new Intl.NumberFormat("de-DE", { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const deInt = new Intl.NumberFormat("de-DE", { maximumFractionDigits: 0 });

/** 48207871000 → "48,2 Mrd €", 2000000 → "2,0 Mio €", 1234 → "1.234 €"; negatives mit echtem Minus. */
export function fmtEuro(n: number): string {
  const sign = n < 0 ? "−" : "";
  const abs = Math.abs(n);
  if (abs >= 1e9) return `${sign}${de.format(abs / 1e9)} Mrd €`;
  if (abs >= 1e6) return `${sign}${de.format(abs / 1e6)} Mio €`;
  return `${sign}${deInt.format(abs)} €`;
}

export function fmtPct(factor: number): string {
  return `${Math.round(factor * 100)} %`;
}

/** Vorzeichenbehaftete Differenz, z. B. "+35,0 Mrd €" / "−2,1 Mrd €". */
export function fmtDelta(n: number): string {
  if (n === 0) return "±0 €";
  return (n > 0 ? "+" : "") + fmtEuro(n);
}
