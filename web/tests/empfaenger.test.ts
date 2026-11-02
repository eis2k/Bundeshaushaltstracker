import { describe, expect, test } from "vitest";
import {
  filtereEmpfaenger,
  fmtSpanne,
  geldAus,
  issueUrl,
  titelZeitreihe,
  type EmpfaengerIndex,
  type EmpfaengerIndexEintrag,
  type EmpfaengerSeite,
} from "../src/lib/model/empfaenger";

function e(id: string, name: string, bund: number, extra: Partial<EmpfaengerIndexEintrag> = {}): EmpfaengerIndexEintrag {
  return { id, name, art: "verein_stiftung", rechtsform: "", sitz: "", lobby_untergrenze_bund: bund, haushalt_soll_letztes_jahr: 0,
           foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: [], ...extra };
}

const idx: EmpfaengerIndex = {
  stand: "2026-11-01", mit_personen: true, titel: {},
  eintraege: [e("a", "Amadeu Antonio Stiftung", 1e6, { epls: ["17"], n_verbindungen: 1 }), e("b", "Goethe-Institut e. V.", 5e6, { art: "oeffentlich", haushalt_soll_letztes_jahr: 2e8, epls: ["05"] }),
              e("c", "Deutsche Stiftung Weltbevölkerung", 2e6, { epls: ["23"] })],
};

const seite: EmpfaengerSeite = {
  id: "amadeu-antonio-stiftung", name: "Amadeu Antonio Stiftung", art: "verein_stiftung", rechtsform: "Stiftung", sitz: "Berlin", website: null,
  stand: "2026-11-01", geprueft: false, lobbyregister: null,
  haushalt: { titel: [
    { id: "17-1702-68402", text: "A", epl: "17", epl_text: "BMBFSFJ", werte: { "2024": { soll: 100, ist: 90 }, "2025": { soll: 120, ist: null } } },
    { id: "17-1702-68403", text: "B", epl: "17", epl_text: "BMBFSFJ", werte: { "2025": { soll: 30, ist: null } } },
  ] },
  lobby_zuwendungen: [{ geber: "BMBF", epl: "30", von: 580_001, bis: 590_000, zweck: "", geschaeftsjahr: "2025" },
                      { geber: "Bundesministerium für Familie, Senioren, Frauen und Jugend", epl: "17", von: 1_040_001, bis: 1_050_000, zweck: "", geschaeftsjahr: "2025" },
                      { geber: "BMBF", epl: "30", von: 10_001, bis: 20_000, zweck: "", geschaeftsjahr: "2025" }],
  lobby_untergrenze_bund: 1_630_003, foerderkatalog: [], personen: [], verbindungen: [], pflichtangaben: null, quellen: [],
};

describe("filtereEmpfaenger", () => {
  test("Suche ist umlaut-tolerant, Sortierung nach Bund-Untergrenze", () => {
    expect(filtereEmpfaenger(idx, "weltbevoelkerung", "alle", "bund").map((x) => x.id)).toEqual(["c"]);
    expect(filtereEmpfaenger(idx, "", "alle", "bund").map((x) => x.id)).toEqual(["b", "c", "a"]);
  });
  test("Filter nach Art, Einzelplan und Sortierung nach Haushalt, Verbindungen und Name", () => {
    expect(filtereEmpfaenger(idx, "", "oeffentlich", "bund").map((x) => x.id)).toEqual(["b"]);
    expect(filtereEmpfaenger(idx, "", "alle", "bund", "17").map((x) => x.id)).toEqual(["a"]);
    expect(filtereEmpfaenger(idx, "", "alle", "haushalt")[0].id).toBe("b");
    expect(filtereEmpfaenger(idx, "", "alle", "verbindungen")[0].id).toBe("a");
    expect(filtereEmpfaenger(idx, "", "alle", "name").map((x) => x.id)).toEqual(["a", "c", "b"]);
  });
});

describe("fmtSpanne", () => {
  test("formatiert Spannen und Einzelwerte", () => {
    expect(fmtSpanne(1_040_001, 1_050_000)).toBe("1,04–1,05 Mio €");
    expect(fmtSpanne(0, 0)).toBe("0 €");
    expect(fmtSpanne(580_001, 590_000)).toBe("580.001–590.000 €");
    expect(fmtSpanne(1_000_000_000, 1_100_000_000)).toBe("1,0–1,1 Mrd €");
  });
});

describe("geldAus und titelZeitreihe", () => {
  test("geldAus nennt jeden Geber einmal, nach Untergrenze absteigend", () => {
    expect(geldAus(seite)).toEqual(["Bundesministerium für Familie, Senioren, Frauen und Jugend", "BMBF"]);
  });
  test("titelZeitreihe summiert Titel je Jahr und lässt fehlende Ist-Werte aus", () => {
    expect(titelZeitreihe(seite, "soll")).toEqual([{ jahr: 2024, wert: 100 }, { jahr: 2025, wert: 150 }]);
    expect(titelZeitreihe(seite, "ist")).toEqual([{ jahr: 2024, wert: 90 }]);
  });
});

describe("issueUrl", () => {
  test("enthält Id, Name und Stand", () => {
    const u = issueUrl(seite);
    expect(u.startsWith("https://github.com/eis2k/Bundeshaushaltstracker/issues/new?")).toBe(true);
    expect(u).toContain(encodeURIComponent("amadeu-antonio-stiftung"));
    expect(decodeURIComponent(u)).toContain("Amadeu Antonio Stiftung");
    expect(decodeURIComponent(u)).toContain("2026-11-01");
  });
});
