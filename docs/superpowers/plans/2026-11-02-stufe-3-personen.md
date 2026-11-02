# Stufe 3: Personen-Akten und Netz – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jede Person aus Lobbyregister (Vertreter von Empfängern mit Bundesmitteln), Bundestag und Bundesregierung bekommt eine Akte mit Funktionen, Organisationen samt deren Bundesgeld, veröffentlichungspflichtigen Angaben, Parteispenden der verbundenen Organisationen und Zeitlinie; auf jeder Akte und jeder Empfänger-Seite öffnet „Umfeld zeigen“ ein Netz zwei Schritte weit. Öffentlich sichtbar sind nur Akten nach der Relevanzregel; alle Akten entstehen im Build, der Schalter `--akten alle` zeigt sie vollständig.

**Architecture:** Die Pipeline bekommt drei Quellmodule (Parteispenden-Tabellen von bundestag.de, Kabinettsliste von bundesregierung.de, Staatssekretäre aus `data/manual/regierung.yaml`) und zwei Build-Module: `personen.py` (Identitäten aus Lobbyregister-Profilen, Biografien und Regierung; Zusammenführung nur mit Beleg; Sichtbarkeitsregel; Akten in 256 Shard-Dateien plus Index) und `netz.py` (Knoten und Kanten aus Empfänger-, Personen- und Spendendaten; vorberechnete Nachbarschaft zwei Schritte weit je Knoten, in Shards). Im Web kommen die Ansichten „Personen“ (Suche), „Akte“ und „Netz“ (d3-force) dazu; Teilen-Links `pe=<id>` und `n=<knoten>`. Moderation läuft über GitHub (CONTRIBUTING.md, PR-Vorlage); der Korrekturknopf verweist dorthin.

