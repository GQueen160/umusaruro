"""Write the blank sign-off sheets for the second-person check.

Skips a season whose sheet already has typed values.

    python3 tools/signoff_sheet.py        # both seasons
    python3 tools/signoff_sheet.py B      # Season B only
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from umusaruro.signoff import SEASONS, read_sheet, write_sheet  # noqa: E402


def main():
    wanted = set(sys.argv[1:]) or {season.name for season in SEASONS}
    for season in SEASONS:
        if season.name not in wanted:
            continue
        path = season.sheet_path
        if path.exists() and any(row["value_on_page"].strip() for row in read_sheet(path)):
            print(f"Season {season.name}: {path} already has typed values; left as is")
            continue
        rows = season.blank_sheet()
        write_sheet(rows, path)
        print(f"Season {season.name}: wrote {len(rows)} rows to {path}")


if __name__ == "__main__":
    main()
