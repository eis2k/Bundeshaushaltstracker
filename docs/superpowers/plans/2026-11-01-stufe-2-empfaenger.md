# Stufe 2: Empfänger – Umsetzungsplan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Jeder Empfänger von Bundesmitteln, der aus amtlichen Quellen hervorgeht, bekommt eine Seite, die drei Fragen beantwortet: Woher kommt das Geld (zehn Jahre, Titel, Ministerium), wer steht dahinter (gesetzliche Vertreter, Interessenvertreter), und welche belegten Verbindungen zu Abgeordneten und Regierungsmitgliedern gibt es; dazu die Pflichtangaben des Empfängers (Lobbyregister, Jahresabschluss).

**Architecture:** Die Pipeline bekommt vier Quellmodule (Lobbyregister-JSON, bundestag.de-Biografien, Förderkatalog-CSV, Haushaltstitel mit Empfängernamen) und ein Modul `empfaenger.py`, das daraus je Empfänger eine JSON-Datei und einen Index baut. Rohdaten liegen unter `data/raw/<quelle>/` (nicht committet), Pflegedaten unter `data/manual/` (Stamm, Aliasse, Ressort-Zuordnung, bestätigte Verbindungen, Jahresabschluss-Kennzahlen), automatisch erzeugte Prüflisten unter `data/review/`. Im Web kommen eine Ansicht „Empfänger“ (Liste mit Suche) und eine Empfänger-Seite dazu, erreichbar über `#v1;a=empfaenger;e=<id>`, aus dem Panel eines Titels und aus der Empfänger-Spalte des Flusses. Verbindungen werden nur bei exakt übereinstimmendem Organisationsnamen automatisch veröffentlicht; Ähnliches landet in der Prüfliste.

**Tech Stack:** wie Stufe 1 (Python 3.13/uv/pydantic/pytest; Svelte 5/Vite/vitest). Neu in der Pipeline: keine zusätzlichen Abhängigkeiten (urllib, csv, html.parser, difflib aus der Standardbibliothek).

**Spec:** `docs/superpowers/specs/2026-11-01-bundeshaushaltstracker-design.md`, §4.6, §4.6a (bindend), §4.7 (Personenkreis), §2 (Quellenregel, Anti-Ziele), §9.

## Global Constraints

- Jede Zahl und jede Person trägt eine Quelle mit URL und Abrufdatum; Eigenangaben (Lobbyregister, Jahresabschluss, Selbstauskunft auf bundestag.de) tragen das Etikett „Eigenangabe, Stand <Datum>“.
- Beträge aus Haushalt (Euro), Lobbyregister (Spannen) und Förderkatalog (Projektsummen) werden nie addiert und nie in den Sankey eingerechnet; Rechnungen mit Spannen nutzen die Untergrenze und sagen das.
- Personenkreis: gesetzliche Vertreter und Interessenvertreter laut Lobbyregister, Abgeordnete, Regierungsmitglieder. Keine anderen Namen (Anti-Ziel „keine Privatpersonen“).
- Verbindungen Person ↔ Organisation: automatisch veröffentlicht nur bei exakter Übereinstimmung des normalisierten Namens, Etikett „automatisch abgeglichen“; sonst Prüfliste. Verwandtschaft nur von Hand mit amtlicher Quelle.
- Keine Wertung: Tatsachensätze mit Quelle und Datum, keine Warnfarben, kein „Verdacht“.
- Build-Schalter `--ohne-personen` lässt alle Namen (Personen und Verbindungen) aus den Build-Dateien weg; Standard ist „mit“.
- Netzzugriffe nur im Kommando `bht fetch-empfaenger` mit Pause ≥ 1,5 s zwischen Anfragen und dem User-Agent der Pipeline; `bht build` arbeitet ausschließlich aus `data/raw/` und `data/manual/`.

## Review Focus

1. **Namenskollision** („Deutsche Bank“ gegen „Deutsche Bank Stiftung“, „Caritas“ gegen „Caritasverband Berlin“) darf keine automatische Verbindung erzeugen. Test in Task 4.
2. **Schalter `--ohne-personen`** muss auch Verbindungen, Regierungsfunktionen und Namen in Prüflisten-Verweisen entfernen, nicht nur den Block „Personen“. Test in Task 5.
3. **Biografie ohne Angaben** (Abgeordneter ohne veröffentlichungspflichtige Angaben, ausgeschiedener Abgeordneter, geändertes Markup) darf den Lauf nicht abbrechen und liefert eine leere Liste mit Hinweis im Log. Test in Task 2.
4. **Förderkatalog-CSV** mit `="…"`-Feldern, Tausenderpunkten, Latin-1 und leerem Ergebnis („Die Suche liefert keine Ergebnisse“) wird korrekt oder als leere Liste gelesen. Test in Task 3.
5. **Geldgeber-Namen** im Lobbyregister sind frei formuliert („BMBF“, „Bundesministerium für Bildung und Forschung“, „Bundesamt für Wirtschaft und Ausfuhrkontrolle“); unbekannte Namen bleiben erhalten und bekommen `epl: null`, nie eine geratene Zuordnung. Test in Task 4.
6. **Teilen-Link mit unbekannter Empfänger-Id** zeigt die Liste mit Hinweis statt einer leeren Seite. Test in Task 6.

---

### Task 1: Lobbyregister-Modul

**Files:**
- Create: `pipeline/src/bhtracker/lobbyregister.py`
- Test: `pipeline/tests/test_lobbyregister.py`, Fixtures `pipeline/tests/fixtures/lobby_liste_ausschnitt.json` (3 Einträge aus `https://www.lobbyregister.bundestag.de/sucheJson`: einer mit Bundeszuwendung, einer ohne, eine natürliche Person) und `pipeline/tests/fixtures/lobby_detail_R004511.json` (Detailprofil `https://www.lobbyregister.bundestag.de/sucheJson/R004511/82516`, gekürzt auf die genutzten Felder, Namen der Vertreter bleiben, weil amtlich veröffentlicht).

**Interfaces:**
- Produces:
  ```python
  LISTE_URL = "https://www.lobbyregister.bundestag.de/sucheJson"
  def detail_url(register_nummer: str, eintrag_id: int) -> str   # f"{LISTE_URL}/{nr}/{id}"
  def hat_bundesmittel(eintrag: dict) -> bool                     # Listeneintrag: publicAllowances fehlt in der Liste → immer False; nur für Detail genutzt
  def auswahl(liste: dict, zusaetzlich: set[str]) -> list[tuple[str, int]]
      # alle ORGANIZATION-Einträge (identity != "NATURAL") mit accountDetails.activeLobbyist True,
      # deren registerNumber in `zusaetzlich` liegt ODER deren Hauptfinanzierungsquelle/… nicht bekannt ist → Auswahl erfolgt nach dem Detailabruf; die Liste liefert (registerNumber, registerEntryId) für ALLE aktiven Organisationen
  @dataclass class Spanne: von: int; bis: int
  @dataclass class Zuwendung: geber: str; ort: str; spanne: Spanne; zweck: str; typ: str; geschaeftsjahr: str   # typ = type.code, z. B. GERMAN_PUBLIC_SECTOR_FEDERAL
  @dataclass class Regierungsfunktion: art: str; funktion: str; stelle: str; beendet: bool; ende: str | None
  @dataclass class Person: nachname: str; vorname: str; funktion: str; rolle: str; regierungsfunktion: Regierungsfunktion | None   # rolle ∈ {"gesetzlicher_vertreter", "interessenvertreter"}
  @dataclass class Profil: nummer: str; eintrag_id: int; version: int; stand: str; url: str; pdf_url: str | None; name: str; rechtsform: str; rechtsform_code: str; sitz: str; land: str; website: str | None; taetigkeit: str; personen: list[Person]; zuwendungen: list[Zuwendung]; finanzierungsquellen: list[str]; spenden: Spanne | None; mitgliedsbeitraege: Spanne | None; lobbyausgaben: Spanne | None; geschaeftsjahr: str | None; jahresabschluss_url: str | None; jahresabschluss_jahr: str | None; mitgliedschaften: list[str]
  def extract_profil(detail: dict) -> Profil
  def bundeszuwendungen(p: Profil) -> list[Zuwendung]             # typ == "GERMAN_PUBLIC_SECTOR_FEDERAL"
  def untergrenze_bund(p: Profil) -> int                          # Summe spanne.von der Bundeszuwendungen
  def fetch_liste(raw_dir: Path, http: Callable[[str], bytes]) -> dict          # speichert raw_dir/"lobbyregister"/"liste.json"
  def fetch_details(raw_dir: Path, paare: list[tuple[str, int]], http, pause: float = 1.5, log: Callable[[str], None] = print) -> list[Path]
      # speichert raw_dir/"lobbyregister"/f"{nr}_{id}.json"; vorhandene Dateien werden nicht erneut geladen
  def lade_profile(raw_dir: Path) -> list[Profil]                 # alle gespeicherten Details
  ```