**Tech Stack:** wie Stufe 2; neu im Web `d3-force` (+ `@types/d3-force`). Pipeline ohne neue Abhängigkeiten.

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md`, §4.7a (bindend), §4.7, §4.6a, §2, §9, §10.

## Global Constraints

- Jede Angabe trägt Quelle (URL), Stand-Datum und Etikett („Eigenangabe“ für Lobbyregister und bundestag.de-Selbstauskünfte, „amtlich“ für bundestag.de-Spendenliste, bundesregierung.de, Haushalt).
- Keine Adressen, keine Spenden natürlicher Personen, keine Wertung, keine Warnfarben, keine mehrstufigen Verbindungssätze (Ketten nur als Kanten im Netz).
- Zusammenführung gleicher Namen nur mit Beleg (§4.7a); getrennte Akten tragen den Hinweis „gleicher Name, nicht zusammengeführt“.
- Sichtbarkeit: Akte öffentlich bei öffentlichem Amt, belegter Verbindung oder Freigabe in `personen.yaml`; sonst Knoten ohne Seite. `--akten alle` hebt das auf; `--ohne-personen` baut weder Akten noch Netz.
- Beträge aus Haushalt, Lobbyregister und Förderkatalog bleiben getrennt; Spenden sind eine vierte, eigene Spalte.
- Netz: höchstens 60 Knoten je Ausschnitt, Ministerien und Parteien werden nicht expandiert, kein Bundestag-Knoten, keine Ausschuss-Knoten.
- Netzzugriffe nur in `bht fetch-personen` mit Pause ≥ 1,5 s.

## Review Focus

1. **Zwei Personen gleichen Namens** (z. B. „Michael Groß“ bei drei Organisationen ohne gegenseitige Nennung) dürfen nicht zu einer Akte verschmelzen; die Akten tragen den Hinweis. Test in Task 3.
2. **Sichtbarkeitsregel**: Ein reiner Vertreter ohne Verbindung und ohne Freigabe hat keine Seite, erscheint aber als Netzknoten und auf der Empfänger-Seite; mit `--akten alle` hat er eine Seite. Test in Task 3 und 5.
3. **Spenden natürlicher Personen** (Spendername ohne Rechtsform, nicht im Empfänger-Stamm) erscheinen nirgends, auch nicht in Prüflisten mit Adresse. Test in Task 1.
4. **Netz-Explosion**: Ein Ministerium mit 400 geförderten Organisationen darf das Umfeld eines Vereins nicht auf 400 Knoten aufblasen; Randknoten werden nicht expandiert, Kappung bei 60 mit „+ n weitere“. Test in Task 4.
5. **Teilen-Link auf nicht freigegebene Akte** zeigt „Akte nicht freigeschaltet“ mit Verweis auf die Empfänger-Seite statt eines Fehlers. Test in Task 6.
6. **Kabinettsseite ändert Markup**: Parser liefert leere Liste und der Lauf bricht nicht ab; der Build nutzt dann nur `regierung.yaml`. Test in Task 2.

---

### Task 1: Parteispenden-Modul

**Files:**
- Create: `pipeline/src/bhtracker/spenden.py`
- Test: `pipeline/tests/test_spenden.py`, Fixture `pipeline/tests/fixtures/spenden_2025_ausschnitt.html` (Tabelle der Seite `https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000/2025`, auf Kopfzeile, eine Monatszeile und vier Datenzeilen gekürzt: eine Organisation mit Adresse, eine natürliche Person mit Adresse, eine Zeile mit Zeilenumbruch im Spendernamen, eine mit zwei Drucksachen-Links).

**Interfaces:**
- Produces:
  ```python
  JAHR_URL = "https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000/{jahr}"
  @dataclass class Spende: jahr: int; partei: str; betrag: int; spender: str; spender_ort: str; eingang: str; veroeffentlicht: str; drucksache: str; drucksache_url: str | None; natuerliche_person: bool
      # spender = erste Zeile des Spender-Felds (Name ohne Adresse); spender_ort = Ortsname aus der letzten Zeile („12345 Musterstadt“ → „Musterstadt“); eingang/veroeffentlicht ISO-Datum
      # natuerliche_person = kein Rechtsformmerkmal (_EIGENNAME aus empfaenger.py) und Name hat ≤ 4 Wörter und beginnt mit Vornamen-Muster (Titel/Vorname Nachname) → True
  def parse_spenden(html: str, jahr: int) -> list[Spende]      # Monatszeilen (eine Zelle) überspringen; Betrag „136.000 Euro“ → 136000
  def fetch_spenden(raw_dir: Path, jahre: list[int], http, pause=1.5) -> list[Path]   # raw_dir/"spenden"/f"{jahr}.html"; laufendes Jahr wird immer neu geladen, abgeschlossene Jahre nur wenn Datei fehlt
  def lade_spenden(raw_dir: Path) -> list[Spende]
  def zuordnen(spenden: list[Spende], stamm_normen: dict[str, str]) -> tuple[dict[str, list[Spende]], list[dict]]
      # exakter norm_name-Treffer → {empfaenger_id: [Spenden]}; Organisationen ohne Treffer → Kandidaten {"spender", "ort", "partei", "betrag", "jahr"} (nur Organisationen!); natürliche Personen werden verworfen und nirgends gespeichert
  ```

- [ ] **Step 1: Fixture anlegen** aus dem Live-Abruf (Seite 2025 lag in der Recherche vor: Tabelle mit Spalten Partei, Spende, Spender, Eingang, Anzeige/Drucksache; Monatszeilen „Dezember 2025“).
- [ ] **Step 2: Failing tests**

```python
def test_parse_spenden_liest_zeilen_und_laesst_monatszeilen_aus():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    assert len(sp) == 4
    csu = next(x for x in sp if x.partei == "CSU")
    assert csu.betrag == 136_000 and csu.spender == "Verband der Bayrischen Metall- und Elektro-Industrie e.V. (VBM)" and csu.spender_ort == "München"
    assert csu.eingang == "2025-12-23" and csu.veroeffentlicht == "2025-12-26" and csu.drucksache == "Drs. 21/4050" and csu.drucksache_url.startswith("https://dserver.bundestag.de/")
    assert csu.natuerliche_person is False

def test_natuerliche_person_erkannt_und_ohne_adresse():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    p = next(x for x in sp if x.partei == "AfD")
    assert p.natuerliche_person is True and p.spender == "Prof. Dr. Erika Musterfrau"
    assert "Musterweg" not in p.spender and "12345" not in p.spender_ort

def test_zuordnen_nur_organisationen_exakt():
    sp = parse_spenden(fixture_text("spenden_2025_ausschnitt.html"), 2025)
    normen = {norm_name("Verband der Bayrischen Metall- und Elektro-Industrie e.V. (VBM)"): "vbm"}
    zu, kandidaten = zuordnen(sp, normen)
    assert [s.partei for s in zu["vbm"]] == ["CSU"]
    assert all(not k.get("natuerliche_person") and "Musterfrau" not in k["spender"] for k in kandidaten)
    assert len(kandidaten) == 2   # die beiden anderen Organisationen ohne Treffer

def test_fetch_spenden_laedt_laufendes_jahr_neu(tmp_path):
    calls = []
    def http(url): calls.append(url); return fixture_bytes("spenden_2025_ausschnitt.html")
    fetch_spenden(tmp_path, [2024, 2026], http, pause=0); fetch_spenden(tmp_path, [2024, 2026], http, pause=0)
    assert len([c for c in calls if c.endswith("/2024")]) == 1 and len([c for c in calls if c.endswith("/2026")]) == 2
