"""Official NISR village locations for the farmer map.

Reads the open-data Village Boundary 2022 layer and keeps a centroid for
each village, not the polygon. The map flies to that point. Survey numbers
still come from the district tables.

    python tools/fetch_villages.py
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

QUERY = (
    "https://services5.arcgis.com/deNm5epdmeZgcm16/arcgis/rest/services/"
    "Village_Boundary_2022/FeatureServer/3/query"
)
OUT = Path(__file__).resolve().parents[1] / "data" / "reference" / "villages.csv"
FIELDS = [
    "province_id", "province", "district_id", "district", "sector_id", "sector",
    "cell_id", "cell", "village_id", "village", "lon", "lat",
]
PAGE = 2000


def fetch(offset: int) -> dict:
    params = {
        "where": "1=1",
        "outFields": "province,province_id,district,district_id,sector,sector_id,cell,cell_id,village,village_id",
        "returnCentroid": "true",
        "returnGeometry": "false",
        "orderByFields": "village_id",
        "resultOffset": str(offset),
        "resultRecordCount": str(PAGE),
        "f": "json",
    }
    url = QUERY + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=90) as response:
        return json.load(response)


def rows_of(payload: dict) -> list[dict]:
    rows = []
    for feature in payload["features"]:
        item = feature["attributes"]
        center = feature["centroid"]
        row = {key: str(item[key]).strip() for key in FIELDS if key not in ("lon", "lat")}
        row["lon"] = f"{float(center['x']):.5f}"
        row["lat"] = f"{float(center['y']):.5f}"
        if not (row["village_id"].startswith(row["cell_id"]) and row["cell_id"].startswith(row["sector_id"])
                and row["sector_id"].startswith(row["district_id"])):
            raise SystemExit(f"codes do not nest: {row['village_id']}")
        rows.append(row)
    return rows


def main():
    found: list[dict] = []
    offset = 0
    while True:
        payload = fetch(offset)
        page = rows_of(payload)
        if not page:
            break
        found.extend(page)
        print(f"{len(found)} villages", file=sys.stderr)
        if len(page) < PAGE:
            break
        offset += PAGE
    ids = {row["village_id"] for row in found}
    if len(ids) != len(found):
        raise SystemExit("duplicate village codes")
    if len(found) < 10000:
        raise SystemExit(f"expected the national village list, found {len(found)}")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(found)
    print(f"wrote {len(found)} villages to {OUT}")


if __name__ == "__main__":
    main()