- Personen: `legalRepresentatives` → rolle `gesetzlicher_vertreter`; `entrustedPersons` → rolle `interessenvertreter`; dieselbe Person in beiden Listen (gleicher Vor- und Nachname) wird einmal geführt mit rolle `gesetzlicher_vertreter` und Funktionstext aus `legalRepresentatives`. `recentGovernmentFunction`: `art` = `type.code`, `funktion` = `houseOfRepresentatives.function.de` oder `federalAdministration.function` oder `federalGovernment.function` (je nach `type`), `stelle` = `federalAdministration.supremeFederalAuthority` falls vorhanden, sonst `type.de`.
- `stand` = `registerEntryDetails.validFromDate[:10]`; `geschaeftsjahr` = `publicAllowances.relatedFiscalYearStart[:4]`; `jahresabschluss_jahr` = `annualReports.previousLastFiscalYearStart[:4]`.

- [ ] **Step 1: Fixtures anlegen.** `lobby_liste_ausschnitt.json` aus `sucheJson` (Struktur `{"results": [...], "resultCount": 3}`), `lobby_detail_R004511.json` aus dem Detailabruf; nur Felder behalten, die oben genannt sind, plus `registerNumber`, `registerEntryDetails`, `accountDetails.activeLobbyist`.

- [ ] **Step 2: Failing tests schreiben**

```python
def test_extract_profil_liest_personen_zuwendungen_und_pflichtangaben():
    p = extract_profil(load_fixture("lobby_detail_R004511.json"))
    assert p.nummer == "R004511" and p.eintrag_id == 82516 and p.version == 12
    assert p.name == "Amadeu Antonio Stiftung" and p.rechtsform == "Rechtsfähige Stiftung bürgerlichen Rechts" and p.sitz == "Berlin"
    assert [x.rolle for x in p.personen].count("gesetzlicher_vertreter") == 2
    assert all(x.regierungsfunktion is None for x in p.personen)
    zb = bundeszuwendungen(p)
    assert len(zb) == 16 and zb[0].geber == "Bundesministerium für Familie, Senioren, Frauen und Jugend"
    assert zb[0].spanne.von == 1_040_001 and zb[0].spanne.bis == 1_050_000 and zb[0].geschaeftsjahr == "2025"
    assert untergrenze_bund(p) == sum(z.spanne.von for z in zb)
    assert p.spenden.von == 4_190_001 and p.lobbyausgaben.bis == 10_000
    assert p.jahresabschluss_url.startswith("https://www.lobbyregister.bundestag.de/media/") and p.jahresabschluss_jahr == "2024"
    assert "Öffentliche Zuwendungen" in p.finanzierungsquellen

def test_person_in_beiden_listen_wird_einmal_gefuehrt():
    d = load_fixture("lobby_detail_R004511.json")   # Reinfrank steht als Vertreter und als Interessenvertreter
    p = extract_profil(d)
    assert [x.nachname for x in p.personen].count("Reinfrank") == 1

def test_regierungsfunktion_wird_uebernommen():
    d = load_fixture("lobby_detail_R004511.json")
    d["lobbyistIdentity"]["legalRepresentatives"][0]["recentGovernmentFunctionPresent"] = True
    d["lobbyistIdentity"]["legalRepresentatives"][0]["recentGovernmentFunction"] = {"ended": True, "endDate": "2025-04", "type": {"code": "HOUSE_OF_REPRESENTATIVES", "de": "Bundestag"}, "houseOfRepresentatives": {"function": {"code": "MEMBER", "de": "Mitglied des Deutschen Bundestages"}}}
    p = extract_profil(d)
    rf = p.personen[0].regierungsfunktion
    assert rf.art == "HOUSE_OF_REPRESENTATIVES" and rf.funktion == "Mitglied des Deutschen Bundestages" and rf.beendet and rf.ende == "2025-04"

def test_auswahl_nur_aktive_organisationen():
    liste = load_fixture("lobby_liste_ausschnitt.json")
    paare = auswahl(liste, set())
    assert all(isinstance(nr, str) and isinstance(i, int) for nr, i in paare)
    assert len(paare) == 2   # natürliche Person fehlt

def test_fetch_details_ueberspringt_vorhandene(tmp_path):
    calls = []
    def http(url): calls.append(url); return json.dumps(load_fixture("lobby_detail_R004511.json")).encode()
    fetch_details(tmp_path, [("R004511", 82516)], http, pause=0)
    fetch_details(tmp_path, [("R004511", 82516)], http, pause=0)
    assert calls == [detail_url("R004511", 82516)]
    assert lade_profile(tmp_path)[0].name == "Amadeu Antonio Stiftung"
```

- [ ] **Step 3: Tests laufen lassen** – Run: `cd pipeline && uv run pytest -q tests/test_lobbyregister.py` – Expected: FAIL (ModuleNotFoundError).
- [ ] **Step 4: `lobbyregister.py` implementieren** (Signaturen oben; Fehlertoleranz: fehlende Blöcke ergeben leere Listen/None; `http` ist injizierbar, Standard `portal.fetch_bytes` falls vorhanden, sonst `urllib.request` mit `portal.USER_AGENT`).
- [ ] **Step 5: Tests grün** – Run: `cd pipeline && uv run pytest -q tests/test_lobbyregister.py` – Expected: 5 passed.
- [ ] **Step 6: Commit** `"Empfänger: Lobbyregister-Modul (Liste, Detailprofile, Pflichtangaben)"`.

---

### Task 2: Bundestag-Modul (Abgeordnete und veröffentlichungspflichtige Angaben)

**Files:**
- Create: `pipeline/src/bhtracker/bundestag.py`
- Test: `pipeline/tests/test_bundestag.py`, Fixtures `pipeline/tests/fixtures/mdb_liste_seite.html` (eine Ajax-Seite von `https://www.bundestag.de/ajax/filterlist/de/abgeordnete/1040594-1040594?limit=12&offset=0`, auf die Linkliste gekürzt) und `pipeline/tests/fixtures/mdb_bio_ausschnitt.html` (Biografie-Ausschnitt mit Name, Fraktion, Block „Mitgliedschaften und Ämter im Bundestag“ und Block „Veröffentlichungspflichtige Angaben“ mit den vier `<h3>`-Kategorien aus dem Beispiel Abdi) sowie `mdb_bio_ohne_angaben.html` (Biografie ohne den Block).

**Interfaces:**
- Produces:
  ```python
  LISTE_URL = "https://www.bundestag.de/ajax/filterlist/de/abgeordnete/1040594-1040594"
  def bio_urls_aus_seite(html: str) -> list[str]          # absolute URLs https://www.bundestag.de/abgeordnete/biografien/<B>/<slug>-<id>
  def alle_bio_urls(http, pause=1.5, schritt=12, log=print) -> list[str]   # offset 0, 12, 24, … bis eine Seite keine neuen URLs liefert
  @dataclass class Angabe: kategorie: str; organisation: str; ort: str; funktion: str
      # kategorie = h3-Text, organisation = erstes <li> ohne abschließendes ", Ort, " → "DEval - Deutsches Evaluierungsinstitut der Entwicklungszusammenarbeit gemeinnützige GmbH", ort = "Berlin", funktion = zweites <li> ("Mitglied des Beirates (ab 07.04.2025)")
  @dataclass class Abgeordneter: name: str; fraktion: str; url: str; mdb_id: int; ausschuesse: list[str]; angaben: list[Angabe]; stand: str; hinweis: str | None
  def parse_bio(html: str, url: str, stand: str) -> Abgeordneter
  def fetch_bios(raw_dir: Path, urls: list[str], http, pause=1.5, log=print) -> list[Path]   # raw_dir/"bundestag"/f"{mdb_id}.html", vorhandene nicht neu laden
  def lade_abgeordnete(raw_dir: Path) -> list[Abgeordneter]     # stand = Dateidatum (ISO) der HTML-Datei
  ```
