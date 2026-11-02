/** Darstellung Hell | Dunkel | System (Spec §4.12): Wahl im Browser gespeichert (localStorage, kein Cookie), Vorgabe System. */

export type Theme = "hell" | "dunkel" | "system";

export const THEME_KEY = "bht-theme";

const REIHE: Theme[] = ["hell", "dunkel", "system"];

export function naechstes(t: Theme): Theme {
  return REIHE[(REIHE.indexOf(t) + 1) % REIHE.length];
}

export function lies(storage: Pick<Storage, "getItem"> | null): Theme {
  try {
    const v = storage?.getItem(THEME_KEY);
    return v === "hell" || v === "dunkel" || v === "system" ? v : "system";
  } catch {
    return "system";
  }
}

export function schreibe(storage: Pick<Storage, "setItem"> | null, t: Theme): void {
  try { storage?.setItem(THEME_KEY, t); } catch { /* Speicher gesperrt (privates Fenster): Wahl gilt nur für diese Sitzung */ }
}

/** Wert für `data-theme` am Wurzelelement; System → kein Attribut (prefers-color-scheme entscheidet). */
export function attribut(t: Theme): "light" | "dark" | null {
  return t === "hell" ? "light" : t === "dunkel" ? "dark" : null;
}

export const THEME_LABEL: Record<Theme, string> = { hell: "Hell", dunkel: "Dunkel", system: "System" };
