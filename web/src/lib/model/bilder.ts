/** Porträts und Logos (Spec §4.13): Verweise aus data/build/bilder.json, Tooltip mit Urheber und Lizenz, Bildnachweise. */

export interface Bild {
  datei: string;
  url: string;
  url_gross: string;
  seite: string;
  lizenz: string;
  lizenz_url: string | null;
  urheber: string;
  qid: string;
  art: "person" | "organisation";
}

export interface Bilder {
  stand: string;
  quelle: string;
  personen: Record<string, Bild>;
  organisationen: Record<string, Bild>;
  pruefliste: unknown[];
  verworfen: unknown[];
}

/** Bild zu einer Kennung „p:<Akte>“ oder „o:<Empfänger>“; sonst null. */
export function bildFuer(b: Bilder | null, id: string | undefined): Bild | null {
  if (!b || !id) return null;
  if (id.startsWith("p:")) return b.personen[id.slice(2)] ?? null;
  if (id.startsWith("o:")) return b.organisationen[id.slice(2)] ?? null;
  return null;
}

export function tooltip(b: Bild): string {
  return b.art === "organisation"
    ? `Logo: ${b.urheber}, ${b.lizenz} (Wikimedia Commons); Marke der Organisation`
    : `Foto: ${b.urheber}, ${b.lizenz} (Wikimedia Commons)`;
}

export interface Bildnachweis { datei: string; urheber: string; lizenz: string; lizenz_url: string | null; seite: string; verwendet: string[] }

/** Jede Datei genau einmal, mit den Namen, bei denen sie erscheint (`namen`: Kennung → Name), nach Datei sortiert. */
export function bildnachweise(b: Bilder | null, namen: Record<string, string>): Bildnachweis[] {
  if (!b) return [];
  const je = new Map<string, Bildnachweis>();
  const alle: [string, Bild][] = [
    ...Object.entries(b.personen).map(([id, x]) => [`p:${id}`, x] as [string, Bild]),
    ...Object.entries(b.organisationen).map(([id, x]) => [`o:${id}`, x] as [string, Bild]),
  ];
  for (const [id, x] of alle) {
    const n = je.get(x.datei) ?? { datei: x.datei, urheber: x.urheber, lizenz: x.lizenz, lizenz_url: x.lizenz_url, seite: x.seite, verwendet: [] };
    const name = namen[id] ?? id;
    if (!n.verwendet.includes(name)) n.verwendet.push(name);
    je.set(x.datei, n);
  }
  return [...je.values()].map((n) => ({ ...n, verwendet: [...n.verwendet].sort((a, c) => a.localeCompare(c, "de")) })).sort((a, c) => a.datei.localeCompare(c.datei, "de"));
}