- Parser: `html.parser`-basiert, kein BeautifulSoup. Kategorien, die Geld betreffen, sind alle `<h3>` im Block außer „Berufliche Tätigkeit vor der Mitgliedschaft im Deutschen Bundestag“ (bleibt gespeichert, Kategorie wird mitgeführt, Zuordnung entscheidet Task 4). `<li>`-Paare: ungerade Position Organisation, gerade Position Funktion; endet ein Organisations-`<li>` nicht mit „, “ (Einzeleintrag ohne Funktion), ist `funktion = ""`.
- `hinweis = "keine veröffentlichungspflichtigen Angaben"` wenn der Block fehlt; der Lauf geht weiter.

- [ ] **Step 1: Fixtures anlegen** (aus den oben genannten Live-Seiten; Namen bleiben, weil amtlich veröffentlicht).
- [ ] **Step 2: Failing tests**

```python
def test_bio_urls_aus_seite():
    urls = bio_urls_aus_seite(fixture_text("mdb_liste_seite.html"))
    assert len(urls) == 12 and urls[0] == "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330"

def test_parse_bio_liest_angaben_und_ausschuesse():
    a = parse_bio(fixture_text("mdb_bio_ausschnitt.html"), "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", "2026-11-01")
    assert a.name == "Sanae Abdi" and a.fraktion == "SPD" and a.mdb_id == 1043330
    assert "Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung" in a.ausschuesse
    k = [x for x in a.angaben if x.kategorie == "Funktionen in Unternehmen"][0]
    assert k.organisation == "DEval - Deutsches Evaluierungsinstitut der Entwicklungszusammenarbeit gemeinnützige GmbH"
    assert k.ort == "Berlin" and k.funktion == "Mitglied des Beirates (ab 07.04.2025)"
    v = [x for x in a.angaben if x.kategorie == "Funktionen in Vereinen, Verbänden und Stiftungen"][0]
    assert v.organisation == "Deutsche Stiftung Weltbevölkerung (DSW)" and v.ort == "Hannover"
    assert a.hinweis is None

def test_parse_bio_ohne_angaben_bricht_nicht_ab():
    a = parse_bio(fixture_text("mdb_bio_ohne_angaben.html"), "https://www.bundestag.de/abgeordnete/biografien/X/x-1", "2026-11-01")
    assert a.angaben == [] and a.hinweis == "keine veröffentlichungspflichtigen Angaben"

def test_alle_bio_urls_stoppt_ohne_neue_links():
    seite = fixture_text("mdb_liste_seite.html")
    def http(url): return (seite if "offset=0" in url else seite).encode()
    urls = alle_bio_urls(http, pause=0)
    assert len(urls) == 12   # zweite Seite liefert nur Bekanntes → Ende
```

- [ ] **Step 3: Run** `cd pipeline && uv run pytest -q tests/test_bundestag.py` – Expected: FAIL (ModuleNotFoundError).
- [ ] **Step 4: `bundestag.py` implementieren.**
- [ ] **Step 5: Run** – Expected: 4 passed.
- [ ] **Step 6: Commit** `"Empfänger: Bundestag-Modul (Biografien, veröffentlichungspflichtige Angaben)"`.

---

### Task 3: Förderkatalog-Modul

**Files:**
- Create: `pipeline/src/bhtracker/foerderkatalog.py`
- Test: `pipeline/tests/test_foerderkatalog.py`, Fixtures `pipeline/tests/fixtures/foekat_humboldt.csv` (CSV-Export der Suche nach „Alexander von Humboldt-Stiftung“, Latin-1, `="…"`-Felder, 9 Zeilen) und `pipeline/tests/fixtures/foekat_leer.html` (Antwortseite „Die Suche liefert keine Ergebnisse“).

**Interfaces:**
- Produces:
  ```python
  BASE = "https://foerderportal.bund.de/foekat/jsp/SucheAction.do"
  @dataclass class Projekt: fkz: str; ressort: str; stelle: str; empfaenger: str; empfaenger_ort: str; ausfuehrende: str; thema: str; lps: str; lps_text: str; von: str; bis: str; summe: float; foerderart: str   # von/bis ISO (aus "01.01.2024")
  def parse_csv(text: str) -> list[Projekt]           # text bereits dekodiert (latin-1); entfernt das `=`-Präfix der Felder; Summe "142.079.051,00" → 142079051.0
  class Sitzung:   # hält Cookies über urllib.request.HTTPCookieProcessor
      def __init__(self, opener=None, pause: float = 1.5)
      def suche_csv(self, name: str) -> str | None     # GET Suchmaske (Sitzung), POST actionMode=searchlist & suche.detailSuche=true & suche.nameZeStSuche=<name> & submitAction=Suchen, dann GET ?actionMode=print&presentationType=csv; None wenn die Ergebnisseite „keine Ergebnisse“ meldet
  def fetch_projekte(raw_dir: Path, empfaenger: list[tuple[str, str]], sitzung: Sitzung, log=print) -> list[Path]
      # empfaenger = (id, suchname); speichert raw_dir/"foerderkatalog"/f"{id}.csv" (leer = 0 Byte, wird beim nächsten Lauf NICHT erneut abgefragt, nur wenn Datei fehlt)
  def lade_projekte(raw_dir: Path) -> dict[str, list[Projekt]]   # id → Projekte
  ```

- [ ] **Step 1: Fixtures anlegen** (Live-Abruf wie in der Recherche vom 1.11.2026: Suchmaske laden, POST, CSV-Export; `foekat_leer.html` aus einer Suche nach „Amadeu Antonio“).
- [ ] **Step 2: Failing tests**

```python
def test_parse_csv_liest_projekte():
    ps = parse_csv(fixture_bytes("foekat_humboldt.csv").decode("latin-1"))
    assert len(ps) == 9
    p = next(x for x in ps if x.fkz == "M538100")
    assert p.ressort == "BMFTR" and p.empfaenger == "Alexander von Humboldt-Stiftung" and p.empfaenger_ort == "Bonn"
    assert p.von == "2024-01-01" and p.bis == "2028-12-31" and p.summe == 142_079_051.0 and p.foerderart == "Direkte Projektförderung"

def test_parse_csv_leer():
    assert parse_csv('="FKZ";="Ressort"\n') == []

def test_sitzung_erkennt_leeres_ergebnis():
    class Opener:
        def __init__(self): self.calls = []
        def open(self, req, timeout=60):
            url = req.full_url if hasattr(req, "full_url") else req
            self.calls.append(url)
            body = fixture_bytes("foekat_leer.html") if "actionMode=print" not in url else b""
            return io.BytesIO(body)
    s = Sitzung(opener=Opener(), pause=0)
    assert s.suche_csv("Amadeu Antonio") is None
    assert not any("presentationType=csv" in u for u in s.opener.calls)   # kein Export bei leerem Ergebnis

def test_fetch_projekte_schreibt_und_ueberspringt(tmp_path):
    class S:
        calls = 0
        def suche_csv(self, name): S.calls += 1; return fixture_bytes("foekat_humboldt.csv").decode("latin-1")
    fetch_projekte(tmp_path, [("humboldt", "Alexander von Humboldt-Stiftung")], S())
    fetch_projekte(tmp_path, [("humboldt", "Alexander von Humboldt-Stiftung")], S())
    assert S.calls == 1 and len(lade_projekte(tmp_path)["humboldt"]) == 9
```

