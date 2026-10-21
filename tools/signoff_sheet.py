"""Write the blank sign-off sheet for the second-person check.

Refuses to overwrite a sheet that already has typed values.

    python3 tools/signoff_sheet.py
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from umusaruro.signoff import SHEET_PATH, blank_sheet, read_sheet, write_sheet  # noqa: E402


def main():
    if SHEET_PATH.exists() and any(row["value_on_page"].strip() for row in read_sheet()):
        raise SystemExit(f"{SHEET_PATH} already has typed values")
    rows = blank_sheet()
    write_sheet(rows)
    print(f"wrote {len(rows)} rows to {SHEET_PATH}")


if __name__ == "__main__":
    main()
