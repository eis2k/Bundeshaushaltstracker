# Stufe 4b: Porträts und Logos Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Porträts der Abgeordneten und Regierungsmitglieder sowie Logos der Empfänger aus Wikidata/Wikimedia Commons mit Lizenz und Urheber anzeigen, als Verweise im Build, mit Bildnachweisen; Platzhalter bleiben, wo nichts Lizenziertes vorliegt.

**Architecture:** Pipeline-Modul `bilder.py` (SPARQL für Mitglieder des 21. Bundestages und für Lobbyregister-IDs, Wikidata-Suche für Regierungsmitglieder ohne Mandat, Commons `imageinfo` für Lizenzdaten) schreibt `data/build/bilder.json`; Rohantworten unter `data/raw/bilder/`. Das Web lädt `bilder.json` einmal und reicht Bilder über einen Modul-Store an `Avatar` (Prop `id`), das bei Fehlern auf Initialen zurückfällt.

**Tech Stack:** Python 3.13 (urllib, json, yaml), pytest; Svelte 5, TypeScript, vitest.

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md` §4.13 (Grundsatz §4.10).

## Global Constraints

- Nur Wikidata/Commons; nur Lizenzen CC0, CC BY, CC BY-SA (alle Versionen) und „Public domain“; alles andere `verworfen`.
- Zuordnung von Organisationen nur über die Lobbyregister-ID (P10301); Personen nur bei eindeutigem Namenstreffer in beiden Richtungen, sonst Prüfliste.
- Keine Bilddateien im Repository; `bilder.json` enthält nur Verweise. User-Agent `USER_AGENT` aus `portal.py`, Pausen zwischen Anfragen (≥ 0,5 s), SPARQL-Endpunkt `https://query.wikidata.org/sparql`.
- Tests ohne Netz (Fixtures, `http`-Parameter injizierbar). `uv run pytest -q` und `npm run check && npm test -- --run` grün vor jedem Commit.
- Branch `stufe-4b` nach dem Merge von 4d; Commit je Task; Ende: Review, Fix-Pass, ff-Merge, Push, Docker.

## Review Focus

1. Kein Bild ohne erlaubte Lizenz: `lizenz_erlaubt` lehnt „GFDL“, „Fair use“, leere Angaben und „CC BY-NC“ ab. Test Task 1.
2. Keine Verwechslung: gleicher Name zweimal im Index oder zweimal in Wikidata → kein Bild, Eintrag in der Prüfliste. Test Task 1.
3. Logos nur über P10301; ein Empfänger ohne Lobbyregister-Nummer bekommt kein Logo. Test Task 1.
4. Avatar fällt bei Ladefehler oder fehlendem Verweis auf Initialen zurück; `alt` ist der Name, Tooltip nennt Urheber und Lizenz. Test Task 2 (Modell `tooltip`), Browser.
5. Bildnachweise listen jede verwendete Datei genau einmal mit Commons-Link. Test Task 3.

---

### Task 1: Pipeline `bilder.py`, Pflegedatei, CLI

**Files:**
- Create: `pipeline/src/bhtracker/bilder.py`, `data/manual/bilder.yaml`, `pipeline/tests/test_bilder.py`, `pipeline/tests/fixtures/bilder_*.json` (kleine SPARQL-/imageinfo-Antworten)
- Modify: `pipeline/src/bhtracker/cli.py` (Unterbefehl `fetch-bilder`), `pipeline/src/bhtracker/personen.py` (`build_akten_und_netz` ruft `build_bilder` nach dem Index, wenn `raw/bilder` vorliegt)

