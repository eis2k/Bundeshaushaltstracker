"""Client für das Download-Portal von bundeshaushalt.de.

Das Portal liefert unter /internalapi/dataportalConfig die Kategorien je Jahr
(soll_YYYY, soll_YYYY_nK für Nachträge, soll_YYYY_e für Entwürfe, ist_YYYY)
und unter /internalapi/dataportal?year=&category=&filter=hh die Dateien.
Die Dateien selbst liegen unter https://www.bundeshaushalt.de/static/daten/...
"""

from __future__ import annotations

import hashlib
import json
import re
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

BASE = "https://www.bundeshaushalt.de"
USER_AGENT = "Bundeshaushaltstracker/0.1 (+https://github.com/eis2k/Bundeshaushaltstracker)"
TIMEOUT = 60


@dataclass(frozen=True)
class Category:
    value: str
    label: str
    filter: str


@dataclass(frozen=True)
class PortalFile:
    name: str
    path: str
    size: int
    ext: str
    category: str


def _urlopen_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read()


def _urlopen_json(url: str):
    return json.loads(_urlopen_bytes(url).decode("utf-8"))


def list_categories(*, fetch: Callable[[str], object] = _urlopen_json) -> dict[int, list[Category]]:
    raw = fetch(f"{BASE}/internalapi/dataportalConfig")
    result: dict[int, list[Category]] = {}
    for entry in raw:  # type: ignore[union-attr]
        cats = [
            Category(value=c["value"], label=c.get("label", ""), filter=c.get("filter", "hh"))
            for c in entry["categories"]
        ]
        result[int(entry["year"])] = cats
    return result


def list_files(year: int, category: str, filter: str = "hh", *,
               fetch: Callable[[str], object] = _urlopen_json) -> list[PortalFile]:
    raw = fetch(f"{BASE}/internalapi/dataportal?year={year}&category={category}&filter={filter}")
    return [
        PortalFile(name=f["name"], path=f["path"], size=int(f.get("fileSize", 0)),
                   ext=f.get("fileExt", Path(f["path"]).suffix[1:]), category=f.get("category", category))
        for f in raw  # type: ignore[union-attr]
    ]


def _soll_rank(f: PortalFile) -> int:
    name = Path(f.path).name.lower()
    if not name.endswith(".csv"):
        return 99
    if "_all" in name:
        return 0
    if "utf8" in name:
        return 1
    if "win_rfc4180" in name:
        return 3
    if "win" in name:
        return 4
    return 2


def choose_soll_file(files: list[PortalFile]) -> PortalFile:
    candidates = [f for f in files if _soll_rank(f) < 99]
    if not candidates:
        raise LookupError("keine CSV-Datei im Angebot")
    return min(candidates, key=_soll_rank)


def choose_ist_file(files: list[PortalFile]) -> PortalFile:
    for f in files:
        if re.fullmatch(r"rechnung_\d{4}\.xml", Path(f.path).name.lower()):
            return f
    raise LookupError("keine rechnung_<jahr>.xml im Angebot")


def latest_soll_category(categories: list[Category]) -> str:
    values = {c.value for c in categories}
    nachtraege = sorted(
        (v for v in values if re.fullmatch(r"soll_\d{4}_n\d+", v)),
        key=lambda v: int(v.rsplit("_n", 1)[1]),
    )
    if nachtraege:
        return nachtraege[-1]
    plain = [v for v in values if re.fullmatch(r"soll_\d{4}", v)]
    if plain:
        return plain[0]
    entwurf = [v for v in values if re.fullmatch(r"soll_\d{4}_e", v)]
    if entwurf:
        return entwurf[0]
    raise LookupError("keine Soll-Kategorie vorhanden")


def _local_path(path: str, raw_dir: Path) -> Path:
    m = re.match(r"^/static/daten/(.+)$", path)
    if not m:
        raise ValueError(f"unerwarteter Portalpfad: {path}")
    return raw_dir.joinpath(*m.group(1).split("/"))


def download(path: str, raw_dir: Path, *,
             fetch_bytes: Callable[[str], bytes] = _urlopen_bytes) -> Path:
    """Lädt eine Portaldatei nach raw_dir (Cache) und protokolliert den Abruf."""
    target = _local_path(path, raw_dir)
    if target.exists():
        return target
    url = f"{BASE}{path}"
    data = fetch_bytes(url)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    log_file = raw_dir / "fetch_log.json"
    log = json.loads(log_file.read_text(encoding="utf-8")) if log_file.exists() else []
    log.append({
        "path": path,
        "url": url,
        "abgerufen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "bytes": len(data),
        "sha256": hashlib.sha256(data).hexdigest(),
    })
    log_file.write_text(json.dumps(log, ensure_ascii=False, indent=1), encoding="utf-8")
    return target