- [ ] **Step 3: Run** `cd pipeline && uv run pytest -q tests/test_foerderkatalog.py` – Expected: FAIL.
- [ ] **Step 4: Implementieren.** Ergebnisseite auf den Text „Die Suche liefert keine Ergebnisse“ prüfen (Latin-1 dekodieren); Trefferzahl aus „(N Treffer)“ ins Log.
- [ ] **Step 5: Run** – Expected: 4 passed.
- [ ] **Step 6: Commit** `"Empfänger: Förderkatalog-Modul (Suche je Empfänger, CSV-Export)"`.

---

### Task 4: Empfänger-Stamm, Namensabgleich, Verbindungen (reine Logik)

**Files:**
- Create: `pipeline/src/bhtracker/empfaenger.py`, `data/manual/empfaenger.yaml`, `data/manual/ressorts.yaml`, `data/manual/verbindungen.yaml`, `data/manual/jahresabschluss.yaml`, `data/review/README.md`
- Test: `pipeline/tests/test_empfaenger.py`

**Interfaces:**
- Consumes: `Profil`, `Person`, `Zuwendung` (Task 1); `Abgeordneter`, `Angabe` (Task 2); `Projekt` (Task 3); `BudgetRow` (model.py).
- `data/manual/empfaenger.yaml`:
  ```yaml
  # Stamm der Empfänger. Automatisch erkannte Empfänger (Lobbyregister mit Bundesmitteln, Titel mit Namen) brauchen keinen Eintrag;
  # Einträge hier ergänzen oder überschreiben: Aliasse, Zuordnung zu Titeln, Förderkatalog-Suchname, Art.
  empfaenger:
    - id: goethe-institut
      name: Goethe-Institut e. V.
      aliasse: ["Goethe-Institut", "Goethe Institut e.V."]
      lobbyregister: null              # R-Nummer oder null
      titel: ["05-0504-68740"]         # Haushaltstitel, die diesen Empfänger nennen
      foerderkatalog: "Goethe-Institut"
      art: verein_stiftung             # unternehmen | verein_stiftung | forschung | oeffentlich | kirche_wohlfahrt | sonstige
      geprueft: true
      quelle: "https://www.bundeshaushalt.de/"
  ```
- `data/manual/ressorts.yaml`: `ressorts: [{epl: "17", kurz: "BMFSFJ", namen: ["Bundesministerium für Familie, Senioren, Frauen und Jugend", "Bundesministerium für Bildung, Familie, Senioren, Frauen und Jugend", "BMBFSFJ", "BMFSFJ"]}, …]` für alle Einzelpläne 04–30 inklusive nachgeordneter Behörden, die im Lobbyregister als Geldgeber auftauchen (BAFA → 09, Projektträger Jülich → 30, DLR-PT → 30, Bundesamt für Naturschutz → 16, BLE → 10, GIZ/Engagement Global → 23, BBK/BKA/BAMF → 06, Umweltbundesamt → 16, KfW → 09 nur mit Hinweis „Durchleitung“). Quelle je Eintrag: Organisationsplan oder Haushaltstitel-URL.
- `data/manual/verbindungen.yaml`: `verbindungen: [{empfaenger: <id>, person: "Vorname Nachname", funktion_person: "…", funktion_beim_empfaenger: "…", typ: manuell, quelle: URL, stand: ISO, geprueft: true}]` (zunächst leer: `verbindungen: []`).
- `data/manual/jahresabschluss.yaml`: `eintraege: [{empfaenger: <id>, geschaeftsjahr: 2024, url: PDF, seite: 2, pruefer: "Gem.Audit PartG mbB", ertraege_gesamt: 12523375, oeffentliche_hand: 7351034, spenden: 3308958, personalaufwand: 6965568, projektfoerderung: 1015267, weitergeleitete_mittel: 901912, jahresergebnis: 1490418, erfasst: ISO, hinweis: "Personalaufwand = alle Beschäftigten; Vorstandsvergütung nicht gesondert ausgewiesen"}]` (Task 9 füllt sie).
- Produces:
  ```python
  RECHTSFORM_TOKENS = ("e. v.", "e.v.", "ev", "ggmbh", "gmbh", "mbh", "ag", "se", "kg", "gug (haftungsbeschränkt)", "gug", "gbr", "ohg", "kgaa", "ug (haftungsbeschränkt)", "ug")
  def norm_name(s: str) -> str          # klein, ß→ss, ä/ö/ü→ae/oe/ue, Rechtsform-Tokens am Ende entfernen, Klammerzusätze entfernen, Satzzeichen → Leerzeichen, Mehrfach-Leerzeichen zusammenziehen, trim. "Stiftung" bleibt.
  def slug(s: str) -> str               # id aus norm_name: Leerzeichen → "-", nur [a-z0-9-], max 60 Zeichen; Kollisionen bekommen "-2", "-3"
  def empfaenger_aus_titeln(rows: list[BudgetRow]) -> dict[str, tuple[str, list[str]]]
      # erkennt Titeltexte mit Muster r"^(Zuschuss|Zuschüsse|Zuwendung|Zuwendungen|Beitrag|Beiträge|Einlage|Zuweisungen?) (an|in) (die |den |das |der )?(?P<name>.+?)( - .*| für .*| zur .*| zum .*)?$" und r"^(?P<name>.+?(e\. ?V\.|gGmbH|GmbH|Stiftung[^,]*|Institut[^,]*)),? [A-ZÄÖÜ][a-zäöü]+( \(Main\))? - .*$" (Name, Ort - Zweck); ergibt norm_name → (Anzeigename, [titel-ids]); Gruppen 684–687, 893, 894 und Titeltexte mit "Postbeamtenversorgungskasse" werden auch ohne Muster erkannt, wenn der Text einen Eigennamen mit Rechtsform enthält
  def ressort_zu_epl(name: str, ressorts: dict) -> str | None    # exakter oder Präfix-Abgleich nach norm_name auf die `namen`-Listen; sonst None
  @dataclass class Kandidat: person: str; funktion_person: str; organisation_text: str; empfaenger_id: str; empfaenger_name: str; aehnlichkeit: float; quelle: str
  @dataclass class Verbindung: typ: str; person: str; funktion_person: str; funktion_beim_empfaenger: str; kategorie: str; abgleich: str; ausschuesse: list[str]; quellen: list[dict]; stand: str
      # typ ∈ {"abgeordneter_funktion", "regierungsfunktion", "manuell"}; abgleich ∈ {"exakt", "geprueft", "eigenangabe"}
  def verbindungen_aus_angaben(abgeordnete: list[Abgeordneter], stamm: dict[str, StammEintrag]) -> tuple[dict[str, list[Verbindung]], list[Kandidat]]
      # exakt: norm_name(angabe.organisation) == norm_name(stamm.name) oder einem Alias → Verbindung(abgleich="exakt", quellen=[bundestag-URL])
      # Kandidat: difflib.SequenceMatcher(None, a, b).ratio() >= 0.85 oder eines enthält das andere (min. 8 Zeichen) → Kandidat
      # Kategorie "Berufliche Tätigkeit vor der Mitgliedschaft im Deutschen Bundestag" erzeugt keine Verbindung, nur Kandidaten mit Hinweis
  def verbindungen_aus_profil(p: Profil) -> list[Verbindung]      # jede Person mit regierungsfunktion → Verbindung(typ="regierungsfunktion", abgleich="eigenangabe", funktion_person=<rf.funktion, rf.stelle, "bis <ende>">)
  def manuelle_verbindungen(yaml_data: dict, empfaenger_id: str) -> list[Verbindung]   # nur geprueft: true
  def verbindungssatz(v: Verbindung, empfaenger_name: str, geld_aus: list[str]) -> str
      # "Sanae Abdi (MdB, SPD) ist laut bundestag.de Mitglied des Beirates (ab 07.04.2025) bei DEval … gGmbH. DEval … erhielt laut Lobbyregister Mittel von: Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung." – nur Tatsachen, Quellenangabe pro Satzteil
  ```

