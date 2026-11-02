"""Abgeordnete des Bundestags: Biografien mit veröffentlichungspflichtigen Angaben (bundestag.de).

Liste:     https://www.bundestag.de/ajax/filterlist/de/abgeordnete/1040594-1040594?limit=12&offset=N
Biografie: https://www.bundestag.de/abgeordnete/biografien/<B>/<slug>-<id>
Die Angaben beruhen auf den Selbstauskünften der Abgeordneten nach §§ 45 ff. Abgeordnetengesetz
und werden mit Abrufdatum übernommen.
"""

from __future__ import annotations

import html
import re
import time
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from .portal import TIMEOUT, USER_AGENT

LISTE_URL = "https://www.bundestag.de/ajax/filterlist/de/abgeordnete/1040594-1040594"
BASE = "https://www.bundestag.de"
KATEGORIE_VORHER = "Berufliche Tätigkeit vor der Mitgliedschaft im Deutschen Bundestag"

_BIO_HREF = re.compile(r'href="((?:https://www\.bundestag\.de)?/abgeordnete/biografien/[A-Z]/[^"#?]+-(\d+))"')
_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_MONATE = {m: i + 1 for i, m in enumerate(("Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"))}
_AUSGESCHIEDEN = re.compile(r"mit Ablauf des (\d{1,2})\. (Januar|Februar|März|April|Mai|Juni|Juli|August|September|Oktober|November|Dezember) (\d{4}) aus dem Deutschen Bundestag ausgeschieden")


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _text(fragment: str) -> str:
    return _WS.sub(" ", html.unescape(_TAG.sub(" ", fragment))).strip()


# ---------------------------------------------------------------- Datenmodell

@dataclass(frozen=True)
class Angabe:
    kategorie: str
    organisation: str
    ort: str
    funktion: str


@dataclass
class Abgeordneter:
    name: str
    fraktion: str
    url: str
    mdb_id: int
    ausschuesse: list[str] = field(default_factory=list)
    angaben: list[Angabe] = field(default_factory=list)
    stand: str = ""
    hinweis: str | None = None
    ausgeschieden: str | None = None   # ISO-Datum des Ausscheidens aus dem Bundestag (Biografie-Text), sonst None


# ---------------------------------------------------------------- Liste

def bio_urls_aus_seite(page_html: str) -> list[str]:
    out: list[str] = []
    for href, _id in _BIO_HREF.findall(page_html):
        url = href if href.startswith("http") else BASE + href
        if url not in out:
            out.append(url)
    return out


def alle_bio_urls(http: Callable[[str], bytes] = _urlopen_bytes, pause: float = 1.5, schritt: int = 12,
                  log: Callable[[str], None] = print) -> list[str]:
    urls: list[str] = []
    offset = 0
    while True:
        page = http(f"{LISTE_URL}?limit={schritt}&offset={offset}").decode("utf-8", errors="replace")
        neu = [u for u in bio_urls_aus_seite(page) if u not in urls]
        if not neu:
            break
        urls.extend(neu)
        offset += schritt
        if offset % 120 == 0:
            log(f"bundestag: {len(urls)} Biografie-Links")
        if pause:
            time.sleep(pause)
    return urls


# ---------------------------------------------------------------- Biografie

def _block(page_html: str, titel: str) -> str | None:
    i = page_html.find(titel)
    if i < 0:
        return None
    start = page_html.rfind('<div class="e-collapse"', 0, i)
    if start < 0:
        start = i
    ends = [page_html.find('<div class="e-collapse"', i), page_html.find("m-biography__marginal", i)]
    ends = [e for e in ends if e > 0]
    return page_html[start:min(ends)] if ends else page_html[start:]


def _org_und_ort(text: str) -> tuple[str, str]:
    t = text.strip().rstrip(",").strip()
    if ", " in t:
        org, ort = t.rsplit(", ", 1)
        return org.strip(), ort.strip()
    return t, ""


