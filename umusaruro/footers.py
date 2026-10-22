"""The Season B footer check.

Workbook Table 29 is titled "2026 Season B" but its footer reads
"Source: NISR, SAS 2025". The evidence contract keeps every Season B
irrigation cell off the screens until a second person resolves that. A
table counts as resolved only when a named person, on a date, typed the
footer they read on the printed page, and it names SAS 2026.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "data" / "season_b_2026" / "footer_check.csv"
EXPECTED = "Source: NISR, SAS 2026"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def normalise(text: str) -> str:
    return " ".join(text.replace("Source :", "Source:").split())


def read(path: Path = PATH) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return {row["table"]: row for row in csv.DictReader(handle)}


def resolved(table: str, path: Path = PATH) -> bool:
    row = read(path).get(table)
    if row is None:
        return False
    return (
        normalise(row["footer_on_page"]) == EXPECTED
        and bool(row["checker"].strip())
        and bool(DATE.match(row["checked_on"].strip()))
    )