```

- [ ] **Step 3: Run** `cd pipeline && uv run pytest -q tests/test_spenden.py` – Expected: FAIL (ModuleNotFoundError).
- [ ] **Step 4: Implementieren** (`html.parser`/Regex wie bundestag.py; `datetime.date.today().year` als laufendes Jahr).
- [ ] **Step 5: Run** – Expected: 4 passed.
- [ ] **Step 6: Commit** `"Personen: Parteispenden-Modul"`.

---

### Task 2: Regierung (Kabinett und Staatssekretäre)

**Files:**
- Create: `pipeline/src/bhtracker/regierung.py`, `data/manual/regierung.yaml`
- Test: `pipeline/tests/test_regierung.py`, Fixture `pipeline/tests/fixtures/kabinett_ausschnitt.html` (zwei Kacheln `bpa-teaser-cabinet` der Seite `https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett`: Bundeskanzler und ein Bundesminister), `kabinett_leer.html` (Seite ohne Kacheln).

**Interfaces:**
- `regierung.yaml`:
  ```yaml
  stand: "2026-11-02"
  quelle_kabinett: "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett"
  mitglieder:            # Staatssekretäre von Hand; Kabinett kommt aus dem Abruf, kann hier aber überschrieben/ergänzt werden
    - name: "…"
      amt: "Parlamentarische Staatssekretärin"      # Bundesminister(in) | Bundeskanzler(in) | Chef(in) des Bundeskanzleramts | Staatsminister(in) | Parlamentarische(r) Staatssekretär(in) | Staatssekretär(in)
      ressort: "Bundesministerium der Finanzen"
      epl: "08"
      seit: "2025-05-06"
      bis: null
      quelle: "https://www.bundesfinanzministerium.de/…"
      mdb_id: 1043330 | null                         # Biografie-Id auf bundestag.de, falls Abgeordnete(r)
  ```
- Produces:
  ```python
  KABINETT_URL = "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett"
  @dataclass class Amtstraeger: name: str; amt: str; ressort: str; epl: str | None; seit: str | None; bis: str | None; quelle: str; stand: str; mdb_id: int | None
  def parse_kabinett(html: str, stand: str, ressorts: dict) -> list[Amtstraeger]   # je Kachel: Name (Link-Text), Amt (Text vor dem Namen, z. B. „Bundesminister des Auswärtigen“), Quelle = absolute Kachel-URL; epl über ressort_zu_epl(amt-Text ohne „Bundesminister(in) …“) und eine feste Tabelle AMT_EPL für Formulierungen wie „des Auswärtigen“ → 05, „der Finanzen“ → 08, „des Innern“ → 06, „der Justiz“ → 07, „für Arbeit und Soziales“ → 11, „der Verteidigung“ → 14, „für Gesundheit“ → 15, „für Verkehr“ → 12, „für Umwelt…“ → 16, „für Bildung, Familie…“ → 17, „für Forschung…“ → 30, „für Wirtschaft und Energie“ → 09, „für Landwirtschaft…“ → 10, „für wirtschaftliche Zusammenarbeit…“ → 23, „für Wohnen…“ → 25, „für Digitales und Staatsmodernisierung“ → 12? → None mit Hinweis (neues Ressort ohne eigenen Einzelplan 2025: epl None), Bundeskanzler/Kanzleramt → 04
  def validate_regierung(data: dict) -> list[str]        # Pflichtfelder name, amt, ressort, quelle(URL), seit (ISO); amt aus erlaubter Liste
  def lade_regierung(manual_file: Path, raw_dir: Path, ressorts: dict) -> list[Amtstraeger]   # Kabinett aus raw_dir/"regierung"/"kabinett.html" (falls vorhanden) + yaml; gleicher Name+Amt → yaml gewinnt
  def fetch_kabinett(raw_dir: Path, http) -> Path
  ```

- [ ] **Step 1: Fixtures anlegen** (aus der Recherche-Datei `kabinett.html`).
- [ ] **Step 2: Failing tests**

```python
def test_parse_kabinett_liest_name_amt_und_epl():
    m = parse_kabinett(fixture_text("kabinett_ausschnitt.html"), "2026-11-02", ressorts())
    assert any(x.name == "Friedrich Merz" and x.amt.startswith("Bundeskanzler") and x.epl == "04" for x in m)
    aa = next(x for x in m if "Auswärtigen" in x.amt)
    assert aa.name == "Dr. Johann Wadephul" and aa.epl == "05" and aa.quelle.startswith("https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett/")

def test_parse_kabinett_ohne_kacheln_liefert_leere_liste():
    assert parse_kabinett(fixture_text("kabinett_leer.html"), "2026-11-02", ressorts()) == []

