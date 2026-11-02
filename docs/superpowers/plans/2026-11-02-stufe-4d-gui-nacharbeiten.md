# Stufe 4d: GUI v3 – Nacharbeiten Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Die ohne neue Datenquelle baubaren Reste aus dem 16-Kachel-Mockup und dem 4c-Review: Investitionen-Linie und einheitliche Grundlagen auf dem Dashboard, Reiter „Nach Bereichen“ mit Ring, Ministerien-Tabelle mit Vorjahresänderung und Leitung im Wechseljahr, Seite „Daten & Quellen“, Dunkelmodus, eingebettetes Umfeld auf der Empfänger-Seite, Link-Kodierung des Topfes.

**Architecture:** Reine Web-Änderungen (Svelte 5, d3-shape für den Ring); Modelle als pure Funktionen mit vitest; keine Pipeline-Änderung (Investitionen aus den Titelreihen der Zeitreihe, Hauptgruppe 7/8). Theme über Design-Tokens in `app.css` und `data-theme` am `<html>`.

**Tech Stack:** Svelte 5 (runes), TypeScript, Vite, vitest, d3-shape, d3-force, lucide-svelte.

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md` §4.12 (und §4.10/§4.11 für Tokens und Rahmen).

## Global Constraints

- Beträge verschiedener Quellen werden nie addiert; jede Zahl trägt ihre Quelle (§2, §4.6a).
- Keine Wertungsfarben für Ausgabenänderungen; Parteifarben nur als Etikett (§4.11).
- Deutsche Beschriftung, Zahlen `de-DE` (`toLocaleString("de-DE")`, `fmtEuro`).
- Oberflächenfarben nur über Tokens aus `web/src/app.css`; Datenfarben aus `views/colors.ts` und `ui/Partei.svelte`.
- `npm run check` 0 Fehler/0 Warnungen, `npm test -- --run` grün, vor jedem Commit.
- Branch `stufe-4d` im selben Checkout; nach jedem Task Commit; am Ende Review, Fix-Pass, ff-Merge, Push, `docker compose up -d --build`.

## Review Focus

1. Investitionen-Linie zählt nur Ausgabetitel der Hauptgruppen 7 und 8 (Titelnummer beginnt mit 7 oder 8), Soll oder Ist strikt getrennt (kein `ist ?? soll`). Test Task 1.
2. Ministerien-Tabelle: Änderung zum Vorjahr nominal Soll gegen Soll, ohne Regler, „–“ ohne Vorjahr; Leitung im Wechseljahr nennt beide Personen mit Zeitraum, zuletzt amtierende zuerst. Test Task 3.
3. „Daten & Quellen“ zeigt nur Stände, die in den Daten stehen (keine erfundenen Abrufdaten); fehlende Angabe → „–“. Test Task 4.
4. Dunkelmodus: keine hart kodierte Oberflächenfarbe mehr in `views/*.svelte` und `ui/*.svelte` (nur Tokens); Wahl überlebt Neuladen ohne Cookie. Test Task 5 (Theme-Modell) und Suche `#[0-9a-f]{6}` in Ansichten.
5. Geteilter Link mit Fokus im Gesamt-Topf öffnet wieder den Gesamt-Topf; `f=` ohne `t=` bleibt Bundesfluss. Test Task 6.

---

### Task 1: Dashboard – Investitionen-Linie und einheitliche Grundlagen

**Files:**
- Modify: `web/src/lib/model/dashboard.ts`, `web/src/lib/views/Dashboard.svelte`, `web/src/lib/ui/MiniFluss.svelte`, `web/src/lib/ui/HerkunftVerwendung.svelte`
- Test: `web/tests/dashboard.test.ts`

**Interfaces:**
- `entwicklungIndex(z: Zeitreihe, stand: "soll" | "ist"): { jahr: number; gesamt: number | null; investitionen: number | null }[]` – `investitionen` = Summe der Titelreihen `z.titel` mit `art === "A"`, ohne `sv`, deren Titelnummer (dritter Teil der Id, `id.split("-")[2]`) mit `7` oder `8` beginnt, als Index (erstes Jahr mit Wert = 100); bei `stand === "ist"` nur Ist, ein fehlendes Ist einer Reihe mit Soll → Jahr `null`.
- `kennzahlen(data, vorjahr, includeSv, factors, empfaenger, personen, roh = data, extraBund = 0)` – `einnahmen` und `haushalt` aus `balance(data, factors, includeSv, extraBund)` (wie Seitenkopf).
- `herkunftVerwendung(data, includeSv, factors, extraBund = 0)` – Posten „Neue Schulden (Kredite)“ aus `balance(...).neueSchulden` statt aus den Kreditzeilen; Anteile weiterhin Summe 100.
- `MiniFluss`: Prop `extraBund = 0`; Kreditknoten aus `balance(...).neueSchulden`; Beschriftung des Haushaltsknotens unter dem Knoten (`y1 + 14`, `text-anchor="middle"`).
- `Dashboard.svelte`: Anteil im Ministeriums-Teaser = `effektive Ausgaben des Einzelplans / balance.ausgaben` (beides mit Faktoren, `effectiveValue`), zweite Linie Investitionen in der SVG mit Legende „Gesamtausgaben“ / „Investitionen (Hauptgruppen 7, 8)“.

- [ ] **Step 1: Failing tests** in `dashboard.test.ts`: Zeitreihe-Fixture mit `titel: {"11-1101-68101": {art:"A", soll:[50,55,60], ist:[50,null,60]}, "12-1201-74101": {art:"A", soll:[10,11,12.1], ist:[10,11,12]}, "12-1201-89101": {art:"A", soll:[10,11,12.1], ist:[10,11,12]}}` → `entwicklungIndex(z,"soll")[2].investitionen` ≈ 121; `entwicklungIndex(z,"ist")[1].gesamt === null` (fehlendes Ist); `kennzahlen(..., fixtureYear, 100).einnahmen === kennzahlen(...).einnahmen + 100`; `herkunftVerwendung(fixtureYear,false,{"11":0.5}).herkunft` Kredit-Posten `=== balance(fixtureYear,{"11":0.5},false).neueSchulden`.
- [ ] **Step 2: Run** `npx vitest run tests/dashboard.test.ts` → FAIL.
- [ ] **Step 3: Implement** Modell und Ansichten.
- [ ] **Step 4:** grün; `npm run check`; Browser `#v1;j=2025;a=dashboard`: zwei Linien, Haushaltsbeschriftung unter dem Knoten.
- [ ] **Step 5: Commit** `git commit -am "GUI 4d: Dashboard mit Investitionen-Linie und einheitlichen Grundlagen"`

---

### Task 2: Geldflüsse – Reiter „Nach Bereichen“ mit Ring

**Files:**
- Create: `web/src/lib/model/bereiche.ts`, `web/src/lib/ui/Ring.svelte`
- Modify: `web/src/lib/views/FlussSeite.svelte`
- Test: `web/tests/bereiche.test.ts`

**Interfaces:**
- `export function ausgabenNachEinzelplan(data: YearData, includeSv: boolean, factors: Factors, max = 8): { epl: string | null; label: string; wert: number; anteil: number }[]` – effektive Ausgaben je Einzelplan (`includeRow`, `effectiveValue`, nur `art === "A"`, nur positive Summen), absteigend, die `max` größten einzeln, Rest als `{ epl: null, label: "Weitere Einzelpläne", … }`; `anteil` in Prozent mit einer Nachkommastelle, Summe 100 ± 0,2.
- `Ring.svelte`: Props `teile: { id: string | null; label: string; wert: number; anteil: number; farbe: string }[]`, `mitte: { wert: string; label: string }`, `onKlick?: (id: string | null) => void`; d3-shape `arc`/`pie` ohne Sortierung, Innenradius 60 %, Tooltip `<title>`.
- `FlussSeite.svelte`: Reiter `bereiche` („Nach Bereichen“, aktiv wenn `modusBereiche`), Mitte dann Ring + Liste (Farbe `colorFor(epl)`, Label, Betrag, Anteil), Klick → `app.zeigeImFluss([epl])` und zurück zum Reiter „Nach Ministerien“. Lokaler Zustand `let bereiche = $state(false)`; die Reiter „Gesamtübersicht“ und „Nach Ministerien“ setzen ihn zurück.

- [ ] **Step 1: Failing tests**: `ausgabenNachEinzelplan(fixtureYear, false, {}, 2)` → zwei Einzelpläne (`"11"` 700, `"14"` 300) und kein Rest (60 ist negativ/0 → entfällt), Anteile 70/30; mit `max = 1` → `["11", null]`, Rest-Label „Weitere Einzelpläne“; Faktor `{"14": 2}` ändert Werte und Anteile.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4:** grün; Browser `#v1;j=2025;a=fluss;t=bund` → Reiter „Nach Bereichen“ zeigt Ring mit acht Teilen plus „Weitere“.
- [ ] **Step 5: Commit** `git commit -am "GUI 4d: Geldflüsse nach Bereichen (Ring)"`

---

### Task 3: Ministerien – Tabelle und Leitung im Wechseljahr

**Files:**
- Modify: `web/src/lib/model/ministerien.ts`, `web/src/lib/views/Ministerien.svelte`, `web/src/lib/ui/Verantwortung.svelte`, `web/src/lib/views/Dashboard.svelte`, `web/src/lib/model/profiteure.ts`
- Test: `web/tests/ministerien.test.ts`

**Interfaces:**
- `ministerien(...)`: im `aktuellesJahr` werden undatierte Kandidaten (`!seit`) zusätzlich zu datierten aufgenommen, `leitungHinweis = "Ernennungsdatum nicht belegt: <Namen>; Stand des Kabinettsabrufs"`; Sortierung Rang, dann `seit` absteigend (zuletzt amtierende zuerst), dann Name.
- `export function chef(leitung: Leitung[]): Leitung | null` in `ministerien.ts` – erste Person mit Rang ≤ 1 (Kanzler, Minister, Chef) nach der Sortierung, sonst `leitung[0] ?? null`; `export function vorgaenger(leitung: Leitung[], chef: Leitung | null): Leitung[]` – weitere Personen mit Rang ≤ 1 (mit `bis`).
- `export function ministerienTabelle(liste: Ministerium[], vorjahr: YearData | null, includeSv: boolean): (Ministerium & { veraenderung: number | null })[]` – `veraenderung` in Prozent (eine Nachkommastelle) aus nominalem Soll (`r.soll`, `includeRow`) des Vorjahres je Einzelplan; `null` ohne Vorjahr oder Vorjahreswert ≤ 0.
- `Ministerien.svelte`: Umschalter Karten | Tabelle (lokal), Tabelle mit Spalten Einzelplan, Leitung (Avatar, Name, Partei-Etikett), Haushalt, Änderung ggü. Vorjahr, Anteil; Klick auf Kopf sortiert (Haushalt ↓ Vorgabe, Änderung, Einzelplan); Klick auf Zeile wählt die Detailkarte. Verantwortung-Karte und Dashboard-Teaser nutzen `chef()`; Verantwortung zeigt Vorgänger als Zeile „zuvor: <Name> (bis <Datum>)“.

- [ ] **Step 1: Failing tests**: Fixture aus `ministerien.test.ts` erweitern: Epl 11 mit „G H“ (bis 2025-05-06) und „A B“ (seit 2025-05-06) → `ministerien(..., 2025, 2025, ...)` Leitung `["a-b", "g-h", "c-d"]` (A B vor G H, Staatssekretärin zuletzt); `chef(...)` = a-b, `vorgaenger(...)` = [g-h]; undatierter Minister im aktuellen Jahr erscheint zusätzlich zur datierten Staatssekretärin mit Hinweis; `ministerienTabelle(liste, year2019, false)` → Epl 11 `veraenderung` ≈ 25 (700 gegen 560), ohne Vorjahr `null`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4:** grün; Browser `#v1;j=2025;a=ministerien` → Tabelle mit Änderung.
- [ ] **Step 5: Commit** `git commit -am "GUI 4d: Ministerien-Tabelle, Leitung im Wechseljahr"`

---

### Task 4: Seite „Daten & Quellen“

**Files:**
- Create: `web/src/lib/model/quellen.ts`, `web/src/lib/views/Daten.svelte`
- Modify: `web/src/lib/model/navigation.ts` (Eintrag `daten`, Icon `Database`, nicht mobil), `web/src/lib/model/share.ts` (`VIEWS` + `daten`), `web/src/lib/model/types.ts` (`ViewId` + `daten`), `web/src/App.svelte` (Route, breit), `web/src/lib/state.svelte.ts` (`ensureVpi`/`ensureSteuern` falls nicht vorhanden)
- Test: `web/tests/quellen.test.ts`

**Interfaces:**
- `export interface QuellenZeile { quelle: string; inhalt: string; zeitraum: string; stand: string | null; lizenz: string; url: string; datei: string | null }`
- `export function quellenTabelle(e: { index: Index | null; empfaenger: EmpfaengerIndex | null; personen: PersonIndex | null; vpi: { quelle?: string; stand?: string } | null; steuern: number }): QuellenZeile[]` – Zeilen in der Reihenfolge der Spec; `stand` aus `index.erzeugt` (Datum, 10 Zeichen), `empfaenger.stand`, `personen.stand`, `vpi.stand`, sonst `null`; `zeitraum` aus `index.jahre` („2015–2026, Ist bis 2025“) bzw. `sv_jahre`; `datei` = Pfad unter `/data/` (z. B. `/data/index.json`, `/data/empfaenger/index.json`, `/data/zeitreihe.json`, `/data/vpi.json`, `/data/steuern.json`, `/data/texte.json`), `null` für Quellen ohne eigene Datei (Kabinett, Parteispenden: stehen in den Akten).
- `export const LUECKEN: string[]` (feste Liste aus §4.12) und `export const LIZENZEN: { was: string; lizenz: string; url: string }[]`.
- `Daten.svelte`: Tabelle, darunter „Bekannte Lücken“ und „Lizenzen“; Fußzeile „Rechtlich verbindlich sind die amtlichen Dokumente“.

- [ ] **Step 1: Failing tests**: `quellenTabelle({index: {jahre:[2015,2026], ist_bis:2025, sv_jahre:[2022,2026], summen:{}, erzeugt:"2026-11-02T00:33:23+00:00"}, empfaenger: {stand:"2026-11-01",…}, personen: {stand:"2026-11-02",…}, vpi: {stand:"2026-10-01"}, steuern: 4})` → erste Zeile `quelle` enthält „bundeshaushalt.de“, `zeitraum === "2015–2026, Ist bis 2025"`, `stand === "2026-11-02"`; Lobbyregister-Zeile `stand === "2026-11-01"`; alles `null` → jede Zeile `stand === null`; `datei` der Zeitreihe `"/data/zeitreihe.json"`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement** (Navigation, Route, Ansicht). **Step 4:** grün; Browser `#v1;j=2025;a=daten`.
- [ ] **Step 5: Commit** `git commit -am "GUI 4d: Seite Daten & Quellen"`

---

### Task 5: Dunkelmodus

**Files:**
- Create: `web/src/lib/model/theme.ts`
- Modify: `web/src/app.css`, `web/src/lib/ui/Kopfzeile.svelte`, `web/src/App.svelte`, Ansichten/UI mit hart kodierten Farben (`Kennzahl`, `Karte`, `Saeulen`, `Gewachsen`, `EmpfaengerSeite`, `EmpfaengerFluss`, `HerkunftVerwendung`, `MiniFluss`, `Panel`, `Presets`, `SteuerPanel`)
- Test: `web/tests/theme.test.ts`

**Interfaces:**
- `export type Theme = "hell" | "dunkel" | "system"`; `export function naechstes(t: Theme): Theme` (hell → dunkel → system → hell); `export function lies(storage: Pick<Storage, "getItem"> | null): Theme` (Schlüssel `bht-theme`, Vorgabe `system`, unbekannte Werte → `system`); `export function schreibe(storage: Pick<Storage, "setItem"> | null, t: Theme): void`; `export function attribut(t: Theme): string | null` (`"light"`, `"dark"`, `null` für System).
- `app.css`: Tokens unter `:root[data-theme="dark"]` und `@media (prefers-color-scheme: dark) { :root:not([data-theme="light"]) {…} }`: `--bg #0f1a2a`, `--panel #16243a`, `--border #27405f`, `--fg #e6eef8`, `--muted #9db3cc`, `--header #e6eef8`, `--header-fg #0f1a2a`, `--nav-bg #13203a`, `--nav-item #16243a`, `--nav-on #3b82f6`, `--chip-blau #1e3a5f`, `--chip-gruen #14402f`, `--chip-orange #4a3418`, `color-scheme: dark`; neue Tokens für bisher harte Farben: `--good-bg`, `--bad-bg`, `--rest` (`#9fb3c8`), `--linie-hell` (`#9cc3ee`), `--gruen-fg` (`#15803d`) mit Dunkel-Varianten.
- `Kopfzeile.svelte`: Knopf mit Lucide `Sun`/`Moon`/`Monitor`, Titel „Darstellung: Hell/Dunkel/System“, ruft `app.setTheme(naechstes(app.theme))`; `AppState.theme` (`$state`, aus `lies(localStorage)` im `init`), `setTheme` schreibt Storage und `document.documentElement.dataset.theme`.

- [ ] **Step 1: Failing tests**: `naechstes("hell") === "dunkel"`, `naechstes("system") === "hell"`; `lies({getItem: () => "dunkel"}) === "dunkel"`, `lies({getItem: () => "x"}) === "system"`, `lies(null) === "system"`; `attribut("system") === null`, `attribut("dunkel") === "dark"`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement**; danach `grep -n "#[0-9a-fA-F]\{6\}" web/src/lib/views/*.svelte web/src/lib/ui/*.svelte` → nur `Partei.svelte` und `colors.ts` (Datenfarben). **Step 4:** grün; Browser: Umschalter wechselt, nach Neuladen bleibt die Wahl.
- [ ] **Step 5: Commit** `git commit -am "GUI 4d: Dunkelmodus (Tokens, Umschalter, Speicherung im Browser)"`

---

### Task 6: Empfänger-Seite mit eingebettetem Umfeld, Link-Kodierung, Abschluss

**Files:**
- Modify: `web/src/lib/views/Netz.svelte` (Prop `kompakt`), `web/src/lib/state.svelte.ts` (`ladeUmfeld`), `web/src/lib/views/EmpfaengerSeite.svelte`, `web/src/lib/model/share.ts`, `README.md`, Spec §7 (4d ✅)
- Test: `web/tests/share.test.ts`

**Interfaces:**
- `AppState.ladeUmfeld(knotenId: string): Promise<Umfeld | null>` – lädt Netz-Index und Shard wie `openNetz`, ändert keine Ansicht, `null` ohne Umfeld.
- `Netz.svelte`: Prop `kompakt = false` → Höhe 300, kein Belegpanel, keine Legende, Knotenklick öffnet die Seite des Knotens (`app.openEmpfaenger`/`openAkte`/`zeigeImFluss` je `art`), `onVoll?: () => void` für „Umfeld zeigen“.
- `EmpfaengerSeite.svelte`: `onMount` → `app.ladeUmfeld("e:" + seite.id)` in lokalen Zustand; Karte „Verbindungsanalyse – Netzwerk“ rendert `<Netz {app} umfeld={u} kompakt onVoll={() => app.openNetz(...)} />`, ohne Umfeld der bisherige Text; Partei in „Personen“ nur bei `akte_sichtbar`.
- `share.ts`: `encodeScenario` schreibt `t=gesamt`, wenn `focus.length > 0 && topf === "gesamt"`; `decodeScenario` unverändert (explizites `t` gewinnt, `f` ohne `t` → bund).

- [ ] **Step 1: Failing tests** in `share.test.ts`: `encodeScenario(s, "fluss", ["11"], "ressort", "gesamt")` enthält `t=gesamt`; ohne Fokus kein `t=`; Rundreise `decodeScenario(encode(... "gesamt", ["11"]))` → `topf === "gesamt"`, `focus === ["11"]`.
- [ ] **Step 2: Run** → FAIL. **Step 3: Implement.** **Step 4:** grün; Browser `#v1;j=2025;a=empfaenger;e=deutsche-welle` zeigt das eingebettete Umfeld. README-Absatz „Oberfläche“ um 4d ergänzen, Spec §7 4d ✅, `npm run build`.
- [ ] **Step 5: Commit** `git add -A web README.md docs && git commit -m "GUI 4d: eingebettetes Umfeld, Link-Kodierung des Topfes, Doku"`

Danach: Review (Opus, Review Focus 1–5), Fix-Pass, ff-Merge nach `main`, Push, `docker compose up -d --build`.
