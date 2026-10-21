"""District rainfall totals for the irrigation gate.

Sums CHIRPS v2.0 Africa monthly rainfall from September 2025 through
February 2026. A district's total is the mean of the six-month sums at the
grid cells whose centres fall inside the district. The cell count is
written beside the total, so a district resting on a handful of cells is
visible. A district with no cell centre inside it stops the run.

Needs rasterio, shapely, and numpy. The raster files and the boundary file
are not committed.

    python tools/chirps_gate.py /tmp/chirps /tmp/chirps/rwa_adm2.geojson
"""

from __future__ import annotations

import csv
import gzip
import json
import shutil
import sys
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from statistics import median

import numpy as np
import rasterio
from rasterio.windows import from_bounds
from shapely import contains_xy
from shapely.geometry import shape

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.transcribe_season_a import DISTRICTS  # noqa: E402

MONTHS = ["2025.09", "2025.10", "2025.11", "2025.12", "2026.01", "2026.02"]
VERSION = "CHIRPS v2.0"
SOURCE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/"
BOUNDARY_SOURCE = "https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/"
OUT = Path(__file__).resolve().parents[1] / "data" / "chirps" / "season_a_2026_rainfall.csv"
RWANDA = (28.8, -2.9, 31.0, -1.0)


def unpack(folder: Path, month: str) -> Path:
    tif = folder / f"chirps-v2.0.{month}.tif"
    packed = folder / f"chirps-v2.0.{month}.tif.gz"
    if not tif.exists():
        with gzip.open(packed, "rb") as source, tif.open("wb") as target:
            shutil.copyfileobj(source, target)
    return tif


def six_month_sum(folder: Path):
    total = None
    transform = None
    for month in MONTHS:
        with rasterio.open(unpack(folder, month)) as raster:
            window = from_bounds(*RWANDA, transform=raster.transform)
            band = raster.read(1, window=window, masked=True)
            if transform is None:
                transform = raster.window_transform(window)
            elif raster.window_transform(window) != transform:
                raise SystemExit(f"{month} grid differs from {MONTHS[0]}")
            total = band if total is None else total + band
    return total, transform


def district_name(feature) -> str:
    name = feature["properties"]["shapeName"].strip()
    return name.removesuffix(" District").strip()


def totals(folder: Path, boundaries: Path):
    grid, transform = six_month_sum(folder)
    rows, cols = np.indices(grid.shape)
    xs, ys = rasterio.transform.xy(transform, rows.ravel(), cols.ravel(), offset="center")
    xs = np.asarray(xs)
    ys = np.asarray(ys)
    values = grid.ravel()
    features = json.loads(boundaries.read_text(encoding="utf-8"))["features"]
    found = {}
    for feature in features:
        name = district_name(feature)
        inside = contains_xy(shape(feature["geometry"]), xs, ys)
        cells = values[inside]
        if cells.size == 0:
            raise SystemExit(f"{name} has no CHIRPS cell centre inside it")
        if np.ma.count_masked(cells):
            raise SystemExit(f"{name} has a CHIRPS cell with no data")
        found[name] = (float(cells.mean()), int(cells.size))
    if set(found) != set(DISTRICTS):
        raise SystemExit(f"boundary names differ: {sorted(set(found) ^ set(DISTRICTS))}")
    return found


def one_decimal(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)


def main():
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/chirps")
    boundaries = Path(sys.argv[2]) if len(sys.argv) > 2 else folder / "rwa_adm2.geojson"
    found = totals(folder, boundaries)
    rounded = {name: one_decimal(total) for name, (total, _cells) in found.items()}
    middle = Decimal(str(median(rounded.values()))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(
            ["district", "total_mm", "cells", "median_mm", "below_median", "months", "version", "source_url", "boundary_url"]
        )
        for name in DISTRICTS:
            writer.writerow(
                [
                    name,
                    rounded[name],
                    found[name][1],
                    middle,
                    "true" if rounded[name] < middle else "false",
                    "2025-09/2026-02",
                    VERSION,
                    SOURCE,
                    BOUNDARY_SOURCE,
                ]
            )
    print(f"wrote {OUT}, median {middle} mm")


if __name__ == "__main__":
    main()
