"""Bezüge der Amtsträger (Spec §4.7b): gesetzlich festgelegte Monatsbeträge je Funktion und Zeitraum.

Sätze (Beträge mit Gültigkeit und Quelle) kommen aus data/manual/bezuege.yaml; die Faktoren stehen hier mit Paragraf:
- Amtsgehalt: Bundeskanzler 5/3, Bundesminister 4/3 des Grundgehalts B 11 (§ 11 Abs. 1 Buchst. a BMinG); Parlamentarische
  Staatssekretäre und Staatsminister 75 % des Ministergehalts (§ 5 Abs. 1 ParlStG, § 8 ParlStG); beamtete Staatssekretäre B 11 (Anlage I BBesG).
- Dienstaufwandsentschädigung (§ 11 Abs. 1 Buchst. c BMinG), Parlamentarische Staatssekretäre 75 % (§ 5 Abs. 1 ParlStG).
- Amtszulage: Präsident 100 %, Vizepräsidenten 50 %, Vorsitzende der Ausschüsse, Untersuchungsausschüsse, Enquete-Kommissionen und
  des Parlamentarischen Kontrollgremiums 15 % der Entschädigung (§ 11 Abs. 2 AbgG).
- Amt und Mandat zugleich: Abgeordnetenentschädigung um 50 % gekürzt, der Kürzungsbetrag höchstens 30 % des Amtseinkommens (§ 29 Abs. 1 AbgG).
- Abgeordnete: Entschädigung und Kostenpauschale im Ein- und Austrittsmonat tageweise, ein Dreißigstel je Kalendertag (§ 32 Abs. 8 AbgG);
  die Kostenpauschale läuft bis zum Ende des Monats nach dem Ausscheiden (§ 32 Abs. 2 AbgG). Regierungsämter: ganze Kalendermonate
  (§ 11 Abs. 1 BMinG, § 5 Abs. 1 ParlStG).
Monatsbeträge sind Tatsachen aus den Quellen; Summen sind daraus gerechnet. Nichts wird geschätzt: fehlt ein Satz für einen Monat,
zählt der Monat nicht und der Block nennt die Lücke.
"""

from __future__ import annotations

import calendar
import re
from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from fractions import Fraction
from pathlib import Path
from urllib.parse import urlparse

import yaml

WP_BEGINN = "2025-03-25"   # konstituierende Sitzung des 21. Deutschen Bundestages (Plenarprotokoll 21/1)

ARTEN = ("abgeordnetenentschaedigung", "kostenpauschale", "mitarbeiterpauschale", "sachleistungskonto", "amtsaufwand_praesident",
         "amtsaufwand_vize", "b11", "dienstaufwand_kanzler", "dienstaufwand_minister")

_ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_CENT = Decimal("0.01")

AMTSGEHALT_FAKTOR = {"kanzler": Fraction(5, 3), "minister": Fraction(4, 3), "parl_sts": Fraction(4, 3) * Fraction(3, 4), "sts": Fraction(1)}
DIENSTAUFWAND = {"kanzler": ("dienstaufwand_kanzler", Fraction(1)), "minister": ("dienstaufwand_minister", Fraction(1)),
                 "parl_sts": ("dienstaufwand_minister", Fraction(3, 4))}
KUERZUNG_AEMTER = ("kanzler", "minister", "parl_sts")
KAPPUNG = Fraction(3, 10)   # § 29 Abs. 1 AbgG: Kürzungsbetrag höchstens 30 % des Einkommens aus dem Amtsverhältnis

