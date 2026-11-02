"""Porträts und Logos (Spec §4.13): Verweise auf Wikidata/Wikimedia Commons mit Lizenz und Urheber, keine Bilddateien.

Personen: Mitglieder des 21. Deutschen Bundestages (P39 = Q1939555, Wahlperiode P2937 = Q124661964), Porträt P18; Zuordnung über den
Namen nur bei eindeutigem Treffer in beiden Richtungen. Regierungsmitglieder ohne Mandat über die Wikidata-Suche (Beschreibung „Politiker“).
Organisationen: Lobbyregister-ID P10301 → Logo P154 (exakter Schlüssel, keine Namenssuche).
Lizenzen: nur CC0, CC BY, CC BY-SA, Public domain (Commons imageinfo/extmetadata). Rohantworten unter data/raw/bilder/.
"""
from __future__ import annotations

import html
import json
import re
import time
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable

import yaml

from .portal import TIMEOUT, USER_AGENT

WP21 = "Q124661964"
SPARQL = "https://query.wikidata.org/sparql"
COMMONS_API = "https://commons.wikimedia.org/w/api.php"
WIKIDATA_API = "https://www.wikidata.org/w/api.php"

SPARQL_MDB = f"""SELECT ?item ?itemLabel ?bild WHERE {{
  ?item p:P39 ?s . ?s ps:P39 wd:Q1939555 ; pq:P2937 wd:{WP21} .
  OPTIONAL {{ ?item wdt:P18 ?bild }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "de,en". }}
}}"""
SPARQL_LOBBY = """SELECT ?item ?lr ?logo WHERE {
  ?item wdt:P10301 ?lr .
  OPTIONAL { ?item p:P154 ?ls . ?ls ps:P154 ?logo . FILTER NOT EXISTS { ?ls pq:P582 ?ende } }
}"""

_TITEL = re.compile(r"(?<![\w-])(?:Prof|Dr|Dipl|Ing|Mag|Med|Jur|Rer|Nat|Phil|Pol|habil|oec|publ|theol)\.(?:-[A-Za-z]+\.?)?(?=[\s-]|$)|(?<![\w-])h\.\s?c\.(?=\s|$)", re.I)
_TAG = re.compile(r"<[^>]+>")
_VERSTECKT = re.compile(r"<[^>]*display:\s*none[^>]*>.*?</[^>]+>", re.I | re.S)
_WS = re.compile(r"\s+")


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json, application/sparql-results+json"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def lizenz_erlaubt(kurz: str) -> bool:
    """Nur freie Lizenzen: CC0, CC BY, CC BY-SA (alle Versionen) und Public domain; NC/ND, GFDL, Fair use und Leeres nicht."""
    k = (kurz or "").strip().lower()
    if not k:
        return False
    if k.startswith("cc0") or k.startswith("public domain") or k == "pd":
        return True
    if k.startswith("cc by"):
        return "-nc" not in k and "-nd" not in k and " nc" not in k and " nd" not in k
    return False


def norm_person(name: str) -> str:
    """Name ohne Titel, einfacher Leerraum, klein; Umlaute bleiben erhalten."""
    s = _TITEL.sub(" ", name)
    s = s.replace("(", " ").replace(")", " ")
    return _WS.sub(" ", s).strip().lower()


def datei_aus_url(u: str) -> str:
    """Commons-Dateiname aus Special:FilePath-URL oder rohem Dateinamen."""
    if "Special:FilePath/" in u:
        u = u.split("Special:FilePath/", 1)[1]
    return urllib.parse.unquote(u).replace("_", " ").strip()


def validate_bilder(data: dict) -> list[str]:
    errors: list[str] = []
    for i, z in enumerate(data.get("zuordnungen") or []):
        if not z.get("akte_id") or not str(z.get("qid", "")).startswith("Q") or not str(z.get("quelle", "")).startswith("http"):
            errors.append(f"zuordnungen[{i}]: akte_id, qid (Q…) und quelle (URL der Fundstelle) nötig")
    for i, g in enumerate(data.get("gesperrt") or []):
        if not g.get("id") or not g.get("grund"):
            errors.append(f"gesperrt[{i}]: id und grund nötig")
    return errors


