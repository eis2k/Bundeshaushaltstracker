"""Netz (Spec §4.7a): Knoten Personen, Organisationen, Ministerien, Parteien; Kanten Geld, Posten, Spende.
Vorberechnetes Umfeld zwei Schritte weit je Knoten, Ministerien und Parteien werden nicht expandiert, Kappung bei 60 Knoten.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path

from .empfaenger import slug
from .personen import Akte, shard
from .spenden import Spende

MAX_KNOTEN = 60
RANDKNOTEN = {"ministerium", "partei"}


@dataclass
class Knoten:
    id: str
    art: str          # person | organisation | ministerium | partei
    label: str
    sichtbar: bool
    seite: str | None


@dataclass
class Kante:
    von: str
    nach: str
    art: str          # geld | posten | spende
    text: str
    wert: int | None
    quelle: dict
    stand: str


def _ministerium_label(epl: str, ressorts: dict) -> str:
    for r in ressorts.get("ressorts") or []:
        if str(r.get("epl")) == str(epl):
            return str(r.get("kurz") or r.get("epl"))
    return f"Einzelplan {epl}"


def baue_graph(empfaenger_seiten: dict[str, dict], akten: list[Akte], spenden_by_org: dict[str, list[Spende]], ressorts: dict) -> tuple[dict[str, Knoten], list[Kante]]:
    knoten: dict[str, Knoten] = {}
    kanten: list[Kante] = []

    def ministerium(epl: str) -> str:
        kid = f"m:{epl}"
        if kid not in knoten:
            knoten[kid] = Knoten(kid, "ministerium", _ministerium_label(epl, ressorts), True, f"v1;a=fluss;t=bund;f={epl}")
        return kid

    for sid, s in empfaenger_seiten.items():
        eid = f"e:{sid}"
        knoten[eid] = Knoten(eid, "organisation", s["name"], True, f"v1;a=empfaenger;e={sid}")
        for z in s.get("lobby_zuwendungen") or []:
            if not z.get("epl"):
                continue
            kanten.append(Kante(ministerium(z["epl"]), eid, "geld", f"{z['geber']} → {s['name']}: ab {z['von']:,} € (Geschäftsjahr {z.get('geschaeftsjahr', '')}, Eigenangabe)".replace(",", "."),
                               int(z.get("von") or 0), {"kurz": "Lobbyregister", "url": (s.get("lobbyregister") or {}).get("url"), "etikett": "Eigenangabe"}, str(z.get("geschaeftsjahr") or "")))
        for t in (s.get("haushalt") or {}).get("titel") or []:
            jahre = sorted(t.get("werte") or {})
            if not jahre or not t.get("epl"):
                continue
            soll = int(t["werte"][jahre[-1]].get("soll") or 0)
            if soll <= 0:
                continue
            kanten.append(Kante(ministerium(t["epl"]), eid, "geld", f"Titel {t['id']} → {s['name']}: Soll {jahre[-1]} {soll:,} €".replace(",", "."), soll,
                               {"kurz": "bundeshaushalt.de", "url": "https://www.bundeshaushalt.de/", "etikett": "amtlich"}, jahre[-1]))
        for sp in spenden_by_org.get(sid, []):
            pid = f"partei:{slug(sp.partei)}"
            if pid not in knoten:
                knoten[pid] = Knoten(pid, "partei", sp.partei, True, None)
            kanten.append(Kante(eid, pid, "spende", f"{s['name']} spendete {sp.betrag:,} € an {sp.partei} ({sp.eingang}, {sp.drucksache})".replace(",", "."), sp.betrag,
                               {"kurz": "bundestag.de", "url": sp.drucksache_url, "etikett": "amtlich"}, sp.eingang))

    for a in akten:
        pid = f"p:{a.id}"
        knoten[pid] = Knoten(pid, "person", a.name, a.sichtbar, f"v1;a=personen;pe={a.id}" if a.sichtbar else None)
        for o in a.organisationen:
            eid = f"e:{o['id']}"
            if eid not in knoten:
                continue
            kanten.append(Kante(pid, eid, "posten", f"{a.name}: {o.get('funktion') or 'Posten'} bei {o['name']} (Stand {o.get('stand', '')})", None,
                               {"kurz": "Lobbyregister", "url": (empfaenger_seiten[o["id"]].get("lobbyregister") or {}).get("url"), "etikett": "Eigenangabe"}, str(o.get("stand") or "")))
        for f in a.funktionen:
            if f.art == "regierung" and f.epl:
                mid = ministerium(f.epl)
                kanten.append(Kante(pid, mid, "posten", f"{a.name}: {f.text}" + (f", seit {f.seit}" if f.seit else ""), None, f.quelle, f.stand))
    return knoten, kanten


def umfeld(start: str, knoten: dict[str, Knoten], kanten: list[Kante], *, max_knoten: int = MAX_KNOTEN) -> dict:
    adj: dict[str, list[tuple[int, str, Kante]]] = defaultdict(list)
    for k in kanten:
        w = k.wert or 0
        adj[k.von].append((w, k.nach, k))
        adj[k.nach].append((w, k.von, k))

    def nachbarn(kid: str) -> list[str]:
        out, seen = [], set()
        for _, other, _k in sorted(adj.get(kid, []), key=lambda x: (-x[0], x[1])):
            if other not in seen:
                seen.add(other)
                out.append(other)
        return out

    reihenfolge: list[str] = [start]
    gesehen = {start}
    ebene1 = [n for n in nachbarn(start) if n not in gesehen]
    for n in ebene1:
        gesehen.add(n)
        reihenfolge.append(n)
    if knoten.get(start) and knoten[start].art not in RANDKNOTEN:
        for n in ebene1:
            if knoten.get(n) and knoten[n].art in RANDKNOTEN:
                continue
            for m in nachbarn(n):
                if m not in gesehen:
                    gesehen.add(m)
                    reihenfolge.append(m)
    gezeigt = reihenfolge[:max_knoten]
    menge = set(gezeigt)
    kn = [asdict(knoten[k]) for k in gezeigt if k in knoten]
    ka = [asdict(k) for k in kanten if k.von in menge and k.nach in menge]
    return {"start": start, "knoten": kn, "kanten": ka, "weitere": max(0, len(reihenfolge) - max_knoten)}


def build_netz(out: Path, knoten: dict[str, Knoten], kanten: list[Kante], *, mit_personen: bool = True) -> Path:
    if not mit_personen:
        knoten = {k: v for k, v in knoten.items() if v.art != "person"}
        kanten = [k for k in kanten if k.von in knoten and k.nach in knoten]
    out_dir = out / "netz"
    out_dir.mkdir(parents=True, exist_ok=True)
    for alt in out_dir.glob("*.json"):
        alt.unlink()
    verbunden = {k.von for k in kanten} | {k.nach for k in kanten}
    shards: dict[str, dict[str, dict]] = defaultdict(dict)
    index: dict[str, str] = {}
    for kid in sorted(verbunden):
        sh = shard(kid)
        shards[sh][kid] = umfeld(kid, knoten, kanten)
        index[kid] = sh
    for sh, inhalt in shards.items():
        (out_dir / f"{sh}.json").write_text(json.dumps(inhalt, ensure_ascii=False), encoding="utf-8", newline="\n")
    index_path = out_dir / "index.json"
    index_path.write_text(json.dumps(index, ensure_ascii=False), encoding="utf-8", newline="\n")
    return index_path
