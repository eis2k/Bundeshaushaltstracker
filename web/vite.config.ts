import { svelte } from "@sveltejs/vite-plugin-svelte";
import { existsSync, readFileSync } from "node:fs";
import { resolve } from "node:path";
import { defineConfig, type Plugin } from "vitest/config";

/** Liefert im Dev-Server die Build-Dateien der Pipeline unter /data/ aus (../data/build). */
function serveBuildData(): Plugin {
  const root = resolve(__dirname, "../data/build");
  return {
    name: "serve-build-data",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        if (!req.url?.startsWith("/data/")) return next();
        const file = resolve(root, decodeURIComponent(req.url.slice("/data/".length).split("?")[0]));
        if (!file.startsWith(root) || !existsSync(file)) { res.statusCode = 404; return res.end("not found"); }
        res.setHeader("Content-Type", "application/json; charset=utf-8");
        res.end(readFileSync(file));
      });
    },
  };
}

export default defineConfig({
  plugins: [svelte(), serveBuildData()],
  resolve: { conditions: process.env.VITEST ? ["browser"] : undefined },
  test: { environment: "node", include: ["tests/**/*.test.ts"] },
});
