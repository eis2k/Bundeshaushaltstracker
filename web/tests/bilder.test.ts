import { describe, expect, test } from "vitest";
import { bildFuer, bildnachweise, tooltip, type Bild, type Bilder } from "../src/lib/model/bilder";

const foto: Bild = { datei: "Anna Muster 2025.jpg", url: "https://u/96.jpg", url_gross: "https://u/256.jpg", seite: "https://commons.wikimedia.org/wiki/File:Anna_Muster_2025.jpg", lizenz: "CC BY-SA 4.0", lizenz_url: null, urheber: "Foto Grafin", qid: "Q1", art: "person" };
const logo: Bild = { ...foto, datei: "A Logo.svg", seite: "https://commons.wikimedia.org/wiki/File:A_Logo.svg", lizenz: "Public domain", urheber: "Verein A", qid: "Q21", art: "organisation" };
const bilder: Bilder = { stand: "2026-11-02", quelle: "Wikidata/Wikimedia Commons", personen: { "anna-muster-mdb-1": foto, "anna-zwei": { ...foto, qid: "Q1" } }, organisationen: { "verein-a": logo }, pruefliste: [], verworfen: [] };

describe("bilder (Stufe 4b)", () => {
  test("bildFuer: p:/o:-Präfix, sonst nichts", () => {
    expect(bildFuer(bilder, "p:anna-muster-mdb-1")).toBe(foto);
    expect(bildFuer(bilder, "o:verein-a")).toBe(logo);
    expect(bildFuer(bilder, "o:anna-muster-mdb-1")).toBeNull();
    expect(bildFuer(bilder, undefined)).toBeNull();
    expect(bildFuer(null, "p:anna-muster-mdb-1")).toBeNull();
  });
  test("tooltip nennt Urheber und Lizenz, Logos als Marke", () => {
    expect(tooltip(foto)).toBe("Foto: Foto Grafin, CC BY-SA 4.0 (Wikimedia Commons)");
    expect(tooltip(logo)).toBe("Logo: Verein A, Public domain (Wikimedia Commons); Marke der Organisation");
  });
  test("bildnachweise: jede Datei einmal, mit Verwendung, sortiert", () => {
    const n = bildnachweise(bilder, { "p:anna-muster-mdb-1": "Anna Muster", "p:anna-zwei": "Anna Zwei", "o:verein-a": "Verein A" });
    expect(n.map((x) => x.datei)).toEqual(["A Logo.svg", "Anna Muster 2025.jpg"]);
    expect(n[1].verwendet).toEqual(["Anna Muster", "Anna Zwei"]);
    expect(n[0]).toMatchObject({ urheber: "Verein A", lizenz: "Public domain", seite: logo.seite });
    expect(bildnachweise(null, {})).toEqual([]);
  });
});
