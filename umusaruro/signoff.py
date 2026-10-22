"""Second-person sign-off for the cells a screen can show.

The checker types each value from the printed page without seeing the
stored value. A cell is checked only when the typed value matches.
A dash, an empty column, and a missing row are all typed as "-".
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from umusaruro.cells import Cell, Cells

SHEET_PATH = Path(__file__).resolve().parents[1] / "data" / "season_a_2026" / "signoff.csv"

PAGES = {"13": 39, "14": 40, "16": 42, "20": 46, "21": 47, "25": 50, "31": 55}

DISTRICTS = [
    "Nyarugenge", "Gasabo", "Kicukiro", "Nyanza", "Gisagara", "Nyaruguru", "Huye",
    "Nyamagabe", "Ruhango", "Muhanga", "Kamonyi", "Karongi", "Rutsiro", "Rubavu",
    "Nyabihu", "Ngororero", "Rusizi", "Nyamasheke", "Rulindo", "Gakenke", "Musanze",
    "Burera", "Gicumbi", "Rwamagana", "Nyagatare", "Gatsibo", "Kayonza", "Kirehe",
    "Ngoma", "Bugesera",
]

FARMER_COLUMNS = {"all": "Overall", "ssf": "SSF", "lsf": "LSF"}

FIELDS = [
    "pdf_page",
    "table",
    "row",
    "column",
    "value_on_page",
    "checker",
    "checked_on",
    "geography",
    "farmer_type",
    "crop",
    "measure",
]

DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


@dataclass(frozen=True)
class Key:
    table: str
    geography: str
    farmer_type: str
    crop: str
    measure: str


def _farmer_rows(table: str, crop: str, measure: str, column: str):
    for geography in DISTRICTS + ["National"]:
        for farmer, label in FARMER_COLUMNS.items():
            yield geography, f"{column}, {label}", Key(table, geography, farmer, crop, measure)


def screen_cells():
    """Every cell the district page, the map, or the method page reads, in printed order."""
    for geography in DISTRICTS:
        yield "13", geography, "Maize", Key("13", geography, "all", "maize", "yield")
    for label, farmer in (("National", "all"), ("SSF", "ssf"), ("LSF", "lsf")):
        yield "13", label, "Maize", Key("13", "National", farmer, "maize", "yield")
    for geography in DISTRICTS + ["National"]:
        yield "14", geography, "Maize", Key("14", geography, "lsf", "maize", "yield")
    yield "16", "Maize", "Post harvesting losses", Key("16", "National", "all", "maize", "post_harvest_loss")
    for row, column, key in _farmer_rows("20", "all_crops", "farmers", "Percentage of farmers who used improved seeds"):
        yield "20", row, column, key
    yield "21", "Maize", "Improved seeds", Key("21", "National", "all", "maize", "improved")
    yield "21", "Bush bean", "Improved seeds", Key("21", "National", "all", "bush_bean", "improved")
    for row, column, key in _farmer_rows("25", "all_crops", "farmers", "Percentage of farmers who used inorganic fertilizers"):
        yield "25", row, column, key
    for row, column, key in _farmer_rows("31", "", "irrigation", "Farmers who practiced irrigation (%)"):
        yield "31", row, column, key


def blank_sheet() -> list[dict[str, str]]:
    rows = []
    for table, row, column, key in screen_cells():
        rows.append(
            {
                "pdf_page": str(PAGES[table]),
                "table": table,
                "row": row,
                "column": column,
                "value_on_page": "",
                "checker": "",
                "checked_on": "",
                "geography": key.geography,
                "farmer_type": key.farmer_type,
                "crop": key.crop,
                "measure": key.measure,
            }
        )
    return rows


def read_sheet(path: Path = SHEET_PATH) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def write_sheet(rows: list[dict[str, str]], path: Path = SHEET_PATH) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def key_of(row: dict[str, str]) -> Key:
    return Key(row["table"], row["geography"], row["farmer_type"], row["crop"], row["measure"])


def typed_matches(typed: str, cell: Cell) -> bool:
    typed = typed.strip().replace(",", "")
    if typed == "-":
        return cell.blank
    if cell.blank:
        return False
    try:
        return Decimal(typed) == cell.value
    except InvalidOperation:
        return False


@dataclass(frozen=True)
class Review:
    matched: list[Key]
    mismatched: list[tuple[Key, str]]
    incomplete: list[Key]
    pending: int


def review(cells: Cells, rows: list[dict[str, str]]) -> Review:
    matched: list[Key] = []
    mismatched: list[tuple[Key, str]] = []
    incomplete: list[Key] = []
    pending = 0
    for row in rows:
        key = key_of(row)
        typed = row["value_on_page"].strip()
        if not typed:
            pending += 1
            continue
        if not row["checker"].strip() or not DATE.match(row["checked_on"].strip()):
            incomplete.append(key)
            continue
        cell = cells.get(key.table, key.geography, key.farmer_type, key.crop, key.measure)
        if typed_matches(typed, cell):
            matched.append(key)
        else:
            mismatched.append((key, typed))
    return Review(matched, mismatched, incomplete, pending)
