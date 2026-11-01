import { applyPresets } from "./model/presets";
import { balance as computeBalance, setFactor as applyFactor } from "./model/scenario";
import { decodeScenario, encodeScenario, knownIds } from "./model/share";
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
}

export type Stand = "soll" | "ist";

function withIst(data: YearData): YearData {
  return { ...data, rows: data.rows.map((r) => (r.ist === null ? r : { ...r, soll: r.ist })) };
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
  balance = $derived<Balance | null>(this.viewData ? computeBalance(this.viewData, this.factors, this.scenario.includeSv) : null);

  constructor(private loader: Loader) {}

  async init(hash: string): Promise<void> {
    this.loading = true;
    try {
      const [index, presets, gesetz] = await Promise.all([this.loader.loadIndex(), this.loader.loadPresets(), this.loader.loadGesetzFrei()]);
      this.index = index;
      this.presets = presets;
      this.gesetz = gesetz;
      const latest = index.jahre[index.jahre.length - 1];
      const probe = await this.loader.loadYear(latest);
      const decoded = decodeScenario(hash, probe);
      const jahr = index.jahre.includes(decoded.scenario.jahr) ? decoded.scenario.jahr : latest;
      this.data = jahr === latest ? probe : await this.loader.loadYear(jahr);
      const final = jahr === latest ? decoded : decodeScenario(hash, this.data);
      this.jahr = jahr;
      this.view = final.view;
      this.schnitt = final.schnitt;
      this.focus = final.focus;
      this.scenario = { ...final.scenario, jahr };
      this.unknownIds = final.unknownIds;
      this.fromShare = hash.replace(/^#/, "").length > 0 && (Object.keys(final.scenario.factors).length > 0 || final.scenario.presets.length > 0);
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

  togglePreset(id: string): void {
    const presets = this.scenario.presets.includes(id)
      ? this.scenario.presets.filter((p) => p !== id)
      : [...this.scenario.presets, id];
    this.scenario = { ...this.scenario, presets };
  }

  setView(view: ViewId): void { this.view = view; }
  setSchnitt(schnitt: Schnitt): void {
    if (schnitt !== this.schnitt) { this.focus = []; this.selected = null; }
    this.schnitt = schnitt;
  }
  setFocus(path: NodeId[]): void { this.focus = path; }
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
    this.scenario = { ...this.scenario, factors: {}, presets: [] };
    this.unknownIds = [];
    this.fromShare = false;
  }

  toHash(): string {
    return encodeScenario(this.scenario, this.view, this.focus, this.schnitt);
  }

  get istVerfuegbar(): boolean {
    return this.index?.ist_bis !== null && this.index?.ist_bis !== undefined && this.jahr <= this.index.ist_bis;
  }
}
