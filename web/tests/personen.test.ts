import { describe, expect, test } from "vitest";
import { filterePersonen, issueUrlAkte, zeitlinieJahre, type Akte, type PersonIndex, type PersonIndexEintrag } from "../src/lib/model/personen";
import { kantenStil, legende, netzPfad, type Umfeld } from "../src/lib/model/netz";

function e(id: string, name: string, extra: Partial<PersonIndexEintrag> = {}): PersonIndexEintrag {
  return { id, name, funktion_kurz: "Vorstand", amt: false, sichtbar: true, n_organisationen: 1, shard: "ab", ...extra };
}

const idx: PersonIndex = {
  stand: "2026-11-02", modus: "relevant",
  eintraege: [e("sanae-abdi", "Sanae Abdi", { amt: true, funktion_kurz: "Mitglied des Bundestages, SPD" }),
              e("friedrich-merz", "Friedrich Merz", { amt: true, funktion_kurz: "Bundeskanzler, Bundeskanzleramt" }),
              e("timo-reinfrank", "Timo Reinfrank", { sichtbar: false }),
              e("tahera-ameer", "Tahera Ameer", { n_organisationen: 2 })],
};

const akte: Akte = {
  id: "tahera-ameer", name: "Tahera Ameer", sichtbar: true, grund_sichtbar: "verbindung", gleichnamig: [], quellen_ids: ["x"], amt: false, verbindung: true, freigabe: false,
  funktionen: [{ art: "gesetzlicher_vertreter", text: "Vorstand", organisation_id: "amadeu-antonio-stiftung", organisation: "Amadeu Antonio Stiftung", epl: null, seit: null, bis: null, stand: "2026-09-02", quelle: { kurz: "Lobbyregister", url: "https://l", etikett: "Eigenangabe" }, ausschuesse: [] }],
  angaben: [], organisationen: [], spenden: [],
  zeitlinie: [{ jahr: 2024, art: "geld", organisation_id: "a", text: "x", wert: 100 }, { jahr: 2025, art: "geld", organisation_id: "a", text: "y", wert: 200 }, { jahr: 2025, art: "posten", organisation_id: "a", text: "Vorstand bei A" }, { jahr: 2025, art: "spende", organisation_id: "a", text: "A spendete", wert: 50 }],
  quellen: [], stand: "2026-11-02",
};

describe("filterePersonen", () => {
  test("Suche, Sichtbarkeit und Funktionsfilter", () => {
    expect(filterePersonen(idx, "abdi", "alle").map((x) => x.id)).toEqual(["sanae-abdi"]);
    expect(filterePersonen(idx, "", "alle").map((x) => x.id)).not.toContain("timo-reinfrank");
    expect(filterePersonen(idx, "", "alle", false).map((x) => x.id)).toContain("timo-reinfrank");
    expect(filterePersonen(idx, "", "abgeordnete").map((x) => x.id)).toEqual(["sanae-abdi"]);
    expect(filterePersonen(idx, "", "regierung").map((x) => x.id)).toEqual(["friedrich-merz"]);
    expect(filterePersonen(idx, "", "vertreter").map((x) => x.id)).toEqual(["tahera-ameer"]);
  });
  test("Sortierung: Amt zuerst, dann Name", () => {
    expect(filterePersonen(idx, "", "alle").map((x) => x.id)).toEqual(["friedrich-merz", "sanae-abdi", "tahera-ameer"]);
  });
});

describe("zeitlinieJahre", () => {
  test("fasst Geld je Jahr zusammen und sammelt Posten", () => {
    const z = zeitlinieJahre(akte);
    expect(z.map((x) => x.jahr)).toEqual([2024, 2025]);
    expect(z[1].geld).toBe(200);
    expect(z[1].posten).toEqual(["Vorstand bei A"]);
    expect(z[1].spenden).toBe(50);
  });
});

describe("issueUrlAkte", () => {
  test("enthält Id und Name", () => {
    const u = issueUrlAkte(akte);
    expect(u.startsWith("https://github.com/eis2k/Bundeshaushaltstracker/issues/new?")).toBe(true);
    expect(decodeURIComponent(u)).toContain("tahera-ameer");
    expect(decodeURIComponent(u)).toContain("Tahera Ameer");
  });
});

describe("netz", () => {
  test("netzPfad nutzt den Shard aus dem Index", () => {
    expect(netzPfad("p:tahera-ameer", { "p:tahera-ameer": "3f" })).toBe("netz/3f.json");
    expect(netzPfad("p:unbekannt", { "p:tahera-ameer": "3f" })).toBeNull();
  });
  test("Kantenstil und Legende: drei Arten, eine Farbe", () => {
    expect(new Set([kantenStil("geld").dasharray, kantenStil("posten").dasharray, kantenStil("spende").dasharray]).size).toBe(3);
    expect(legende().map((l) => l.art)).toEqual(["geld", "posten", "spende"]);
    const u: Umfeld = { start: "p:x", knoten: [], kanten: [], weitere: 0 };
    expect(u.weitere).toBe(0);
  });
});
