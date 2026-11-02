import { describe, expect, test } from "vitest";
import { AppState, type Loader } from "../src/lib/state.svelte";
import { EINTRAEGE } from "../src/lib/model/navigation";
import type { Index, Preset, YearData } from "../src/lib/model/types";
import { fixtureYear } from "./fixtures";

const year2019: YearData = {
  ...fixtureYear,
  jahr: 2019,
  rows: fixtureYear.rows.filter((r) => r.id !== "14-1401-55101").map((r) => ({ ...r, soll: Math.round(r.soll * 0.8) })),
};
const index: Index = { jahre: [2019, 2025], ist_bis: 2025, summen: {}, erzeugt: "2026-11-01" };
const presets: Preset[] = [{ id: "rente_halb", name: "Rente halb", beschreibung: "", regeln: [{ ziel: "11-1102-63681", faktor: 0.5 }] }];

const loader: Loader = {
  loadIndex: async () => index,
  loadYear: async (j) => (j === 2019 ? year2019 : fixtureYear),
  loadPresets: async () => presets,
  loadGesetzFrei: async () => ({}),
};

describe("AppState", () => {
  test("init loads index, presets and the latest year with Soll", async () => {
    const s = new AppState(loader);
    await s.init("");
    expect(s.jahr).toBe(2025);
    expect(s.data?.jahr).toBe(2025);
    expect(s.presets.length).toBe(1);
    expect(s.balance?.ausgaben).toBe(950);
  });

  test("setFactor updates balance and togglePreset applies rules", async () => {
    const s = new AppState(loader);
    await s.init("");
    s.setFactor("11-1102-63681", 0.5);
    expect(s.balance?.ausgaben).toBe(750);
    s.togglePreset("rente_halb");
    expect(s.scenario.presets).toEqual(["rente_halb"]);
    s.setFactor("11-1102-63681", 1);               // Nutzerwert entfernt → Preset greift
    expect(s.factors["11-1102-63681"]).toBe(0.5);
    s.togglePreset("rente_halb");
    expect(s.scenario.presets).toEqual([]);
    expect(s.balance?.ausgaben).toBe(950);
  });

  test("changing the year keeps factors and reports ids missing in that year", async () => {
    const s = new AppState(loader);
    await s.init("");
    s.setFactor("11-1102-63681", 0.5);
    s.setFactor("14-1401-55101", 0.8);
    await s.setJahr(2019);
    expect(s.jahr).toBe(2019);
    expect(s.scenario.factors).toEqual({ "11-1102-63681": 0.5, "14-1401-55101": 0.8 });
    expect(s.unknownIds).toEqual(["14-1401-55101"]);
    expect(s.balance?.ausgaben).toBe(Math.round(950 * 0.8 - 300 * 0.8) - 160);
  });

  test("hash roundtrip restores year, view, focus, factors and presets", async () => {
    const s = new AppState(loader);
    await s.init("");
    s.setFactor("14", 2);
    s.togglePreset("rente_halb");
    s.setView("karte");
    s.setFocus(["11", "11-1102"]);
    const h = s.toHash();
    expect(h).toBe("v1;j=2025;a=karte;t=bund;f=11/1102;p=rente_halb;o=14:200");  // Fokus schaltet auf den Bund
    const t = new AppState(loader);
    await t.init("#" + h);
    expect(t.jahr).toBe(2025);
    expect(t.view).toBe("karte");
    expect(t.focus).toEqual(["11", "11-1102"]);
    expect(t.scenario.factors).toEqual({ "14": 2 });
    expect(t.scenario.presets).toEqual(["rente_halb"]);
    expect(t.fromShare).toBe(true);
    expect(t.selected).toBe("11-1102");
  });

  test("reset clears factors and presets but keeps year and view", async () => {
    const s = new AppState(loader);
    await s.init("#v1;j=2019;a=saeulen;o=14:200;p=rente_halb");
    expect(s.jahr).toBe(2019);
    s.reset();
    expect(s.scenario.factors).toEqual({});
    expect(s.scenario.presets).toEqual([]);
    expect(s.jahr).toBe(2019);
    expect(s.view).toBe("saeulen");
  });

  test("Ist mode swaps soll for ist where available", async () => {
    const s = new AppState(loader);
    await s.init("");
    s.setStand("ist");
    const row = s.viewData!.rows.find((r) => r.id === "11-1102-63681")!;
    expect(row.soll).toBe(390);
    expect(s.balance?.ausgaben).toBe(950 - 10);
  });
});

