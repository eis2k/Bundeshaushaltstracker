"""Kommandozeile der Pipeline: ``bht fetch``, ``bht build``, ``bht check``.

Regeln je Jahr (siehe Konzept §9 und Ledger):
- Soll-Grundlage ist die CSV des Portals (bevorzugt *_ALL mit Anlagen); Nachtrags-CSVs
  (nur geänderte Titel) werden in Reihenfolge n1, n2 … darübergelegt.
- Liegt eine Haushaltsrechnung (rechnung_<jahr>.xml) vor, gilt deren Soll als Endstand
  (inkl. aller Nachträge) und liefert die Ist-Werte.
- Die Summen werden gegen data/manual/gesamtplan_summen.yaml geprüft; bei Abweichung Exit 1.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

from . import portal
from .build import build_index, build_year, build_zeitreihe
from .checks import CheckResult, check_totals, load_expected
from .model import BudgetRow
from .nachtrag import apply_nachtrag
from .parse_csv import parse_soll_csv
from .parse_xml import parse_rechnung_xml
from .sv import load_manual, mark_sv

REPO = Path(__file__).resolve().parents[3]
DEFAULT_RAW = REPO / "data" / "raw"
DEFAULT_OUT = REPO / "data" / "build"
DEFAULT_MANUAL = REPO / "data" / "manual"


# ---------------------------------------------------------------- fetch

def cmd_fetch(args: argparse.Namespace) -> int:
    raw = Path(args.raw)
    cats = portal.list_categories()
    for jahr in range(args.von, args.bis + 1):
        cs = cats.get(jahr, [])
        soll_cats = sorted({c.value for c in cs if c.value.startswith("soll_")})
        for cat in soll_cats:
            try:
                files = portal.list_files(jahr, cat)
                f = portal.choose_soll_file(files)
            except LookupError as e:
                print(f"{jahr} {cat}: {e}")
                continue
            p = portal.download(f.path, raw)
            print(f"{jahr} {cat}: {p.relative_to(raw)}")
            if "_all" in f.path.lower():
                for g in files:
                    if g.path.lower().endswith(".csv") and "_all" not in g.path.lower():
                        portal.download(g.path, raw)
        if any(c.value == f"ist_{jahr}" for c in cs):
            try:
                f = portal.choose_ist_file(portal.list_files(jahr, f"ist_{jahr}"))
                p = portal.download(f.path, raw)
                print(f"{jahr} ist: {p.relative_to(raw)}")
            except LookupError as e:
                print(f"{jahr} ist: {e}")
    return 0


# ---------------------------------------------------------------- build

def _soll_files(soll_dir: Path) -> tuple[Path | None, Path | None, list[Path]]:
    """Liefert (Hauptdatei, Kern-Datei falls _ALL vorhanden, Nachtragsdateien in Reihenfolge)."""
    csvs = sorted(soll_dir.glob("*.csv"))
    main = kern = None
    if csvs:
        ranked = sorted(csvs, key=lambda p: portal._soll_rank(portal.PortalFile(p.name, f"/static/daten/x/{p.name}", 0, "csv", "")))
        main = ranked[0]
        if "_all" in main.name.lower():
            kern = next((p for p in csvs if p is not main and "_all" not in p.name.lower()), None)
    nachtraege: list[Path] = []
    for d in sorted(soll_dir.glob("n*"), key=lambda d: int(re.sub(r"\D", "", d.name) or 0)):
        if d.is_dir():
            c = sorted(d.glob("*.csv"))
            if c:
                ranked = sorted(c, key=lambda p: portal._soll_rank(portal.PortalFile(p.name, f"/static/daten/x/{p.name}", 0, "csv", "")))
                nachtraege.append(ranked[0])
    return main, kern, nachtraege


def _quelle(path: Path, raw: Path, dokument: str) -> dict:
    rel = "/static/daten/" + path.relative_to(raw).as_posix()
    log_file = raw / "fetch_log.json"
    abgerufen = None
    if log_file.exists():
        for e in json.loads(log_file.read_text(encoding="utf-8")):
            if e.get("path") == rel:
                abgerufen = e.get("abgerufen")
    return {"dokument": dokument, "datei": path.name, "url": portal.BASE + rel, "abgerufen": abgerufen}


def _mark_sv_xml_rows(rows: list[BudgetRow], manual: dict) -> list[BudgetRow]:
    return mark_sv(rows, None, manual)


def build_one_year(jahr: int, raw: Path, out: Path, manual: dict, expected: dict, toleranz: int
                   ) -> tuple[CheckResult | None, list[BudgetRow] | None, list[BudgetRow] | None]:
    soll_dir = raw / str(jahr) / "soll"
    main, kern, nachtraege = _soll_files(soll_dir) if soll_dir.exists() else (None, None, [])
    ist_file = raw / str(jahr) / "ist" / f"rechnung_{jahr}.xml"
    if main is None and not ist_file.exists():
        return None, None, None

    rows_soll: list[BudgetRow] = []
    quelle: dict = {"soll": None, "ist": None, "hinweise": []}
    if main is not None:
        rows_soll = parse_soll_csv(main, jahr)
        rows_kern = parse_soll_csv(kern, jahr) if kern else None
        rows_soll = mark_sv(rows_soll, rows_kern, manual)
        quelle["soll"] = _quelle(main, raw, f"Bundeshaushaltsplan {jahr} (Download-Portal)")
        for n in nachtraege:
            rows_soll = apply_nachtrag(rows_soll, _mark_sv_xml_rows(parse_soll_csv(n, jahr), manual))
            quelle["hinweise"].append(f"Nachtrag angewandt: {n.parent.name}/{n.name}")

    rows_ist: list[BudgetRow] | None = None
    if ist_file.exists():
        rows_ist = _mark_sv_xml_rows(parse_rechnung_xml(ist_file, jahr), manual)
        quelle["ist"] = _quelle(ist_file, raw, f"Haushaltsrechnung {jahr} (Download-Portal)")
        # Soll-Endstand aus der Rechnung übernehmen (enthält alle Nachträge)
        soll_by_id = {r.id: r for r in rows_ist}
        if rows_soll:
            rows_soll = [r.model_copy(update={"soll": soll_by_id[r.id].soll}) if r.id in soll_by_id else r
                         for r in rows_soll]
            known = {r.id for r in rows_soll}
            kap_text = {r.kap: r.kap_text for r in rows_soll if r.kap_text}
            rows_soll += [r.model_copy(update={"stand": "soll", "kap_text": kap_text.get(r.kap, "")})
                          for r in rows_ist if r.id not in known]
            quelle["hinweise"].append("Soll-Werte aus der Haushaltsrechnung (Endstand inkl. Nachträge)")
        else:
            rows_soll = [r.model_copy(update={"stand": "soll"}) for r in rows_ist]
            quelle["hinweise"].append("Keine Soll-CSV: Soll und Texte aus der Haushaltsrechnung")

    res = check_totals(rows_soll, jahr, expected.get(jahr, {}), toleranz=toleranz)
    for d in res.diffs:
        print("FEHLER", d)
    if res.ok:
        build_year(rows_soll, rows_ist, jahr, quelle, out)
    return res, rows_soll, rows_ist


def cmd_build(args: argparse.Namespace) -> int:
    raw, out, manual_dir = Path(args.raw), Path(args.out), Path(args.manual)
    manual = load_manual(manual_dir / "sondervermoegen.yaml")
    exp_all = load_expected(Path(args.summen))
    toleranz = int(exp_all.get("toleranz", 1_000_000))
    totals: dict[int, CheckResult] = {}
    years: dict[int, list[BudgetRow]] = {}
    ist_years: dict[int, list[BudgetRow]] = {}
    failed = False
    for jahr in range(args.von, args.bis + 1):
        res, rows_soll, rows_ist = build_one_year(jahr, raw, out, manual, exp_all["jahre"], toleranz)
        if res is None:
            print(f"{jahr}: keine Rohdaten, übersprungen")
            continue
        if not res.ok:
            failed = True
            continue
        totals[jahr] = res
        years[jahr] = rows_soll or []
        if rows_ist:
            ist_years[jahr] = rows_ist
        print(f"{jahr}: ok  Ausgaben {res.ausgaben/1e9:,.1f} Mrd  Einnahmen {res.einnahmen/1e9:,.1f} Mrd  Kredite {res.kredite/1e9:,.1f} Mrd")
    if failed:
        return 1
    if not years:
        print("nichts gebaut")
        return 1
    build_zeitreihe(years, ist_years, out)
    build_index(sorted(years), totals, ist_bis=max(ist_years) if ist_years else None, out=out)
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    args.von = args.bis = args.jahr
    args.out = str(Path(args.out) / "_check")
    return cmd_build(args)


# ---------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="bht", description="Pipeline des Bundeshaushaltstrackers")
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--raw", default=str(DEFAULT_RAW))
        sp.add_argument("--out", default=str(DEFAULT_OUT))
        sp.add_argument("--manual", default=str(DEFAULT_MANUAL))
        sp.add_argument("--summen", default=str(DEFAULT_MANUAL / "gesamtplan_summen.yaml"))

    f = sub.add_parser("fetch", help="Dateien des Download-Portals laden")
    f.add_argument("--from", dest="von", type=int, default=2015)
    f.add_argument("--to", dest="bis", type=int, default=2026)
    common(f)
    f.set_defaults(func=cmd_fetch)

    b = sub.add_parser("build", help="Build-Dateien erzeugen")
    b.add_argument("--from", dest="von", type=int, default=2015)
    b.add_argument("--to", dest="bis", type=int, default=2026)
    common(b)
    b.set_defaults(func=cmd_build)

    c = sub.add_parser("check", help="nur Summenprüfung eines Jahres")
    c.add_argument("jahr", type=int)
    common(c)
    c.set_defaults(func=cmd_check)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