def test_validate_regierung_pflichtfelder():
    data = {"mitglieder": [{"name": "X", "amt": "Staatssekretär", "ressort": "Bundesministerium der Finanzen", "epl": "08", "seit": "2025-05-06", "quelle": "https://x"}]}
    assert validate_regierung(data) == []
    data["mitglieder"][0].pop("quelle")
    assert any("quelle" in e for e in validate_regierung(data))
    data["mitglieder"][0]["quelle"] = "https://x"; data["mitglieder"][0]["amt"] = "Kaiser"
    assert any("amt" in e for e in validate_regierung(data))

def test_lade_regierung_yaml_ueberschreibt_abruf(tmp_path):
    ...  # kabinett.html Fixture in tmp raw + yaml mit gleichem Namen und Amt, anderem epl → yaml-Wert
```

- [ ] **Step 3: Run** – Expected: FAIL.
- [ ] **Step 4: Implementieren**; `regierung.yaml` zunächst mit `mitglieder: []`.
- [ ] **Step 5: Run** – Expected: 4 passed.
- [ ] **Step 6: Commit** `"Personen: Regierungsmodul (Kabinett, regierung.yaml)"`.

---

### Task 3: Personen-Identitäten, Akten-Build, Sichtbarkeit

**Files:**
- Create: `pipeline/src/bhtracker/personen.py`, `data/manual/personen.yaml`
- Test: `pipeline/tests/test_personen.py`

**Interfaces:**
- Consumes: `Profil`/`Person` (lobbyregister.py), `Abgeordneter`/`Angabe` (bundestag.py), `Amtstraeger` (regierung.py), `Spende` + `zuordnen` (spenden.py), Stamm/Empfänger-Build (empfaenger.py: `baue_stamm`, Seiten-JSON für Geld je Organisation), `norm_name`, `slug`.
- `personen.yaml`:
  ```yaml
  zusammenfuehren:      # Belegte Identitäten über Quellen hinweg
    - ids: ["max-mustermann-lr-r001234", "max-mustermann-mdb-1043330"]
      quelle: "https://…"
      hinweis: "bundestag.de nennt die Funktion bei …"
  trennen:              # ausdrücklich getrennt halten, auch wenn Regel (b) greift
    - ids: ["…", "…"]
      quelle: "…"
  freigabe:             # Akten ohne Amt/Verbindung, die ein Prüfer freischaltet
    - id: "…"
      quelle: "…"
      geprueft_von: "github-login"
      datum: "2026-11-02"
  ```
- Produces:
  ```python
  def shard(id: str) -> str                       # ersten zwei Hex-Zeichen von sha1(id)
  @dataclass class Funktion: art: str; text: str; organisation_id: str | None; organisation: str; epl: str | None; seit: str | None; bis: str | None; stand: str; quelle: dict
      # art ∈ {"mdb", "regierung", "gesetzlicher_vertreter", "interessenvertreter", "fruehere_regierungsfunktion"}
  @dataclass class Akte: id: str; name: str; quellen_ids: list[str]; funktionen: list[Funktion]; amt: bool; verbindung: bool; freigabe: bool; sichtbar: bool; gleichnamig: list[str]; angaben: list[dict]; organisationen: list[str]; spenden: list[dict]; zeitlinie: list[dict]; quellen: list[dict]; stand: str
  def roh_identitaeten(profile, abgeordnete, regierung) -> list[Akte]
      # je Quelle eine Roh-Akte: Lobbyregister → id f"{slug(name)}-lr-{nummer.lower()}" je Organisation; MdB → f"{slug(name)}-mdb-{mdb_id}"; Regierung → f"{slug(name)}-breg"
  def zusammenfuehren(roh: list[Akte], profile_by_nr: dict[str, Profil], manual: dict) -> tuple[list[Akte], list[dict]]
      # Regeln §4.7a: (a) MdB-Angabe nennt exakt die Organisation des Lobbyregister-Eintrags; (b) Lobbyregister-Person mit recentGovernmentFunction HOUSE_OF_REPRESENTATIVES und MdB gleichen Namens; (c) gleicher Name bei zwei Organisationen und eine nennt die andere in `mitgliedschaften` oder ≥ 2 gemeinsame Vertreternamen; (d) manual zusammenfuehren; `trennen` schlägt alles. Ergebnis-Id = die „stärkste“ Quelle (mdb > breg > lr) ohne Quellenkürzel: slug(name), bei Kollision mit anderer Person Suffix der Quelle. Kandidaten = gleiche Namen ohne Beleg.
  def sichtbarkeit(a: Akte, verbindungen_by_person: set[str], manual: dict, modus: str) -> bool   # modus "relevant" | "alle"
  def build_personen(manual_dir, raw_dir, out, empfaenger_seiten: dict[str, dict], stand: str, *, modus="relevant", mit_personen=True) -> Path
      # schreibt out/"personen"/"index.json" {stand, modus, eintraege:[{id,name,funktion_kurz,amt,sichtbar,n_organisationen,shard}]} und out/"personen"/f"{shard}.json" {id: Akte-JSON}; Prüfliste data/review/personen_kandidaten.yaml
  ```
- Akte-JSON (je Person):
  ```json
  {"id","name","sichtbar":true,"grund_sichtbar":"amt"|"verbindung"|"freigabe"|"alle"|null,"gleichnamig":["id",…],
   "funktionen":[{"art":"mdb","text":"Mitglied des Bundestages, SPD","organisation":"Deutscher Bundestag","organisation_id":null,"epl":null,"seit":null,"bis":null,"stand":"2026-11-01","quelle":{"kurz":"bundestag.de","url":"…","etikett":"amtlich"},"ausschuesse":[…]}],
   "organisationen":[{"id":"amadeu-antonio-stiftung","name":"…","funktion":"Vorstand","rolle":"gesetzlicher_vertreter","stand":"2026-09-02","lobby_untergrenze_bund":…,"haushalt_soll_letztes_jahr":…,"foerderkatalog_summe":…,"geld_aus":[…]}],
   "angaben":[{"kategorie":"…","organisation":"…","funktion":"…","stand":"…","quelle":{…}}],
   "spenden":[{"organisation_id":"…","organisation":"…","partei":"…","betrag":136000,"eingang":"…","drucksache":"…","drucksache_url":"…","quelle":{"kurz":"bundestag.de","url":"…","etikett":"amtlich"}}],
   "zeitlinie":[{"jahr":2024,"art":"geld","organisation_id":"…","text":"… erhielt laut Lobbyregister ab 1,04 Mio € vom BMBFSFJ","wert":1040001},{"jahr":2026,"art":"posten","text":"Vorstand bei …, Stand 2026-09-02"}],
   "quellen":[…],"stand":"2026-11-02"}
  ```

- [ ] **Step 1: Failing tests** (Fixtures: Lobbyregister-Profil R004511, Biografie Abdi, Kabinett-Ausschnitt; synthetische zweite Organisation mit gleichem Vertreternamen)

```python
def test_roh_identitaeten_je_quelle():
    akten = roh_identitaeten([profil_aas], [mdb_abdi], [kanzler])
    assert {a.id for a in akten} >= {"timo-reinfrank-lr-r004511", "sanae-abdi-mdb-1043330", "friedrich-merz-breg"}

