/** Seite „Daten & Quellen“ (Spec §4.12): nur Stände, die in den Daten stehen; Lücken und Lizenzen als feste Listen. */

import type { EmpfaengerIndex } from "./empfaenger";
import type { PersonIndex } from "./personen";
import type { Texte } from "./load";
import type { Index } from "./types";

export interface QuellenZeile { quelle: string; inhalt: string; zeitraum: string; stand: string | null; lizenz: string; url: string; datei: string | null }

export interface QuellenEingabe {
  index: Index | null;
  empfaenger: EmpfaengerIndex | null;
  personen: PersonIndex | null;
  vpi: { quelle?: string; stand?: string } | null;
  /** Zahl der Steuer-Modelle im Build. */
  steuern: number;
  /** Erklärtexte (Stand je Text). */
  texte: Texte | null;
}

const DL_DE = "Datenlizenz Deutschland – Namensnennung 2.0";

function datum(s: string | null | undefined): string | null {
  return s ? s.slice(0, 10) : null;
}

function spanne(jahre: number[] | undefined): string {
  if (!jahre?.length) return "–";
  const von = Math.min(...jahre), bis = Math.max(...jahre);
  return von === bis ? String(von) : `${von}–${bis}`;
}

export function quellenTabelle(e: QuellenEingabe): QuellenZeile[] {
  const erzeugt = datum(e.index?.erzeugt);
  const haushaltZeitraum = e.index ? `${spanne(e.index.jahre)}${e.index.ist_bis ? `, Ist bis ${e.index.ist_bis}` : ""}` : "–";
  const svJahre = e.index?.sv_jahre?.length ? e.index.sv_jahre.join(", ") : null;
  const letztesJahr = e.index?.jahre?.length ? Math.max(...e.index.jahre) : null;
  const texteStand = e.texte ? Object.values(e.texte).map((t) => t.stand).filter(Boolean).sort().at(-1) ?? null : null;
  return [
    { quelle: "Bundeshaushalt (bundeshaushalt.de, BMF)", inhalt: `Soll je Titel aller Einzelpläne, Ist aus der Haushaltsrechnung; Zeitreihe je Einzelplan, Kapitel und Titel${svJahre ? `; Wirtschaftspläne der Sondervermögen für ${svJahre}` : ""}`, zeitraum: haushaltZeitraum, stand: erzeugt, lizenz: DL_DE, url: "https://www.bundeshaushalt.de", datei: "/data/zeitreihe.json" },
    { quelle: "Sozialkassen (DRV, BMG KJ 1 und SPV-Finanzentwicklung, BA-Geschäftsberichte)", inhalt: "Einnahmen und Ausgaben von Rente, Krankenversicherung, Pflege und Bundesagentur je Jahr, Quelle je Datei vermerkt", zeitraum: e.index ? spanne(e.index.jahre) : "–", stand: erzeugt, lizenz: "Amtliche Veröffentlichungen", url: "https://www.deutsche-rentenversicherung.de/DRV/DE/Experten/Zahlen-und-Fakten/zahlen-und-fakten_node.html", datei: letztesJahr ? `/data/sozialkassen/${letztesJahr}.json` : null },
    { quelle: "Lobbyregister des Deutschen Bundestages", inhalt: "Eintragungen, Zuwendungen des Bundes (Spannen), gesetzliche Vertreter, Jahresabschlüsse; Eigenangaben der Organisationen", zeitraum: "laufende Versionen", stand: datum(e.empfaenger?.stand), lizenz: "Amtliche Veröffentlichung (§ 1 LobbyRG)", url: "https://www.lobbyregister.bundestag.de", datei: "/data/empfaenger/index.json" },
    { quelle: "Förderkatalog des Bundes", inhalt: "Projektförderung (Kennzeichen, Ressort, Laufzeit, Bundesanteil); höchstens 100 Projekte je Suche", zeitraum: "laufende Projekte", stand: datum(e.empfaenger?.stand), lizenz: DL_DE, url: "https://foerderportal.bund.de/foekat/", datei: "/data/empfaenger/index.json" },
    { quelle: "Biografien auf bundestag.de", inhalt: "Mandate, Fraktion, Ausschüsse, veröffentlichungspflichtige Angaben der Abgeordneten (Selbstauskünfte)", zeitraum: "21. Wahlperiode", stand: datum(e.personen?.stand), lizenz: "Amtliche Veröffentlichung", url: "https://www.bundestag.de/abgeordnete", datei: "/data/personen/index.json" },
    { quelle: "Kabinett (bundesregierung.de) und Pflegedatei", inhalt: "Mitglieder der Bundesregierung, Staatssekretäre, Ernennungsdaten mit Fundstelle", zeitraum: "aktuelles Kabinett", stand: datum(e.personen?.stand), lizenz: "Amtliche Veröffentlichung", url: "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett", datei: null },
    { quelle: "Parteispenden (Bundestagspräsident)", inhalt: "Veröffentlichungspflichtige Spenden über 35.000 € (davor 50.000 €) an Parteien, Drucksachen", zeitraum: "seit 2015", stand: datum(e.personen?.stand), lizenz: "Amtliche Veröffentlichung", url: "https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000", datei: null },
    { quelle: "Verbraucherpreisindex (Destatis)", inhalt: "Preisbereinigung für den Zeitvergleich", zeitraum: "ab 2015", stand: datum(e.vpi?.stand), lizenz: DL_DE, url: e.vpi?.quelle ?? "https://www.destatis.de", datei: "/data/vpi.json" },
    { quelle: "Steuer-Modelle", inhalt: `${e.steuern} Modelle mit Annahmen, jede mit Quelle und Basisjahr (BMF, DIW, Drucksachen)`, zeitraum: "Basisjahr je Modell", stand: null, lizenz: "Quellen je Annahme", url: "https://www.bundesfinanzministerium.de", datei: "/data/steuern.json" },
    { quelle: "Erklärtexte", inhalt: "Kurze Einordnungen zu großen Titeln mit Belegen", zeitraum: "–", stand: texteStand, lizenz: "CC BY 4.0", url: "https://github.com/eis2k/Bundeshaushaltstracker", datei: "/data/texte.json" },
  ];
}