NICHT_BEZIFFERBAR_MDB = [
    "Dienstreisen, Netzkarte der Bahn, Inlandsflüge gegen Nachweis, Büro am Sitz des Bundestages, Dienstfahrzeuge in Berlin und IT-System (§ 12 Abs. 4, §§ 16, 17 AbgG): Sachleistungen ohne Betrag je Person.",
    "Zuschuss zur Kranken- und Pflegeversicherung oder Beihilfe (§ 27 AbgG): hälftiger Beitrag, Wahl der Person, Betrag nicht veröffentlicht.",
    "Übergangsgeld nach dem Ausscheiden (§ 18 AbgG): je Jahr Mitgliedschaft ein Monat Entschädigung, höchstens 18 Monate; Anwartschaft.",
    "Altersentschädigung (§§ 19, 20 AbgG): 2,5 % der Entschädigung je Jahr Mitgliedschaft, höchstens 65 %, ab 67; Anwartschaft.",
    "Kürzungen der Kostenpauschale (§ 14 AbgG: 200/300/20 € je Fehltag; § 12 Abs. 6 AbgG: 25 % weniger bei Dienstwagen zur ausschließlichen Verfügung, etwa bei Regierungsmitgliedern und im Präsidium) sind hier nicht abgezogen.",
    "Zulagen der Fraktionen (Fraktionsvorsitz, Parlamentarische Geschäftsführung) kommen aus Fraktionsmitteln und werden nicht je Person amtlich veröffentlicht.",
]
NICHT_BEZIFFERBAR_REGIERUNG = [
    "Ortszuschlag (§ 11 Abs. 1 Buchst. b BMinG, 1⅓ des B-11-Ortszuschlags; entfällt bei Amtswohnung, § 12 Abs. 1 BMinG): hängt vom Familienstand ab, nicht veröffentlicht.",
    "Entschädigung bei getrennter Haushaltsführung (§ 11 Abs. 1 Buchst. d BMinG, jährlich 3.600 DM): Voraussetzung nicht veröffentlicht.",
    "Übergangsgeld nach dem Ausscheiden (§ 14 BMinG: 6 bis 24 Monate, erste drei Monate voll, danach die Hälfte); Anwartschaft.",
    "Ruhegehalt (§ 15 BMinG: ab vier Amtsjahren 27,74 % von Amtsgehalt und Ortszuschlag, je weiteres Jahr 2,39167 %, höchstens 71,75 %); Anwartschaft.",
    "Amtswohnung, Dienstwagen und Beihilfe (§ 12 BMinG): Sachleistungen ohne Betrag je Person.",
]


@dataclass(frozen=True)
class Satz:
    art: str
    ab: str
    monat: Decimal | None
    jahr: Decimal | None
    quelle: str
    fundstelle: str
    datum: str

    @property
    def monatsbetrag(self) -> Decimal:
        return self.monat if self.monat is not None else (self.jahr or Decimal(0)) / 12


# ---------------------------------------------------------------- Pflegedatei

def validate_bezuege(data: dict) -> list[str]:
    errors: list[str] = []
    for i, s in enumerate((data or {}).get("saetze") or []):
        wer = f"Satz {i + 1} ({s.get('art', '?')})"
        if s.get("art") not in ARTEN:
            errors.append(f"{wer}: art unbekannt")
        if not _ISO.match(str(s.get("ab") or "")):
            errors.append(f"{wer}: ab muss ISO-Datum sein")
        if (s.get("monat") is None) == (s.get("jahr") is None):
            errors.append(f"{wer}: genau eines von monat/jahr angeben")
        if not str(s.get("quelle") or "").startswith("http"):
            errors.append(f"{wer}: quelle (URL) fehlt")
        if not s.get("fundstelle"):
            errors.append(f"{wer}: fundstelle fehlt")
        if not _ISO.match(str(s.get("datum") or "")):
            errors.append(f"{wer}: datum muss ISO-Datum sein")
        betrag = s.get("monat") if s.get("monat") is not None else s.get("jahr")
        if betrag is not None and not (isinstance(betrag, (int, float)) and betrag > 0):
            errors.append(f"{wer}: Betrag muss größer als 0 sein")
    gesehen: set[tuple[str, str]] = set()
    for s in (data or {}).get("saetze") or []:
        key = (str(s.get("art")), str(s.get("ab")))
        if key in gesehen:
            errors.append(f"Satz {key[0]} ab {key[1]} ist doppelt")
        gesehen.add(key)
    for i, v in enumerate((data or {}).get("vorsitz_ab") or []):
        wer = f"vorsitz_ab Eintrag {i + 1}"
        if not v.get("akte_id") or not _ISO.match(str(v.get("ab") or "")):
            errors.append(f"{wer}: akte_id und ab (ISO) nötig")
        if not str(v.get("quelle") or "").startswith("http") or not _ISO.match(str(v.get("datum") or "")):
            errors.append(f"{wer}: quelle (URL) und datum nötig")
        if not v.get("fundstelle"):
            errors.append(f"{wer}: fundstelle fehlt")
    return errors


def lade_bezuege(path: Path) -> list[Satz]:
    if not path.exists():
        return []
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    fehler = validate_bezuege(data)
    if fehler:
        raise ValueError("bezuege.yaml: " + "; ".join(fehler))
    out: list[Satz] = []
    for s in data.get("saetze") or []:
        out.append(Satz(art=s["art"], ab=str(s["ab"]), monat=Decimal(str(s["monat"])) if s.get("monat") is not None else None,
                        jahr=Decimal(str(s["jahr"])) if s.get("jahr") is not None else None,
                        quelle=str(s["quelle"]), fundstelle=str(s["fundstelle"]), datum=str(s["datum"])))
    return sorted(out, key=lambda x: (x.art, x.ab))


