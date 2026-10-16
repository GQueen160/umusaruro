"""Transcribe the Season A 2026 tables named in the evidence contract.

Reads a pdftotext -layout extract. Does not download the PDF. A dash, an
empty column, and a district with no row stay blank. They are not written
as zero.

    pdftotext -layout SAS_2026_Season_A.pdf /tmp/sas2026a.txt
    python tools/transcribe_season_a.py /tmp/sas2026a.txt
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

SOURCE = (
    "https://statistics.gov.rw/sites/default/files/documents/2026-04/"
    "SAS%202026%20Season%20A%20_Final%20Report.pdf"
)
SURVEY = "SAS"
SEASON = "A"
YEAR = "2026"

DISTRICTS = [
    "Nyarugenge",
    "Gasabo",
    "Kicukiro",
    "Nyanza",
    "Gisagara",
    "Nyaruguru",
    "Huye",
    "Nyamagabe",
    "Ruhango",
    "Muhanga",
    "Kamonyi",
    "Karongi",
    "Rutsiro",
    "Rubavu",
    "Nyabihu",
    "Ngororero",
    "Rusizi",
    "Nyamasheke",
    "Rulindo",
    "Gakenke",
    "Musanze",
    "Burera",
    "Gicumbi",
    "Rwamagana",
    "Nyagatare",
    "Gatsibo",
    "Kayonza",
    "Kirehe",
    "Ngoma",
    "Bugesera",
]

YIELD_CROPS = [
    "maize",
    "sorghum",
    "paddy_rice",
    "wheat",
    "other_cereals",
    "cassava",
    "sweet_potatoes",
    "irish_potatoes",
    "yams_taro",
    "bananas",
    "cooking_banana",
    "dessert_banana",
    "banana_for_beer",
    "beans",
    "bush_bean",
    "climbing_bean",
    "peas",
    "ground_nuts",
    "soya_beans",
    "vegetables",
    "fruits",
    "fodder_crops",
    "other_crops",
]

TOKEN = re.compile(r"-|\d[\d,]*\.?\d*")
OUT = Path(__file__).resolve().parents[1] / "data" / "season_a_2026" / "cells.csv"
FIELDS = [
    "survey",
    "season",
    "year",
    "table",
    "geography",
    "farmer_type",
    "crop",
    "measure",
    "value",
    "unit",
    "blank",
    "printed",
    "source_url",
    "checked",
]


def cell(table, geography, farmer_type, crop, measure, raw, unit, printed):
    blank = printed != "number"
    return {
        "survey": SURVEY,
        "season": SEASON,
        "year": YEAR,
        "table": table,
        "geography": geography,
        "farmer_type": farmer_type,
        "crop": crop,
        "measure": measure,
        "value": "" if blank else raw.replace(",", ""),
        "unit": unit,
        "blank": "true" if blank else "false",
        "printed": printed,
        "source_url": SOURCE,
        "checked": "false",
    }


def printed_of(token):
    if token is None:
        return "", "empty"
    if token == "-":
        return "", "dash"
    return token, "number"


def lines_of(text):
    return text.splitlines()


def table_start(lines, title):
    for i, line in enumerate(lines):
        if line.startswith(title) and "...." not in line:
            return i
    raise SystemExit(f"missing {title}")


def yield_rows(lines, title, table, farmer_for_row):
    start = table_start(lines, title)
    found = {}
    for line in lines[start:]:
        if line.startswith("Source"):
            break
        parts = line.split()
        if not parts:
            continue
        name = parts[0]
        if name not in DISTRICTS and name not in {"National", "SSF", "LSF"}:
            continue
        values = parts[1:]
        if len(values) != len(YIELD_CROPS):
            raise SystemExit(f"{title} {name} has {len(values)} values, expected {len(YIELD_CROPS)}")
        found[name] = values
    rows = []
    for name, values in found.items():
        geography, farmer_type = farmer_for_row(name)
        for crop, token in zip(YIELD_CROPS, values):
            raw, printed = printed_of(token)
            rows.append(cell(table, geography, farmer_type, crop, "yield", raw, "kg_per_ha", printed))
    return found, rows


def farmer_table_13(name):
    if name == "SSF":
        return "National", "ssf"
    if name == "LSF":
        return "National", "lsf"
    if name == "National":
        return "National", "all"
    return name, "all"


def farmer_table_14(name):
    if name == "National":
        return "National", "lsf"
    return name, "lsf"


def tokens(line):
    return [(m.start(), m.end(), m.group()) for m in TOKEN.finditer(line)]


def assign_columns(line, edges):
    columns = [None] * len(edges)
    for _start, end, token in tokens(line):
        index = min(range(len(edges)), key=lambda i: abs(edges[i] - end))
        distance = abs(edges[index] - end)
        if columns[index] is not None or distance > 5:
            raise SystemExit(f"column assign failed at {token!r} on {line.strip()[:80]}")
        columns[index] = token
    return columns


def grid(lines, title, reference_name, groups, crop=""):
    """groups is a list of (measure, [farmer_type, ...]) matching header order."""
    start = table_start(lines, title)
    block = []
    for line in lines[start + 1 :]:
        if line.startswith("Source"):
            break
        block.append(line)
    reference = next(line for line in block if line.split()[:1] == [reference_name])
    edges = [end for _s, end, _t in tokens(reference)]
    width = sum(len(farmers) for _measure, farmers in groups)
    if len(edges) != width:
        raise SystemExit(f"{title} reference width {len(edges)} != {width}")
    rows = []
    seen = []
    for line in block:
        parts = line.split()
        if not parts or parts[0] not in DISTRICTS + ["National"]:
            continue
        name = parts[0]
        seen.append(name)
        columns = assign_columns(line, edges)
        cursor = 0
        for measure, farmers in groups:
            for farmer in farmers:
                token = columns[cursor]
                cursor += 1
                raw, printed = printed_of(token)
                rows.append(
                    cell(title_table(title), name if name != "National" else "National", farmer, crop, measure, raw, "percent", printed)
                )
    if seen != DISTRICTS + ["National"]:
        raise SystemExit(f"{title} row order {seen}")
    return rows


def title_table(title):
    number = title.split()[1].rstrip(":")
    return number


def prefixed_rows(lines, title, labels, measures, unit, geography="National"):
    start = table_start(lines, title)
    table = title_table(title)
    wanted = sorted(labels, key=len, reverse=True)
    rows = []
    seen = []
    for line in lines[start + 1 :]:
        if line.startswith("Source"):
            break
        stripped = line.strip()
        label = next((name for name in wanted if stripped.startswith(name + " ") or stripped == name), None)
        if label is None:
            continue
        rest = stripped[len(label) :].split()
        if len(rest) != len(measures):
            raise SystemExit(f"{title} {label} has {rest}")
        seen.append(label)
        crop = "all_crops" if label == "National" else slug(label)
        for measure, token in zip(measures, rest):
            raw, printed = printed_of(token)
            rows.append(cell(table, geography, "all", crop, measure, raw, unit, printed))
    if seen != labels:
        raise SystemExit(f"{title} labels {seen}")
    return rows


def slug(label):
    return (
        label.lower()
        .replace("&", "")
        .replace("  ", " ")
        .replace(" ", "_")
        .replace("__", "_")
    )


def seed_source_rows(lines):
    start = table_start(lines, "Table 22:")
    measures = [
        "government",
        "recognized_seed_multipliers",
        "agro_dealers",
        "ngos",
        "market",
        "agriculture_cooperative",
        "other",
        "total",
    ]
    rows = []
    seen = []
    for line in lines[start + 1 :]:
        if line.startswith("Source"):
            break
        parts = line.split()
        if not parts or parts[0] not in DISTRICTS + ["National"]:
            continue
        name, values = parts[0], parts[1:]
        if len(values) != len(measures):
            raise SystemExit(f"Table 22 {name} has {values}")
        seen.append(name)
        for measure, token in zip(measures, values):
            raw, printed = printed_of(token)
            rows.append(cell("22", name, "all", "all_crops", measure, raw, "percent", printed))
    if seen != DISTRICTS + ["National"]:
        raise SystemExit(f"Table 22 order {seen}")
    return rows


def absent_lsf_yields():
    rows = []
    for crop in YIELD_CROPS:
        rows.append(cell("14", "Nyarugenge", "lsf", crop, "yield", "", "kg_per_ha", "absent"))
    return rows


def require(rows, **query):
    hits = [row for row in rows if all(row[key] == value for key, value in query.items())]
    if len(hits) != 1:
        raise SystemExit(f"expected one row for {query}, found {len(hits)}")
    return hits[0]


def check(rows):
    expect = {
        ("13", "Nyagatare", "all", "maize", "yield"): "2887",
        ("13", "Kirehe", "all", "maize", "yield"): "2515",
        ("13", "Kamonyi", "all", "maize", "yield"): "1863",
        ("13", "National", "all", "maize", "yield"): "1994",
        ("13", "National", "ssf", "maize", "yield"): "1897",
        ("13", "National", "lsf", "maize", "yield"): "4337",
        ("13", "National", "all", "beans", "yield"): "700",
        ("13", "National", "lsf", "beans", "yield"): "542",
        ("14", "Kamonyi", "lsf", "maize", "yield"): "6470",
        ("14", "Nyagatare", "lsf", "maize", "yield"): "5292",
        ("14", "National", "lsf", "maize", "yield"): "4337",
        ("20", "Nyagatare", "ssf", "all_crops", "farmers"): "53.8",
        ("20", "Nyagatare", "lsf", "all_crops", "farmers"): "92.9",
        ("20", "Kamonyi", "ssf", "all_crops", "farmers"): "45.3",
        ("20", "Kamonyi", "lsf", "all_crops", "farmers"): "100.0",
        ("20", "National", "ssf", "all_crops", "farmers"): "35.2",
        ("20", "National", "lsf", "all_crops", "farmers"): "82.6",
        ("20", "Rwamagana", "ssf", "all_crops", "farmers"): "53.6",
        ("20", "Rwamagana", "lsf", "all_crops", "farmers"): "78.1",
        ("25", "Nyagatare", "ssf", "all_crops", "farmers"): "67.9",
        ("25", "Nyagatare", "lsf", "all_crops", "farmers"): "91.7",
        ("25", "Kamonyi", "ssf", "all_crops", "farmers"): "47.2",
        ("25", "Kamonyi", "lsf", "all_crops", "farmers"): "93.3",
        ("25", "Gakenke", "ssf", "all_crops", "farmers"): "85.1",
        ("25", "Gakenke", "lsf", "all_crops", "farmers"): "66.7",
        ("25", "Kirehe", "ssf", "all_crops", "farmers"): "76.0",
        ("25", "Kirehe", "lsf", "all_crops", "farmers"): "92.9",
        ("31", "National", "all", "", "irrigation"): "14.4",
        ("31", "National", "ssf", "", "irrigation"): "12.6",
        ("31", "National", "lsf", "", "irrigation"): "60.3",
        ("31", "Nyagatare", "ssf", "", "irrigation"): "6.4",
        ("31", "Nyagatare", "lsf", "", "irrigation"): "50.0",
        ("31", "Kirehe", "ssf", "", "irrigation"): "14.9",
        ("31", "Kirehe", "lsf", "", "irrigation"): "78.6",
        ("31", "Kamonyi", "ssf", "", "irrigation"): "22.4",
        ("31", "Kamonyi", "lsf", "", "irrigation"): "93.3",
        ("16", "National", "all", "maize", "post_harvest_loss"): "0.3",
        ("16", "National", "all", "maize", "other"): "0.2",
        ("21", "National", "all", "maize", "improved"): "64.3",
        ("21", "National", "all", "bush_bean", "improved"): "0.5",
    }
    for key, value in expect.items():
        table, geography, farmer, crop, measure = key
        row = require(rows, table=table, geography=geography, farmer_type=farmer, crop=crop, measure=measure)
        if row["value"] != value or row["blank"] != "false":
            raise SystemExit(f"{key} stored {row['value']!r}, expected {value}")
    blanks = {
        ("14", "Karongi", "lsf", "maize", "yield"): "dash",
        ("14", "Nyarugenge", "lsf", "maize", "yield"): "absent",
        ("20", "Nyarugenge", "lsf", "all_crops", "farmers"): "empty",
        ("20", "Karongi", "lsf", "all_crops", "farmers"): "dash",
        ("31", "Gicumbi", "lsf", "", "irrigation"): "dash",
        ("31", "Nyarugenge", "lsf", "", "irrigation"): "empty",
    }
    for key, printed in blanks.items():
        table, geography, farmer, crop, measure = key
        row = require(rows, table=table, geography=geography, farmer_type=farmer, crop=crop, measure=measure)
        if row["blank"] != "true" or row["value"] != "" or row["printed"] != printed:
            raise SystemExit(f"blank failed for {key}: {row}")
    districts_13 = {row["geography"] for row in rows if row["table"] == "13" and row["crop"] == "maize" and row["farmer_type"] == "all" and row["geography"] != "National"}
    if districts_13 != set(DISTRICTS):
        raise SystemExit(f"table 13 districts {sorted(districts_13)}")
    above = [
        row["geography"]
        for row in rows
        if row["table"] == "13" and row["crop"] == "maize" and row["farmer_type"] == "all" and row["geography"] != "National" and int(row["value"]) >= 2260
    ]
    if sorted(above) != ["Kirehe", "Nyagatare"]:
        raise SystemExit(f"districts at or above 2.26 t/ha: {above}")


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/sas2026a.txt")
    lines = lines_of(path.read_text(encoding="utf-8", errors="replace"))
    _found13, rows13 = yield_rows(lines, "Table 13:", "13", farmer_table_13)
    found14, rows14 = yield_rows(lines, "Table 14:", "14", farmer_table_14)
    if set(DISTRICTS) - set(found14) != {"Nyarugenge"}:
        raise SystemExit(f"unexpected missing large-farm districts: {set(DISTRICTS) - set(found14)}")
    farmer_groups = [
        ("farmers", ["all", "ssf", "lsf"]),
        ("plots", ["all", "ssf", "lsf"]),
        ("land", ["all", "ssf", "lsf"]),
    ]
    practice_groups = [
        ("erosion", ["all", "ssf", "lsf"]),
        ("mechanization", ["all", "ssf", "lsf"]),
        ("irrigation", ["all", "ssf", "lsf"]),
        ("agroforestry", ["all", "ssf", "lsf"]),
    ]
    use_labels = [
        "Maize",
        "Sorghum",
        "Paddy rice",
        "Wheat",
        "Other cereals",
        "Sweet potato",
        "Irish potato",
        "Yam & Taro",
        "Cassava",
        "Bush bean",
        "Climbing bean",
        "Pea",
        "Groundnut",
        "Soybean",
        "Cooking banana",
        "Dessert banana",
        "Banana for beer",
        "Vegetables",
        "Fruits",
        "Fodder crops",
        "Other crops",
    ]
    seed_labels = [
        "Maize",
        "Paddy rice",
        "Wheat",
        "Irish potato",
        "Cassava",
        "Bush bean",
        "Climbing bean",
        "Pea",
        "Soybean",
        "Cooking banana",
        "Dessert banana",
        "Banana for beer",
        "Vegetables",
        "Fruits",
        "Fodder crops",
        "Other crops",
        "National",
    ]
    rows = []
    rows.extend(rows13)
    rows.extend(rows14)
    rows.extend(absent_lsf_yields())
    rows.extend(
        prefixed_rows(
            lines,
            "Table 16:",
            use_labels,
            ["sold", "own_consumption", "wages", "farm_rent", "gift", "barter", "seeds", "fodder", "stored", "post_harvest_loss", "other"],
            "percent",
        )
    )
    rows.extend(grid(lines, "Table 20:", "Gasabo", farmer_groups, crop="all_crops"))
    rows.extend(
        prefixed_rows(lines, "Table 21:", seed_labels, ["traditional", "improved", "total"], "percent")
    )
    rows.extend(seed_source_rows(lines))
    rows.extend(grid(lines, "Table 25:", "Gasabo", farmer_groups, crop="all_crops"))
    rows.extend(grid(lines, "Table 31:", "Gasabo", practice_groups))
    check(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    print(f"wrote {len(rows)} cells to {OUT}")


if __name__ == "__main__":
    main()