/** Bekannte Lücken (Spec §4.12), benannt statt geschätzt. */
export const LUECKEN: string[] = [
  "Kostenpauschale der Abgeordneten für 2025 und B 11 nach März 2024 sind nicht erfasst; die Bezüge bleiben dort ohne Wert.",
  "Ernennungsdaten einzelner Regierungsmitglieder sind nicht mit Urkunde oder Protokoll belegt; sie erscheinen nur im aktuellen Jahr, mit Hinweis.",
  "Der Förderkatalog liefert höchstens 100 Projekte je Suche; Summen sind Untergrenzen.",
  "Empfänger erscheinen nur, wo ein Haushaltstitel sie in der Zweckbestimmung nennt oder das Lobbyregister eine Zuwendung angibt; Sammeltitel bleiben ohne Empfänger.",
  "Lobbyregister-Beträge sind Spannen und Eigenangaben; gezeigt wird die Untergrenze.",
  "Ressortzuschnitte ändern sich zwischen Wahlperioden; Zeitreihen je Einzelplan sind nicht um Ressortwechsel bereinigt.",
];

export const LIZENZEN: { was: string; lizenz: string; url: string }[] = [
  { was: "Quellcode des Bundeshaushaltstrackers", lizenz: "MIT", url: "https://github.com/eis2k/Bundeshaushaltstracker" },
  { was: "Aufbereitete Daten und Texte", lizenz: "CC BY 4.0", url: "https://creativecommons.org/licenses/by/4.0/deed.de" },
  { was: "Amtliche Ursprungsdaten", lizenz: "überwiegend Datenlizenz Deutschland 2.0", url: "https://www.govdata.de/dl-de/by-2-0" },
  { was: "Symbole (Lucide)", lizenz: "ISC", url: "https://lucide.dev/license" },
  { was: "Diagramme (D3)", lizenz: "ISC", url: "https://github.com/d3/d3/blob/main/LICENSE" },
];