def _gesperrt(manual: dict) -> set[str]:
    return {str(g["id"]) for g in (manual.get("gesperrt") or []) if g.get("id")}


def zuordnen_personen(akten: list[dict], mdb: list[dict], suche: dict[str, list[dict]], manual: dict) -> tuple[dict[str, dict], list[dict]]:
    """Akte → {qid, datei}; nur sichtbare Akten mit Mandat oder Regierungsamt, nur eindeutige Namen in beiden Richtungen; manuell schlägt Regel."""
    gesperrt = _gesperrt(manual)
    manuell = {str(z["akte_id"]): str(z["qid"]) for z in (manual.get("zuordnungen") or []) if z.get("akte_id") and z.get("qid")}
    relevant = [a for a in akten if a.get("sichtbar") and any(x in ("mdb", "regierung") for x in a.get("arten") or [])]
    namen: dict[str, list[dict]] = {}
    for a in relevant:
        namen.setdefault(norm_person(a["name"]), []).append(a)
    # je Item nur eine Zeile (SPARQL liefert je Bild eine), das erste Bild zählt
    gesehen: set[str] = set()
    wd: dict[str, list[dict]] = {}
    for m in mdb:
        if m["qid"] in gesehen:
            continue
        gesehen.add(m["qid"])
        wd.setdefault(norm_person(m.get("label") or ""), []).append(m)
    bild_je_qid: dict[str, str | None] = {}
    for m in mdb:
        if m.get("bild") and not bild_je_qid.get(m["qid"]):
            bild_je_qid[m["qid"]] = m["bild"]
    for liste in suche.values():
        for t in liste:
            if t.get("bild") and not bild_je_qid.get(t["qid"]):
                bild_je_qid[t["qid"]] = t["bild"]
    treffer: dict[str, dict] = {}
    pruefliste: list[dict] = []
    for a in relevant:
        aid = a["id"]
        if aid in gesperrt:
            continue
        if aid in manuell:
            qid = manuell[aid]
            bild = bild_je_qid.get(qid)
            if bild:
                treffer[aid] = {"qid": qid, "datei": datei_aus_url(bild)}
            else:
                pruefliste.append({"akte_id": aid, "name": a["name"], "grund": "manuelle Zuordnung ohne Bild in den Rohdaten", "kandidaten": [qid]})
            continue
        key = norm_person(a["name"])
        if len(namen.get(key, [])) > 1:
            pruefliste.append({"akte_id": aid, "name": a["name"], "grund": "Name im Index mehrdeutig", "kandidaten": [m["qid"] for m in wd.get(key, [])]})
            continue
        if "mdb" in (a.get("arten") or []):
            kandidaten = wd.get(key, [])
        else:
            # ohne Mandat kein Abgleich mit der Abgeordnetenliste (Namensvetter): nur Suchtreffer mit gleichem Label und Politiker-Beschreibung
            kandidaten = [t for t in suche.get(a["name"], []) if norm_person(t.get("label") or "") == key and re.search(r"politiker|politician", t.get("beschreibung") or "", re.I)]
        if len(kandidaten) == 1:
            bild = kandidaten[0].get("bild")
            if bild:
                treffer[aid] = {"qid": kandidaten[0]["qid"], "datei": datei_aus_url(bild)}
        elif len(kandidaten) > 1:
            pruefliste.append({"akte_id": aid, "name": a["name"], "grund": "Name in Wikidata mehrdeutig", "kandidaten": [k["qid"] for k in kandidaten]})
    return treffer, pruefliste


def zuordnen_organisationen(empfaenger: list[dict], lobby: list[dict], manual: dict) -> dict[str, dict]:
    """Empfänger → {qid, datei} über die Lobbyregister-Nummer; nur mit Logo, nicht gesperrt."""
    return zuordnen_organisationen_mit_pruefliste(empfaenger, lobby, manual)[0]


