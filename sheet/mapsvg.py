"""Draw the district map as inline SVG from the simplified outlines.

The outlines come from `data/boundaries/rwa_districts.geojson`, written by
`tools/district_map.py`. They only draw shapes. No statistic is computed
from them.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

BOUNDARIES = Path(__file__).resolve().parents[1] / "data" / "boundaries" / "rwa_districts.geojson"
WIDTH = 800.0
PAD = 8.0


@dataclass(frozen=True)
class Shape:
    district: str
    path: str
    x: float
    y: float


@dataclass(frozen=True)
class Outline:
    width: int
    height: int
    shapes: dict[str, Shape]
    license: str
    source: str


@lru_cache(maxsize=1)
def outline() -> Outline:
    collection = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
    features = collection["features"]
    points = [p for f in features for poly in f["geometry"]["coordinates"] for ring in poly for p in ring]
    lons = [p[0] for p in points]
    lats = [p[1] for p in points]
    squeeze = math.cos(math.radians((min(lats) + max(lats)) / 2))
    span_x = (max(lons) - min(lons)) * squeeze
    span_y = max(lats) - min(lats)
    scale = (WIDTH - 2 * PAD) / span_x
    height = span_y * scale + 2 * PAD

    def project(lon: float, lat: float) -> tuple[float, float]:
        return PAD + (lon - min(lons)) * squeeze * scale, PAD + (max(lats) - lat) * scale

    shapes = {}
    for feature in features:
        name = feature["properties"]["district"]
        commands = []
        biggest, centre = 0, (0.0, 0.0)
        for polygon in feature["geometry"]["coordinates"]:
            for ring in polygon:
                xy = [project(lon, lat) for lon, lat in ring]
                commands.append("M" + "L".join(f"{x:.1f},{y:.1f}" for x, y in xy) + "Z")
            outer = [project(lon, lat) for lon, lat in polygon[0]]
            if len(outer) > biggest:
                biggest = len(outer)
                centre = (sum(x for x, _ in outer) / len(outer), sum(y for _, y in outer) / len(outer))
        shapes[name] = Shape(name, "".join(commands), round(centre[0], 1), round(centre[1], 1))
    return Outline(int(WIDTH), int(math.ceil(height)), shapes, collection["license"], collection["catalog"])
