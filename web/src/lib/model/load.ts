import type { GesetzFreiMap, Index, Preset, YearData } from "./types";

const BASE = `${import.meta.env.BASE_URL ?? "/"}data/`;
const cache = new Map<string, Promise<unknown>>();

async function getJson<T>(name: string): Promise<T> {
  if (!cache.has(name)) {
    cache.set(name, fetch(BASE + name).then((r) => {
      if (!r.ok) throw new Error(`Daten nicht ladbar: ${name} (${r.status})`);
      return r.json();
    }));
  }
  return cache.get(name) as Promise<T>;
}

export const loadIndex = () => getJson<Index>("index.json");
export const loadYear = (jahr: number) => getJson<YearData>(`bund/${jahr}.json`);
export const loadPresets = async () => (await getJson<{ presets: Preset[] }>("presets.json")).presets;
export const loadGesetzFrei = async (): Promise<GesetzFreiMap> => {
  const raw = await getJson<{ eintraege: { id: string; status: "gesetz" | "frei"; grundlage: string; quelle: string }[] }>("gesetz_frei.json");
  return Object.fromEntries(raw.eintraege.map((e) => [e.id, { status: e.status, grundlage: e.grundlage, quelle: e.quelle }]));
};