def lade_vorsitz_ab(path: Path) -> dict[str, str]:
    """akte_id → ISO-Datum des Beginns eines Ausschussvorsitzes (gepflegt mit Quelle)."""
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return {str(v["akte_id"]): str(v["ab"]) for v in data.get("vorsitz_ab") or []}


def satz_am(saetze: list[Satz], art: str, datum: str) -> Satz | None:
    treffer = [s for s in saetze if s.art == art and s.ab <= datum]
    return max(treffer, key=lambda s: s.ab) if treffer else None


# ---------------------------------------------------------------- Hilfen

def monate(von: str, bis: str) -> list[str]:
    """Kalendermonate „YYYY-MM“ von `von` bis `bis`, beide einschließlich."""
    j, m = int(von[:4]), int(von[5:7])
    ej, em = int(bis[:4]), int(bis[5:7])
    out: list[str] = []
    while (j, m) <= (ej, em):
        out.append(f"{j:04d}-{m:02d}")
        m += 1
        if m > 12:
            j, m = j + 1, 1
    return out


def _monatsende(monat: str) -> str:
    j, m = int(monat[:4]), int(monat[5:7])
    return f"{j:04d}-{m:02d}-{calendar.monthrange(j, m)[1]:02d}"


def _folgemonat_ende(datum: str) -> str:
    j, m = int(datum[:4]), int(datum[5:7])
    m += 1
    if m > 12:
        j, m = j + 1, 1
    return _monatsende(f"{j:04d}-{m:02d}")


def tag_danach(datum: str) -> str:
    return (date.fromisoformat(datum) + timedelta(days=1)).isoformat()


def rolle_amt(amt: str) -> str:
    a = (amt or "").strip().lower()
    if a.startswith("bundeskanzler"):
        return "kanzler"
    if a.startswith("parlamentarische") or a.startswith("staatsminister"):
        return "parl_sts"
    if a.startswith("staatssekretär"):
        return "sts"
    return "minister"   # Bundesminister, Bundesministerin, Chef/Chefin des Bundeskanzleramts


_ZULAGE_GREMIUM = re.compile(r"(ausschuss|untersuchungsausschuss|enquete-kommission|parlamentarisches kontrollgremium)", re.I)
# Unterausschüsse (auch der Rechnungsprüfungsausschuss als Unterausschuss des Haushaltsausschusses), Beiräte, Kommissionen und sonstige Gremien: keine Zulage
_KEIN_ZULAGE_GREMIUM = re.compile(r"(unterausschuss|rechnungsprüfungsausschuss|beirat|kinderkommission|gremium nach|vertrauensgremium|finanzierungsgremium)", re.I)


def amtszulage_faktor(aemter: list[str]) -> Decimal:
    """§ 11 Abs. 2 AbgG; „Amtierende“ und „Stellvertretende“ zählen nicht (VG Berlin, VG 5 K 805/22)."""
    faktor = Decimal(0)
    for eintrag in aemter or []:
        rolle, _, gremium = eintrag.partition(":")
        r = rolle.strip().lower()
        g = gremium.strip()
        if r.startswith("präsident"):
            return Decimal(1)
        if r.startswith("vizepräsident"):
            faktor = max(faktor, Decimal("0.5"))
        elif r in ("vorsitzender", "vorsitzende") and _ZULAGE_GREMIUM.search(g) and not _KEIN_ZULAGE_GREMIUM.search(g):
            faktor = max(faktor, Decimal("0.15"))
    return faktor


def _cent(x: Decimal) -> Decimal:
    return x.quantize(_CENT, rounding=ROUND_HALF_UP)


def _dec(faktor: Fraction | Decimal) -> Decimal:
    return Decimal(faktor.numerator) / Decimal(faktor.denominator) if isinstance(faktor, Fraction) else Decimal(faktor)


def _kurz(url: str) -> str:
    host = urlparse(url).hostname
    return host.replace("www.", "") if host else url


def _quelle(s: Satz | None) -> dict:
    if s is None:
        return {"kurz": "", "url": None, "fundstelle": ""}
    return {"kurz": _kurz(s.quelle), "url": s.quelle, "fundstelle": s.fundstelle}