def test_gleicher_name_ohne_beleg_bleibt_getrennt():
    p2 = profil_mit(name="Zweite Stiftung", nummer="R009999", personen=[Person("Reinfrank", "Timo", "Vorstand", "gesetzlicher_vertreter", None)])
    akten, kandidaten = zusammenfuehren(roh_identitaeten([profil_aas, p2], [], []), {p.nummer: p for p in (profil_aas, p2)}, {})
    reinfrank = [a for a in akten if a.name == "Timo Reinfrank"]
    assert len(reinfrank) == 2 and all(len(a.gleichnamig) == 1 for a in reinfrank)
    assert any(k["name"] == "Timo Reinfrank" for k in kandidaten)

def test_gegenseitige_nennung_fuehrt_zusammen():
    p2 = profil_mit(name="Zweite Stiftung", nummer="R009999", personen=[…Reinfrank…], mitgliedschaften=["Amadeu Antonio Stiftung"])
    akten, _ = zusammenfuehren(…)
    assert len([a for a in akten if a.name == "Timo Reinfrank"]) == 1 and sorted(a.quellen_ids) == ["timo-reinfrank-lr-r004511", "timo-reinfrank-lr-r009999"]

def test_mdb_angabe_fuehrt_mit_lobbyregister_zusammen():
    # Abdi nennt DEval; ein Lobbyregister-Profil „Deutsches Evaluierungsinstitut der Entwicklungszusammenarbeit (DEval) gGmbH“ mit Vertreterin „Sanae Abdi“ → eine Akte mit zwei Funktionen
    ...

def test_sichtbarkeit_regeln():
    assert sichtbarkeit(akte(amt=True), set(), {}, "relevant") is True
    assert sichtbarkeit(akte(amt=False), {"x"}, {}, "relevant") is True        # id in verbindungen
    assert sichtbarkeit(akte(amt=False, id="y"), set(), {}, "relevant") is False
    assert sichtbarkeit(akte(amt=False, id="y"), set(), {"freigabe": [{"id": "y", "quelle": "https://x"}]}, "relevant") is True
    assert sichtbarkeit(akte(amt=False, id="y"), set(), {}, "alle") is True

def test_build_personen_schreibt_shards_und_index(tmp_path):
    ...  # index["eintraege"] enthält Abdi mit sichtbar True und Reinfrank (keine Verbindung) mit sichtbar False; Shard-Datei enthält Abdi-Akte mit funktionen[0].art == "mdb" und angaben; Reinfrank-Akte steht in der Shard-Datei nur, wenn modus "alle"; Spenden einer Organisation erscheinen in den Akten ihrer Vertreter; Prüfliste geschrieben

