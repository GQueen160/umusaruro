"""Season A back-series, 2019 to 2026, from the NISR SAS workbooks.

For each year the workbook named in data/raw/MANIFEST.csv is read, and five
district tables are cleaned into one tidy file:

    maize_yield      average maize yield, all farmers           (kg/ha)
    maize_yield_lsf  average maize yield, large-scale farmers   (kg/ha; t/ha in 2019)
    seed             farmers who used improved seed             (%: overall, SSF, LSF)
    fertilizer       farmers who used inorganic fertilizer      (%: overall, SSF, LSF)
    irrigation       farmers who practised irrigation           (%: overall, SSF, LSF)

Table numbers change every year, and so do the headers. Columns are found by
their header text, never by position, and a table whose columns cannot be
found exactly once stops the build.

Rules, the same as for the printed tables:
  * A value is rounded to the digits the reports print: whole kg/ha, one
    decimal for percentages. The workbook value is kept beside it.
  * An empty cell, a dash, or a zero is a blank. NISR prints workbook zeros
    as a dash (checked in Season B 2026 and below for Season A 2026).
  * Every row joins on the official NISR district_id.

Checks that must pass before anything is written:
  * 30 districts in every table (a large-farm table may leave a district out)
  * percentages within 0 to 100, yields above zero
  * the national value lies within the district range
  * the national large-farm yield is the same in both yield tables
  * every 2026 value equals the printed 2026 report cell (data/season_a_2026)

    python tools/build_history.py
"""

from __future__ import annotations

import csv
import sys
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from umusaruro import xlsx  # noqa: E402

RAW = ROOT / "data" / "raw"
OUT_DIR = ROOT / "data" / "history"
OUT = OUT_DIR / "season_a.csv"
QUALITY = OUT_DIR / "quality.csv"
DISTRICTS_CSV = ROOT / "data" / "reference" / "districts.csv"
PRINTED_2026 = ROOT / "data" / "season_a_2026" / "cells.csv"

FIELDS = ["year", "season", "lever", "district_id", "geography", "farmer_type", "value", "unit",
          "blank", "printed", "workbook_value", "table", "source_url", "landing_page"]
QUALITY_FIELDS = ["year", "lever", "table", "title", "farmer_type", "numbers", "blanks", "absent", "national",
                  "district_min", "district_max"]

PLAN = {
    2019: ("sas_2019_annual_tables.xlsx", {"maize_yield": "13", "maize_yield_lsf": "16", "seed": "28", "fertilizer": "37", "irrigation": "48"}),
    2020: ("sas_2020_tables.xlsx", {"maize_yield": "14", "maize_yield_lsf": "17", "seed": "29", "fertilizer": "38", "irrigation": "52"}),
    2021: ("sas_2021_tables.xlsx", {"maize_yield": "17", "maize_yield_lsf": "21", "seed": "33", "fertilizer": "42", "irrigation": "56"}),
    2022: ("sas_2022_tables.xlsx", {"maize_yield": "17", "maize_yield_lsf": "20", "seed": "32", "fertilizer": "41", "irrigation": "55"}),
    2023: ("sas_2023_annual_tables.xlsx", {"maize_yield": "16", "maize_yield_lsf": "19", "seed": "31", "fertilizer": "44", "irrigation": "62"}),
    2024: ("sas_2024_season_a_tables.xlsx", {"maize_yield": "11", "maize_yield_lsf": "12", "seed": "18", "fertilizer": "23", "irrigation": "29"}),
    2025: ("sas_2025_season_a_tables.xlsx", {"maize_yield": "12", "maize_yield_lsf": "13", "seed": "19", "fertilizer": "24", "irrigation": "30"}),
    2026: ("sas_2026_season_a_tables.xlsx", {"maize_yield": "13", "maize_yield_lsf": "14", "seed": "20", "fertilizer": "25", "irrigation": "31"}),
}
PRINTED_2026_TABLES = {"maize_yield": ("yield", "maize"), "maize_yield_lsf": ("yield", "maize"),
                       "seed": ("farmers", "all_crops"), "fertilizer": ("farmers", "all_crops"), "irrigation": ("irrigation", "")}