**Interfaces (`bilder.py`):**
- `WP21 = "Q124661964"`, `SPARQL = "https://query.wikidata.org/sparql"`, `COMMONS_API = "https://commons.wikimedia.org/w/api.php"`, `WIKIDATA_API = "https://www.wikidata.org/w/api.php"`.
- `def lizenz_erlaubt(kurz: str) -> bool` – `True` für `CC0`, `CC BY …`, `CC BY-SA …`, `Public domain`; `False` sonst (auch `CC BY-NC…`, `GFDL`, leer).
- `def norm_person(name: str) -> str` – entfernt Titel (`Dr.`, `Prof.`, `Dr. h. c.`, `Dipl.-…`), mehrfachen Leerraum, Kleinschreibung; Umlaute bleiben.
- `def zuordnen_personen(akten: list[dict], mdb: list[dict], suche: dict[str, list[dict]], manual: dict) -> tuple[dict[str, dict], list[dict]]` – `akten` = Index-Einträge (`id`, `name`, `sichtbar`, `arten`), `mdb` = Zeilen `{qid, label, bild}` aus SPARQL, `suche` = Name → Treffer `{qid, label, beschreibung, bild}` der Wikidata-Suche (für Regierungsmitglieder ohne Mandat); Ergebnis `{akte_id: {qid, datei}}` nur bei eindeutigem Treffer (Name genau einmal unter den sichtbaren Akten mit `arten` ∋ mdb oder regierung und genau einmal in `mdb` bzw. genau ein Suchtreffer mit `beschreibung` ~ /politiker/i); manuelle `zuordnungen` (`akte_id → qid`) gewinnen, `gesperrt` schließt aus; Prüfliste `[{akte_id, name, grund, kandidaten: [qid…]}]`.
- `def zuordnen_organisationen(empfaenger: list[dict], lobby: list[dict], manual: dict) -> dict[str, dict]` – `empfaenger` = Index-Einträge (`id`, `lobbyregister`), `lobby` = `{qid, lr, logo}`; Ergebnis `{empf_id: {qid, datei}}` nur mit Logo und nicht gesperrt.
- `def datei_aus_url(u: str) -> str` – `http://commons.wikimedia.org/wiki/Special:FilePath/Foo%20Bar.svg` → `Foo Bar.svg`.
- `def commons_meta(datei: str, info: dict) -> dict | None` – aus einer `imageinfo`-Seite: `{datei, url (thumburl ohne Query), url_gross (`https://commons.wikimedia.org/wiki/Special:FilePath/<datei>?width=256`), seite (`https://commons.wikimedia.org/wiki/File:<datei>`), lizenz (LicenseShortName), lizenz_url (LicenseUrl oder None), urheber (Artist ohne HTML, gekürzt auf 120 Zeichen; leer → "unbekannt" nur bei CC0/Public domain, sonst None → verworfen)}`; `None`, wenn `lizenz_erlaubt` falsch oder Urheber bei Attribution nötig fehlt.
- `def fetch_bilder(raw_dir: Path, akten: list[dict], empfaenger: list[dict], http: Callable[[str], bytes] = _urlopen_bytes, pause: float = 0.5) -> dict` – schreibt `raw/bilder/mdb.json` (SPARQL), `raw/bilder/lobby.json`, `raw/bilder/suche.json` (je Regierungsmitglied ohne Mandat), `raw/bilder/commons.json` (imageinfo aller Kandidatendateien, 50 je Anfrage, `iiprop=url|extmetadata&iiurlwidth=96`), `raw/bilder/stand.json` (`{stand}`); gibt Zählung zurück.
- `def build_bilder(manual_dir: Path, raw_dir: Path, out: Path, akten: list[dict], empfaenger: list[dict], stand: str) -> dict` – liest Rohdaten und Pflegedatei, schreibt `out/bilder.json`: `{stand, quelle: "Wikidata/Wikimedia Commons", personen: {id: Bild}, organisationen: {id: Bild}, pruefliste: [...], verworfen: [{id, datei, lizenz}]}`; Bild = `commons_meta` + `{qid, art}`; gibt `{personen, organisationen, pruefliste, verworfen}` als Zahlen zurück; ohne `raw/bilder` wird keine Datei geschrieben (und eine alte entfernt).
- `data/manual/bilder.yaml`: `stand`, `zuordnungen: []` (`{akte_id, qid, quelle}`), `gesperrt: []` (Ids mit Grund). `validate_bilder(data) -> list[str]`.
- CLI: `bht fetch-bilder [--raw …]` ruft `fetch_bilder` mit den Index-Einträgen aus `data/build` (Personen und Empfänger); `bht build` ruft `build_bilder` über `build_akten_und_netz`.

- [ ] **Step 1: Failing tests** (`test_bilder.py`): `lizenz_erlaubt` (CC BY-SA 4.0 ja, CC BY-NC 2.0 nein, GFDL nein, "" nein, Public domain ja); `norm_person("Dr. Johann David Wadephul") == "johann david wadephul"`; `zuordnen_personen` mit zwei gleichnamigen Akten → Prüfliste, eindeutig → Treffer, manuelle Zuordnung gewinnt, gesperrt → nichts; Regierungsmitglied ohne Mandat über `suche` mit einem Politiker-Treffer → Treffer, mit zwei → Prüfliste; `zuordnen_organisationen` ordnet nur über die R-Nummer zu, ohne Logo nichts; `commons_meta` aus Fixture liefert Urheber ohne HTML und Thumb-URL ohne Query, verwirft `CC BY-NC`; `build_bilder` mit Fixture-Rohdaten schreibt `bilder.json` mit `personen`/`organisationen`/`pruefliste`/`verworfen`; `fetch_bilder` mit Fake-`http` schreibt die vier Rohdateien und fragt Commons in Blöcken ≤ 50.
- [ ] **Step 2: Run** `uv run pytest tests/test_bilder.py -q` → FAIL.
- [ ] **Step 3: Implement.** **Step 4:** grün, `uv run pytest -q` grün.
- [ ] **Step 5: Commit** `git add pipeline data/manual/bilder.yaml && git commit -m "Stufe 4b: Pipeline bilder.py (Wikidata/Commons, Lizenzprüfung, Zuordnung, Prüfliste)"`