def test_ohne_personen_baut_nichts(tmp_path):
    ...  # out/"personen" existiert nicht, Rückgabe None
```

- [ ] **Step 2: Run** `cd pipeline && uv run pytest -q tests/test_personen.py` – Expected: FAIL.
- [ ] **Step 3: Implementieren** (Shard-Dateien enthalten nur sichtbare Akten; der Index enthält alle Personen mit `sichtbar`, damit Netz und Empfänger-Seite wissen, ob es eine Seite gibt).
- [ ] **Step 4: Run** – Expected: alle grün.
- [ ] **Step 5: Commit** `"Personen: Identitäten, Akten-Build, Sichtbarkeitsregel"`.

---

### Task 4: Netz-Build

**Files:**
- Create: `pipeline/src/bhtracker/netz.py`
- Test: `pipeline/tests/test_netz.py`

**Interfaces:**
- Knoten-Ids: `p:<personen-id>`, `e:<empfaenger-id>`, `m:<epl>`, `partei:<slug>`.
- Produces:
  ```python
  @dataclass class Knoten: id: str; art: str; label: str; sichtbar: bool; seite: str | None   # art ∈ {"person","organisation","ministerium","partei"}; seite = Teilen-Hash der Zielseite oder None
  @dataclass class Kante: von: str; nach: str; art: str; text: str; wert: int | None; quelle: dict; stand: str   # art ∈ {"geld","posten","spende"}
  def baue_graph(empfaenger_seiten: dict[str, dict], akten: list[Akte], spenden_by_org: dict[str, list[Spende]], ressorts: dict) -> tuple[dict[str, Knoten], list[Kante]]
      # geld: m:<epl> → e:<id> je Lobbyregister-Zuwendung mit epl (wert = Untergrenze) und je Haushaltstitel (wert = Soll letztes Jahr); posten: p → e (Vertreter), p → m (Regierung); spende: e → partei
  def umfeld(start: str, knoten, kanten, *, max_knoten=60) -> dict
      # Breitensuche zwei Schritte; Knoten der Arten ministerium/partei werden nicht expandiert; Sortierung der Nachbarn nach Kantenwert absteigend, Kappung bei max_knoten mit "weitere": n
      # Ergebnis {"start": id, "knoten": [Knoten-Dicts], "kanten": [Kanten-Dicts], "weitere": n}
  def build_netz(out: Path, knoten, kanten, *, mit_personen=True) -> Path   # out/"netz"/f"{shard}.json" {knoten_id: umfeld}, nur für Knoten mit mindestens einer Kante; ohne Personen: nur Organisationen/Ministerien/Parteien ohne Personenknoten
  ```

- [ ] **Step 1: Failing tests**

```python
def test_graph_hat_drei_kantenarten(): ...   # aus Mini-Daten: Ministerium 17 → AAS (geld), Reinfrank → AAS (posten), VBM → CSU (spende)
def test_umfeld_expandiert_ministerien_nicht():
    # Ministerium 30 fördert 200 Organisationen; Umfeld von Organisation A enthält m:30, aber nicht die 199 anderen
    u = umfeld("e:a", knoten, kanten)
    assert "m:30" in {k["id"] for k in u["knoten"]} and len(u["knoten"]) <= 60 and not any(k["id"] == "e:b150" for k in u["knoten"])
def test_umfeld_zwei_schritte_ueber_person():
    # Org A — Person P — Org B: Umfeld von A enthält B (zwei Schritte über den Personenknoten)
def test_kappung_mit_weitere():
    # Person mit 80 Organisationen → 60 Knoten, weitere == 21 (Start zählt mit)
def test_build_netz_shards(tmp_path): ...   # Datei je Shard, Eintrag für "p:…" und "e:…"; mit_personen=False → keine p:-Knoten
```

- [ ] **Step 2: Run** – Expected: FAIL. **Step 3: Implementieren.** **Step 4: Run** – Expected: grün.
- [ ] **Step 5: Commit** `"Personen: Netz-Build (Knoten, Kanten, Umfeld zwei Schritte)"`.

---

### Task 5: CLI, Build-Integration, echte Daten

**Files:**
- Modify: `pipeline/src/bhtracker/cli.py`, `pipeline/src/bhtracker/empfaenger.py` (Empfänger-Seite bekommt `personen[].akte_id` und `personen[].akte_sichtbar`; `build_empfaenger` gibt die Seiten-Dicts zurück oder schreibt sie so, dass `build_personen` sie lesen kann → Ruling im Ledger), `pipeline/README.md`
- Test: `pipeline/tests/test_cli.py` (ergänzen), `pipeline/tests/test_empfaenger_build.py` (ergänzen)

**Interfaces:**
- CLI: `bht fetch-personen [--quellen spenden,kabinett,ausgeschiedene] [--pause 1.5]` lädt Spendenseiten 2015 bis heute, die Kabinettsseite und die Biografien der ausgeschiedenen Abgeordneten (`https://www.bundestag.de/abgeordnete/biografien/ausgeschiedene`, Links direkt in der Seite). `bht build [--akten relevant|alle] [--ohne-personen]`: nach `build_empfaenger` folgen `build_personen` und `build_netz`; Reihenfolge: Empfänger → Personen (Akte-Ids) → Empfänger-Seiten um `akte_id` ergänzen → Netz.

