import { applyPresets } from "./model/presets";
import { attribut, lies, schreibe, type Theme } from "./model/theme";
import { balance as computeBalance, setFactor as applyFactor } from "./model/scenario";
import { decodeScenario, encodeScenario, knownIds, type TopfId } from "./model/share";
import { buildToepfe, type SozialkassenYear, type ToepfeResult } from "./model/toepfe";
import { defaultWerte, normalisiere, steuerEinnahmen, type SteuerErgebnis, type SteuerSzenario } from "./model/steuern";
import type { Balance, GesetzFreiMap, Index, NodeId, Preset, Scenario, SolverReport, ViewId, YearData } from "./model/types";
import { deflate, type Vpi, type Zeitreihe } from "./model/zeitreihe";
import type { Schnitt } from "./model/schnitte";
import type { EmpfaengerIndex, EmpfaengerSeite } from "./model/empfaenger";
import type { Akte, PersonIndex } from "./model/personen";
import type { Umfeld } from "./model/netz";
import type { NavEintrag } from "./model/navigation";
import { aktuellesGlied, pfad as pfadAus, type Glied, type Ziel } from "./model/pfad";

export interface Loader {
  loadIndex: () => Promise<Index>;
  loadYear: (jahr: number) => Promise<YearData>;
  loadPresets: () => Promise<Preset[]>;
  loadGesetzFrei: () => Promise<GesetzFreiMap>;
  loadZeitreihe?: () => Promise<Zeitreihe>;
  loadVpi?: () => Promise<Vpi>;
  loadSozialkassen?: (jahr: number) => Promise<SozialkassenYear>;
  loadSteuern?: () => Promise<SteuerSzenario[]>;
  loadTexte?: () => Promise<Record<string, { text: string; quelle: string[]; stand: string }>>;
  loadKonkordanz?: () => Promise<Record<string, { ab: number; hinweis: string; quelle?: string }>>;
  loadEmpfaengerIndex?: () => Promise<EmpfaengerIndex>;
  loadEmpfaenger?: (id: string) => Promise<EmpfaengerSeite>;
  loadPersonIndex?: () => Promise<PersonIndex>;
  loadPersonShard?: (shard: string) => Promise<Record<string, Akte>>;
  loadNetzIndex?: () => Promise<Record<string, string>>;
  loadNetzShard?: (shard: string) => Promise<Record<string, Umfeld>>;
}

export type Stand = "soll" | "ist";

function withIst(data: YearData): YearData {
  return { ...data, rows: data.rows.map((r) => (r.ist === null ? r : { ...r, soll: r.ist })) };
}

function scaleSozialkassen(sk: SozialkassenYear, vpi: Vpi, bezugsjahr: number): SozialkassenYear {
  if (!vpi[sk.jahr] || !vpi[bezugsjahr] || sk.jahr === bezugsjahr) return sk;
  const f = (v: number) => Math.round(deflate(v, sk.jahr, bezugsjahr, vpi));
  const toepfe = Object.fromEntries(Object.entries(sk.toepfe).map(([id, t]) => [id, {
    ...t,
    einnahmen: t.einnahmen.map((e) => ({ ...e, betrag: f(e.betrag) })),
    ausgaben: t.ausgaben.map((e) => ({ ...e, betrag: f(e.betrag) })),
  }]));
  return { ...sk, toepfe };
}

/** Rechnet alle Beträge eines Jahres in Preise des Bezugsjahres um. */
function inPrices(data: YearData, vpi: Vpi, bezugsjahr: number): YearData {
  if (!vpi[data.jahr] || !vpi[bezugsjahr] || data.jahr === bezugsjahr) return data;
  const f = (v: number | null) => (v === null ? null : Math.round(deflate(v, data.jahr, bezugsjahr, vpi)));
  return { ...data, rows: data.rows.map((r) => ({ ...r, soll: f(r.soll) ?? 0, ist: f(r.ist) })) };
}

