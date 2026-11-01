// Kopiert die Build-Dateien der Pipeline (../data/build) nach dist/data, damit die statische Seite sie ausliefern kann.
import { cpSync, existsSync, mkdirSync, rmSync } from "node:fs";
import { resolve } from "node:path";

const src = resolve("../data/build");
const dst = resolve("dist/data");
if (!existsSync(src)) {
  console.error("data/build fehlt. Erst die Pipeline laufen lassen: cd pipeline && uv run bht build");
  process.exit(1);
}
rmSync(dst, { recursive: true, force: true });
mkdirSync(dst, { recursive: true });
cpSync(src, dst, { recursive: true, filter: (p) => !p.includes("_check") && !p.includes("_texts_check") });
console.log("Daten kopiert nach", dst);
