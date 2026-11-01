import { applyPresets } from "./model/presets";
import { balance as computeBalance, setFactor as applyFactor } from "./model/scenario";
import { decodeScenario, encodeScenario, knownIds, type TopfId } from "./model/share";
import { buildToepfe, type SozialkassenYear, type ToepfeResult } from "./model/toepfe";
import { defaultWerte, normalisiere, steuerEinnahmen, type SteuerErgebnis, type SteuerSzenario } from "./model/steuern";
import type { Balance, GesetzFreiMap, Index, NodeId, Preset, Scenario, SolverReport, ViewId, YearData } from "./model/types";
import { deflate, type Vpi, type Zeitreihe } from "./model/zeitreihe";
import type { Schnitt } from "./model/schnitte";

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
    } catch (e) {
      this.error = e instanceof Error ? e.message : String(e);
    } finally {
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

  setView(view: ViewId): void { this.view = view; }
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
    return encodeScenario(this.scenario, this.view, this.focus, this.schnitt, this.topf);
  }

  get istVerfuegbar(): boolean {
    return this.index?.ist_bis !== null && this.index?.ist_bis !== undefined && this.jahr <= this.index.ist_bis;
  }
}
