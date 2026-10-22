"""Transcribe the Season B 2026 tables named in the evidence contract.

The printed report is the source. The NISR workbook is read only to check
it: every transcribed cell must round to the workbook value, and a printed
dash must be an empty or zero workbook cell. The footer of each table is
recorded from both files, because workbook Table 29 says "SAS 2025".

    pdftotext -layout "SAS 2026B_Main report.pdf" /tmp/sas2026b.txt
    python tools/transcribe_season_b.py /tmp/sas2026b.txt "Tables_2026 Season B.xlsx"
"""

from __future__ import annotations

import csv
import sys
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import transcribe_season_a as season_a  # noqa: E402
from umusaruro import xlsx  # noqa: E402

SOURCE = "https://statistics.gov.rw/sites/default/files/documents/2026-09/SAS%202026B_Main%20report.pdf"
SURVEY = "SAS"
SEASON = "B"
YEAR = "2026"
DISTRICTS = season_a.DISTRICTS
FIELDS = season_a.FIELDS

OUT_DIR = Path(__file__).resolve().parents[1] / "data" / "season_b_2026"
CELLS_OUT = OUT_DIR / "cells.csv"
FOOTERS_OUT = OUT_DIR / "footer_check.csv"
FOOTER_FIELDS = ["table", "pdf_page", "pdf_footer", "workbook_footer", "footer_on_page", "checker", "checked_on"]

PAGES = {"18": 46, "23": 51, "29": 57}
WORKBOOK_NATIONAL = {"18": "National", "23": "Total", "29": "National"}
FARMER_GROUPS = [
    ("farmers", ["all", "ssf", "lsf"]),
    ("plots", ["all", "ssf", "lsf"]),
    ("land", ["all", "ssf", "lsf"]),
]
PRACTICE_GROUPS = [
    ("erosion", ["all", "ssf", "lsf"]),
    ("mechanization", ["all", "ssf", "lsf"]),
    ("irrigation", ["all", "ssf", "lsf"]),
    ("agroforestry", ["all", "ssf", "lsf"]),
]
def cell(table, geography, farmer_type, crop, measure, raw, unit, printed):
    row = season_a.cell(table, geography, farmer_type, crop, measure, raw, unit, printed)
    row.update(survey=SURVEY, season=SEASON, year=YEAR, source_url=SOURCE)
    return row


def workbook_table(rows: list[list], table: str, width: int):
    """District rows, the national row, and the footer of one workbook table."""
    found = {}
    footer = ""
    for row in rows:
        label = next((v for v in row if isinstance(v, str) and v.strip()), "")
        name = label.strip()
        if name.startswith("Source"):
            footer = name
            continue
        if name in DISTRICTS or name == WORKBOOK_NATIONAL[table]:
            start = row.index(label) + 1
            values = (row[start : start + width] + [None] * width)[:width]
            found["National" if name == WORKBOOK_NATIONAL[table] else name] = values
    if set(found) != set(DISTRICTS) | {"National"}:
        raise SystemExit(f"workbook Table {table} rows {sorted(found)}")
    return found, footer


def pdf_footer(lines: list[str], title: str) -> str:
    start = season_a.table_start(lines, title)
    for line in lines[start + 1 :]:
        if line.strip().startswith("Source"):
            return " ".join(line.split()).replace("Source :", "Source:")
    raise SystemExit(f"{title} has no source line")


def agrees(row: dict, workbook_value) -> bool:
    """A printed number must be the workbook value rounded to the digits the report printed."""
    if row["printed"] == "number":
        printed = Decimal(row["value"])
        half_step = Decimal(5).scaleb(printed.as_tuple().exponent - 1)
        return workbook_value is not None and abs(printed - workbook_value) <= half_step
    if row["printed"] == "dash":
        return workbook_value is None or workbook_value == 0
    return workbook_value is None


def cross_check(rows: list[dict], table: str, groups, workbook: dict[str, list]) -> int:
    order = [(measure, farmer) for measure, farmers in groups for farmer in farmers]
    disagreements = []
    for row in rows:
        index = order.index((row["measure"], row["farmer_type"]))
        value = workbook[row["geography"]][index]
        if not agrees(row, value):
            disagreements.append(f"Table {table} {row['geography']} {row['measure']} {row['farmer_type']}: "
                                 f"report {row['value'] or row['printed']}, workbook {value}")
    if disagreements:
        raise SystemExit("report and workbook disagree:\n" + "\n".join(disagreements))
    return len(rows)