def _angaben(block: str) -> list[Angabe]:
    out: list[Angabe] = []
    for m in re.finditer(r"<h3[^>]*>(.*?)</h3>\s*<ul[^>]*>(.*?)</ul>", block, re.S):
        kategorie = _text(m.group(1))
        items = [_text(li) for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(2), re.S)]
        i = 0
        while i < len(items):
            raw = items[i]
            # Organisationszeile endet mit Komma (", Ort, "), dann folgt die Funktionszeile
            if raw.rstrip().endswith(","):
                org, ort = _org_und_ort(raw)
                funktion = items[i + 1] if i + 1 < len(items) else ""
                i += 2
            else:
                org, ort = _org_und_ort(raw)
                funktion = ""
                i += 1
            if org:
                out.append(Angabe(kategorie, org, ort, funktion.strip()))
    return out


def parse_bio(page_html: str, url: str, stand: str) -> Abgeordneter:
    m = re.search(r'<h1 class="m-biography__introName">(.*?)</h1>', page_html, re.S)
    name = _text(m.group(1)) if m else ""
    fm = re.search(r'alt="Logo der Fraktion ([^"]+)"', page_html) or re.search(r"Fraktion ([^\"<]+?) des Deutschen Bundestages", page_html)
    fraktion = html.unescape(fm.group(1)).strip() if fm else ""
    idm = re.search(r"-(\d+)/?$", url)
    mdb_id = int(idm.group(1)) if idm else 0
    ausschuesse: list[str] = []
    ab = _block(page_html, "Mitgliedschaften und Ämter im Bundestag")
    if ab:
        for a in re.findall(r'<a [^>]*class="a-link --inList[^"]*"[^>]*>(.*?)</a>', ab, re.S):
            label = re.search(r'<span class="a-link__label">(.*?)</span>', a, re.S)
            t = _text(label.group(1) if label else a)
            if t and t not in ausschuesse:
                ausschuesse.append(t)
    aus = _AUSGESCHIEDEN.search(_text(page_html))
    ausgeschieden = f"{aus.group(3)}-{_MONATE[aus.group(2)]:02d}-{int(aus.group(1)):02d}" if aus else None
    hinweise = [f"aus dem Bundestag ausgeschieden mit Ablauf des {ausgeschieden}"] if ausgeschieden else []
    block = _block(page_html, "Veröffentlichungspflichtige Angaben")
    if block is None:
        hinweise.append("keine veröffentlichungspflichtigen Angaben")
    return Abgeordneter(name, fraktion, url, mdb_id, ausschuesse, _angaben(block) if block is not None else [], stand,
                        "; ".join(hinweise) or None, ausgeschieden)


# ---------------------------------------------------------------- Abruf und Ablage

def _dir(raw_dir: Path) -> Path:
    d = raw_dir / "bundestag"
    d.mkdir(parents=True, exist_ok=True)
    return d


def fetch_bios(raw_dir: Path, urls: list[str], http: Callable[[str], bytes] = _urlopen_bytes, pause: float = 1.5,
               log: Callable[[str], None] = print) -> list[Path]:
    d = _dir(raw_dir)
    written: list[Path] = []
    for i, url in enumerate(urls, 1):
        idm = re.search(r"-(\d+)/?$", url)
        if not idm:
            continue
        target = d / f"{idm.group(1)}.html"
        if target.exists():
            continue
        body = http(url)
        target.write_bytes(body)
        (d / f"{idm.group(1)}.url").write_text(url, encoding="utf-8")
        written.append(target)
        if i % 50 == 0:
            log(f"bundestag: {i}/{len(urls)} Biografien")
        if pause:
            time.sleep(pause)
    return written


def lade_abgeordnete(raw_dir: Path) -> list[Abgeordneter]:
    d = raw_dir / "bundestag"
    if not d.exists():
        return []
    out: list[Abgeordneter] = []
    for p in sorted(d.glob("*.html")):
        urlfile = p.with_suffix(".url")
        url = urlfile.read_text(encoding="utf-8").strip() if urlfile.exists() else f"{BASE}/abgeordnete/biografien/-/-{p.stem}"
        stand = datetime.fromtimestamp(p.stat().st_mtime, tz=timezone.utc).date().isoformat()
        out.append(parse_bio(p.read_text(encoding="utf-8", errors="replace"), url, stand))
    return out