- [ ] **Step 1: Manuelle Dateien anlegen** (`empfaenger.yaml` mit mindestens den 30 größten namentlich genannten Titel-Empfängern aus 2025 als geprüfte Einträge inkl. `titel`-Zuordnung; `ressorts.yaml` vollständig für Epl. 04–30; `verbindungen.yaml` leer; `jahresabschluss.yaml` leer; `data/review/README.md` erklärt die Kandidatenliste).
- [ ] **Step 2: Failing tests**

```python
def test_norm_name_entfernt_rechtsform_und_umlaute():
    assert norm_name("Deutsche Stiftung Weltbevölkerung (DSW)") == "deutsche stiftung weltbevoelkerung"
    assert norm_name("Goethe-Institut e. V.") == norm_name("Goethe Institut e.V.") == "goethe institut"
    assert norm_name("Fraunhofer-Gesellschaft zur Förderung der angewandten Forschung e. V.") == "fraunhofer gesellschaft zur foerderung der angewandten forschung"

def test_empfaenger_aus_titeln_erkennt_namen():
    rows = [row("04-0452-68591", "Zuschuss an die Rundfunkanstalt Deutsche Welle"), row("05-0504-68740", "Goethe-Institut e. V., München - Betrieb und operative Mittel"),
            row("11-1101-68101", "Bürgergeld"), row("17-1702-68604", "Zuschuss an das Deutsche Jugendinstitut e. V., München")]
    e = empfaenger_aus_titeln(rows)
    assert e[norm_name("Rundfunkanstalt Deutsche Welle")][1] == ["04-0452-68591"]
    assert e[norm_name("Goethe-Institut e. V.")][0] == "Goethe-Institut e. V."
    assert e[norm_name("Deutsches Jugendinstitut e. V.")][1] == ["17-1702-68604"]
    assert norm_name("Bürgergeld") not in e

def test_ressort_zu_epl_unbekannt_bleibt_none():
    r = {"ressorts": [{"epl": "30", "kurz": "BMFTR", "namen": ["Bundesministerium für Bildung und Forschung", "BMBF", "Bundesministerium für Forschung, Technologie und Raumfahrt"]}]}
    assert ressort_zu_epl("BMBF", r) == "30"
    assert ressort_zu_epl("Bundesministerium für Forschung, Technologie und Raumfahrt (BMFTR)", r) == "30"
    assert ressort_zu_epl("Stadt Köln", r) is None

def test_verbindung_nur_bei_exaktem_namen():
    stamm = {"deutsche-bank": Stamm("deutsche-bank", "Deutsche Bank AG", []), "dsw": Stamm("dsw", "Deutsche Stiftung Weltbevölkerung (DSW)", [])}
    mdb = Abgeordneter("Sanae Abdi", "SPD", "https://www.bundestag.de/abgeordnete/biografien/A/abdi_sanae-1043330", 1043330, ["Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung"],
                       [Angabe("Funktionen in Vereinen, Verbänden und Stiftungen", "Deutsche Stiftung Weltbevölkerung (DSW)", "Hannover", "Mitglied des Parlamentarischen Beirates (ab 07.07.2025)"),
                        Angabe("Funktionen in Unternehmen", "Deutsche Bank Stiftung", "Frankfurt", "Kuratorium")], "2026-11-01", None)
    verb, kandidaten = verbindungen_aus_angaben([mdb], stamm)
    assert [v.abgleich for v in verb["dsw"]] == ["exakt"] and verb["dsw"][0].funktion_beim_empfaenger.startswith("Mitglied des Parlamentarischen Beirates")
    assert "deutsche-bank" not in verb
    assert any(k.empfaenger_id == "deutsche-bank" and k.organisation_text == "Deutsche Bank Stiftung" for k in kandidaten)

def test_berufliche_taetigkeit_vorher_erzeugt_keine_verbindung():
    stamm = {"giz": Stamm("giz", "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH", [])}
    mdb = Abgeordneter("Sanae Abdi", "SPD", "https://x", 1, [], [Angabe("Berufliche Tätigkeit vor der Mitgliedschaft im Deutschen Bundestag", "Deutsche Gesellschaft für Internationale Zusammenarbeit (GIZ) GmbH", "Bonn", "Projekt- und Finanzmanagerin, Rückkehrrecht")], "2026-11-01", None)
    verb, kandidaten = verbindungen_aus_angaben([mdb], stamm)
    assert verb == {} and kandidaten[0].empfaenger_id == "giz"

def test_verbindungssatz_ist_tatsachensatz():
    v = Verbindung("abgeordneter_funktion", "Sanae Abdi", "MdB, SPD", "Mitglied des Beirates (ab 07.04.2025)", "Funktionen in Unternehmen", "exakt", ["Ausschuss für wirtschaftliche Zusammenarbeit und Entwicklung"], [{"kurz": "bundestag.de", "url": "https://x"}], "2026-11-01")
    s = verbindungssatz(v, "DEval gGmbH", ["Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung"])
    assert s.startswith("Sanae Abdi (MdB, SPD) ist laut bundestag.de Mitglied des Beirates (ab 07.04.2025) bei DEval gGmbH.")
    assert "Verdacht" not in s and "DEval gGmbH erhielt laut Lobbyregister Mittel von: Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung" in s
```

- [ ] **Step 3: Run** `cd pipeline && uv run pytest -q tests/test_empfaenger.py` – Expected: FAIL.
- [ ] **Step 4: Implementieren** (`Stamm`-Dataclass: id, name, aliasse, dann mit Standardwerten lobbyregister=None, titel=[], foerderkatalog=None, art="sonstige", geprueft=False, quelle=None; die Tests rufen `Stamm(id, name, aliasse)` positional).
- [ ] **Step 5: Run** – Expected: 6 passed.
- [ ] **Step 6: Commit** `"Empfänger: Stamm, Namensabgleich und Verbindungslogik"`.

---

### Task 5: Build der Empfänger-Dateien, CLI `fetch-empfaenger`, Schalter `--ohne-personen`

**Files:**
- Modify: `pipeline/src/bhtracker/empfaenger.py` (Build-Teil), `pipeline/src/bhtracker/cli.py`, `pipeline/README.md`, `.gitignore` (`data/raw/**` bleibt; `data/review/` wird committet)
- Test: `pipeline/tests/test_empfaenger_build.py`

**Interfaces:**
- Produces:
  ```python
  def baue_stamm(manual: dict, profile: list[Profil], years: dict[int, list[BudgetRow]]) -> dict[str, Stamm]
      # Reihenfolge: manuelle Einträge; dann Lobbyregister-Profile mit Bundeszuwendungen (id = slug(name), lobbyregister = nummer); dann Titel-Empfänger ohne Treffer.
      # Zusammenführung Profil ↔ Titel-Empfänger nur bei exakt gleichem norm_name oder Alias; Ähnliches → data/review/empfaenger_kandidaten.yaml
  def build_empfaenger(manual_dir: Path, raw_dir: Path, out: Path, years: dict[int, list[BudgetRow]], ist_years: dict[int, list[BudgetRow]], *, mit_personen: bool = True, stand: str) -> Path
      # schreibt out/"empfaenger"/"index.json" und out/"empfaenger"/f"{id}.json" sowie data/review/verbindungen_kandidaten.yaml und data/review/empfaenger_kandidaten.yaml (Pfad: manual_dir.parent/"review")
  ```
