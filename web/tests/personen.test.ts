import { describe, expect, test } from "vitest";
import { FUNKTION_LABELS, bezuegeNachPosten, filterePersonen, issueUrlAkte, zeigeBei, zeitlinieJahre, type Akte, type Bezuege, type BezugZeile, type PersonIndex, type PersonIndexEintrag } from "../src/lib/model/personen";
import { kantenStil, kanteBeschreibung, legende, netzPfad, type NetzKnoten, type Umfeld } from "../src/lib/model/netz";

function e(id: string, name: string, extra: Partial<PersonIndexEintrag> = {}): PersonIndexEintrag {
  return { id, name, funktion_kurz: "Vorstand", amt: false, sichtbar: true, n_organisationen: 1, shard: "ab", arten: ["gesetzlicher_vertreter"], ...extra };
}

const idx: PersonIndex = {
  stand: "2026-11-02", modus: "relevant",
  eintraege: [e("sanae-abdi", "Sanae Abdi", { amt: true, funktion_kurz: "Mitglied des Bundestages, SPD", arten: ["mdb"] }),
              // Important 2: zusammengeführte Akte, Bundestags-Funktion steht vorn
              e("friedrich-merz", "Friedrich Merz", { amt: true, funktion_kurz: "Mitglied des Bundestages, CDU/CSU", arten: ["mdb", "regierung"] }),
              e("timo-reinfrank", "Timo Reinfrank", { sichtbar: false }),
              e("tahera-ameer", "Tahera Ameer", { n_organisationen: 2 })],
};

const akte: Akte = {
  id: "tahera-ameer", name: "Tahera Ameer", sichtbar: true, grund_sichtbar: "verbindung", gleichnamig: [], quellen_ids: ["x"], amt: false, verbindung: true, freigabe: false,
  funktionen: [{ art: "gesetzlicher_vertreter", text: "Vorstand", organisation_id: "amadeu-antonio-stiftung", organisation: "Amadeu Antonio Stiftung", epl: null, seit: null, bis: null, stand: "2026-09-02", quelle: { kurz: "Lobbyregister", url: "https://l", etikett: "Eigenangabe" }, ausschuesse: [] }],
  angaben: [], organisationen: [], spenden: [],
  zeitlinie: [{ jahr: 2024, art: "geld", quelle: "lobbyregister", organisation_id: "a", text: "x", wert: 100 }, { jahr: 2025, art: "geld", quelle: "lobbyregister", organisation_id: "a", text: "y", wert: 200 },
              { jahr: 2025, art: "geld", quelle: "haushalt", organisation_id: "a", text: "Titel", wert: 5000 }, { jahr: 2025, art: "posten", organisation_id: "a", text: "Vorstand bei A" }, { jahr: 2025, art: "spende", organisation_id: "a", text: "A spendete", wert: 50 }],
  quellen: [], stand: "2026-11-02",
};

describe("filterePersonen", () => {
  test("Suche, Sichtbarkeit und Funktionsfilter", () => {
    expect(filterePersonen(idx, "abdi", "alle").map((x) => x.id)).toEqual(["sanae-abdi"]);
    expect(filterePersonen(idx, "", "alle").map((x) => x.id)).not.toContain("timo-reinfrank");
    expect(filterePersonen(idx, "", "alle", false).map((x) => x.id)).toContain("timo-reinfrank");
    expect(filterePersonen(idx, "", "abgeordnete").map((x) => x.id)).toEqual(["friedrich-merz", "sanae-abdi"]);
    expect(filterePersonen(idx, "", "regierung").map((x) => x.id)).toEqual(["friedrich-merz"]);
    expect(filterePersonen(idx, "", "vertreter").map((x) => x.id)).toEqual(["tahera-ameer"]);
  });
  test("Sortierung: Amt zuerst, dann Name", () => {
    expect(filterePersonen(idx, "", "alle").map((x) => x.id)).toEqual(["friedrich-merz", "sanae-abdi", "tahera-ameer"]);
  });
});

describe("zeitlinieJahre", () => {
  test("hält Geld je Quelle getrennt (Important 3) und sammelt Posten", () => {
    const z = zeitlinieJahre(akte);
    expect(z.map((x) => x.jahr)).toEqual([2024, 2025]);
    expect(z[1].lobby).toBe(200);
    expect(z[1].haushalt).toBe(5000);
    expect(z[0].haushalt).toBe(0);
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

describe("bezuegeNachPosten", () => {
  const z = (posten: string, komponente: string): BezugZeile => ({ posten, komponente, rechtsgrundlage: "§", monatlich: 1, zeitraum_von: null, zeitraum_bis: null, monate: null, summe: null, empfaenger: "person", quelle: { kurz: "q", url: null } });
  test("gruppiert Zeilen je Posten in Reihenfolge", () => {
    const b: Bezuege = { summe_person: 1, summe_aufwand: 2, hinweise: [], nicht_bezifferbar: [], wp_beginn: "2025-03-25",
      zeilen: [z("Mitglied des Bundestages", "Abgeordnetenentschädigung"), z("Bundeskanzler", "Amtsgehalt"), z("Mitglied des Bundestages", "Kostenpauschale")] };
    expect(bezuegeNachPosten(b).map((g) => [g.posten, g.zeilen.length])).toEqual([["Mitglied des Bundestages", 2], ["Bundeskanzler", 1]]);
  });
});


describe("Etiketten und „bei“", () => {
  test("laufende Regierungsfunktion aus dem Lobbyregister heißt nicht „Frühere“", () => {
    expect(FUNKTION_LABELS.regierungsfunktion).toBe("Öffentliche Funktion laut Lobbyregister");
    expect(FUNKTION_LABELS.fruehere_regierungsfunktion).toBe("Frühere öffentliche Funktion");
  });
  test("zeigeBei unterdrückt doppelte Organisationsnamen und den Bundestag", () => {
    expect(zeigeBei({ art: "regierung", text: "Bundesminister der Finanzen, Bundesministerium der Finanzen", organisation: "Bundesministerium der Finanzen" })).toBe(false);
    expect(zeigeBei({ art: "mdb", text: "Mitglied des Bundestages, SPD", organisation: "Deutscher Bundestag" })).toBe(false);
    expect(zeigeBei({ art: "gesetzlicher_vertreter", text: "Vorstand", organisation: "Amadeu Antonio Stiftung" })).toBe(true);
  });
});

describe("kanteBeschreibung", () => {
  test("liefert Art, Betrag, Quelle und beide Knoten", () => {
    const knoten: Record<string, NetzKnoten> = {
      "e:vbm": { id: "e:vbm", art: "organisation", label: "VBM e.V.", sichtbar: true, seite: "v1;a=empfaenger;e=vbm" },
      "partei:csu": { id: "partei:csu", art: "partei", label: "CSU", sichtbar: true, seite: null },
    };
    const b = kanteBeschreibung({ von: "e:vbm", nach: "partei:csu", art: "spende", text: "VBM e.V. spendete 136.000 € an CSU", wert: 136000, quelle: { kurz: "bundestag.de", url: "https://d", etikett: "amtlich" }, stand: "2025-12-23" }, knoten);
    expect(b.art).toBe("Spende");
    expect(b.betrag).toBe(136000);
    expect(b.von?.label).toBe("VBM e.V.");
    expect(b.nach?.label).toBe("CSU");
    expect(b.quelle.kurz).toBe("bundestag.de");
    expect(b.stand).toBe("2025-12-23");
  });
});