- [ ] **Step 1: Failing tests** (`--akten alle` erzeugt mehr sichtbare Akten als `relevant`; Empfänger-Seite trägt `akte_id` je Person; `--ohne-personen` erzeugt weder `personen/` noch `netz/`).
- [ ] **Step 2: Run** – Expected: FAIL. **Step 3: Implementieren.** **Step 4: Run** `cd pipeline && uv run pytest -q` – Expected: grün.
- [ ] **Step 5: Echte Daten:** `uv run bht fetch-personen` (Spenden 12 Seiten, Kabinett, 19 Biografien). Dann `regierung.yaml` füllen (Task 8 zieht vor: Staatssekretäre aller Ressorts mit Quelle). Dann `uv run bht build` (Standard `--akten relevant`). Erwartet: `personen/index.json` mit ≈ 11.300 + 660 Einträgen, sichtbar ≈ 1.000 (Amt, Verbindungen, Regierungsfunktionen), `netz/` ≈ 256 Shards.
- [ ] **Step 6: Stichprobe:** Akte Sanae Abdi (MdB, Angaben, DSW), Akte eines Vorstands mit Regierungsfunktion (sichtbar durch Verbindung), Akte eines reinen Vertreters (nicht sichtbar), Umfeld AAS (Ministerien 17/30/06 als Randknoten, Vorstände als Personenknoten).
- [ ] **Step 7: Commit** `"Personen: fetch-personen, Build-Integration, erster Daten-Build"`.

---

### Task 6: Web-Modell (Typen, Laden, Links, Zustand)

**Files:**
- Create: `web/src/lib/model/personen.ts`, `web/src/lib/model/netz.ts`
- Modify: `web/src/lib/model/types.ts` (ViewId + `"personen" | "netz"`), `web/src/lib/model/share.ts` (`pe=`, `n=`), `web/src/lib/model/load.ts`, `web/src/lib/state.svelte.ts`, `web/package.json` (d3-force)
- Test: `web/tests/personen.test.ts`, `web/tests/netz.test.ts`, `web/tests/share.test.ts`, `web/tests/state.test.ts`

**Interfaces:**
- `personen.ts`: Typen `PersonIndexEintrag {id,name,funktion_kurz,amt,sichtbar,n_organisationen,shard}`, `PersonIndex {stand,modus,eintraege}`, `Akte` (wie JSON), `filterePersonen(index, q, filter: "alle"|"abgeordnete"|"regierung"|"vertreter", nurSichtbar=true)`, `zeitlinieJahre(akte) -> {jahr, geld: number, posten: string[]}[]`, `issueUrlAkte(akte)`.
- `netz.ts`: Typen `NetzKnoten`, `NetzKante`, `Umfeld`; `shardOf(id)` (sha1 im Browser über `crypto.subtle` ist asynchron → im Build wird der Shard in den Index geschrieben; `netz.ts` berechnet nichts selbst: `umfeldPfad(knotenId, shardIndex: Record<string,string>)`); `legende()`; `kantenStil(art)` (gestrichelt für Posten, durchgezogen Geld, gepunktet Spende; eine Farbe).
- `share.ts`: `pe=<id>` (Regex `[a-z0-9-]{1,100}`), `n=<knoten>` (Regex `^(p|e|m|partei):[a-z0-9-]{1,100}$`).
- `state`: `personIndex`, `akte`, `akteFehlt`, `netz`, `netzStart`; `ensurePersonen()`, `openAkte(id)`, `openNetz(knotenId)`; Loader `loadPersonIndex`, `loadPersonShard(shard)`, `loadNetzShard(shard)`; Index liefert je Person den Shard, Netz-Index `netz/index.json` {knoten_id: shard}.

- [ ] **Step 1: Failing tests** (Filter, Zeitlinie, Link-Round-Trip, `openAkte` mit unsichtbarer Id → `akteFehlt` = "nicht freigeschaltet", `openNetz` lädt Shard).
- [ ] **Step 2: Run** – Expected: FAIL. **Step 3: Implementieren** (`npm i d3-force @types/d3-force`). **Step 4: Run** `npm test && npm run check` – Expected: grün.
- [ ] **Step 5: Commit** `"Personen: Web-Modell, Links pe= und n=, Zustand"`.