describe("GUI v2 Navigation", () => {
  test("waehle öffnet Ansicht und setzt Simulator-Kennzeichen; alter Link bleibt gleich", async () => {
    const s = new AppState(loader);
    await s.init("#v1;j=2025;a=karte;f=11");
    expect(s.view).toBe("karte");
    s.waehle(EINTRAEGE.find((e) => e.id === "simulator")!);
    expect(s.view).toBe("fluss"); expect(s.gestalten).toBe(true);
    expect(s.toHash()).not.toContain("simulator");
    s.waehle(EINTRAEGE.find((e) => e.id === "ministerien")!);
    expect(s.view).toBe("ministerien"); expect(s.gestalten).toBe(false);
    expect(s.toHash()).toContain("a=ministerien");
  });
});

describe("Review-Fixes", () => {
  test("inflation adjustment also scales the Sozialkassen", async () => {
    const sk = { jahr: 2019, toepfe: { grv: { name: "GRV", kurz: "Rentenkasse", farbe: "beitraege", geschaetzt: false, quelle: null, bundesmittel: [], einnahmen: [{ id: "beitraege", text: "B", betrag: 1000 }], ausgaben: [{ id: "renten", text: "R", betrag: 1000 }] } }, querfluesse: [] };
    const s = new AppState({ ...loader, loadSozialkassen: async () => sk, loadVpi: async () => ({ 2019: 100, 2025: 125 }) });
    await s.init("#v1;j=2019;a=fluss");
    await s.setReal(true);
    expect(s.viewSozialkassen!.toepfe.grv.einnahmen[0].betrag).toBe(1250);
    expect(s.toepfe!.toepfe[0].ausgaben).toBe(1250);
  });

  test("setting a focus path switches the flow to the Bund", async () => {
    const s = new AppState(loader);
    await s.init("");
    expect(s.topf).toBe("gesamt");
    s.setFocus(["11"]);
    expect(s.topf).toBe("bund");
  });
});

describe("Empfänger (Stufe 2)", () => {
  const empfIndex = { stand: "2026-11-01", mit_personen: true, titel: { "11-1102-63681": { id: "drv", name: "Deutsche Rentenversicherung Bund" } },
    eintraege: [{ id: "drv", name: "Deutsche Rentenversicherung Bund", art: "oeffentlich", rechtsform: "", sitz: "", lobby_untergrenze_bund: 0, haushalt_soll_letztes_jahr: 400, foerderkatalog_summe: 0, n_personen: 0, n_verbindungen: 0, lobbyregister: null, epls: ["11"] }] };
  const drv = { id: "drv", name: "Deutsche Rentenversicherung Bund", art: "oeffentlich", rechtsform: "", sitz: "", website: null, stand: "2026-11-01", geprueft: true, lobbyregister: null,
    haushalt: { titel: [] }, lobby_zuwendungen: [], lobby_untergrenze_bund: 0, foerderkatalog: [], personen: [], verbindungen: [], pflichtangaben: null, quellen: [] };
  const eloader: Loader = {
    ...loader,
    loadEmpfaengerIndex: async () => empfIndex as never,
    loadEmpfaenger: async (id: string) => { if (id !== "drv") throw new Error("404"); return drv as never; },
  };

  test("openEmpfaenger lädt die Seite, setzt die Ansicht und schreibt e= in den Link", async () => {
    const s = new AppState(eloader);
    await s.init("");
    await s.openEmpfaenger("drv");
    expect(s.view).toBe("empfaenger");
    expect(s.empfaengerSeite?.name).toBe("Deutsche Rentenversicherung Bund");
    expect(s.toHash()).toContain("e=drv");
    expect(s.empfaengerByTitel["11-1102-63681"].id).toBe("drv");
  });

  test("openEmpfaenger mit unbekannter Id setzt empfaengerFehlt und bleibt in der Liste", async () => {
    const s = new AppState(eloader);
    await s.init("");
    await s.openEmpfaenger("gibt-es-nicht");
    expect(s.view).toBe("empfaenger");
    expect(s.empfaengerSeite).toBeNull();
    expect(s.empfaengerFehlt).toBe("gibt-es-nicht");
    expect(s.toHash()).not.toContain("e=");
  });

  test("init mit e= im Link öffnet die Seite; openEmpfaengerListe setzt den Ressort-Filter", async () => {
    const s = new AppState(eloader);
    await s.init("#v1;j=2025;a=empfaenger;e=drv");
    expect(s.view).toBe("empfaenger");
    expect(s.empfaengerSeite?.id).toBe("drv");
    s.openEmpfaengerListe({ epl: "11" });
    expect(s.empfaengerId).toBeNull();
    expect(s.empfaengerFilterEpl).toBe("11");
  });
});

