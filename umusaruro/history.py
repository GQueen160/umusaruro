"""Load the Season A back-series, 2019 to 2026.

One row per year, lever, district (or National) and farmer type, built by
tools/build_history.py from the NISR workbooks listed in data/raw/MANIFEST.csv.
A blank has no value, and reading it as a number fails, as for the printed
cells. Districts are keyed by the official NISR district_id.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

from umusaruro.cells import BlankCell, CellFileError

PATH = Path(__file__).resolve().parents[1] / "data" / "history" / "season_a.csv"
LEVERS = ("maize_yield", "maize_yield_lsf", "seed", "fertilizer", "irrigation")


@dataclass(frozen=True)
class Point:
    year: int
    lever: str
    district_id: str
    geography: str
    farmer_type: str
    value: Decimal | None
    unit: str
    printed: str
    table: str
    source_url: str

    @property
    def blank(self) -> bool:
        return self.value is None

    def number(self) -> Decimal:
        if self.value is None:
            raise BlankCell(f"SAS A {self.year} table {self.table} {self.geography} {self.farmer_type} {self.lever} is blank")
        return self.value


class History:
    def __init__(self, points: list[Point]):
        self.points = points
        self._index: dict[tuple[int, str, str, str], Point] = {}
        for p in points:
            key = (p.year, p.lever, p.geography, p.farmer_type)
            if key in self._index:
                raise CellFileError(f"duplicate point {key}")
            self._index[key] = p

    @property
    def years(self) -> list[int]:
        return sorted({p.year for p in self.points})

    def get(self, year: int, lever: str, geography: str, farmer_type: str) -> Point:
        return self._index[(year, lever, geography, farmer_type)]

    def series(self, lever: str, geography: str, farmer_type: str) -> list[Point]:
        return [self._index[key] for year in self.years
                if (key := (year, lever, geography, farmer_type)) in self._index]


def load(path: Path = PATH) -> History:
    points = []
    with path.open(newline="", encoding="utf-8") as handle:
        for r in csv.DictReader(handle):
            blank = r["blank"] == "true"
            if blank != (r["value"] == "") or blank != (r["printed"] != "number"):
                raise CellFileError(f"blank flag contradicts the row: {r}")
            if r["lever"] not in LEVERS:
                raise CellFileError(f"unknown lever: {r}")
            points.append(Point(
                year=int(r["year"]), lever=r["lever"], district_id=r["district_id"], geography=r["geography"],
                farmer_type=r["farmer_type"], value=None if blank else Decimal(r["value"]), unit=r["unit"],
                printed=r["printed"], table=r["table"], source_url=r["source_url"],
            ))
    return History(points)