- JSON je Empfänger (`out/empfaenger/<id>.json`):
  ```json
  {"id":"…","name":"…","art":"verein_stiftung","rechtsform":"…","sitz":"Berlin","website":"…","stand":"2026-11-01",
   "lobbyregister":{"nummer":"R004511","eintrag_id":82516,"version":12,"stand":"2026-09-02","url":"…","pdf_url":"…"}|null,
   "haushalt":{"titel":[{"id":"05-0504-68740","text":"…","epl":"05","epl_text":"Auswärtiges Amt","werte":{"2015":{"soll":1,"ist":2},…}}]},
   "lobby_zuwendungen":[{"geber":"…","epl":"17"|null,"von":1040001,"bis":1050000,"zweck":"…","geschaeftsjahr":"2025"}],
   "lobby_untergrenze_bund":12345,
   "foerderkatalog":[{"fkz":"…","ressort":"BMFTR","epl":"30"|null,"thema":"…","von":"2024-01-01","bis":"2028-12-31","summe":142079051.0,"foerderart":"…"}],
   "personen":[{"name":"Timo Reinfrank","funktion":"Vorstand","rolle":"gesetzlicher_vertreter","regierungsfunktion":null,"quelle":{"kurz":"Lobbyregister","url":"…","stand":"2026-09-02"}}],
   "verbindungen":[{"typ":"…","person":"…","funktion_person":"…","funktion_beim_empfaenger":"…","kategorie":"…","abgleich":"exakt","satz":"…","ausschuesse":[…],"geld_aus":[…],"quellen":[{"kurz":"bundestag.de","url":"…","stand":"…"}],"stand":"…"}],
   "pflichtangaben":{"finanzierungsquellen":["Öffentliche Zuwendungen","…"],"spenden":{"von":…,"bis":…},"mitgliedsbeitraege":{…}|null,"lobbyausgaben":{…}|null,"geschaeftsjahr":"2025",
                     "jahresabschluss":{"url":"…","geschaeftsjahr":"2024","kennzahlen":{…}|null,"seite":2|null,"pruefer":"…"|null,"hinweis":"…"|null}|null},
   "quellen":[{"kurz":"Lobbyregister","url":"…","abgerufen":"2026-11-01","etikett":"Eigenangabe"}, {"kurz":"bundeshaushalt.de","url":"…"}, {"kurz":"Förderkatalog","url":"https://foerderportal.bund.de/foekat/"}, {"kurz":"bundestag.de","url":"…"}]}
  ```
- `index.json`: `{"stand": ISO, "mit_personen": bool, "eintraege": [{"id","name","art","rechtsform","sitz","lobby_untergrenze_bund","haushalt_soll_letztes_jahr","foerderkatalog_summe","n_personen","n_verbindungen","lobbyregister": "R…"|null, "epls": ["17","30"]}], "titel": {"05-0504-68740": {"id": "goethe-institut", "name": "Goethe-Institut e. V."}}}` (`epls` = Einzelpläne aus Titeln, Lobbyregister-Gebern und Förderkatalog-Ressorts; `titel` = Karte Titel-Id → Empfänger für Fluss und Panel, Task 8)
- `--ohne-personen`: `personen: []`, `verbindungen: []`, `n_personen: 0`, `n_verbindungen: 0`, `mit_personen: false`; Prüflisten werden trotzdem geschrieben (sie liegen nicht im Web-Build).
- CLI: `bht fetch-empfaenger [--quellen lobbyregister,bundestag,foerderkatalog] [--limit N] [--pause 1.5]` lädt Liste + alle aktiven Organisationsprofile (≈ 6.700 Abrufe, Pause 1,5 s ≈ 3 h; `--limit` für Tests), alle Biografien (≈ 630), Förderkatalog für alle Stamm-Einträge mit Bundesmitteln oder Titeln. `bht build` ruft `build_empfaenger` nach `build_sozialkassen`, wenn `data/raw/lobbyregister/liste.json` existiert; sonst Meldung „empfaenger: keine Rohdaten, übersprungen“.

- [ ] **Step 1: Failing tests** (mit Fixtures aus Task 1–3 in einem `tmp_path`-Raw-Ordner und einem Mini-Haushalt aus zwei Jahren)

```python
def test_build_schreibt_index_und_seiten(tmp_path):
    raw, out, manual = make_raw(tmp_path), tmp_path / "build", make_manual(tmp_path)
    build_empfaenger(manual, raw, out, years, ist_years, stand="2026-11-01")
    idx = json.loads((out / "empfaenger" / "index.json").read_text(encoding="utf-8"))
    e = next(x for x in idx["eintraege"] if x["id"] == "amadeu-antonio-stiftung")
    assert e["lobby_untergrenze_bund"] > 0 and e["n_personen"] == 2
    seite = json.loads((out / "empfaenger" / "amadeu-antonio-stiftung.json").read_text(encoding="utf-8"))
    assert seite["lobby_zuwendungen"][0]["epl"] == "17"
    assert seite["pflichtangaben"]["jahresabschluss"]["url"].startswith("https://")
    assert all("abgerufen" in q or "stand" in q for q in seite["quellen"])

def test_titel_empfaenger_bekommt_zeitreihe(tmp_path):
    ...  # Goethe-Institut aus manual mit titel 05-0504-68740 → seite["haushalt"]["titel"][0]["werte"]["2025"]["soll"] == <Fixture-Wert>, Jahre 2024 und 2025 vorhanden

def test_betraege_bleiben_getrennt(tmp_path):
    ...  # keine Feldsumme über Quellen: Schlüssel "gesamt" existiert nirgends in der Seite

def test_ohne_personen_entfernt_alle_namen(tmp_path):
    build_empfaenger(manual, raw, out, years, ist_years, mit_personen=False, stand="2026-11-01")
    text = (out / "empfaenger" / "amadeu-antonio-stiftung.json").read_text(encoding="utf-8")
    assert "Reinfrank" not in text and json.loads(text)["verbindungen"] == []
    assert json.loads((out / "empfaenger" / "index.json").read_text(encoding="utf-8"))["mit_personen"] is False

def test_aehnliche_namen_landen_in_prueflisten(tmp_path):
    ...  # Titel „Zuschuss an die Amadeu-Antonio-Stiftung Berlin“ (nicht exakt) → data/review/empfaenger_kandidaten.yaml enthält beide Namen, Seite hat keinen Titel

def test_cli_build_ohne_rohdaten_ueberspringt(tmp_path, capsys):
    ...  # cmd_build mit leerem raw: Ausgabe enthält "empfaenger: keine Rohdaten"
```

- [ ] **Step 2: Run** `cd pipeline && uv run pytest -q tests/test_empfaenger_build.py` – Expected: FAIL.
- [ ] **Step 3: Implementieren** (Build, CLI-Unterbefehl, Schalter, README-Abschnitt „Empfänger-Daten“).
- [ ] **Step 4: Run** `cd pipeline && uv run pytest -q` – Expected: alle grün (bisher 62 + neue).
- [ ] **Step 5: Echte Daten laden**: `uv run bht fetch-empfaenger --quellen lobbyregister` (im Hintergrund, Log in `data/raw/fetch_log.json` ergänzen), danach `bundestag`, danach `foerderkatalog`. Erwartet: ≈ 6.700 Profile, ≈ 630 Biografien, Förderkatalog-CSV für alle Stamm-Einträge mit Bundesmitteln.
- [ ] **Step 6: `uv run bht build`** – Expected: „empfaenger: N Seiten“ mit N ≥ 1.400; Prüflisten in `data/review/`.
- [ ] **Step 7: Stichprobe** gegen Live-Seiten: Amadeu Antonio Stiftung (16 Bundeszuwendungen, 2 Vorstände, Jahresabschluss-Link), Goethe-Institut (Titel 05-0504-68740 mit Zeitreihe), ein Unternehmen (z. B. Robert Bosch GmbH).
- [ ] **Step 8: Commit** `"Empfänger: Build der Empfänger-Seiten, fetch-empfaenger, Schalter --ohne-personen"` (Build-Dateien `data/build/empfaenger/` und `data/review/` eingeschlossen).

---

### Task 6: Web-Modell (Typen, Laden, Teilen-Link, Zustand)

**Files:**
- Create: `web/src/lib/model/empfaenger.ts`
- Modify: `web/src/lib/model/types.ts` (ViewId um `"empfaenger"`), `web/src/lib/model/share.ts` (`VIEWS`, `e=<id>`), `web/src/lib/model/load.ts`, `web/src/lib/state.svelte.ts`
- Test: `web/tests/empfaenger.test.ts`, `web/tests/share.test.ts` (ergänzen), `web/tests/state.test.ts` (ergänzen)