def zuordnen_organisationen_mit_pruefliste(empfaenger: list[dict], lobby: list[dict], manual: dict) -> tuple[dict[str, dict], list[dict]]:
    """Wie zuordnen_organisationen; dazu Prüfliste für Items, die im Index mehreren Nummern gehören (Mutter und Tochter mit einem Wikidata-Item)."""
    gesperrt = _gesperrt(manual)
    je_lr: dict[str, dict] = {}
    for l in lobby:
        if not l.get("lr"):
            continue
        cur = je_lr.setdefault(str(l["lr"]), {"qid": l["qid"], "logos": []})
        if l.get("logo"):
            cur["logos"].append(datei_aus_url(l["logo"]))
    nummern_je_qid: dict[str, set[str]] = {}
    for e in empfaenger:
        nr = e.get("lobbyregister")
        if nr and str(nr) in je_lr:
            nummern_je_qid.setdefault(je_lr[str(nr)]["qid"], set()).add(str(nr))
    out: dict[str, dict] = {}
    pruefliste: list[dict] = []
    for e in empfaenger:
        nr = e.get("lobbyregister")
        if not nr or e["id"] in gesperrt:
            continue
        l = je_lr.get(str(nr))
        if not l or not l["logos"]:
            continue
        if len(nummern_je_qid.get(l["qid"], set())) > 1:
            pruefliste.append({"id": e["id"], "grund": "Wikidata-Item trägt mehrere Lobbyregister-Nummern des Index", "kandidaten": [l["qid"]]})
            continue
        out[e["id"]] = {"qid": l["qid"], "datei": sorted(l["logos"])[0]}
    return out, pruefliste


def commons_meta(datei: str, info: dict) -> dict | None:
    """Verweis mit Lizenz und Urheber aus einer imageinfo-Seite; None, wenn die Lizenz nicht erlaubt ist oder ein nötiger Urheber fehlt."""
    ii = (info.get("imageinfo") or [{}])[0]
    em = ii.get("extmetadata") or {}
    val = lambda k: _WS.sub(" ", html.unescape(_TAG.sub(" ", _VERSTECKT.sub("", str((em.get(k) or {}).get("value", "")))))).strip()  # noqa: E731
    lizenz = val("LicenseShortName")
    if not lizenz_erlaubt(lizenz):
        return None
    # Vom Urheber vorgegebene Nennung (Attribution) vor dem Artist-Feld; „Unknown author“ u. Ä. gilt als leer
    urheber = val("Attribution") or val("Artist")
    if re.fullmatch(r"(unknown\b.*|unbekannt.*|anonymous|anonym|n/?a|-)", urheber, re.I):
        urheber = ""
    if len(urheber) > 120:
        urheber = urheber[:119].rstrip() + "…"
    nennung = val("AttributionRequired").lower() != "false" and not (lizenz.lower().startswith("cc0") or lizenz.lower().startswith("public domain"))
    if not urheber:
        if nennung:
            return None
        urheber = "unbekannt"
    thumb = (ii.get("thumburl") or "").split("?", 1)[0] or f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(datei)}?width=120"
    restriktionen = val("Restrictions") or None
    lizenz_url = val("LicenseUrl") or None
    return {
        "datei": datei,
        "url": thumb,
        "url_gross": f"https://commons.wikimedia.org/wiki/Special:FilePath/{urllib.parse.quote(datei)}?width=256",
        "seite": f"https://commons.wikimedia.org/wiki/File:{urllib.parse.quote(datei.replace(' ', '_'))}",
        "lizenz": lizenz,
        "lizenz_url": lizenz_url,
        "urheber": urheber,
        "restriktionen": restriktionen,
    }


# ---------------------------------------------------------------- Abruf
def _sparql(query: str, http: Callable[[str], bytes]) -> list[dict]:
    url = f"{SPARQL}?format=json&query={urllib.parse.quote(query)}"
    data = json.loads(http(url).decode("utf-8"))
    return data.get("results", {}).get("bindings", [])


