"""District, sector, cell, and village locations.

Village centroids come from the NISR Village Boundary 2022 open-data
layer. A tap on the map is matched to the nearest village inside the
district the simplified outline contains. The outlines are for the map.
They are not used to compute rainfall.
"""

from __future__ import annotations

import csv
import json
import re
from functools import lru_cache
from math import cos, radians
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VILLAGES = ROOT / "data" / "reference" / "villages.csv"
BOUNDARIES = ROOT / "data" / "boundaries" / "rwa_districts.geojson"


def norm(text) -> str:
    text = " ".join(str(text).replace("\u00a0", " ").split()).strip().lower()
    return re.sub(r"[^0-9a-z\s]", " ", text)


def spoken(name: str, text: str) -> bool:
    name = norm(name)
    if len(name) < 3:
        return False
    return re.search(rf"(?<![\w]){re.escape(name)}(?![\w])", text) is not None


@lru_cache(maxsize=1)
def villages() -> tuple[dict, ...]:
    rows = []
    with VILLAGES.open(newline="", encoding="utf-8") as handle:
        for record in csv.DictReader(handle):
            province = record["province"]
            if province == "Estern Province":
                province = "Eastern Province"
            rows.append({
                "province": province,
                "district_id": record["district_id"],
                "district": record["district"],
                "sector_id": record["sector_id"],
                "sector": record["sector"],
                "cell_id": record["cell_id"],
                "cell": record["cell"],
                "village_id": record["village_id"],
                "village": record["village"],
                "lon": float(record["lon"]),
                "lat": float(record["lat"]),
            })
    return tuple(rows)


def _mean(rows: list[dict]) -> dict:
    lon = sum(row["lon"] for row in rows) / len(rows)
    lat = sum(row["lat"] for row in rows) / len(rows)
    return {"lon": round(lon, 5), "lat": round(lat, 5)}


def districts() -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in villages():
        grouped.setdefault(row["district"], []).append(row)
    out = []
    for name in sorted(grouped):
        sample = grouped[name][0]
        out.append({"id": sample["district_id"], "name": name, **_mean(grouped[name])})
    return out


def sectors(district: str) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in villages():
        if row["district"] == district:
            grouped.setdefault(row["sector_id"], []).append(row)
    out = []
    for key in sorted(grouped):
        sample = grouped[key][0]
        out.append({"id": key, "name": sample["sector"], **_mean(grouped[key])})
    return out


def cells(sector_id: str) -> list[dict]:
    grouped: dict[str, list[dict]] = {}
    for row in villages():
        if row["sector_id"] == sector_id:
            grouped.setdefault(row["cell_id"], []).append(row)
    out = []
    for key in sorted(grouped):
        sample = grouped[key][0]
        out.append({"id": key, "name": sample["cell"], **_mean(grouped[key])})
    return out


def villages_in(cell_id: str) -> list[dict]:
    return [dict(row) for row in villages() if row["cell_id"] == cell_id]


def by_id(village_id: str) -> dict | None:
    for row in villages():
        if row["village_id"] == village_id:
            return dict(row)
    return None


def search(query: str, limit: int = 8) -> list[dict]:
    text = norm(query)
    if len(text) < 2:
        return []
    scored = []
    for row in villages():
        village = norm(row["village"])
        sector = norm(row["sector"])
        cell = norm(row["cell"])
        district = norm(row["district"])
        if text == village:
            rank = 0
        elif village.startswith(text):
            rank = 1
        elif text in village or text == sector or text == cell:
            rank = 2
        elif text in sector or text in cell or text == district:
            rank = 3
        else:
            continue
        scored.append((rank, village, row))
    scored.sort(key=lambda item: (item[0], item[1], item[2]["district"]))
    return [dict(row) for _, _, row in scored[:limit]]


def _km(lon1, lat1, lon2, lat2) -> float:
    mid = radians((lat1 + lat2) / 2)
    dx = (lon1 - lon2) * cos(mid) * 111.32
    dy = (lat1 - lat2) * 110.57
    return (dx * dx + dy * dy) ** 0.5


@lru_cache(maxsize=1)
def _rings() -> dict[str, list]:
    payload = json.loads(BOUNDARIES.read_text(encoding="utf-8"))
    found = {}
    for feature in payload["features"]:
        name = feature["properties"]["district"]
        geometry = feature["geometry"]
        polygons = geometry["coordinates"] if geometry["type"] == "MultiPolygon" else [geometry["coordinates"]]
        found[name] = [polygon[0] for polygon in polygons]
    return found


def _inside(lon: float, lat: float, ring) -> bool:
    hit = False
    j = len(ring) - 1
    for i, (xi, yi) in enumerate(ring):
        xj, yj = ring[j]
        if (yi > lat) != (yj > lat) and lon < (xj - xi) * (lat - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def district_at(lon: float, lat: float) -> str | None:
    for name, rings in _rings().items():
        if any(_inside(lon, lat, ring) for ring in rings):
            return name
    return None


def _nearest(lon: float, lat: float, rows) -> tuple[dict, float]:
    best = None
    distance = None
    for row in rows:
        km = _km(lon, lat, row["lon"], row["lat"])
        if distance is None or km < distance:
            best, distance = row, km
    return dict(best), distance


def locate(lon: float, lat: float) -> dict | None:
    """Nearest village. Prefer the district the tap falls inside."""
    district = district_at(lon, lat)
    pool = [row for row in villages() if row["district"] == district] if district else list(villages())
    if not pool:
        pool = list(villages())
    place, distance = _nearest(lon, lat, pool)
    if district is None:
        other, other_km = _nearest(lon, lat, villages())
        if other_km > 25:
            return None
        place, distance = other, other_km
    elif distance > 8:
        other, other_km = _nearest(lon, lat, villages())
        if other_km * 2 < distance:
            place, distance = other, other_km
    place["distance_km"] = round(distance, 2)
    return place


def district_place(name: str) -> dict | None:
    rows = [row for row in villages() if row["district"] == name]
    if not rows:
        return None
    center = _mean(rows)
    return {"district": name, "sector": "", "cell": "", "village": "", "village_id": "", **center}


def sector_place(sector_id: str) -> dict | None:
    rows = [row for row in villages() if row["sector_id"] == sector_id]
    if not rows:
        return None
    sample = rows[0]
    center = _mean(rows)
    return {
        "district": sample["district"],
        "sector": sample["sector"],
        "sector_id": sector_id,
        "cell": "",
        "village": "",
        "village_id": "",
        **center,
    }