FARMER_TYPES = {"overall": "all", "ssf": "ssf", "lsf": "lsf"}
ANSWERS = {"yes", "no", "traditional", "improved"}
WANTED_ANSWER = {"seed": "improved", "fertilizer": "yes", "irrigation": "yes"}
NATIONAL_LABELS = {
    "national": "all", "total": "all",
    "ssf": "ssf", "small scale farmer": "ssf", "small scale farmers": "ssf",
    "lsf": "lsf", "larger scale farmer": "lsf", "large scale farmer": "lsf", "national_lsf": "lsf",
}


@dataclass
class Table:
    number: str
    title: str
    label_col: int
    header: list[list[str]]
    districts: dict[str, list]
    national: dict[str, list]


def districts() -> list[dict]:
    with DISTRICTS_CSV.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def manifest() -> dict[str, dict]:
    with (RAW / "MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
        return {Path(row["path"]).name: row for row in csv.DictReader(handle)}


def text(value) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def find_sheet(book: dict[str, list[list]], number: str) -> list[list]:
    if f"Table {number}" in book:
        return book[f"Table {number}"]
    for rows in book.values():
        for row in rows[:3]:
            if any(text(v).startswith(f"Table {number}:") for v in row):
                return rows
    raise SystemExit(f"no sheet for Table {number}")


def parse(rows: list[list], number: str, names: set[str]) -> Table:
    title = next(i for i, row in enumerate(rows) if any(text(v).startswith(f"Table {number}") for v in row))
    first = None
    label_col = None
    found, national = {}, {}
    for i, row in enumerate(rows[title + 1 :], start=title + 1):
        labels = [(j, text(v)) for j, v in enumerate(row) if text(v)]
        if not labels:
            continue
        j, label = labels[0]
        if label in names:
            first = i if first is None else first
            label_col = j if label_col is None else label_col
            if j != label_col or label in found:
                raise SystemExit(f"Table {number}: {label} out of place")
            found[label] = row
        elif first is not None and label.lower() in NATIONAL_LABELS:
            national[label.lower()] = row
    if first is None:
        raise SystemExit(f"Table {number}: no district rows")
    header = []
    for row in rows[title + 1 : first]:
        cells = [text(v) for v in row]
        if not any(cells[label_col + 1 :]):
            continue
        filled, carry = [], ""
        for j in range(len(cells)):
            if j > label_col:
                carry = cells[j] or carry
            filled.append(carry.lower() if j > label_col else "")
        header.append(filled)
    title_text = " ".join(text(v) for v in rows[title] if text(v))
    return Table(number, title_text, label_col, header, found, national)


def path_of(table: Table, col: int) -> list[str]:
    return [row[col] if col < len(row) else "" for row in table.header]


def columns(table: Table) -> range:
    return range(table.label_col + 1, max(len(row) for row in table.header))


def only(table: Table, matches: list[int], what: str) -> int:
    if len(matches) != 1:
        raise SystemExit(f"Table {table.number}: expected one column for {what}, found {matches}")
    return matches[0]


def yield_column(table: Table, large_only: bool) -> int:
    matches = []
    for col in columns(table):
        path = path_of(table, col)
        if path[-1] != "maize":
            continue
        if large_only and not any("large scale" in part for part in path):
            continue
        matches.append(col)
    return only(table, matches, "maize")


def farmer_columns(table: Table, lever: str) -> dict[str, int]:
    has_answers = any(set(row) & ANSWERS for row in table.header)
    out = {}
    for farmer_label, farmer_type in FARMER_TYPES.items():
        matches = []
        for col in columns(table):
            path = path_of(table, col)
            if farmer_label not in path:
                continue
            groups = [part for part in path if part.startswith(("percentage of farmers", "farmers who"))]
            if not groups:
                continue
            if any(part.startswith("farmers who") for part in groups) and not any("irrigat" in part for part in groups):
                continue
            if has_answers and WANTED_ANSWER[lever] not in path:
                continue
            matches.append(col)
        out[farmer_type] = only(table, matches, f"{lever} {farmer_label}")
    return out


def classify(value) -> tuple[Decimal | None, str]:
    if value is None or text(value) == "" and not isinstance(value, Decimal):
        return None, "empty"
    if isinstance(value, Decimal):
        return (None, "zero") if value == 0 else (value, "number")
    if text(value) in {"-", "–"}:
        return None, "dash"
    raise SystemExit(f"unexpected cell {value!r}")


def rounded(value: Decimal, unit: str) -> str:
    step = Decimal("1") if unit == "kg_per_ha" else Decimal("0.1")
    return str(value.quantize(step, rounding=ROUND_HALF_UP))


def unit_of(year: int, lever: str) -> str:
    if lever.startswith("maize_yield"):
        return "t_per_ha" if (year, lever) == (2019, "maize_yield_lsf") else "kg_per_ha"
    return "percent"


def row_for(year, lever, geography, district_id, farmer_type, raw, unit, table, source) -> dict:
    value, printed = classify(raw)
    return {
        "year": str(year), "season": "A", "lever": lever, "district_id": district_id, "geography": geography,
        "farmer_type": farmer_type,
        "value": rounded(value, unit) if value is not None else "",
        "unit": unit, "blank": "false" if value is not None else "true", "printed": printed,
        "workbook_value": str(value) if value is not None else "",
        "table": table, "source_url": source["url"], "landing_page": source["landing_page"],
    }


def national_type(table: Table, label: str, lever: str) -> str:
    return "lsf" if lever == "maize_yield_lsf" else NATIONAL_LABELS[label]


def extract(year: int, lever: str, table: Table, codes: dict[str, str], source: dict) -> list[dict]:
    unit = unit_of(year, lever)
    if lever.startswith("maize_yield"):
        col = yield_column(table, large_only=(year, lever) == (2019, "maize_yield_lsf"))
        picks = {"lsf" if lever == "maize_yield_lsf" else "all": col}
    else:
        picks = farmer_columns(table, lever)
    rows = []
    for name, district_id in codes.items():
        for farmer_type, col in picks.items():
            if name in table.districts:
                raw = table.districts[name][col] if col < len(table.districts[name]) else None
                rows.append(row_for(year, lever, name, district_id, farmer_type, raw, unit, table.number, source))
            else:
                row = row_for(year, lever, name, district_id, farmer_type, None, unit, table.number, source)
                row["printed"] = "absent"
                rows.append(row)
    for label, values in table.national.items():
        farmer_type = national_type(table, label, lever)
        if lever.startswith("maize_yield"):
            col = picks.get("lsf" if lever == "maize_yield_lsf" else "all")
        else:
            if NATIONAL_LABELS[label] != "all":
                continue
            for farmer, col in picks.items():
                raw = values[col] if col < len(values) else None
                rows.append(row_for(year, lever, "National", "", farmer, raw, unit, table.number, source))
            continue
        raw = values[col] if col < len(values) else None
        rows.append(row_for(year, lever, "National", "", farmer_type, raw, unit, table.number, source))
    return rows


def dedupe_national(rows: list[dict]) -> list[dict]:
    """A yield table can print the national large-farm figure twice; both copies must agree."""
    seen, out = {}, []
    for row in rows:
        key = (row["year"], row["lever"], row["geography"], row["farmer_type"])
        if key in seen:
            if seen[key]["workbook_value"] != row["workbook_value"]:
                raise SystemExit(f"two values for {key}: {seen[key]['workbook_value']} and {row['workbook_value']}")
            continue
        seen[key] = row
        out.append(row)
    return out


def check(rows: list[dict], titles: dict[tuple[str, str], str]) -> list[dict]:
    problems, quality = [], []
    groups = {}
    for row in rows:
        groups.setdefault((row["year"], row["lever"], row["table"], row["farmer_type"]), []).append(row)
    for (year, lever, table, farmer), members in sorted(groups.items()):
        district_rows = [r for r in members if r["geography"] != "National"]
        national_only = lever == "maize_yield" and farmer != "all"
        if len(district_rows) != (0 if national_only else 30):
            problems.append(f"{year} {lever} {farmer}: {len(district_rows)} districts")
        values = [Decimal(r["value"]) for r in district_rows if r["blank"] == "false"]
        national = [r for r in members if r["geography"] == "National"]
        for r in members:
            if r["blank"] == "false":
                v = Decimal(r["value"])
                if r["unit"] == "percent" and not 0 <= v <= 100:
                    problems.append(f"{year} {lever} {r['geography']} {farmer}: {v}% outside 0-100")
                if r["unit"] != "percent" and v <= 0:
                    problems.append(f"{year} {lever} {r['geography']} {farmer}: yield {v}")
        nat = national[0]["value"] if national and national[0]["blank"] == "false" else ""
        if nat and values and not min(values) <= Decimal(nat) <= max(values):
            problems.append(f"{year} {lever} {farmer}: national {nat} outside districts {min(values)}-{max(values)}")
        if farmer == "all" and not nat:
            problems.append(f"{year} {lever}: no national value")
        quality.append({
            "year": year, "lever": lever, "table": table, "title": titles[(year, lever)], "farmer_type": farmer,
            "numbers": str(len(values)),
            "blanks": str(sum(r["blank"] == "true" and r["printed"] != "absent" for r in district_rows)),
            "absent": str(sum(r["printed"] == "absent" for r in district_rows)),
            "national": nat, "district_min": str(min(values)) if values else "", "district_max": str(max(values)) if values else "",
        })
    for year in PLAN:
        both = [r for r in rows if r["year"] == str(year) and r["geography"] == "National" and r["farmer_type"] == "lsf"
                and r["lever"] in ("maize_yield", "maize_yield_lsf") and r["blank"] == "false"]
        in_kg = {(Decimal(r["value"]) * 1000 if r["unit"] == "t_per_ha" else Decimal(r["value"])) for r in both}
        if len(both) == 2 and max(in_kg) - min(in_kg) > (100 if year == 2019 else 1):
            problems.append(f"{year}: national large-farm maize yield differs between tables: {sorted(in_kg)}")
    if problems:
        raise SystemExit("history checks failed:\n" + "\n".join(problems))
    return quality


def agrees(printed: dict, row: dict) -> bool:
    if printed["blank"] == "true" or row["blank"] == "true":
        return printed["blank"] == row["blank"]
    p = Decimal(printed["value"])
    half_step = Decimal(5).scaleb(p.as_tuple().exponent - 1)
    return abs(p - Decimal(row["workbook_value"])) <= half_step and printed["value"] == row["value"]


def check_against_print(rows: list[dict]) -> int:
    with PRINTED_2026.open(newline="", encoding="utf-8") as handle:
        printed = list(csv.DictReader(handle))
    index = {(r["table"], r["measure"], r["crop"], r["geography"], r["farmer_type"]): r for r in printed}
    compared, problems = 0, []
    for row in rows:
        if row["year"] != "2026":
            continue
        measure, crop = PRINTED_2026_TABLES[row["lever"]]
        match = index.get((row["table"], measure, crop, row["geography"], row["farmer_type"]))
        if match is None:
            problems.append(f"2026 {row['lever']} {row['geography']} {row['farmer_type']}: not in the printed cells")
            continue
        compared += 1
        if not agrees(match, row):
            problems.append(f"2026 Table {row['table']} {row['geography']} {row['farmer_type']}: "
                            f"report {match['value'] or match['printed']}, workbook {row['workbook_value'] or row['printed']}")
    if problems:
        raise SystemExit("2026 workbook and printed report disagree:\n" + "\n".join(problems))
    return compared


def write(path: Path, fields: list[str], rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def build() -> tuple[list[dict], list[dict], int]:
    codes = {row["district"]: row["district_id"] for row in districts()}
    sources = manifest()
    rows, titles = [], {}
    for year, (filename, tables) in PLAN.items():
        book = xlsx.sheets(RAW / "sas" / filename)
        for lever, number in tables.items():
            table = parse(find_sheet(book, number), number, set(codes))
            titles[(str(year), lever)] = table.title
            rows.extend(extract(year, lever, table, codes, sources[filename]))
    rows = dedupe_national(rows)
    quality = check(rows, titles)
    compared = check_against_print(rows)
    return rows, quality, compared


def main():
    rows, quality, compared = build()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    write(OUT, FIELDS, rows)
    write(QUALITY, QUALITY_FIELDS, quality)
    numbers = sum(r["blank"] == "false" for r in rows)
    print(f"wrote {len(rows)} rows ({numbers} numbers) to {OUT.relative_to(ROOT)}; "
          f"{compared} 2026 values equal the printed report")


if __name__ == "__main__":
    main()
