import json
from pathlib import Path

from bhtracker.portal import (
    Category,
    PortalFile,
    choose_ist_file,
    choose_soll_file,
    download,
    latest_soll_category,
    list_categories,
    list_files,
)

CONFIG = [
    {"year": 2027, "categories": [
        {"value": "soll_2027_e", "label": "Bundeshaushaltsplan", "filter": "hh"},
        {"value": "soll_2027_e", "label": "Bundeshaushaltsplan - Einzelpläne", "filter": "epl"}]},
    {"year": 2021, "categories": [
        {"value": "soll_2021", "label": "Bundeshaushaltsplan", "filter": "hh"},
        {"value": "soll_2021_n1", "label": "1. Nachtragshaushalt", "filter": "hh"},
        {"value": "soll_2021_n2", "label": "2. Nachtragshaushalt", "filter": "hh"},
        {"value": "ist_2021", "label": "Haushaltsrechnung", "filter": "hh"}]},
    {"year": 2011, "categories": [{"value": "soll_2011", "label": "Bundeshaushaltsplan"}]},
]

FILES_2025 = [
    {"name": "Bundeshaushalt-2025.pdf", "path": "/static/daten/2025/soll/Bundeshaushalt-2025.pdf", "fileSize": 55429828, "fileExt": "pdf", "category": "soll_2025"},
    {"name": "HH_2025 [CSV]", "path": "/static/daten/2025/soll/HH_2025.csv", "fileSize": 1637610, "fileExt": "csv", "category": "soll_2025"},
    {"name": "HH_2025_ALL [CSV]", "path": "/static/daten/2025/soll/HH_2025_ALL.csv", "fileSize": 1777353, "fileExt": "csv", "category": "soll_2025"},
    {"name": "haushalt_2025 [XML]", "path": "/static/daten/2025/soll/haushalt_2025.xml", "fileSize": 1560658, "fileExt": "xml", "category": "soll_2025"},
]


def fake_json(expected_url_part):
    def fetch(url: str):
        assert expected_url_part in url, url
        return CONFIG if "dataportalConfig" in url else FILES_2025
    return fetch


def test_list_categories_parses_config():
    cats = list_categories(fetch=fake_json("dataportalConfig"))
    assert cats[2021] == [
        Category(value="soll_2021", label="Bundeshaushaltsplan", filter="hh"),
        Category(value="soll_2021_n1", label="1. Nachtragshaushalt", filter="hh"),
        Category(value="soll_2021_n2", label="2. Nachtragshaushalt", filter="hh"),
        Category(value="ist_2021", label="Haushaltsrechnung", filter="hh"),
    ]
    assert cats[2011][0].filter == "hh"  # fehlender Filter wird als hh gelesen


def test_list_files_builds_portal_files():
    files = list_files(2025, "soll_2025", fetch=fake_json("year=2025&category=soll_2025&filter=hh"))
    assert files[1] == PortalFile(name="HH_2025 [CSV]", path="/static/daten/2025/soll/HH_2025.csv",
                                  size=1637610, ext="csv", category="soll_2025")


def pf(path, ext=None):
    return PortalFile(name=Path(path).name, path=path, size=1, ext=ext or Path(path).suffix[1:], category="x")


def test_choose_soll_file_prefers_all_then_utf8_then_plain():
    assert choose_soll_file([pf("/static/daten/2025/soll/HH_2025.csv"), pf("/static/daten/2025/soll/HH_2025_ALL.csv")]).path.endswith("HH_2025_ALL.csv")
    assert choose_soll_file([
        pf("/static/daten/2015/soll/Haushalt_2015_win.csv"),
        pf("/static/daten/2015/soll/Haushalt_2015_win_rfc4180.csv"),
        pf("/static/daten/2015/soll/Haushalt_2015_utf8.csv"),
        pf("/static/daten/2015/soll/Haushaltsplan-2015.pdf"),
    ]).path.endswith("Haushalt_2015_utf8.csv")
    assert choose_soll_file([
        pf("/static/daten/2023/soll/n1/hh_2023_n1_win.csv"),
        pf("/static/daten/2023/soll/n1/hh_2023_n1_utf8.csv"),
    ]).path.endswith("hh_2023_n1_utf8.csv")


def test_choose_ist_file_picks_rechnung_xml():
    files = [pf("/static/daten/2024/ist/HR2024.xlsx"), pf("/static/daten/2024/ist/rechnung_2024.xml")]
    assert choose_ist_file(files).path.endswith("rechnung_2024.xml")


def test_latest_soll_category_prefers_last_nachtrag_and_avoids_entwurf():
    cats_2021 = [Category("soll_2021", "", "hh"), Category("soll_2021_n1", "", "hh"),
                 Category("soll_2021_n2", "", "hh"), Category("ist_2021", "", "hh")]
    assert latest_soll_category(cats_2021) == "soll_2021_n2"
    assert latest_soll_category([Category("soll_2019", "", "hh"), Category("ist_2019", "", "hh")]) == "soll_2019"
    assert latest_soll_category([Category("soll_2027_e", "", "hh")]) == "soll_2027_e"
    assert latest_soll_category([Category("soll_2026_e", "", "hh"), Category("soll_2026", "", "hh")]) == "soll_2026"


def test_download_caches_and_logs(tmp_path: Path):
    calls = []

    def fetch_bytes(url: str) -> bytes:
        calls.append(url)
        return b"a;b\n1;2\n"

    p1 = download("/static/daten/2023/soll/n1/hh_2023_n1_utf8.csv", tmp_path, fetch_bytes=fetch_bytes)
    p2 = download("/static/daten/2023/soll/n1/hh_2023_n1_utf8.csv", tmp_path, fetch_bytes=fetch_bytes)
    assert p1 == p2 == tmp_path / "2023" / "soll" / "n1" / "hh_2023_n1_utf8.csv"
    assert p1.read_bytes() == b"a;b\n1;2\n"
    assert calls == ["https://www.bundeshaushalt.de/static/daten/2023/soll/n1/hh_2023_n1_utf8.csv"]
    log = json.loads((tmp_path / "fetch_log.json").read_text(encoding="utf-8"))
    assert len(log) == 1
    assert log[0]["path"] == "/static/daten/2023/soll/n1/hh_2023_n1_utf8.csv"
    assert log[0]["bytes"] == 8 and len(log[0]["sha256"]) == 64 and "abgerufen" in log[0]
