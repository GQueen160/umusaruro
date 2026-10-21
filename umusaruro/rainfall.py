"""Load the CHIRPS district totals behind the irrigation gate.

Rainfall is an external gate. It never replaces a NISR cell.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "chirps" / "season_a_2026_rainfall.csv"


@dataclass(frozen=True)
class Rainfall:
    district: str
    total_mm: Decimal
    cells: int
    median_mm: Decimal
    below_median: bool
    months: str
    version: str
    source_url: str
    boundary_url: str


def load(path: Path = CSV_PATH) -> dict[str, Rainfall]:
    found: dict[str, Rainfall] = {}
    with path.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            total = Decimal(record["total_mm"])
            middle = Decimal(record["median_mm"])
            below = record["below_median"] == "true"
            if below != (total < middle):
                raise ValueError(f"below_median contradicts the totals for {record['district']}")
            found[record["district"]] = Rainfall(
                district=record["district"],
                total_mm=total,
                cells=int(record["cells"]),
                median_mm=middle,
                below_median=below,
                months=record["months"],
                version=record["version"],
                source_url=record["source_url"],
                boundary_url=record["boundary_url"],
            )
    return found