/** Gesamter Nutzerzustand der App; der Rechenkern hängt als abgeleitete Werte daran. */
export class AppState {
  jahr = $state(2025);
  view = $state<ViewId>("fluss");
  focus = $state<NodeId[]>([]);
  selected = $state<NodeId | null>(null);
  scenario = $state<Scenario>({ jahr: 2025, factors: {}, presets: [], includeSv: false });
  stand = $state<Stand>("soll");
  schnitt = $state<Schnitt>("ressort");
  /** Welcher Topf im Fluss gezeigt wird: Gesamtfluss, Bund oder eine Sozialkasse. */
  topf = $state<TopfId>("gesamt");
  sozialkassen = $state<SozialkassenYear | null>(null);
  steuern = $state<SteuerSzenario[]>([]);
  texte = $state<Record<string, { text: string; quelle: string[]; stand: string }>>({});
  konkordanz = $state<Record<string, { ab: number; hinweis: string; quelle?: string }>>({});
  index = $state<Index | null>(null);
  /** Darstellung Hell | Dunkel | System (Spec §4.12), aus dem Browser-Speicher. */
  theme = $state<Theme>("system");

  setTheme(t: Theme): void {
    this.theme = t;
    if (typeof localStorage !== "undefined") schreibe(localStorage, t);
    if (typeof document !== "undefined") { const a = attribut(t); if (a) document.documentElement.dataset.theme = a; else delete document.documentElement.dataset.theme; }
  }

  /** Vorjahr des gewählten Jahres (für die Veränderung auf dem Dashboard), nachgeladen. */
  vorjahrData = $state<YearData | null>(null);
  data = $state<YearData | null>(null);
  presets = $state<Preset[]>([]);
  gesetz = $state<GesetzFreiMap>({});
  unknownIds = $state<NodeId[]>([]);
  fromShare = $state(false);
  loading = $state(false);
  error = $state<string | null>(null);
  zeitreihe = $state<Zeitreihe | null>(null);
  vpi = $state<Vpi | null>(null);
  /** Inflationsbereinigt: alle Beträge in Preisen des letzten Jahres. */
  real = $state(false);
  /** Empfänger (Stufe 2): Index, geöffnete Seite, Filter der Liste. */
  empfaengerIndex = $state<EmpfaengerIndex | null>(null);
  empfaengerId = $state<string | null>(null);
  empfaengerSeite = $state<EmpfaengerSeite | null>(null);
  empfaengerFehlt = $state<string | null>(null);
  empfaengerFilterEpl = $state<string | null>(null);
  empfaengerByTitel = $derived<Record<string, { id: string; name: string }>>(this.empfaengerIndex?.titel ?? {});
  /** Personen und Netz (Stufe 3). */
  personIndex = $state<PersonIndex | null>(null);
  akteId = $state<string | null>(null);
  akte = $state<Akte | null>(null);
  akteFehlt = $state<"nicht freigeschaltet" | "unbekannt" | null>(null);
  netzIndex = $state<Record<string, string> | null>(null);
  netzStart = $state<string | null>(null);
  netz = $state<Umfeld | null>(null);
  netzFehlt = $state<string | null>(null);
  /** Netzansicht ohne gewählten Knoten (Link `a=netz` ohne `n=`). */
  netzLeer = $derived(this.view === "netz" && !this.netzStart);
  /** Recherchepfad (Spec §4.10): die tatsächliche Spur der Klicks im Inhalt; Seitenleiste und init leeren sie. */
  spur = $state<Glied[]>([]);
  private springt = false;
  glied = $derived<Glied>(aktuellesGlied({
    view: this.view, topf: this.topf, focus: this.focus, selected: this.selected,
    eplNamen: this.data?.epl ?? {}, titelNamen: this.titelNamen(), topfNamen: this.topfNamen(),
    empfaengerId: this.empfaengerId, empfaengerName: this.empfaengerSeite?.name ?? null, empfaengerFilterEpl: this.empfaengerFilterEpl,
    akteId: this.akteId, akteName: this.akte?.name ?? null, netzStart: this.netzStart,
    netzLabel: this.netz?.knoten.find((k) => k.id === this.netz?.start)?.label ?? null,
  }));
  pfad = $derived<Glied[]>(pfadAus(this.spur, this.glied));