**Interfaces:**
- Produces (`empfaenger.ts`):
  ```ts
  export type EmpfaengerArt = "unternehmen" | "verein_stiftung" | "forschung" | "oeffentlich" | "kirche_wohlfahrt" | "sonstige";
  export interface EmpfaengerIndexEintrag { id: string; name: string; art: EmpfaengerArt; rechtsform: string; sitz: string; lobby_untergrenze_bund: number; haushalt_soll_letztes_jahr: number; foerderkatalog_summe: number; n_personen: number; n_verbindungen: number; lobbyregister: string | null }
  export interface EmpfaengerIndex { stand: string; mit_personen: boolean; eintraege: EmpfaengerIndexEintrag[] }
  export interface EmpfaengerSeite { /* Felder wie JSON in Task 5 */ }
  export type EmpfaengerSort = "bund" | "haushalt" | "name" | "verbindungen";
  export function filtereEmpfaenger(index: EmpfaengerIndex, q: string, art: EmpfaengerArt | "alle", sort: EmpfaengerSort, epl?: string): EmpfaengerIndexEintrag[]
      // q: Teilstring auf norm (klein, Umlaute aufgelöst) von name; sort "bund" = lobby_untergrenze_bund absteigend, "haushalt" = haushalt_soll_letztes_jahr absteigend, "name" = de-Locale, "verbindungen" = n_verbindungen absteigend, dann bund
      // epl: nur Einträge, die (laut Index-Feld `epls: string[]`, in Task 5 ergänzen) Geld aus diesem Einzelplan erhalten
  export function fmtSpanne(von: number, bis: number): string          // "1,04–1,05 Mio €"; von === bis → fmtEuro
  export function geldAus(seite: EmpfaengerSeite): string[]            // eindeutige Geber-Namen aus lobby_zuwendungen, sortiert nach Untergrenze absteigend
  export function titelZeitreihe(seite: EmpfaengerSeite, stand: "soll" | "ist"): { jahr: number; wert: number }[]   // Summe über alle Titel je Jahr, fehlende Ist-Werte ausgelassen
  export function issueUrl(seite: EmpfaengerSeite): string           // https://github.com/eis2k/Bundeshaushaltstracker/issues/new?title=…&body=… (URL-kodiert, Body nennt id, Name, Stand und bittet um Beleg-URL)
  ```
- `share.ts`: `VIEWS` um `"empfaenger"`; `encodeScenario(..., empfaenger?: string | null)` hängt `e=<id>` an, wenn gesetzt; `decodeScenario` liefert zusätzlich `empfaenger: string | null` (Zeichen erlaubt: `[a-z0-9-]`, sonst null).
- `state.svelte.ts`: `empfaengerIndex = $state<EmpfaengerIndex | null>(null)`, `empfaengerId = $state<string | null>(null)`, `empfaengerSeite = $state<EmpfaengerSeite | null>(null)`, `empfaengerFehlt = $state<string | null>(null)` (unbekannte Id aus dem Link); `empfaengerFilterEpl = $state<string | null>(null)`, `empfaengerByTitel = $derived(this.empfaengerIndex?.titel ?? {})`, `async ensureEmpfaenger()`, `openEmpfaengerListe(filter?: { epl?: string })` (setzt view `"empfaenger"`, `empfaengerId = null`, `empfaengerFilterEpl`), `async openEmpfaenger(id: string | null)` (lädt Seite, setzt view `"empfaenger"`, bei 404 `empfaengerFehlt = id`, `empfaengerSeite = null`), `toHash()` trägt `e=`; `init` wertet `e=` aus. Loader-Felder `loadEmpfaengerIndex?`, `loadEmpfaenger?`.

- [ ] **Step 1: Failing tests**

```ts
test("filtereEmpfaenger: Suche ist umlaut-tolerant, Sortierung nach Bund-Untergrenze", () => {
  const idx = { stand: "2026-11-01", mit_personen: true, eintraege: [e("a", "Amadeu Antonio Stiftung", 1e6), e("b", "Goethe-Institut e. V.", 5e6), e("c", "Deutsche Stiftung Weltbevölkerung", 2e6)] };
  expect(filtereEmpfaenger(idx, "weltbevoelkerung", "alle", "bund").map((x) => x.id)).toEqual(["c"]);
  expect(filtereEmpfaenger(idx, "", "alle", "bund").map((x) => x.id)).toEqual(["b", "c", "a"]);
});
test("fmtSpanne", () => { expect(fmtSpanne(1_040_001, 1_050_000)).toBe("1,04–1,05 Mio €"); expect(fmtSpanne(0, 0)).toBe("0 €"); });
test("titelZeitreihe summiert Titel je Jahr und lässt fehlende Ist-Werte aus", () => { … });
test("issueUrl enthält Id und Stand", () => { expect(issueUrl(seite)).toContain(encodeURIComponent("amadeu-antonio-stiftung")); });
// share.test.ts
test("e=<id> wird kodiert und dekodiert; ungültige Zeichen ergeben null", () => {
  const h = encodeScenario(base, "empfaenger", [], "ressort", "gesamt", "goethe-institut");
  expect(h).toContain("a=empfaenger"); expect(h).toContain("e=goethe-institut");
  expect(decodeScenario(h, fixtureYear).empfaenger).toBe("goethe-institut");
  expect(decodeScenario("v1;e=../x", fixtureYear).empfaenger).toBeNull();
});
// state.test.ts
test("openEmpfaenger mit unbekannter Id setzt empfaengerFehlt und bleibt in der Liste", async () => { … loader.loadEmpfaenger wirft → app.empfaengerFehlt === "gibt-es-nicht", app.view === "empfaenger", app.empfaengerSeite === null });
```

- [ ] **Step 2: Run** `cd web && npx vitest run tests/empfaenger.test.ts tests/share.test.ts tests/state.test.ts` – Expected: FAIL.
- [ ] **Step 3: Implementieren.** `loadEmpfaengerIndex = () => getJson<EmpfaengerIndex>("empfaenger/index.json")`, `loadEmpfaenger = (id) => getJson<EmpfaengerSeite>(\`empfaenger/${id}.json\`)`.
- [ ] **Step 4: Run** `cd web && npm test && npm run check` – Expected: alle grün, 0 Fehler.
- [ ] **Step 5: Commit** `"Empfänger: Web-Modell, Laden, Teilen-Link e=, Zustand"`.

---

### Task 7: Ansicht „Empfänger“ und Empfänger-Seite

**Files:**
- Create: `web/src/lib/views/Empfaenger.svelte` (Liste), `web/src/lib/views/EmpfaengerSeite.svelte`
- Modify: `web/src/App.svelte` (Zweig `app.view === "empfaenger"`), `web/src/lib/ui/Kopfzeile.svelte` (`views` um `{ id: "empfaenger", label: "Empfänger" }`; Statistik-Zeile bleibt die des Haushalts), `web/src/lib/ui/Panel.svelte` (in der Ansicht „empfaenger“ zeigt das Panel den Hinweistext „Empfänger-Seiten: Belege aus Lobbyregister, Haushalt, Förderkatalog und bundestag.de. Eigenangaben sind gekennzeichnet.“ statt Titelinfos)

**Liste (`Empfaenger.svelte`):** Suchfeld (aria-label „Empfänger suchen“), Filter-Chips Art (alle / Unternehmen / Vereine und Stiftungen / Forschung / öffentliche Einrichtungen / Kirche und Wohlfahrt / sonstige), Sortierung (Bund laut Lobbyregister, Haushaltstitel, Verbindungen, Name), optional Ressort-Filter aus `?epl` (Link aus dem Panel, Task 8), Tabelle: Name (Link), Rechtsform, Sitz, „Bund laut Lobbyregister (Untergrenze)“, „Haushaltstitel <letztes Jahr>“, Verbindungen (Zahl, mit Etikett „belegt“). Fußzeile: Stand, Quellen, Hinweis „Die drei Geldspalten stammen aus verschiedenen Quellen und werden nicht addiert.“ Zeilen zeigen anfangs 100, Knopf „mehr“.

