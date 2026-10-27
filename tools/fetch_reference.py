"""Official NISR codes for provinces, districts and sectors.

Reads the attribute table of the NISR Sector Boundary 2022 layer (no
geometry) and writes two files:

    data/reference/sectors.csv    one row per sector, 416 rows
    data/reference/districts.csv  one row per district, 30 rows

Every cleaned table joins on district_id, never on a spelled name. The
district names must equal the 30 names printed in the SAS tables.

    python tools/fetch_reference.py
"""

from __future__ import annotations

import csv
import json
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.transcribe_season_a import DISTRICTS  # noqa: E402

LAYER = "https://services5.arcgis.com/deNm5epdmeZgcm16/arcgis/rest/services/Sector_Boundary_2022/FeatureServer/1"
QUERY = (LAYER + "/query?where=1%3D1&outFields=province,province_id,district,district_id,sector,sector_id"
         "&returnGeometry=false&orderByFields=sector_id&f=json")
OUT = Path(__file__).resolve().parents[1] / "data" / "reference"
SECTOR_FIELDS = ["province_id", "province", "district_id", "district", "sector_id", "sector"]
DISTRICT_FIELDS = ["province_id", "province", "district_id", "district", "sectors"]


def fetch(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def tidy(features: list[dict]) -> list[dict]:
    rows = []
    for feature in features:
        a = {key: str(value).strip() for key, value in feature["attributes"].items()}
        if not (a["sector_id"].startswith(a["district_id"]) and a["district_id"].startswith(a["province_id"])):
            raise SystemExit(f"codes do not nest: {a}")
        rows.append({field: a[field] for field in SECTOR_FIELDS})
    return sorted(rows, key=lambda row: row["sector_id"])


def districts_of(sectors: list[dict]) -> list[dict]:
    out = {}
    for row in sectors:
        entry = out.setdefault(row["district_id"], {field: row[field] for field in DISTRICT_FIELDS[:-1]} | {"sectors": 0})
        if entry["district"] != row["district"]:
            raise SystemExit(f"district {row['district_id']} has two names")
        entry["sectors"] += 1
    return [out[key] for key in sorted(out)]


def check(sectors: list[dict], districts: list[dict]) -> None:
    if len(sectors) != 416 or len({row["sector_id"] for row in sectors}) != 416:
        raise SystemExit(f"expected 416 distinct sectors, found {len(sectors)}")
    if [row["district"] for row in districts] != DISTRICTS:
        raise SystemExit("district names or order differ from the SAS tables")


def write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main():
    payload = fetch(QUERY)
    if payload.get("exceededTransferLimit"):
        raise SystemExit("the layer returned a partial page")
    sectors = tidy(payload["features"])
    districts = districts_of(sectors)
    check(sectors, districts)
    OUT.mkdir(parents=True, exist_ok=True)
    write(OUT / "sectors.csv", SECTOR_FIELDS, sectors)
    write(OUT / "districts.csv", DISTRICT_FIELDS, districts)
    print(f"wrote {len(sectors)} sectors and {len(districts)} districts to {OUT}")


if __name__ == "__main__":
    main()
