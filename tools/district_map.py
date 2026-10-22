"""Simplified district outlines for the map.

Reads the geoBoundaries Rwanda ADM2 file used by the rainfall gate and
writes a small GeoJSON with one feature per Season A district. Rings are
simplified with Douglas-Peucker at 0.002 degrees (about 220 m), and
coordinates are rounded to four decimals. The outlines only draw the map.
Nothing is computed from them.

Standard library only.

    python tools/district_map.py /tmp/umap/rwa_adm2.geojson
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tools.transcribe_season_a import DISTRICTS  # noqa: E402

BOUNDARY_SOURCE = "https://www.geoboundaries.org/api/current/gbOpen/RWA/ADM2/"
PINNED = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/RWA/ADM2/geoBoundaries-RWA-ADM2.geojson"
TOLERANCE = 0.002
OUT = Path(__file__).resolve().parents[1] / "data" / "boundaries" / "rwa_districts.geojson"


def _distance(point, start, end) -> float:
    (x, y), (x1, y1), (x2, y2) = point, start, end
    dx, dy = x2 - x1, y2 - y1
    if dx == 0 and dy == 0:
        return ((x - x1) ** 2 + (y - y1) ** 2) ** 0.5
    t = max(0.0, min(1.0, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
    return ((x - x1 - t * dx) ** 2 + (y - y1 - t * dy) ** 2) ** 0.5


def simplify(points: list, tolerance: float) -> list:
    keep = [False] * len(points)
    keep[0] = keep[-1] = True
    stack = [(0, len(points) - 1)]
    while stack:
        first, last = stack.pop()
        far, index = 0.0, None
        for i in range(first + 1, last):
            d = _distance(points[i], points[first], points[last])
            if d > far:
                far, index = d, i
        if index is not None and far > tolerance:
            keep[index] = True
            stack.extend([(first, index), (index, last)])
    return [p for p, k in zip(points, keep) if k]


def simplify_ring(ring: list) -> list | None:
    # A closed ring's first and last points coincide, so split it at the
    # point farthest from the start; otherwise the whole ring collapses.
    start = ring[0]
    far = max(range(len(ring)), key=lambda i: (ring[i][0] - start[0]) ** 2 + (ring[i][1] - start[1]) ** 2)
    half = simplify(ring[: far + 1], TOLERANCE) + simplify(ring[far:], TOLERANCE)[1:]
    out = [[round(x, 4), round(y, 4)] for x, y in half]
    deduped = [p for i, p in enumerate(out) if i == 0 or p != out[i - 1]]
    return deduped if len(deduped) >= 4 else None


def district_name(feature) -> str:
    return feature["properties"]["shapeName"].strip().removesuffix(" District").strip()


def polygons(geometry) -> list:
    if geometry["type"] == "Polygon":
        return [geometry["coordinates"]]
    if geometry["type"] == "MultiPolygon":
        return geometry["coordinates"]
    raise SystemExit(f"unexpected geometry {geometry['type']}")


def main():
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/umap/rwa_adm2.geojson")
    features = json.loads(source.read_text(encoding="utf-8"))["features"]
    found = {}
    for feature in features:
        name = district_name(feature)
        shapes = []
        for polygon in polygons(feature["geometry"]):
            outer = simplify_ring(polygon[0])
            if outer is None:
                continue
            holes = [h for h in (simplify_ring(r) for r in polygon[1:]) if h]
            shapes.append([outer, *holes])
        if not shapes:
            raise SystemExit(f"{name} vanished when simplified")
        found[name] = shapes
    if set(found) != set(DISTRICTS):
        raise SystemExit(f"boundary names differ: {sorted(set(found) ^ set(DISTRICTS))}")
    collection = {
        "type": "FeatureCollection",
        "source": PINNED,
        "catalog": BOUNDARY_SOURCE,
        "license": "geoBoundaries gbOpen RWA ADM2, from Open Data Rwanda, CC BY 4.0",
        "simplified": f"Douglas-Peucker {TOLERANCE} degrees, 4 decimals",
        "features": [
            {
                "type": "Feature",
                "properties": {"district": name},
                "geometry": {"type": "MultiPolygon", "coordinates": found[name]},
            }
            for name in DISTRICTS
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(collection, separators=(",", ":")) + "\n", encoding="utf-8")
    points = sum(len(r) for shapes in found.values() for p in shapes for r in p)
    print(f"wrote {OUT}, {points} points")


if __name__ == "__main__":
    main()