def require(rows, **query):
    hits = [row for row in rows if all(row[key] == value for key, value in query.items())]
    if len(hits) != 1:
        raise SystemExit(f"expected one row for {query}, found {len(hits)}")
    return hits[0]


def check(rows):
    """National rows against the report text, and blanks that must stay blank."""
    expect = {
        ("18", "National", "all", "farmers"): "20.9",
        ("18", "National", "ssf", "farmers"): "19.4",
        ("18", "National", "lsf", "farmers"): "65.0",
        ("23", "National", "all", "farmers"): "57.5",
        ("23", "National", "ssf", "farmers"): "56.7",
        ("23", "National", "lsf", "farmers"): "80.2",
        ("29", "National", "all", "irrigation"): "13.1",
        ("29", "National", "ssf", "irrigation"): "11.5",
        ("29", "National", "lsf", "irrigation"): "56.2",
        ("18", "Nyagatare", "ssf", "farmers"): "66.9",
        ("18", "Nyagatare", "lsf", "farmers"): "79.2",
        ("29", "Kirehe", "ssf", "irrigation"): "12.4",
        ("29", "Kirehe", "lsf", "irrigation"): "80.0",
    }
    for (table, geography, farmer, measure), value in expect.items():
        row = require(rows, table=table, geography=geography, farmer_type=farmer, measure=measure)
        if row["value"] != value or row["blank"] != "false":
            raise SystemExit(f"{table} {geography} {farmer} {measure} stored {row['value']!r}, expected {value}")
    blanks = {
        ("18", "Nyarugenge", "lsf", "farmers"): "dash",
        ("18", "Ngororero", "lsf", "farmers"): "dash",
        ("23", "Nyarugenge", "lsf", "farmers"): "empty",
        ("29", "Nyarugenge", "lsf", "irrigation"): "empty",
        ("29", "Rutsiro", "lsf", "irrigation"): "dash",
    }
    for (table, geography, farmer, measure), printed in blanks.items():
        row = require(rows, table=table, geography=geography, farmer_type=farmer, measure=measure)
        if row["blank"] != "true" or row["printed"] != printed:
            raise SystemExit(f"blank failed for {table} {geography} {farmer} {measure}: {row}")


def typed_footers() -> dict[str, dict]:
    if not FOOTERS_OUT.exists():
        return {}
    with FOOTERS_OUT.open(newline="", encoding="utf-8") as handle:
        return {row["table"]: row for row in csv.DictReader(handle)}


def main():
    text_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/sas2026b.txt")
    book_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/tmp/Tables_2026 Season B.xlsx")
    lines = season_a.lines_of(text_path.read_text(encoding="utf-8", errors="replace"))
    sheets = xlsx.sheets(book_path)

    plan = [
        ("18", "Table 18:", FARMER_GROUPS, "all_crops"),
        ("23", "Table 23:", FARMER_GROUPS, "all_crops"),
        ("29", "Table 29:", PRACTICE_GROUPS, ""),
    ]
    rows, footers, compared = [], [], 0
    previous = typed_footers()
    for table, title, groups, crop in plan:
        found = season_a.grid(lines, title, "Gasabo", groups, crop=crop, make=cell)
        width = sum(len(farmers) for _measure, farmers in groups)
        workbook, book_footer = workbook_table(sheets[f"Table {table}"], table, width)
        compared += cross_check(found, table, groups, workbook)
        rows.extend(found)
        typed = previous.get(table, {})
        footers.append({
            "table": table,
            "pdf_page": str(PAGES[table]),
            "pdf_footer": pdf_footer(lines, title),
            "workbook_footer": " ".join(book_footer.split()),
            "footer_on_page": typed.get("footer_on_page", ""),
            "checker": typed.get("checker", ""),
            "checked_on": typed.get("checked_on", ""),
        })
    check(rows)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with CELLS_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    with FOOTERS_OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FOOTER_FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(footers)
    print(f"wrote {len(rows)} cells to {CELLS_OUT}; {compared} agree with the workbook")
    for row in footers:
        flag = "" if row["pdf_footer"] == row["workbook_footer"] else "   <- differs"
        print(f"Table {row['table']}: report '{row['pdf_footer']}', workbook '{row['workbook_footer']}'{flag}")


if __name__ == "__main__":
    main()
