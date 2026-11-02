import { describe, expect, test } from "vitest";
import { attribut, lies, naechstes, schreibe } from "../src/lib/model/theme";

describe("theme (Dunkelmodus, Spec §4.12)", () => {
  test("naechstes: hell → dunkel → system → hell", () => {
    expect(naechstes("hell")).toBe("dunkel");
    expect(naechstes("dunkel")).toBe("system");
    expect(naechstes("system")).toBe("hell");
  });
  test("lies: Wert aus dem Speicher, sonst system; unbekannte Werte → system", () => {
    expect(lies({ getItem: () => "dunkel" })).toBe("dunkel");
    expect(lies({ getItem: () => "x" })).toBe("system");
    expect(lies({ getItem: () => null })).toBe("system");
    expect(lies(null)).toBe("system");
    expect(lies({ getItem: () => { throw new Error("blocked"); } })).toBe("system");
  });
  test("schreibe und attribut", () => {
    const store: Record<string, string> = {};
    schreibe({ setItem: (k, v) => { store[k] = v; } }, "dunkel");
    expect(store["bht-theme"]).toBe("dunkel");
    expect(attribut("dunkel")).toBe("dark");
    expect(attribut("hell")).toBe("light");
    expect(attribut("system")).toBeNull();
  });
});
