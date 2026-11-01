import { describe, expect, test } from "vitest";
import { buildTreemap, treemapRoot } from "../src/lib/views/treemapData";
import { buildTree } from "../src/lib/model/tree";
import { fixtureYear, SUM_A_KERN } from "./fixtures";

describe("treemapRoot", () => {
  test("without focus the root is the whole Bund with Einzelpläne as children", () => {
    const tree = buildTree(fixtureYear, false);
    const root = treemapRoot(tree, {}, []);
    expect(root.id).toBe("bund");
    expect(root.children.map((c) => c.id).sort()).toEqual(["11", "14", "60"]);
    expect(root.minderausgaben).toBe(-50);
  });

  test("focus on a Kapitel makes it the root with Titel children, negative values clipped to 0", () => {
    const tree = buildTree(fixtureYear, false);
    const root = treemapRoot(tree, {}, ["60", "60-6001"]);
    expect(root.id).toBe("60-6001");
    expect(root.children[0].value).toBe(0);
    expect(root.minderausgaben).toBe(-50);
  });

  test("values follow the factors", () => {
    const tree = buildTree(fixtureYear, false);
    const root = treemapRoot(tree, { "11-1102-63681": 0.5 }, ["11", "11-1102"]);
    const t = root.children.find((c) => c.id === "11-1102-63681")!;
    expect(t.value).toBe(200);
    expect(t.original).toBe(400);
    expect(t.changed).toBe(true);
  });
});

describe("buildTreemap", () => {
  test("areas sum to the positive Ausgaben and every leaf has a rectangle", () => {
    const tree = buildTree(fixtureYear, false);
    const layout = buildTreemap(treemapRoot(tree, {}, []), 800, 400);
    const leaves = layout.leaves();
    expect(leaves.reduce((s, l) => s + (l.value ?? 0), 0)).toBe(SUM_A_KERN + 50);
    for (const l of leaves) {
      expect(l.x1).toBeGreaterThanOrEqual(l.x0);
      expect(l.y1).toBeGreaterThanOrEqual(l.y0);
      expect(l.x1).toBeLessThanOrEqual(800.001);
      expect(l.y1).toBeLessThanOrEqual(400.001);
    }
  });

  test("an unknown focus falls back to the Bund root", () => {
    const tree = buildTree(fixtureYear, false);
    expect(treemapRoot(tree, {}, ["99"]).id).toBe("bund");
  });
});
