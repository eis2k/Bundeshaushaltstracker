"""Einheitliches Zeilenmodell für Haushaltstitel und Betragsparser."""

from __future__ import annotations

from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from pydantic import BaseModel

Unit = Literal["tsd", "eur"]


def parse_amount(text: str | None, unit: Unit) -> int:
    """Wandelt einen amtlichen Betragstext in ganze Euro.

    Formate: "48207871" (Tsd €, CSV), "1.088.350,00" (Euro, XML),
    nachgestelltes Minus "16,43-". Leer oder None ergibt 0.
    """
    raw = (text or "").strip()
    if not raw:
        return 0
    negative = raw.endswith("-")
    raw = raw.rstrip("-").strip()
    if raw.startswith("-"):
        negative = True
        raw = raw[1:]
    raw = raw.replace(".", "").replace(",", ".")
    if not raw:
        return 0
    value = Decimal(raw)
    if unit == "tsd":
        value *= 1000
    euro = int(value.quantize(Decimal("1"), rounding=ROUND_HALF_UP))
    return -euro if negative else euro


class BudgetRow(BaseModel):
    jahr: int
    stand: Literal["soll", "ist"]
    art: Literal["E", "A"]
    epl: str
    kap: str
    titel: str
    epl_text: str
    kap_text: str
    titel_text: str
    fkt: str
    flex: bool | None = None
    tgr: str | None = None
    tgr_text: str | None = None
    soll: int
    ist: int | None = None
    sv: bool = False
    """Anlage zum Haushalt (nicht Kernhaushalt): Sondervermögen, EU-Anlagen, Behörden-Wirtschaftspläne."""
    anlage: bool = False
    transfer: bool = False

    @property
    def id(self) -> str:
        return f"{self.epl}-{self.kap}-{self.titel}"

    @property
    def hg(self) -> str:
        return self.titel[0]

    @property
    def gruppe(self) -> str:
        return self.titel[:3]
