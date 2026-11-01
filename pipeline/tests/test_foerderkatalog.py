import io
from pathlib import Path

from bhtracker.foerderkatalog import Sitzung, fetch_projekte, lade_projekte, parse_csv

FIXTURES = Path(__file__).parent / "fixtures"


def fixture_bytes(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_parse_csv_liest_projekte():
    ps = parse_csv(fixture_bytes("foekat_humboldt.csv").decode("latin-1"))
    assert len(ps) == 9
    p = next(x for x in ps if x.fkz == "M538100")
    assert p.ressort == "BMFTR" and p.empfaenger == "Alexander von Humboldt-Stiftung" and p.empfaenger_ort == "Bonn"
    assert p.von == "2024-01-01" and p.bis == "2028-12-31"
    assert p.summe == 142_079_051.0 and p.foerderart == "Direkte Projektförderung"
    assert p.thema.startswith("Alexander von Humboldt-Professur")


def test_parse_csv_leer():
    assert parse_csv('="FKZ";="Ressort"\n') == []


def test_sitzung_erkennt_leeres_ergebnis():
    class Opener:
        def __init__(self):
            self.calls = []

        def open(self, req, timeout=60):
            url = req.full_url if hasattr(req, "full_url") else req
            self.calls.append(url)
            body = fixture_bytes("foekat_leer.html") if "actionMode=print" not in url else b""
            return io.BytesIO(body)

    s = Sitzung(opener=Opener(), pause=0)
    assert s.suche_csv("Amadeu Antonio") is None
    assert not any("presentationType=csv" in u for u in s.opener.calls)  # kein Export bei leerem Ergebnis
    assert any("actionMode=searchmask" in u for u in s.opener.calls)


def test_sitzung_exportiert_bei_treffern():
    class Opener:
        def open(self, req, timeout=60):
            url = req.full_url if hasattr(req, "full_url") else req
            if "actionMode=print" in url:
                return io.BytesIO(fixture_bytes("foekat_humboldt.csv"))
            return io.BytesIO("<html>Suchergebnis (9 Treffer)</html>".encode("latin-1"))

    s = Sitzung(opener=Opener(), pause=0)
    text = s.suche_csv("Alexander von Humboldt-Stiftung")
    assert text is not None and len(parse_csv(text)) == 9


def test_fetch_projekte_schreibt_und_ueberspringt(tmp_path):
    class S:
        calls = 0

        def suche_csv(self, name):
            S.calls += 1
            return fixture_bytes("foekat_humboldt.csv").decode("latin-1")

    fetch_projekte(tmp_path, [("humboldt", "Alexander von Humboldt-Stiftung")], S())
    fetch_projekte(tmp_path, [("humboldt", "Alexander von Humboldt-Stiftung")], S())
    assert S.calls == 1
    assert len(lade_projekte(tmp_path)["humboldt"]) == 9


def test_fetch_projekte_merkt_sich_leeres_ergebnis(tmp_path):
    class S:
        calls = 0

        def suche_csv(self, name):
            S.calls += 1
            return None

    fetch_projekte(tmp_path, [("aas", "Amadeu Antonio")], S())
    fetch_projekte(tmp_path, [("aas", "Amadeu Antonio")], S())
    assert S.calls == 1 and lade_projekte(tmp_path) == {"aas": []}
