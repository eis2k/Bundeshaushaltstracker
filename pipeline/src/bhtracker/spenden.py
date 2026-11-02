"""Parteispenden über 35.000 € (bis 4.3.2024: 50.000 €), veröffentlicht vom Bundestagspräsidenten als Drucksache.

Quelle: https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000/<jahr>
(Tabelle: Partei, Spende, Spender mit Anschrift, Eingang, Anzeige/Drucksache; Monatszeilen als Zwischenüberschrift).
Anschriften werden nicht übernommen, nur Name und Ort. Spenden natürlicher Personen werden erkannt und nirgends gespeichert.
"""

from __future__ import annotations

import html
import re
import time
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Callable

from .empfaenger import _EIGENNAME, norm_name
from .portal import TIMEOUT, USER_AGENT

JAHR_URL = "https://www.bundestag.de/parlament/praesidium/parteienfinanzierung/fundstellen50000/{jahr}"
BASE = "https://www.bundestag.de"

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_DATUM = re.compile(r"(\d{2})\.(\d{2})\.(\d{4})")
_PLZ_ORT = re.compile(r"^\d{5}\s+(.+)$")
_TITEL = re.compile(r"^(?:Herrn?|Frau|Prof\.|Dr\.|Dipl\.-?\w*\.?|Ing\.|h\.c\.|mult\.|med\.|rer\.|nat\.|jur\.|phil\.|Frhr\.|Freiherr|Graf|Gräfin|von|zu|van|de)\s+", re.I)
_ZUSATZ = {"von", "van", "vom", "de", "der", "den", "zu", "zur", "zum", "graf", "gräfin", "freiherr", "freifrau", "frhr.", "baron", "baronin", "und", "y", "da", "di"}
_CO = re.compile(r"\s+c/o\s+.*$", re.I)


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


@dataclass(frozen=True)
class Spende:
    jahr: int
    partei: str
    betrag: int
    spender: str
    spender_ort: str
    eingang: str
    veroeffentlicht: str
    drucksache: str
    drucksache_url: str | None
    natuerliche_person: bool


def _text(fragment: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", fragment))).strip()


def _zeilen(cell_html: str) -> list[str]:
    """Zeilen eines Zellinhalts (getrennt durch <br>); weiche Trennstriche fügen die Wortteile wieder zusammen."""
    t = cell_html.replace("&shy;", "­")
    t = re.sub(r"­\s*(<[^>]+>\s*)*\s*", "­", t)
    parts = re.split(r"<br\s*/?>", t, flags=re.I)
    out = []
    for p in parts:
        z = re.sub(r"\s*­\s*", "", _text(p))   # weicher Trennstrich: Wortteile ohne Leerzeichen zusammenfügen
        if z:
            out.append(z)
    return out


def _iso(s: str) -> str:
    m = _DATUM.search(s)
    return f"{m.group(3)}-{m.group(2)}-{m.group(1)}" if m else ""


def _betrag(s: str) -> int:
    digits = re.sub(r"[^\d]", "", s.split(",")[0])
    return int(digits) if digits else 0


def ist_natuerliche_person(name: str) -> bool:
    """Kein Organisationsmerkmal, höchstens fünf Wörter nach Abzug von Anrede, Titeln und Namenszusätzen: dann eine natürliche Person.
    Ein „c/o“-Zusatz (Zustelladresse) zählt nicht zum Namen."""
    rest = _CO.sub("", name).strip()
    if _EIGENNAME.search(rest):
        return False
    for _ in range(6):
        neu = _TITEL.sub("", rest)
        if neu == rest:
            break
        rest = neu
    worte = [w for w in rest.replace(",", " ").split() if w and w.lower() not in _ZUSATZ]
    return 1 <= len(worte) <= 5 and all(w[0].isupper() or w[0] in "'’" for w in worte)


def parse_spenden(page_html: str, jahr: int) -> list[Spende]:
    out: list[Spende] = []
    table = re.search(r"<table.*?</table>", page_html, re.S)
    if not table:
        return out
    for row in re.findall(r"<tr.*?</tr>", table.group(0), re.S):
        tds = re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)
        if len(tds) < 5:
            continue  # Kopf- oder Monatszeile
        partei = _text(tds[0])
        betrag = _betrag(_text(tds[1]))
        zeilen = _zeilen(tds[2])
        if not zeilen or not partei:
            continue
        name = zeilen[0]
        ort = ""
        for z in reversed(zeilen[1:]):
            m = _PLZ_ORT.match(z)
            if m:
                ort = m.group(1).strip()
                break
        eingang = _iso(_text(tds[3]))
        veroeff_zeilen = _zeilen(tds[4])
        veroeffentlicht = _iso(veroeff_zeilen[0]) if veroeff_zeilen else ""
        drs = ""
        m = re.search(r"Drs\.\s*([\d]+/\d+)", _text(tds[4]))
        if m:
            drs = f"Drs. {m.group(1)}"
        link = re.search(r'href="([^"]+)"', tds[4])
        url = link.group(1) if link else None
        if url and url.startswith("/"):
            url = BASE + url
        out.append(Spende(jahr, partei, betrag, name, ort, eingang, veroeffentlicht, drs, url, ist_natuerliche_person(name)))
    return out


def _dir(raw_dir: Path) -> Path:
    d = raw_dir / "spenden"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_spenden(raw_dir: Path, jahre: list[int], http: Callable[[str], bytes] = _urlopen_bytes, pause: float = 1.5,
                  heute_jahr: int | None = None) -> list[Path]:
    """Abgeschlossene Jahre nur laden, wenn die Datei fehlt; das laufende Jahr immer neu (die Liste wächst)."""
    heute = heute_jahr or date.today().year
    d = _dir(raw_dir)
    written: list[Path] = []
    for jahr in jahre:
        target = d / f"{jahr}.html"
        if target.exists() and jahr < heute:
            continue
        target.write_bytes(http(JAHR_URL.format(jahr=jahr)))
        written.append(target)
        if pause:
            time.sleep(pause)
    return written


def lade_spenden(raw_dir: Path) -> list[Spende]:
    d = raw_dir / "spenden"
    if not d.exists():
        return []
    out: list[Spende] = []
    for p in sorted(d.glob("*.html")):
        try:
            jahr = int(p.stem)
        except ValueError:
            continue
        out.extend(parse_spenden(p.read_text(encoding="utf-8", errors="replace"), jahr))
    return out


def zuordnen(spenden: list[Spende], stamm_normen: dict[str, str]) -> tuple[dict[str, list[Spende]], list[dict]]:
    """Exakter Namenstreffer → Empfänger-Id; Organisationen ohne Treffer als Kandidaten; natürliche Personen fallen weg."""
    zu: dict[str, list[Spende]] = {}
    kandidaten: list[dict] = []
    for s in spenden:
        if s.natuerliche_person:
            continue
        sid = stamm_normen.get(norm_name(s.spender))
        if sid:
            zu.setdefault(sid, []).append(s)
        else:
            kandidaten.append({"spender": s.spender, "ort": s.spender_ort, "partei": s.partei, "betrag": s.betrag, "jahr": s.jahr, "drucksache": s.drucksache})
    return zu, kandidaten
