"""Bundesregierung: Kabinett von bundesregierung.de und Staatssekretäre aus data/manual/regierung.yaml.

Kabinettsseite: https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett
Je Kachel (li.bpa-teaser-wrapper): Name (Titel-Link), Links „Lebenslauf“ und Amtsbezeichnung.
"""

from __future__ import annotations

import html
import re
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

from .empfaenger import ressort_zu_epl
from .portal import TIMEOUT, USER_AGENT

KABINETT_URL = "https://www.bundesregierung.de/breg-de/bundesregierung/bundeskabinett"
BASE = "https://www.bundesregierung.de"

AEMTER = (
    "Bundeskanzler", "Bundeskanzlerin", "Bundesminister", "Bundesministerin", "Chef des Bundeskanzleramts", "Chefin des Bundeskanzleramts",
    "Staatsminister", "Staatsministerin", "Parlamentarischer Staatssekretär", "Parlamentarische Staatssekretärin", "Staatssekretär", "Staatssekretärin",
)

# Amtsbezeichnung → Einzelplan, wo der Ressortname nicht als Alias in ressorts.yaml steht
AMT_EPL: tuple[tuple[str, str, str], ...] = (
    ("bundeskanzler", "04", "Bundeskanzleramt"),
    ("chef des bundeskanzleramt", "04", "Bundeskanzleramt"),
    ("chefin des bundeskanzleramt", "04", "Bundeskanzleramt"),
    ("besondere aufgaben", "04", "Bundeskanzleramt"),
    ("des auswärtigen", "05", "Auswärtiges Amt"),
    ("des innern", "06", "Bundesministerium des Innern"),
    ("der justiz", "07", "Bundesministerium der Justiz und für Verbraucherschutz"),
    ("der finanzen", "08", "Bundesministerium der Finanzen"),
    ("für wirtschaft und energie", "09", "Bundesministerium für Wirtschaft und Energie"),
    ("für landwirtschaft", "10", "Bundesministerium für Landwirtschaft, Ernährung und Heimat"),
    ("für arbeit und soziales", "11", "Bundesministerium für Arbeit und Soziales"),
    ("für verkehr", "12", "Bundesministerium für Verkehr"),
    ("der verteidigung", "14", "Bundesministerium der Verteidigung"),
    ("für gesundheit", "15", "Bundesministerium für Gesundheit"),
    ("für umwelt", "16", "Bundesministerium für Umwelt, Klimaschutz, Naturschutz und nukleare Sicherheit"),
    ("für bildung, familie", "17", "Bundesministerium für Bildung, Familie, Senioren, Frauen und Jugend"),
    ("für wirtschaftliche zusammenarbeit", "23", "Bundesministerium für wirtschaftliche Zusammenarbeit und Entwicklung"),
    ("für wohnen", "25", "Bundesministerium für Wohnen, Stadtentwicklung und Bauwesen"),
    ("für forschung", "30", "Bundesministerium für Forschung, Technologie und Raumfahrt"),
    ("für digitales", "", "Bundesministerium für Digitales und Staatsmodernisierung"),
)

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _text(fragment: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", fragment))).strip()


@dataclass
class Amtstraeger:
    name: str
    amt: str
    ressort: str
    epl: str | None
    seit: str | None
    bis: str | None
    quelle: str
    stand: str
    mdb_id: int | None = None


def amt_zu_ressort(amt: str, ressorts: dict) -> tuple[str, str | None]:
    """Amtsbezeichnung („Bundesminister des Auswärtigen“) → (Ressortname, Einzelplan)."""
    low = amt.lower()
    for muster, epl, ressort in AMT_EPL:
        if muster in low:
            return ressort, (epl or None)
    epl = ressort_zu_epl(amt, ressorts)
    return amt, epl


def parse_kabinett(page_html: str, stand: str, ressorts: dict) -> list[Amtstraeger]:
    out: list[Amtstraeger] = []
    for tile in re.split(r'(?=<li class="bpa-teaser-wrapper">)', page_html):
        if "bpa-teaser-cabinet" not in tile:
            continue
        name_m = re.search(r'<span class="bpa-teaser-title-text-inner">\s*(.*?)\s*</span>', tile, re.S)
        href_m = re.search(r'<a href="([^"#]+)"[^>]*class="bpa-link"', tile)
        items = re.findall(r'<li class="bpa-teaser-cabinet-item">(.*?)</li>', tile, re.S)
        amt = ""
        for it in items:
            t = _text(it)
            if t and t.lower() != "lebenslauf":
                amt = t
        if not name_m or not amt:
            continue
        name = _text(name_m.group(1))
        href = href_m.group(1) if href_m else KABINETT_URL
        if href.startswith("/"):
            href = BASE + href
        ressort, epl = amt_zu_ressort(amt, ressorts)
        out.append(Amtstraeger(name=name, amt=amt, ressort=ressort, epl=epl, seit=None, bis=None, quelle=href, stand=stand))
    return out


def validate_regierung(data: dict) -> list[str]:
    errors: list[str] = []
    for i, m in enumerate(data.get("mitglieder") or []):
        wer = m.get("name") or f"Eintrag {i + 1}"
        for key in ("name", "amt", "ressort", "quelle"):   # seit nur, wenn belegt (kein Platzhalter)
            if not m.get(key):
                errors.append(f"{wer}: Feld '{key}' fehlt")
        amt = str(m.get("amt") or "")
        if amt and not any(amt.startswith(a) for a in AEMTER):
            errors.append(f"{wer}: amt '{amt}' nicht erlaubt")
        if m.get("seit") and not _ISO.match(str(m["seit"])):
            errors.append(f"{wer}: seit muss ISO-Datum sein")
        if m.get("bis") and not _ISO.match(str(m["bis"])):
            errors.append(f"{wer}: bis muss ISO-Datum sein")
        q = str(m.get("quelle") or "")
        if q and not q.startswith("http"):
            errors.append(f"{wer}: quelle muss eine URL sein")
    return errors


def lade_regierung(manual_file: Path, raw_dir: Path, ressorts: dict) -> list[Amtstraeger]:
    """Kabinett aus dem Abruf plus Pflegedatei; gleicher Name und gleiches Amt → Pflegedatei gewinnt."""
    data = {}
    if manual_file.exists():
        with open(manual_file, encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    fehler = validate_regierung(data)
    if fehler:
        raise ValueError("regierung.yaml: " + "; ".join(fehler))
    stand = str(data.get("stand") or "")
    out: list[Amtstraeger] = []
    kab = raw_dir / "regierung" / "kabinett.html"
    if kab.exists():
        out.extend(parse_kabinett(kab.read_text(encoding="utf-8", errors="replace"), stand, ressorts))
    for m in data.get("mitglieder") or []:
        amt = str(m["amt"])
        ressort, epl_auto = amt_zu_ressort(f"{amt} {m.get('ressort', '')}", ressorts)
        a = Amtstraeger(name=str(m["name"]), amt=amt, ressort=str(m.get("ressort") or ressort),
                        epl=str(m["epl"]) if m.get("epl") else (ressort_zu_epl(str(m.get("ressort") or ""), ressorts) or epl_auto),
                        seit=str(m.get("seit")) if m.get("seit") else None, bis=str(m.get("bis")) if m.get("bis") else None,
                        quelle=str(m["quelle"]), stand=stand, mdb_id=int(m["mdb_id"]) if m.get("mdb_id") else None)
        out = [x for x in out if not (x.name == a.name and x.amt.split()[0] == a.amt.split()[0])]
        out.append(a)
    return out


def fetch_kabinett(raw_dir: Path, http: Callable[[str], bytes] = _urlopen_bytes) -> Path:
    d = raw_dir / "regierung"
    d.mkdir(parents=True, exist_ok=True)
    target = d / "kabinett.html"
    target.write_bytes(http(KABINETT_URL))
    return target