# ---------------------------------------------------------------- Rechnung

def _zeitraum(f: dict, stand: str) -> tuple[str | None, str]:
    von = f.get("seit")
    if f.get("art") == "mdb":
        von = von if von and von > WP_BEGINN else WP_BEGINN
    bis = f.get("bis") or stand
    if bis > stand:
        bis = stand
    return von, bis


def _tagesfaktor(monat: str, von: str, bis: str, echtes_bis: bool) -> Decimal:
    """§ 32 Abs. 8 AbgG: im Ein- und Austrittsmonat ein Dreißigstel je Kalendertag, höchstens ein voller Monat."""
    tage_im_monat = calendar.monthrange(int(monat[:4]), int(monat[5:7]))[1]
    erster, letzter = 1, tage_im_monat
    if von[:7] == monat:
        erster = int(von[8:10])
    if echtes_bis and bis[:7] == monat:
        letzter = int(bis[8:10])
    tage = letzter - erster + 1
    if erster == 1 and letzter == tage_im_monat:
        return Decimal(1)
    return min(Decimal(1), Decimal(tage) / Decimal(30))


def _zeile(posten: str, komponente: str, rechtsgrundlage: str, art: str, faktor: Fraction | Decimal, von: str | None, bis: str,
           saetze: list[Satz], stand: str, empfaenger: str, luecken: dict[str, dict[str, int]], *,
           tageweise: bool = False, echtes_bis: bool = False) -> tuple[dict, dict[str, Decimal]]:
    """Eine Zeile des Blocks plus die gerechneten Monatsbeträge (für die Kürzung nach § 29 AbgG)."""
    fak = _dec(faktor)
    letzter = satz_am(saetze, art, bis if von else stand)
    monatlich = _cent(letzter.monatsbetrag * fak) if letzter else None
    zeile = {"posten": posten, "komponente": komponente, "rechtsgrundlage": rechtsgrundlage, "monatlich": float(monatlich) if monatlich is not None else None,
             "zeitraum_von": von, "zeitraum_bis": bis if von else None, "monate": None, "summe": None, "empfaenger": empfaenger, "quelle": _quelle(letzter),
             "quellen": [_quelle(letzter)] if letzter else []}
    je_monat: dict[str, Decimal] = {}
    if von is None:
        return zeile, je_monat
    summe = Decimal(0)
    verwendet: list[Satz] = []
    for m in monate(von, bis):
        s = satz_am(saetze, art, f"{m}-01")
        if s is None:
            luecken[komponente][m[:4]] += 1
            continue
        if s not in verwendet:
            verwendet.append(s)
        tf = _tagesfaktor(m, von, bis, echtes_bis) if tageweise else Decimal(1)
        betrag = _cent(s.monatsbetrag * fak * tf)
        je_monat[m] = betrag
        summe += betrag
    zeile["monate"] = len(je_monat)
    zeile["summe"] = float(_cent(summe)) if je_monat else None
    if verwendet:
        zeile["quellen"] = [_quelle(s) for s in sorted(verwendet, key=lambda s: s.ab)]
    return zeile, je_monat