def _wert(b: dict, k: str) -> str | None:
    v = b.get(k)
    return v.get("value") if v else None


def _qid(uri: str | None) -> str:
    return (uri or "").rsplit("/", 1)[-1]


def fetch_bilder(raw_dir: Path, akten: list[dict], empfaenger: list[dict], http: Callable[[str], bytes] = _urlopen_bytes, pause: float = 0.5) -> dict:
    """Holt SPARQL-Listen, Suchtreffer für Regierungsmitglieder ohne Mandat und Commons-Metadaten aller Kandidatendateien nach raw/bilder/."""
    d = raw_dir / "bilder"
    d.mkdir(parents=True, exist_ok=True)
    mdb = [{"qid": _qid(_wert(b, "item")), "label": _wert(b, "itemLabel") or "", "bild": _wert(b, "bild")} for b in _sparql(SPARQL_MDB, http)]
    time.sleep(pause)
    lobby = [{"qid": _qid(_wert(b, "item")), "lr": _wert(b, "lr"), "logo": _wert(b, "logo")} for b in _sparql(SPARQL_LOBBY, http)]

    # Regierungsmitglieder ohne Mandat: Suche nach Name, Bild über wbgetentities
    mdb_namen = {norm_person(m["label"]) for m in mdb}
    suche: dict[str, list[dict]] = {}
    for a in akten:
        arten = a.get("arten") or []
        if not a.get("sichtbar") or "regierung" not in arten or "mdb" in arten or norm_person(a["name"]) in mdb_namen:
            continue
        time.sleep(pause)
        suchname = _TITEL.sub(" ", a["name"]).strip()
        suchname = _WS.sub(" ", suchname)
        url = f"{WIKIDATA_API}?action=wbsearchentities&format=json&language=de&uselang=de&type=item&limit=10&search={urllib.parse.quote(suchname)}"
        hits = json.loads(http(url).decode("utf-8")).get("search", [])
        treffer = [{"qid": h["id"], "label": h.get("label", ""), "beschreibung": h.get("description", ""), "bild": None} for h in hits]
        polit = [t for t in treffer if re.search(r"politiker|politician", t["beschreibung"], re.I)]
        if polit:
            time.sleep(pause)
            ids = "|".join(t["qid"] for t in polit[:10])
            ent = json.loads(http(f"{WIKIDATA_API}?action=wbgetentities&format=json&props=claims&ids={ids}").decode("utf-8")).get("entities", {})
            for t in polit:
                claims = ent.get(t["qid"], {}).get("claims", {}).get("P18", [])
                if claims:
                    t["bild"] = claims[0]["mainsnak"]["datavalue"]["value"]
        suche[a["name"]] = treffer
    # Commons-Metadaten aller Kandidaten, 50 je Anfrage
    dateien: list[str] = []
    for m in mdb:
        if m.get("bild"):
            dateien.append(datei_aus_url(m["bild"]))
    lr_nummern = {str(e.get("lobbyregister")) for e in empfaenger if e.get("lobbyregister")}
    for l in lobby:
        if l.get("logo") and str(l.get("lr")) in lr_nummern:
            dateien.append(datei_aus_url(l["logo"]))
    for liste in suche.values():
        for t in liste:
            if t.get("bild"):
                dateien.append(datei_aus_url(t["bild"]))
    dateien = list(dict.fromkeys(dateien))
    commons: dict[str, dict] = {}
    for i in range(0, len(dateien), 50):
        block = dateien[i:i + 50]
        titles = "|".join(f"File:{x}" for x in block)
        url = f"{COMMONS_API}?action=query&format=json&prop=imageinfo&iiprop=url%7Cextmetadata&iiurlwidth=96&titles={urllib.parse.quote(titles)}"
        pages = json.loads(http(url).decode("utf-8")).get("query", {}).get("pages", {})
        for p in pages.values():
            title = str(p.get("title", ""))
            name = title[5:] if title.startswith("File:") else title
            commons[name] = p
        time.sleep(pause)
    # alles erst am Ende schreiben, damit ein Abbruch keine gemischten Stände hinterlässt
    (d / "mdb.json").write_text(json.dumps(mdb, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "lobby.json").write_text(json.dumps(lobby, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "suche.json").write_text(json.dumps(suche, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "commons.json").write_text(json.dumps(commons, ensure_ascii=False), encoding="utf-8", newline="\n")
    (d / "stand.json").write_text(json.dumps({"stand": time.strftime("%Y-%m-%d")}), encoding="utf-8", newline="\n")
    return {"mdb": len(mdb), "lobby": len(lobby), "suche": len(suche), "commons": len(commons)}


# ---------------------------------------------------------------- Build
def _lade(p: Path):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def build_bilder(manual_dir: Path, raw_dir: Path, out: Path, akten: list[dict], empfaenger: list[dict], stand: str) -> dict | None:
    """Schreibt out/bilder.json aus den Rohdaten; ohne raw/bilder nichts (eine alte Datei wird entfernt)."""
    d = raw_dir / "bilder"
    ziel = out / "bilder.json"
    if not (d / "mdb.json").exists():
        # Rohdaten sind nicht versioniert: ohne sie bleibt eine vorhandene bilder.json erhalten (sonst verschwänden alle Verweise still)
        print(f"bilder: keine Rohdaten unter {d}; {'vorhandene bilder.json bleibt' if ziel.exists() else 'keine bilder.json'} – bht fetch-bilder zum Aktualisieren", file=sys.stderr)
        return None
    manual_file = manual_dir / "bilder.yaml"
    manual = yaml.safe_load(manual_file.read_text(encoding="utf-8")) or {} if manual_file.exists() else {}
    fehler = validate_bilder(manual)
    if fehler:
        raise ValueError("bilder.yaml: " + "; ".join(fehler))
    mdb = _lade(d / "mdb.json") or []
    lobby = _lade(d / "lobby.json") or []
    suche = _lade(d / "suche.json") or {}
    commons = _lade(d / "commons.json") or {}
    roh_stand = (_lade(d / "stand.json") or {}).get("stand", stand)

    personen_treffer, pruefliste = zuordnen_personen(akten, mdb, suche, manual)
    org_treffer, org_pruefliste = zuordnen_organisationen_mit_pruefliste(empfaenger, lobby, manual)
    pruefliste = pruefliste + org_pruefliste
    personen: dict[str, dict] = {}
    organisationen: dict[str, dict] = {}
    verworfen: list[dict] = []
    for ziel_dict, treffer, art in ((personen, personen_treffer, "person"), (organisationen, org_treffer, "organisation")):
        for oid, t in treffer.items():
            info = commons.get(t["datei"])
            meta = commons_meta(t["datei"], info) if info else None
            if meta:
                ziel_dict[oid] = {**meta, "qid": t["qid"], "art": art}
            else:
                lizenz = ""
                if info:
                    em = ((info.get("imageinfo") or [{}])[0]).get("extmetadata") or {}
                    lizenz = str((em.get("LicenseShortName") or {}).get("value", ""))
                verworfen.append({"id": oid, "datei": t["datei"], "lizenz": lizenz or "unbekannt"})
    relevant = [a["id"] for a in akten if a.get("sichtbar") and any(x in ("mdb", "regierung") for x in a.get("arten") or [])]
    ohne = sorted(aid for aid in relevant if aid not in personen)
    ziel.write_text(json.dumps({"stand": roh_stand, "quelle": "Wikidata/Wikimedia Commons", "personen": personen, "organisationen": organisationen,
                                "pruefliste": pruefliste, "verworfen": verworfen, "ohne_bild": {"anzahl": len(ohne), "ids": ohne}}, ensure_ascii=False, indent=0), encoding="utf-8", newline="\n")
    return {"personen": len(personen), "organisationen": len(organisationen), "pruefliste": len(pruefliste), "verworfen": len(verworfen), "ohne_bild": len(ohne)}