---

### Task 2: Web – Bilder im Avatar

**Files:**
- Create: `web/src/lib/model/bilder.ts`, `web/src/lib/ui/bilder.svelte.ts`, `web/tests/bilder.test.ts`
- Modify: `web/src/lib/model/load.ts` (`loadBilder`), `web/src/lib/state.svelte.ts` (`ensureBilder`, im `init` nachgeladen, Fehler → leer), `web/src/lib/ui/Avatar.svelte` (Prop `id?: string`), alle `Avatar`-Aufrufe (Dashboard, FlussSeite/Fluss-Karten, Verantwortung, EmpfaengerSeite, Ministerien, PolitikVerantwortung, Personen, EmpfaengerFluss, Akte, Netz) mit `id="p:<akteId>"` bzw. `id="o:<empfId>"`; `web/src/lib/views/Netz.svelte` (Personen- und Organisationsknoten mit Bild als `<image>` mit `clipPath`, sonst Form)

**Interfaces:**
- `export interface Bild { datei: string; url: string; url_gross: string; seite: string; lizenz: string; lizenz_url: string | null; urheber: string; qid: string; art: "person" | "organisation" }`
- `export interface Bilder { stand: string; quelle: string; personen: Record<string, Bild>; organisationen: Record<string, Bild>; pruefliste: unknown[]; verworfen: unknown[] }`
- `export function bildFuer(b: Bilder | null, id: string | undefined): Bild | null` – `"p:<id>"` → `personen`, `"o:<id>"` → `organisationen`, sonst `null`.
- `export function tooltip(b: Bild): string` – `Foto: <urheber>, <lizenz> (Wikimedia Commons)` bzw. `Logo: <urheber>, <lizenz> (Wikimedia Commons); Marke der Organisation`.
- `export function bildnachweise(b: Bilder | null): { datei: string; urheber: string; lizenz: string; seite: string; verwendet: string[] }[]` – jede Datei einmal, `verwendet` = Namen der Ids, sortiert nach Datei.
- `bilder.svelte.ts`: `export const bilderStore = $state<{ wert: Bilder | null }>({ wert: null })`.
- `Avatar.svelte`: `let { name, art = "person", size = 36, id }`; `bild = $derived(bildFuer(bilderStore.wert, id))`; `<img src={bild.url} alt={name} title={tooltip(bild)} loading="lazy" onerror={() => (fehler = true)}>` in derselben runden Form bzw. Kachel; bei `fehler` oder ohne Bild die Initialen.

- [ ] **Step 1: Failing tests**: `bildFuer` mit `p:`/`o:`/unbekannt; `tooltip` für Person und Organisation; `bildnachweise` fasst gleiche Datei zusammen und sortiert.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4:** grün; `npm run check` 0; Browser mit lokalem `bilder.json` (aus Task 1 Fixture oder echtem Fetch): Bild erscheint auf Dashboard und Politik, Ladefehler zeigt Initialen (im Test-HTML eine falsche URL).
- [ ] **Step 5: Commit** `git commit -am "Stufe 4b: Bilder im Avatar (Store, Tooltip mit Urheber und Lizenz, Rückfall auf Initialen)"`

---

### Task 3: Bildnachweise, Impressum, echte Daten, Abschluss

**Files:**
- Modify: `web/src/lib/views/Daten.svelte` (Abschnitt „Bildnachweise“ und Quellenzeile), `web/src/lib/model/quellen.ts` (Zeile Wikidata/Commons mit `stand` aus `bilder.stand`), `web/public/impressum.html`, `README.md`, Spec §7 (4b ✅), `data/raw/bilder/*` (abgerufen), `data/build/bilder.json`
- Test: `web/tests/quellen.test.ts` (Zeile Wikidata)

- [ ] **Step 1: Failing test**: `quellenTabelle({…, bilder: {stand: "2026-11-02"}})` enthält eine Zeile `quelle` ~ /Wikidata/ mit `stand === "2026-11-02"` und `datei === "/data/bilder.json"`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (Daten-Seite mit Tabelle der Bildnachweise aus `bildnachweise()`, Impressum-Satz „Porträts und Logos stammen aus Wikimedia Commons; Urheber und Lizenz stehen am Bild und unter Daten & Quellen → Bildnachweise.“). **Step 4:** `uv run bht fetch-bilder` (echt), Rebuild (`rebuild_stufe3.py`), `bilder.json` prüfen (Zahlen, Prüfliste), grün, `npm run build`.
- [ ] **Step 5: Commit** `git add -A web README.md docs data/build data/raw/bilder && git commit -m "Stufe 4b: Bildnachweise, Impressum, Daten (Porträts und Logos)"`

Danach: Review (Opus, Review Focus 1–5), Fix-Pass, ff-Merge nach `main`, Push, `docker compose up -d --build`.