  bezugsjahr = $derived(this.index ? this.index.jahre[this.index.jahre.length - 1] : this.jahr);
  viewData = $derived<YearData | null>(this.data
    ? (() => {
        const base = this.stand === "ist" ? withIst(this.data) : this.data;
        return this.real && this.vpi ? inPrices(base, this.vpi, this.bezugsjahr) : base;
      })()
    : null);
  applied = $derived<{ factors: Record<NodeId, number>; solver: SolverReport | null }>(
    this.viewData ? applyPresets(this.viewData, this.scenario, this.presets, this.gesetz) : { factors: {}, solver: null },
  );
  factors = $derived(this.applied.factors);
  solver = $derived(this.applied.solver);
  aktiveSteuern = $derived<SteuerErgebnis>(steuerEinnahmen(this.steuern, this.scenario.steuern));
  balance = $derived<Balance | null>(this.viewData ? computeBalance(this.viewData, this.factors, this.scenario.includeSv, this.aktiveSteuern.bund) : null);
  /** Sozialkassen des Jahres, bei Inflationsbereinigung in Preisen des Bezugsjahres. */
  viewSozialkassen = $derived<SozialkassenYear | null>(this.sozialkassen && this.sozialkassen.jahr === this.jahr
    ? (this.real && this.vpi ? scaleSozialkassen(this.sozialkassen, this.vpi, this.bezugsjahr) : this.sozialkassen) : null);
  toepfe = $derived<ToepfeResult | null>(this.viewData && this.viewSozialkassen
    ? buildToepfe(this.viewData, this.viewSozialkassen, this.factors, this.scenario.includeSv) : null);

  constructor(private loader: Loader) {}

