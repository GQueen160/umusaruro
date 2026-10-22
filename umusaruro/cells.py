"""Load a cell file: Season A 2026 by default, or Season B 2026.

A blank cell has no value. Reading it as a number fails. Zero is only
returned when the published table printed a zero. Each season loads into
its own Cells, so a Season B cell can never stand in for a Season A cell.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "season_a_2026" / "cells.csv"
SEASON_B_PATH = Path(__file__).resolve().parents[1] / "data" / "season_b_2026" / "cells.csv"


class BlankCell(LookupError):
    """The published table has no number in this cell."""


class CellFileError(ValueError):
    """The cell file contradicts its own blank flag."""


@dataclass(frozen=True)
class Cell:
    survey: str
    season: str
    year: str
    table: str
    geography: str
    farmer_type: str
    crop: str
    measure: str
    value: Decimal | None
    unit: str
    blank: bool
    printed: str
    source_url: str
    checked: bool

    def number(self) -> Decimal:
        if self.blank or self.value is None:
            raise BlankCell(
                f"SAS {self.season} {self.year} table {self.table} "
                f"{self.geography} {self.farmer_type} {self.crop} {self.measure} is blank"
            )
        return self.value


class Cells:
    def __init__(self, rows: list[Cell]):
        self.rows = rows
        self._index: dict[tuple[str, str, str, str, str], Cell] = {}
        for row in rows:
            key = (row.table, row.geography, row.farmer_type, row.crop, row.measure)
            if key in self._index:
                raise CellFileError(f"duplicate cell {key}")
            self._index[key] = row

    def get(self, table: str, geography: str, farmer_type: str, crop: str, measure: str) -> Cell:
        key = (table, geography, farmer_type, crop, measure)
        try:
            return self._index[key]
        except KeyError as exc:
            raise KeyError(key) from exc


def load(path: Path = CSV_PATH) -> Cells:
    rows: list[Cell] = []
    with path.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            blank = record["blank"] == "true"
            raw = record["value"]
            if blank and raw != "":
                raise CellFileError(f"blank cell has a value: {record}")
            if not blank and raw == "":
                raise CellFileError(f"numbered cell is empty: {record}")
            if record["printed"] == "number" and blank:
                raise CellFileError(f"printed number marked blank: {record}")
            if record["printed"] != "number" and not blank:
                raise CellFileError(f"non-number marked filled: {record}")
            rows.append(
                Cell(
                    survey=record["survey"],
                    season=record["season"],
                    year=record["year"],
                    table=record["table"],
                    geography=record["geography"],
                    farmer_type=record["farmer_type"],
                    crop=record["crop"],
                    measure=record["measure"],
                    value=None if blank else Decimal(raw),
                    unit=record["unit"],
                    blank=blank,
                    printed=record["printed"],
                    source_url=record["source_url"],
                    checked=record["checked"] == "true",
                )
            )
    return Cells(rows)