describe("Personen und Netz (Stufe 3)", () => {
  const personIndex = { stand: "2026-11-02", modus: "relevant", eintraege: [
    { id: "sanae-abdi", name: "Sanae Abdi", funktion_kurz: "MdB", amt: true, sichtbar: true, n_organisationen: 0, shard: "aa", arten: ["mdb"] },
    { id: "timo-reinfrank", name: "Timo Reinfrank", funktion_kurz: "Vorstand", amt: false, sichtbar: false, n_organisationen: 1, shard: "bb", arten: ["gesetzlicher_vertreter"] } ] };
  const akteAbdi = { id: "sanae-abdi", name: "Sanae Abdi", sichtbar: true, grund_sichtbar: "amt", gleichnamig: [], quellen_ids: ["x"], amt: true, verbindung: false, freigabe: false,
    funktionen: [], angaben: [], organisationen: [], spenden: [], zeitlinie: [], quellen: [], stand: "2026-11-02" };
  const umfeld = { start: "p:sanae-abdi", knoten: [{ id: "p:sanae-abdi", art: "person", label: "Sanae Abdi", sichtbar: true, seite: "v1;a=personen;pe=sanae-abdi" }], kanten: [], weitere: 0 };
  const ploader: Loader = {
    ...loader,
    loadPersonIndex: async () => personIndex as never,
    loadPersonShard: async (shard: string) => (shard === "aa" ? { "sanae-abdi": akteAbdi } : {}) as never,
    loadNetzIndex: async () => ({ "p:sanae-abdi": "cc" }) as never,
    loadNetzShard: async (shard: string) => (shard === "cc" ? { "p:sanae-abdi": umfeld } : {}) as never,
  };

  test("openAkte lädt die Akte aus dem Shard und schreibt pe= in den Link", async () => {
    const s = new AppState(ploader);
    await s.init("");
    await s.openAkte("sanae-abdi");
    expect(s.view).toBe("personen");
    expect(s.akte?.name).toBe("Sanae Abdi");
    expect(s.toHash()).toContain("pe=sanae-abdi");
  });

  test("openAkte auf nicht freigeschaltete Akte meldet das statt zu scheitern", async () => {
    const s = new AppState(ploader);
    await s.init("");
    await s.openAkte("timo-reinfrank");
    expect(s.akte).toBeNull();
    expect(s.akteFehlt).toBe("nicht freigeschaltet");
    await s.openAkte("gibt-es-nicht");
    expect(s.akteFehlt).toBe("unbekannt");
    expect(s.toHash()).not.toContain("pe=");
  });

  test("openNetz lädt das Umfeld; init mit n= öffnet das Netz", async () => {
    const s = new AppState(ploader);
    await s.init("#v1;j=2025;a=netz;n=p:sanae-abdi");
    expect(s.view).toBe("netz");
    expect(s.netz?.start).toBe("p:sanae-abdi");
    expect(s.toHash()).toContain("n=p:sanae-abdi");
    await s.openNetz("e:unbekannt");
    expect(s.netz).toBeNull();
    expect(s.netzFehlt).toBe("e:unbekannt");
  });

  test("a=netz ohne Knoten ist eine leere Netzansicht, kein Fehler", async () => {
    const s = new AppState(ploader);
    await s.init("#v1;j=2025;a=netz");
    expect(s.view).toBe("netz");
    expect(s.netzLeer).toBe(true);
    expect(s.netzFehlt).toBeNull();
    await s.openNetz("p:sanae-abdi");
    expect(s.netzLeer).toBe(false);
  });

  test("zurück aus dem Netz führt zur Akte, von der es geöffnet wurde (Important 8)", async () => {
    const s = new AppState(ploader);
    await s.init("");
    await s.openAkte("sanae-abdi");
    await s.openNetz("p:sanae-abdi");
    expect(s.view).toBe("netz");
    await s.closeNetz();
    expect(s.view).toBe("personen");
    expect(s.akte?.id).toBe("sanae-abdi");
    expect(s.toHash()).not.toContain("n=");
    // ohne Herkunft: Personenliste
    const t = new AppState(ploader);
    await t.init("#v1;j=2025;a=netz;n=p:sanae-abdi");
    await t.closeNetz();
    expect(t.view).toBe("personen");
    expect(t.akte).toBeNull();
  });
});