  async init(hash: string): Promise<void> {
    this.loading = true;
    if (typeof localStorage !== "undefined") this.setTheme(lies(localStorage));
    this.springt = true;   // beim Laden eines Links entsteht keine Spur
    try {
      const [index, presets, gesetz, steuern] = await Promise.all([
        this.loader.loadIndex(), this.loader.loadPresets(), this.loader.loadGesetzFrei(),
        this.loader.loadSteuern ? this.loader.loadSteuern().catch(() => [] as SteuerSzenario[]) : Promise.resolve([] as SteuerSzenario[]),
      ]);
      this.index = index;
      this.presets = presets;
      this.gesetz = gesetz;
      this.steuern = steuern;
      if (this.loader.loadTexte) this.loader.loadTexte().then((t) => (this.texte = t)).catch(() => undefined);
      if (this.loader.loadKonkordanz) this.loader.loadKonkordanz().then((k) => (this.konkordanz = k)).catch(() => undefined);
      void this.ensureEmpfaenger();
      const latest = index.jahre[index.jahre.length - 1];
      const probe = await this.loader.loadYear(latest);
      const steuerIds = steuern.map((s) => s.id);
      const decoded = decodeScenario(hash, probe, steuerIds);
      const jahr = index.jahre.includes(decoded.scenario.jahr) ? decoded.scenario.jahr : latest;
      this.data = jahr === latest ? probe : await this.loader.loadYear(jahr);
      const final = jahr === latest ? decoded : decodeScenario(hash, this.data, steuerIds);
      if (final.scenario.steuern) {
        const bereinigt = normalisiere(steuern, final.scenario.steuern);
        final.scenario.steuern = Object.keys(bereinigt).length ? bereinigt : undefined;
      }
      this.jahr = jahr;
      this.view = final.view;
      this.schnitt = final.schnitt;
      this.topf = final.topf;
      // Ein geteilter Fokuspfad öffnet den letzten Knoten auch im Panel
      this.selected = final.focus.length ? final.focus[final.focus.length - 1] : null;
      await this.loadSk(jahr);
      this.focus = final.focus;
      this.scenario = { ...final.scenario, jahr };
      this.unknownIds = final.unknownIds;
      this.fromShare = hash.replace(/^#/, "").length > 0 && (Object.keys(final.scenario.factors).length > 0 || final.scenario.presets.length > 0 || Object.keys(final.scenario.steuern ?? {}).length > 0);
      this.error = null;
      if (final.view === "empfaenger" || final.empfaenger) {
        await this.ensureEmpfaenger();
        if (final.empfaenger) await this.openEmpfaenger(final.empfaenger);
      }
      if (final.view === "personen" || final.person) {
        await this.ensurePersonen();
        if (final.person) await this.openAkte(final.person);
      }
      if (final.view === "netz" && final.netz) await this.openNetz(final.netz);
    } catch (e) {
      this.error = e instanceof Error ? e.message : String(e);
    } finally {
      this.spur = [];
      this.springt = false;
      this.loading = false;
    }
  }

  async setJahr(jahr: number): Promise<void> {
    if (jahr === this.jahr && this.data) return;
    this.loading = true;
    try {
      const data = await this.loader.loadYear(jahr);
      this.data = data;
      this.jahr = jahr;
      await this.loadSk(jahr);
      this.scenario = { ...this.scenario, jahr };
      const known = knownIds(data);
      this.unknownIds = Object.keys(this.scenario.factors).filter((id) => !known.has(id));
      if (this.index?.ist_bis !== null && this.index?.ist_bis !== undefined && jahr > this.index.ist_bis) this.stand = "soll";
      this.focus = this.focus.filter((id) => known.has(id));
      if (this.selected && !known.has(this.selected)) this.selected = null;
      this.error = null;
    } catch (e) {
      this.error = e instanceof Error ? e.message : String(e);
    } finally {
      this.loading = false;
    }
  }

  setFactor(id: NodeId, factor: number): void {
    this.scenario = applyFactor(this.scenario, id, factor);
  }

  toggleSteuer(id: string): void {
    const steuern = { ...(this.scenario.steuern ?? {}) };
    if (steuern[id]) delete steuern[id];
    else {
      const s = this.steuern.find((x) => x.id === id);
      if (!s) return;
      steuern[id] = defaultWerte(s);
    }
    this.scenario = { ...this.scenario, steuern: Object.keys(steuern).length ? steuern : undefined };
  }

  setAnnahme(id: string, key: string, wert: number): void {
    const aktuell = this.scenario.steuern?.[id];
    if (!aktuell) return;
    this.scenario = { ...this.scenario, steuern: { ...this.scenario.steuern, [id]: { ...aktuell, [key]: wert } } };
  }

  togglePreset(id: string): void {
    const presets = this.scenario.presets.includes(id)
      ? this.scenario.presets.filter((p) => p !== id)
      : [...this.scenario.presets, id];
    this.scenario = { ...this.scenario, presets };
  }

  /** Sprung in den Geldfluss aus dem Inhalt heraus (Akte, Empfänger-Seite, Netz, Ministerien, Zeitvergleich): merkt die verlassene Seite. */
  zeigeImFluss(focus: NodeId[], selected: NodeId | null = null): void {
    this.merke();
    this.setTopf("bund");
    this.focus = focus;
    this.selected = selected ?? focus[focus.length - 1] ?? null;
    this.setView("fluss");
  }

  /** Reiter der Unteransichten (Fluss/Karte/Säulen, Personen/Netz): Navigation, keine Spur. */
  waehleUnteransicht(view: ViewId): void {
    this.spur = [];
    if (view === "personen") this.openPersonenListe();
    else if (view === "netz") { this.netz = null; this.netzStart = null; this.netzFehlt = null; this.setView("netz"); }
    else this.setView(view);
  }

  /** Hauptnavigation (Seitenleiste / untere Leiste). */
  waehle(eintrag: NavEintrag): void {
    if (eintrag.view === "empfaenger") this.openEmpfaengerListe();
    else if (eintrag.view === "personen") this.openPersonenListe();
    else this.setView(eintrag.view);
    this.spur = [];
  }

  setView(view: ViewId): void {
    this.view = view;
    if (view === "empfaenger") void this.ensureEmpfaenger();
    if (view === "personen") void this.ensurePersonen();
  }

  private titelNamen(): Record<string, string> {
    const out: Record<string, string> = {};
    const data = this.data;
    if (!data) return out;
    for (const id of [...this.focus, this.selected]) {
      if (!id || /^\d{2}$/.test(id)) continue;
      const row = data.rows.find((r) => r.id === id);
      if (row) out[id] = row.text;
      else if (/^\d{2}-\d{4}$/.test(id)) out[id] = data.kap[id.slice(3)] ?? `Kapitel ${id.slice(3)}`;
    }
    return out;
  }
  private topfNamen(): Record<string, string> {
    const out: Record<string, string> = { gesamt: "Gesamtfluss", bund: "Bund" };
    for (const t of this.toepfe?.toepfe ?? []) out[t.id] = t.kurz;
    return out;
  }
  /** Hängt die verlassene Seite an die Spur (Navigation aus dem Inhalt heraus). */
  private merke(): void {
    if (this.springt) return;
    const g = this.glied;
    const letztes = this.spur[this.spur.length - 1];
    if (letztes && letztes.label === g.label) return;
    this.spur = [...this.spur, g].slice(-8);
  }
  /** Springt auf Glied `i` der Spur zurück und kürzt die Spur dorthin. */
  async springe(i: number): Promise<void> {
    const g = this.spur[i];
    if (!g) return;
    this.spur = this.spur.slice(0, i);
    this.springt = true;
    try {
      await this.gehe(g.ziel);
    } finally {
      this.springt = false;
    }
  }
  private async gehe(z: Ziel): Promise<void> {
    if (z.art === "haushalt") { this.setTopf(z.topf); this.focus = z.focus; this.selected = z.focus[z.focus.length - 1] ?? null; this.setView(z.view); }
    else if (z.art === "empfaengerliste") this.openEmpfaengerListe(z.epl ? { epl: z.epl } : undefined);
    else if (z.art === "empfaenger") await this.openEmpfaenger(z.id);
    else if (z.art === "personenliste") this.openPersonenListe();
    else if (z.art === "akte") await this.openAkte(z.id);
    else if (z.art === "netz") await this.openNetz(z.knoten);
    else this.setView("ministerien");
  }

  async ensureVorjahr(): Promise<void> {
    const vj = this.jahr - 1;
    if (this.vorjahrData?.jahr === vj || !(this.index?.jahre ?? []).includes(vj)) { if (this.vorjahrData?.jahr !== vj) this.vorjahrData = null; return; }
    try { const d = await this.loader.loadYear(vj); if (this.jahr - 1 === vj) this.vorjahrData = d; } catch { this.vorjahrData = null; }
  }

  async ensurePersonen(): Promise<void> {
    if (!this.personIndex && this.loader.loadPersonIndex) {
      try { this.personIndex = await this.loader.loadPersonIndex(); } catch { this.personIndex = { stand: "", modus: "relevant", eintraege: [] }; }
    }
  }

  openPersonenListe(): void {
    this.view = "personen";
    this.akteId = null;
    this.akte = null;
    this.akteFehlt = null;
    void this.ensurePersonen();
  }

  /** Öffnet eine Akte; nicht freigeschaltete oder unbekannte Ids werden benannt statt zu scheitern. */
  async openAkte(id: string | null): Promise<void> {
    if (id && !(this.view === "personen" && this.akteId === id)) this.merke();
    this.view = "personen";
    await this.ensurePersonen();
    this.akte = null;
    this.akteId = null;
    this.akteFehlt = null;
    if (!id) return;
    const eintrag = this.personIndex?.eintraege.find((e) => e.id === id);
    if (!eintrag) { this.akteFehlt = "unbekannt"; return; }
    if (!eintrag.sichtbar) { this.akteFehlt = "nicht freigeschaltet"; return; }
    try {
      if (!this.loader.loadPersonShard) throw new Error("kein Loader");
      const sh = await this.loader.loadPersonShard(eintrag.shard);
      const a = sh[id];
      if (!a) { this.akteFehlt = "unbekannt"; return; }
      this.akte = a;
      this.akteId = id;
    } catch {
      this.akteFehlt = "unbekannt";
    }
  }

  /** Öffnet das Umfeld eines Knotens (p:, e:, m:, partei:). */
  async openNetz(knotenId: string | null): Promise<void> {
    if (knotenId && !(this.view === "netz" && this.netzStart === knotenId)) this.merke();
    this.view = "netz";
    this.netz = null;
    this.netzFehlt = null;
    this.netzStart = knotenId;
    if (!knotenId) return;
    try {
      if (!this.netzIndex && this.loader.loadNetzIndex) this.netzIndex = await this.loader.loadNetzIndex();
      const sh = this.netzIndex?.[knotenId];
      if (!sh || !this.loader.loadNetzShard) { this.netzFehlt = knotenId; return; }
      const data = await this.loader.loadNetzShard(sh);
      const u = data[knotenId];
      if (!u) { this.netzFehlt = knotenId; return; }
      this.netz = u;
    } catch {
      this.netzFehlt = knotenId;
    }
  }

  /** Verlässt das Netz zurück zum letzten Glied der Spur; ohne Spur zur Personenliste. */
  async closeNetz(): Promise<void> {
    this.netz = null;
    this.netzStart = null;
    this.netzFehlt = null;
    if (this.spur.length) await this.springe(this.spur.length - 1);
    else this.openPersonenListe();
  }

  async ensureEmpfaenger(): Promise<void> {
    if (!this.empfaengerIndex && this.loader.loadEmpfaengerIndex) {
      try { this.empfaengerIndex = await this.loader.loadEmpfaengerIndex(); } catch { this.empfaengerIndex = { stand: "", mit_personen: false, eintraege: [], titel: {} }; }
    }
  }

  /** Öffnet die Liste; `epl` filtert auf Empfänger, die Geld aus diesem Einzelplan erhalten. */
  openEmpfaengerListe(filter?: { epl?: string }): void {
    if (!(this.view === "empfaenger" && !this.empfaengerId && (this.empfaengerFilterEpl ?? null) === (filter?.epl ?? null))) this.merke();
    this.view = "empfaenger";
    this.empfaengerId = null;
    this.empfaengerSeite = null;
    this.empfaengerFehlt = null;
    this.empfaengerFilterEpl = filter?.epl ?? null;
    void this.ensureEmpfaenger();
  }

  /** Öffnet eine Empfänger-Seite; unbekannte Id → Liste mit Hinweis. */
  async openEmpfaenger(id: string | null): Promise<void> {
    if (id && !(this.view === "empfaenger" && this.empfaengerId === id)) this.merke();
    this.view = "empfaenger";
    await this.ensureEmpfaenger();
    if (!id) { this.openEmpfaengerListe(); return; }
    this.empfaengerFehlt = null;
    try {
      if (!this.loader.loadEmpfaenger) throw new Error("kein Loader");
      this.empfaengerSeite = await this.loader.loadEmpfaenger(id);
      this.empfaengerId = id;
    } catch {
      this.empfaengerSeite = null;
      this.empfaengerId = null;
      this.empfaengerFehlt = id;
    }
  }
  setTopf(topf: TopfId): void {
    if (topf !== this.topf) { this.focus = []; this.selected = null; }
    this.topf = topf;
  }
  private async loadSk(jahr: number): Promise<void> {
    if (!this.loader.loadSozialkassen) return;
    try { this.sozialkassen = await this.loader.loadSozialkassen(jahr); }
    catch { this.sozialkassen = null; }
  }
  setSchnitt(schnitt: Schnitt): void {
    if (schnitt !== this.schnitt) { this.focus = []; this.selected = null; }
    this.schnitt = schnitt;
  }
  setFocus(path: NodeId[]): void {
    this.focus = path;
    if (path.length) this.topf = "bund";   // ein Fokuspfad gehört immer zum Bundeshaushalt
  }
  setSelected(id: NodeId | null): void { this.selected = id; }
  setStand(stand: Stand): void { this.stand = stand; }
  async setReal(on: boolean): Promise<void> {
    if (on && !this.vpi && this.loader.loadVpi) this.vpi = await this.loader.loadVpi();
    this.real = on;
  }
  async ensureZeitreihe(): Promise<void> {
    if (!this.zeitreihe && this.loader.loadZeitreihe) this.zeitreihe = await this.loader.loadZeitreihe();
    if (!this.vpi && this.loader.loadVpi) this.vpi = await this.loader.loadVpi();
  }
  setIncludeSv(on: boolean): void { this.scenario = { ...this.scenario, includeSv: on }; }

  reset(): void {
    this.scenario = { ...this.scenario, factors: {}, presets: [], steuern: undefined };
    this.unknownIds = [];
    this.fromShare = false;
  }

  toHash(): string {
    return encodeScenario(this.scenario, this.view, this.focus, this.schnitt, this.topf, this.view === "empfaenger" ? this.empfaengerId : null,
                          this.view === "personen" ? this.akteId : null, this.view === "netz" ? this.netzStart : null);
  }

  get istVerfuegbar(): boolean {
    return this.index?.ist_bis !== null && this.index?.ist_bis !== undefined && this.jahr <= this.index.ist_bis;
  }
}
