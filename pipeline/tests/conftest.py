import os
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fx() -> Path:
    return FIXTURES


def raw_file(name: str) -> Path | None:
    """Pfad zu einer vollständigen Rohdatei, falls lokal vorhanden (sonst None).

    Suchreihenfolge: $BHT_RAW_DIR, dann data/raw im Repo.
    """
    candidates = []
    if os.environ.get("BHT_RAW_DIR"):
        candidates.append(Path(os.environ["BHT_RAW_DIR"]))
    candidates.append(Path(__file__).resolve().parents[2] / "data" / "raw")
    for base in candidates:
        for p in base.rglob(name):
            return p
    return None