**Seite (`EmpfaengerSeite.svelte`):** Reihenfolge laut Spec §4.6a: Kopf; Block „Belegte Verbindungen“ (je Verbindung der Tatsachensatz `satz`, darunter Quellenlinks mit Stand und das Etikett „automatisch abgeglichen“ bzw. „geprüft“ bzw. „Eigenangabe im Lobbyregister“; keine Verbindung → „In den ausgewerteten Quellen keine belegte Verbindung, Stand <stand>“; `mit_personen === false` → „Personenangaben sind in dieser Fassung nicht veröffentlicht“); Block „Geld vom Bund“ mit drei Unterabschnitten, jeder mit Quellen-Etikett: Haushaltstitel (Tabelle Titel × Jahre, Soll/Ist-Umschalter übernimmt `app.stand`, Balkenreihe der Summe je Jahr als einfache SVG-Säulen), Lobbyregister (Geber, Spanne, Zweck, Geschäftsjahr; Zeile „Untergrenze zusammen“), Förderkatalog (FKZ-Link `https://foerderportal.bund.de/foekat/jsp/SucheAction.do?actionMode=view&fkz=<fkz>`, Ressort, Thema, Laufzeit, Bundesanteil); Block „Wer steht dahinter“ (Name, Funktion, Rolle, ggf. Regierungsfunktion „bis <Datum>“, Quelle Lobbyregister Version/Stand); Block „Pflichtangaben des Empfängers“ (Finanzierungsquellen, Spenden, Mitgliedsbeiträge, Lobbyausgaben, Jahresabschluss: Link, Geschäftsjahr, Kennzahlen-Tabelle mit Seitenangabe und Prüfer, Hinweis); Block „Quellen und Stand“; Knopf „Fehler melden / Beleg einreichen“ (`issueUrl`). Zurück-Link zur Liste; Knopf „Teilen“ der Kopfzeile funktioniert unverändert (Hash enthält `e=`).

- [ ] **Step 1: Komponenten schreiben** (keine Komponententests im Projekt; Logik liegt in `empfaenger.ts`).
- [ ] **Step 2: Run** `cd web && npm run check && npm run build` – Expected: 0 Fehler.
- [ ] **Step 3: Browser-Prüfung** im Dev-Server: Liste lädt, Suche „Amadeu“, Seite öffnet, alle Blöcke sichtbar, Teilen-Link `#v1;j=2025;a=empfaenger;e=amadeu-antonio-stiftung` lädt die Seite direkt, unbekannte Id zeigt Liste mit Hinweis, Handybreite (375 px) ohne horizontales Scrollen.
- [ ] **Step 4: Commit** `"Empfänger: Liste und Empfänger-Seite"`.

---

### Task 8: Verknüpfung mit Fluss und Panel

**Files:**
- Modify: `web/src/lib/views/sankeyData.ts` (Spalte 5), `web/src/lib/views/Fluss.svelte` (Klick auf Empfänger-Knoten), `web/src/lib/ui/Panel.svelte` (Titel-Abschnitt), `web/src/lib/state.svelte.ts` (Karte Titel-Id → Empfänger-Id aus dem Index: Task 5 ergänzt `index.json` um `"titel": {"05-0504-68740": "goethe-institut", …}`)
- Test: `web/tests/sankeyData.test.ts` (ergänzen)

**Interfaces:**
- `buildSankey(..., opts: { …; empfaengerByTitel?: Record<string, { id: string; name: string }> })`: Spalte 5 zeigt für jeden Fokus-Titel mit Eintrag einen Knoten `empfaenger:<id>` (kind `"empfaenger"`, label Name, colorKey `"rest"`), Band Titel → Empfänger in Titelhöhe; alle übrigen Titel bündeln sich wie bisher in `EMPFAENGER_UNBEKANNT`.
- `Fluss.svelte`: Klick auf `empfaenger:<id>` ruft `onEmpfaenger?.(id)` (neue Prop) → `app.openEmpfaenger(id)`; `EMPFAENGER_UNBEKANNT` bleibt nicht klickbar.
- `Panel.svelte`, Titel-Abschnitt: wenn `app.empfaengerByTitel[info.id]` existiert → Zeile „Empfänger: <Name> – Seite öffnen“; sonst, wenn der Titel zu Gruppe 63–69 oder 88/89 gehört → Zeile „Empfänger nicht veröffentlicht“ mit zwei Links: „Bekannte Empfänger dieses Ministeriums laut Lobbyregister“ (`app.openEmpfaengerListe({ epl })`, setzt den Ressort-Filter der Liste) und „Anfrage nach dem Informationsfreiheitsgesetz stellen“ (`https://fragdenstaat.de/anfrage-stellen/`, rel noopener).

- [ ] **Step 1: Failing test**

```ts
test("Spalte 5 löst namentlich bekannte Titel zum Empfänger auf, Rest bleibt gebündelt", () => {
  const s = buildSankey(fixtureYear, base, {}, ["11", "11-1102"], { ...opts, empfaengerByTitel: { "11-1102-63681": { id: "deutsche-rentenversicherung", name: "Deutsche Rentenversicherung Bund" } } });
  expect(s.nodes.find((n) => n.id === "empfaenger:deutsche-rentenversicherung")?.label).toBe("Deutsche Rentenversicherung Bund");
  expect(s.links.find((l) => l.source === "11-1102-63681")?.target).toBe("empfaenger:deutsche-rentenversicherung");
  expect(s.links.find((l) => l.source === "11-1102-63682")?.target).toBe(EMPFAENGER_UNBEKANNT);
});
```

- [ ] **Step 2: Run** `cd web && npx vitest run tests/sankeyData.test.ts` – Expected: FAIL.
- [ ] **Step 3: Implementieren** (sankeyData, Fluss, Panel, State-Karte aus `index.json`).
- [ ] **Step 4: Run** `cd web && npm test && npm run check` – Expected: grün.
- [ ] **Step 5: Browser-Prüfung**: Fokus auf Epl. 05 → Kapitel 0504 → Titel Goethe-Institut zeigt Empfänger-Knoten, Klick öffnet Seite; ein Titel ohne Empfänger zeigt im Panel die zwei Links.
- [ ] **Step 6: Commit** `"Empfänger: Verknüpfung mit Fluss und Panel"`.

---

### Task 9: Jahresabschluss-Kennzahlen (Handerfassung) und Stichproben

**Files:**
- Modify: `data/manual/jahresabschluss.yaml`, danach `uv run bht build` und Commit der Build-Dateien

- [ ] **Step 1:** Die 25 nach Lobbyregister-Untergrenze größten Empfänger der Arten `verein_stiftung` und `kirche_wohlfahrt` mit `jahresabschluss_url` auswählen (Skript-Einzeiler über `index.json`).
- [ ] **Step 2:** Je PDF: Seiten rendern (pypdfium2 + Pillow, wie in der Recherche), Kennzahlen ablesen, Eintrag mit `seite`, `pruefer`, `hinweis` anlegen. Nur ablesbare Zahlen; fehlt ein Posten, bleibt er `null`. Keine Umrechnung, keine Quoten in der Datei (Quoten rechnet die Seite und kennzeichnet sie als Rechnung).
- [ ] **Step 3:** Build, Stichprobe im Browser (Amadeu Antonio Stiftung: Erträge 12.523.375, öffentliche Hand 7.351.034, Personalaufwand 6.965.568, Seite 2, Prüfer Gem.Audit PartG mbB, Hinweis zur Vorstandsvergütung).
- [ ] **Step 4: Commit** `"Empfänger: Jahresabschluss-Kennzahlen für 25 Empfänger"`.

---

### Task 10: Abschluss

- [ ] README: Abschnitt „Wer bekommt es“ auf den Stand bringen (Quellen, Etiketten, Prüflisten, Schalter), Abschnitt „Mitmachen“ um „Beleg einreichen“ ergänzen.
- [ ] Spec §7 Stufe 2 abhaken (mit Branch und Plan), §7 um „2b Personal-Regler“ ergänzen.
- [ ] `pipeline/README.md`: Kommandos `fetch-empfaenger`, Laufzeiten, Pausen, Rohdaten-Ordner.
- [ ] Ledger `docs/superpowers/plans/2026-11-01-stufe-2-empfaenger.ledger.md` vervollständigen.
- [ ] `cd pipeline && uv run pytest -q`, `cd web && npm test && npm run check && npm run build` – Expected: alles grün.
- [ ] Review (opus-Subagent, ganzer Branch), Fix-Pass, ff-Merge nach `main`, Push.
