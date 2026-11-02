/** Modul-Store für die Bildverweise (Spec §4.13), damit Avatar ohne App-Zugriff an Porträts und Logos kommt. */
import type { Bilder } from "../model/bilder";

export const bilderStore = $state<{ wert: Bilder | null }>({ wert: null });

export function setBilder(b: Bilder | null): void {
  bilderStore.wert = b;
}