def berechne_bezuege(funktionen: list[dict], saetze: list[Satz], stand: str, vorsitz_ab: str | None = None) -> dict:
    zeilen: list[dict] = []
    hinweise: list[str] = []
    nicht: list[str] = []
    luecken: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    mdb = [f for f in funktionen if f.get("art") == "mdb"]
    reg = [f for f in funktionen if f.get("art") == "regierung"]
    if not mdb and not reg:
        return {"zeilen": [], "summe_person": 0.0, "summe_aufwand": 0.0, "hinweise": [], "nicht_bezifferbar": [], "wp_beginn": WP_BEGINN}

    def merke(text: str) -> None:
        if text not in hinweise:
            hinweise.append(text)

    entschaedigung_je_monat: dict[str, Decimal] = {}
    amtsgehalt_je_monat: dict[str, Decimal] = {}
    reg_ohne_zeitraum = False

    for f in mdb:
        von, bis = _zeitraum(f, stand)
        echtes_bis = bool(f.get("bis"))
        posten = f.get("text") or "Mitglied des Bundestages"
        if f.get("seit_hinweis"):
            merke(f"{posten}: {f['seit_hinweis']}")
        elif not f.get("seit"):
            merke(f"{posten}: kein Eintrittsdatum in der Biografie; gerechnet ab Beginn der 21. Wahlperiode ({WP_BEGINN}).")
        z, je = _zeile(posten, "Abgeordnetenentschädigung", "§ 11 Abs. 1 AbgG", "abgeordnetenentschaedigung", Fraction(1), von, bis, saetze, stand, "person", luecken,
                       tageweise=True, echtes_bis=echtes_bis)
        zeilen.append(z)
        for m, b in je.items():
            entschaedigung_je_monat[m] = entschaedigung_je_monat.get(m, Decimal(0)) + b
        faktor = amtszulage_faktor(f.get("aemter") or [])
        if faktor:
            komponente = "Amtszulage Präsidium" if faktor >= Decimal("0.5") else "Amtszulage Ausschussvorsitz"
            z_von = max(vorsitz_ab, von) if vorsitz_ab else None
            zeilen.append(_zeile(posten, komponente, "§ 11 Abs. 2 AbgG", "abgeordnetenentschaedigung", faktor, z_von, bis, saetze, stand, "person", luecken,
                                 tageweise=True, echtes_bis=echtes_bis)[0])
            if not vorsitz_ab:
                merke(f"{komponente}: Beginn des Vorsitzes nicht belegt, deshalb nur Monatsbetrag ohne Summe.")
            else:
                merke(f"{komponente}: gerechnet ab {vorsitz_ab} (Beginn laut Pflegedatei bezuege.yaml mit Fundstelle).")
            if faktor >= Decimal("0.5"):
                art = "amtsaufwand_praesident" if faktor == 1 else "amtsaufwand_vize"
                zeilen.append(_zeile(posten, "Amtsaufwandsentschädigung Präsidium", "§ 12 Abs. 5 AbgG", art, Fraction(1), z_von, bis, saetze, stand, "person", luecken)[0])
        kp_bis = _folgemonat_ende(bis) if echtes_bis else bis
        if kp_bis > stand:
            kp_bis = stand
        zeilen.append(_zeile(posten, "Kostenpauschale", "§ 12 Abs. 2 AbgG (steuerfrei)", "kostenpauschale", Fraction(1), von, kp_bis, saetze, stand, "person", luecken, tageweise=True)[0])
        if echtes_bis:
            merke("Kostenpauschale läuft bis zum Ende des Monats nach dem Ausscheiden (§ 32 Abs. 2 AbgG); die Mitarbeiterpauschale kann bis zu fünf Monate weiterlaufen (§ 32 Abs. 3 AbgG), hier nicht gerechnet.")
        zeilen.append(_zeile(posten, "Mitarbeiterpauschale", "§ 12 Abs. 3 AbgG (Höchstbetrag, gegen Nachweis)", "mitarbeiterpauschale", Fraction(1), von, bis, saetze, stand, "dritte", luecken)[0])
        zeilen.append(_zeile(posten, "Sachleistungskonto", "§ 12 Abs. 4 AbgG (Höchstbetrag, nicht bar)", "sachleistungskonto", Fraction(1), von, bis, saetze, stand, "dritte", luecken)[0])
        merke("Erst- und Austrittsmonat der Entschädigung und der Kostenpauschale tageweise, ein Dreißigstel je Kalendertag (§ 32 Abs. 8 AbgG); Mitarbeiterpauschale und Sachleistungskonto je angefangenem Monat als Höchstbetrag.")
        merke("Mitarbeiterpauschale: fließt an die Mitarbeiter, nicht an den Abgeordneten; Abrechnung durch die Bundestagsverwaltung.")
        if any(m >= "2026-07" for m in monate(von, bis)):
            merke("Anpassung 2026 (Drucksache 21/6330): Juli 12.330,48 €, August 11.336,46 €, ab September wieder 11.833,47 €; gerechnet mit 11.833,47 € durchgehend.")
        for x in NICHT_BEZIFFERBAR_MDB:
            if x not in nicht:
                nicht.append(x)

    for f in reg:
        rolle = rolle_amt(f.get("amt") or f.get("text") or "")
        von, bis = _zeitraum(f, stand)
        posten = f.get("text") or "Bundesregierung"
        if von is None:
            reg_ohne_zeitraum = reg_ohne_zeitraum or rolle in KUERZUNG_AEMTER
            merke(f"{posten}: Zeitraum nicht belegt, keine Summe.")
        grund = {"kanzler": "§ 11 Abs. 1 Buchst. a BMinG (5/3 von B 11)", "minister": "§ 11 Abs. 1 Buchst. a BMinG (4/3 von B 11)",
                 "parl_sts": "§ 5 Abs. 1 ParlStG (75 % des Ministergehalts)", "sts": "Anlage I BBesG (B 11)"}[rolle]
        z, je = _zeile(posten, "Amtsgehalt", grund, "b11", AMTSGEHALT_FAKTOR[rolle], von, bis, saetze, stand, "person", luecken)
        zeilen.append(z)
        if rolle in KUERZUNG_AEMTER:
            for m, b in je.items():
                amtsgehalt_je_monat[m] = max(amtsgehalt_je_monat.get(m, Decimal(0)), b)
        if rolle in DIENSTAUFWAND:
            art, fak = DIENSTAUFWAND[rolle]
            grund_d = "§ 11 Abs. 1 Buchst. c BMinG" + (", § 5 Abs. 1 ParlStG (75 %)" if rolle == "parl_sts" else "")
            zeilen.append(_zeile(posten, "Dienstaufwandsentschädigung", grund_d, art, fak, von, bis, saetze, stand, "person", luecken)[0])
        for x in NICHT_BEZIFFERBAR_REGIERUNG:
            if x not in nicht:
                nicht.append(x)
        merke("Grundgehalt B 11 nach Anlage IV BBesG, Tabellenstand 1. März 2024; spätere Anpassungen sind noch nicht verkündet und werden erst mit Fundstelle übernommen.")

    # § 29 Abs. 1 AbgG: Amt und Mandat zugleich — 50 % der Entschädigung, höchstens 30 % des Amtseinkommens
    if mdb and reg:
        gemeinsam = sorted(set(entschaedigung_je_monat) & set(amtsgehalt_je_monat))
        if gemeinsam:
            summe = Decimal(0)
            letzter_monat = Decimal(0)
            for m in gemeinsam:
                kuerzung = min(_cent(entschaedigung_je_monat[m] / 2), _cent(amtsgehalt_je_monat[m] * _dec(KAPPUNG)))
                summe -= kuerzung
                letzter_monat = kuerzung
            zr = [_zeitraum(f, stand) for f in mdb + reg if _zeitraum(f, stand)[0] is not None and (f.get("art") == "mdb" or rolle_amt(f.get("amt") or f.get("text") or "") in KUERZUNG_AEMTER)]
            zeilen.append({"posten": mdb[0].get("text") or "Mitglied des Bundestages", "komponente": "Kürzung der Abgeordnetenentschädigung (Amt und Mandat)",
                           "rechtsgrundlage": "§ 29 Abs. 1 AbgG (50 %, höchstens 30 % des Amtseinkommens)", "monatlich": float(-letzter_monat),
                           "zeitraum_von": max(z[0] for z in zr), "zeitraum_bis": min(z[1] for z in zr), "monate": len(gemeinsam), "summe": float(_cent(summe)),
                           "empfaenger": "person", "quelle": {"kurz": "gesetze-im-internet.de", "url": "https://www.gesetze-im-internet.de/abgg/__29.html", "fundstelle": "§ 29 Abs. 1 AbgG"}})
            merke("§ 29 Abs. 1 AbgG: Kürzungsbetrag höchstens 30 % des Amtseinkommens; gerechnet mit dem Amtsgehalt. Der nicht veröffentlichte Ortszuschlag würde die Kappung leicht anheben.")
        if reg_ohne_zeitraum:
            merke("§ 29 Abs. 1 AbgG: Kürzung der Abgeordnetenentschädigung um 50 % bei Amt und Mandat; Zeitraum nicht belegt, deshalb nicht gerechnet.")

    for komponente, jahre in luecken.items():
        for jahr, n in sorted(jahre.items()):
            merke(f"{komponente}: Betrag für {jahr} noch nicht belegt ({n} Monate), nicht in der Summe.")
    merke("Monatsbeträge sind gesetzlich festgelegt; Summen sind daraus gerechnet, keine Einzelabrechnung.")

    summe_person = sum((Decimal(str(z["summe"])) for z in zeilen if z["summe"] is not None and z["empfaenger"] == "person"), Decimal(0))
    summe_aufwand = sum((Decimal(str(z["summe"])) for z in zeilen if z["summe"] is not None and z["empfaenger"] == "dritte"), Decimal(0))
    return {"zeilen": zeilen, "summe_person": float(_cent(summe_person)), "summe_aufwand": float(_cent(summe_aufwand)),
            "hinweise": hinweise, "nicht_bezifferbar": nicht, "wp_beginn": WP_BEGINN}
