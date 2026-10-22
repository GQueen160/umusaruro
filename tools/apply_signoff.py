"""Compare the typed sign-off values with the cell files, Season A and Season B.

Marks a cell checked only when the typed value matches. Writes nothing, for
either season, if any typed value disagrees, or if a typed row has no
checker or date.

    python3 tools/apply_signoff.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from umusaruro.cells import load  # noqa: E402
from umusaruro.signoff import SEASONS, read_sheet, review  # noqa: E402


def main():
    results = []
    failed = False
    for season in SEASONS:
        cells = load(season.cells_path)
        result = review(cells, read_sheet(season.sheet_path))
        results.append((season, result))
        for key in result.incomplete:
            failed = True
            print(f"Season {season.name}, no checker or date: table {key.table} {key.geography} "
                  f"{key.farmer_type} {key.crop} {key.measure}")
        for key, typed in result.mismatched:
            failed = True
            stored = cells.get(key.table, key.geography, key.farmer_type, key.crop, key.measure)
            shown = "-" if stored.blank else stored.value
            print(f"Season {season.name}, mismatch: table {key.table} {key.geography} {key.farmer_type} "
                  f"{key.crop} {key.measure}: typed {typed}, file {shown}")
    if failed:
        raise SystemExit("nothing written; resolve the rows above against the PDF")

    for season, result in results:
        matched = {(k.table, k.geography, k.farmer_type, k.crop, k.measure) for k in result.matched}
        with season.cells_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            fields = reader.fieldnames
            records = list(reader)
        for record in records:
            key = (record["table"], record["geography"], record["farmer_type"], record["crop"], record["measure"])
            record["checked"] = "true" if key in matched else "false"
        with season.cells_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
            writer.writeheader()
            writer.writerows(records)
        print(f"Season {season.name}: {len(matched)} cells checked, {result.pending} still to type")


if __name__ == "__main__":
    main()