---

### Task 7: Ansichten Personen, Akte, Netz; Verknüpfung

**Files:**
- Create: `web/src/lib/views/Personen.svelte`, `web/src/lib/views/Akte.svelte`, `web/src/lib/views/Netz.svelte`
- Modify: `web/src/App.svelte`, `web/src/lib/ui/Kopfzeile.svelte` (Views „Personen“), `web/src/lib/views/EmpfaengerSeite.svelte` (Knopf „Umfeld zeigen“; Personen mit Akte verlinkt, ohne Akte Hinweis „Akte nicht freigeschaltet“), `web/src/lib/views/Empfaenger.svelte` (Spalte „Umfeld“ optional nein; nur Link auf Seite)

**Akte.svelte:** Kopf (Name, Funktionen mit Etikett und Quelle, „gleicher Name, nicht zusammengeführt“ mit Links), Knopf „Umfeld zeigen“, Block „Organisationen und ihr Geld vom Bund“ (Tabelle: Organisation, Posten, Stand, Bund laut Lobbyregister, Haushaltstitel, Förderkatalog, Spenden an Parteien), Block „Veröffentlichungspflichtige Angaben“ (nur MdB, wörtlich je Kategorie), Block „Parteispenden der verbundenen Organisationen“, Block „Zeitlinie“ (SVG: Jahre 2015–2026, Geldbalken je Jahr, Posten als Punkte mit Stand), Block „Quellen und Stand“, Knöpfe „Fehler melden / Beleg einreichen“ (Issue) und „Korrektur vorschlagen (Pull Request)“ (Link auf `CONTRIBUTING.md`).

**Netz.svelte:** d3-force-Layout im SVG, Knotenformen je Art (Kreis Person, Quadrat Organisation, Raute Ministerium, Sechseck Partei), eine Farbe, Kantenstil je Art, Tooltip mit Text, Quelle und Stand, Klick auf Knoten → Akte/Seite (nicht freigeschaltete Personen ohne Link), „+ n weitere“ als Hinweis, Legende, Knopf „zurück“. Zoom per Mausrad wie im Fluss.

- [ ] **Step 1: Komponenten schreiben.** **Step 2:** `npm run check && npm run build` – Expected: 0 Fehler.
- [ ] **Step 3: Browser-Prüfung**: Personen-Suche „Abdi“, Akte, Umfeld von der Akte und von der AAS-Seite, Teilen-Links `pe=` und `n=`, Handybreite.
- [ ] **Step 4: Commit** `"Personen: Ansichten Personen, Akte und Netz"`.

---

### Task 8: Pflegedaten und Moderation

**Files:**
- Modify: `data/manual/regierung.yaml` (Kabinett-Abgleich, alle Parlamentarischen und beamteten Staatssekretäre der amtierenden Regierung mit Quelle „Leitung“-Seite des Ressorts und Datum), `data/manual/personen.yaml` (Zusammenführungen aus der Prüfliste, die ein Beleg stützt; sonst leer)
- Create: `CONTRIBUTING.md` (Moderationsregeln: wer einreicht, wer prüft, was ein Beleg ist, Relevanzregel, Freigabe), `.github/PULL_REQUEST_TEMPLATE.md` (Quelle, Datum, betroffene Datei, Art der Änderung), `.github/ISSUE_TEMPLATE/beleg.md`
- Modify: `web/public/impressum.html` (Abschnitt „Gegendarstellung und Korrektur“, Platzhalter für Betreiber bleiben), `README.md` („Wer entscheidet“ und „Mitmachen“ auf Stand)

- [ ] **Step 1:** Staatssekretäre recherchieren (Ressortseiten), in `regierung.yaml` eintragen, `uv run pytest -q tests/test_regierung.py` (Validierung der Repo-Datei) – Expected: grün.
- [ ] **Step 2:** Texte schreiben; `uv run bht build`; Browser-Prüfung einer Regierungs-Akte.
- [ ] **Step 3: Commit** `"Personen: Regierung, Moderationsregeln, Gegendarstellungsweg"`.

---

### Task 9: Abschluss

- [ ] Spec §7 Stufe 3 abhaken, 3b (Versionshistorie, frühere Wahlperioden, Rechenschaftsberichte) eintragen; `pipeline/README.md` um `fetch-personen`, `--akten` ergänzen; Ledger.
- [ ] `cd pipeline && uv run pytest -q`, `cd web && npm test && npm run check && npm run build`.
- [ ] Review (opus-Subagent, ganzer Branch, Fokus auf Identität, Sichtbarkeit, Satzvorlagen, Netz-Kappung), Fix-Pass, ff-Merge nach `main`, Push.
