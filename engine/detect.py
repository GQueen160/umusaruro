"""Propose how each table in a file should be read, and read it.

`propose(sheets, default_year)` looks at every sheet and returns one
proposal per table: its title, year, season, measure, and for each column
the crop, measure, farm type, and basis it carries, or why it is skipped.
Proposals are plain dicts, stored as JSON, shown on the review screen,
and editable there. Nothing is published until a person confirms them.

`extract(sheets, proposal)` reads the confirmed proposal into tidy rows.
Blanks stay blank: an empty cell, a dash, or a zero is recorded with its
reason and no value, because NISR prints workbook zeros as a dash.

Two layouts are understood:

  wide   districts down the side, crops or farm types across, a title
         above (the NISR layout)
  long   one row per district (and year, crop...), one column per measure
"""

from __future__ import annotations

from collections import Counter
from decimal import Decimal

from engine import vocab
from engine.vocab import MEASURES, PRACTICES, norm

MIN_DISTRICTS = 20


def text(value) -> str:
    return " ".join(value.split()) if isinstance(value, str) else ""


def classify(value) -> tuple[Decimal | None, str]:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None, "empty"
    if isinstance(value, Decimal):
        return (None, "zero") if value == 0 else (value, "number")
    if text(value) in {"-", "–", "—", "..", "n/a", "na", "x"}:
        return None, "dash"
    return None, "text"


def find_title(rows: list[list], sheet: str) -> tuple[int, str]:
    for i, row in enumerate(rows[:6]):
        joined = " ".join(text(v) for v in row if text(v))
        if vocab.table_number(joined) or (len(joined) > 25 and not vocab.district(joined)):
            if not any(vocab.district(text(v)) for v in row):
                return i, joined
    return -1, sheet


def district_rows(rows: list[list], start: int) -> tuple[int | None, dict[int, dict], dict[int, str], Counter]:
    label_col, found, national, seen = None, {}, {}, Counter()
    for i, row in enumerate(rows[start:], start=start):
        if label_col is None:
            label_col = next((j for j, v in enumerate(row) if vocab.district(text(v))), None)
            if label_col is None:
                continue
        label = text(row[label_col]) if label_col < len(row) else ""
        place = vocab.district(label)
        if place:
            found[i] = place
            seen[place["district_id"]] += 1
        elif norm(label) in vocab.NATIONAL_LABELS:
            national[i] = norm(label)
    return label_col, found, national, seen


def header_paths(rows: list[list], start: int, first: int, label_col: int, width: int) -> list[list[str]]:
    header = []
    for row in rows[start:first]:
        cells = [text(row[j]) if j < len(row) else "" for j in range(width)]
        if not any(cells[label_col + 1:]):
            continue
        filled, carry = [], ""
        for j in range(width):
            if j > label_col:
                carry = cells[j] or carry
            filled.append(norm(carry) if j > label_col else "")
        header.append(filled)
    return header


def propose_wide(rows, sheet, title_i, title, label_col, found, national, default_year) -> dict:
    first = min(found)
    width = max(len(r) for r in rows[title_i + 1:]) if rows[title_i + 1:] else 0
    header = header_paths(rows, title_i + 1, first, label_col, width)
    measure = vocab.title_measure(title)
    proposal = {
        "sheet": sheet, "title": title, "number": vocab.table_number(title), "layout": "wide",
        "year": vocab.year(title) or default_year, "season": vocab.season(title), "measure": measure,
        "label_col": label_col, "districts": len(found), "national_rows": sorted(set(national.values())),
        "columns": [], "status": "recognised", "reason": "",
    }
    if measure is None:
        proposal.update(status="unrecognised", reason="the title names no measure the engine reads")
    if not header:
        proposal.update(status="unrecognised", reason="no header row above the districts")
        return proposal
    large_only = "large scale" in norm(title) or "large-scale" in norm(title)
    has_answers = any(set(row) & vocab.ANSWERS for row in header)
    has_farmer_columns = any(vocab.farmer_type([row[j]]) for row in header for j in range(len(row)))
    taken = set()
    for col in range(label_col + 1, width):
        parts = [row[col] for row in header if col < len(row)]
        leaf = parts[-1] if parts else ""
        column = {"col": col, "header": " / ".join(dict.fromkeys(p for p in parts if p)), "crop": "", "measure": "",
                  "farmer_type": "", "basis": "", "unit": "", "keep": False, "why": ""}
        proposal["columns"].append(column)
        if not leaf:
            column["why"] = "no header"
            continue
        if measure is None:
            column["why"] = "table not recognised"
            continue
        kind = MEASURES[measure].kind if measure in MEASURES else "input"
        if kind == "crop":
            if leaf in vocab.AGGREGATES:
                column["why"] = "a total of several crops"
                continue
            crop = vocab.crop(leaf)
            if crop is None:
                column["why"] = "not a crop the engine knows"
                continue
            farmer = "lsf" if large_only else (vocab.farmer_type(parts) or "all")
            column.update(crop=crop, measure=measure, farmer_type=farmer,
                          unit=vocab.yield_unit(title) if measure == "yield" else MEASURES[measure].unit)
        else:
            col_measure = vocab.group_measure(" ".join(parts)) if measure == PRACTICES else measure
            if col_measure is None:
                column["why"] = "not a practice the engine knows"
                continue
            farmer = vocab.farmer_type(parts) or (None if has_farmer_columns else "all")
            if farmer is None:
                column["why"] = "no farm type in the header"
                continue
            if has_answers and not (set(parts) & vocab.KEEP_ANSWERS):
                column["why"] = "the 'no' or 'traditional' share"
                continue
            column.update(measure=col_measure, farmer_type=farmer, basis=vocab.basis(parts) or "farmers",
                          unit=MEASURES[col_measure].unit)
        key = (column["crop"], column["measure"], column["farmer_type"], column["basis"])
        if key in taken:
            column.update(keep=False, why="repeats an earlier column")
            continue
        taken.add(key)
        column["keep"] = True
    if proposal["status"] == "recognised" and not any(c["keep"] for c in proposal["columns"]):
        proposal.update(status="unrecognised", reason="no column could be read")
    return proposal


LONG_ROLES = [("year", ("year",)), ("season", ("season",)), ("crop", ("crop",)),
              ("farmer_type", ("farmer", "farm type", "farm size")), ("indicator", ("indicator", "measure", "variable")),
              ("value", ("value",))]


def propose_long(rows, sheet, title, label_col, found, default_year) -> dict:
    first = min(found)
    head_i = max((i for i in range(first) if any(text(v) for v in rows[i])), default=None)
    head = [norm(v) for v in rows[head_i]] if head_i is not None else []
    width = max(len(r) for r in rows[first:])
    proposal = {"sheet": sheet, "title": title, "number": vocab.table_number(title), "layout": "long",
                "year": vocab.year(title) or default_year, "season": vocab.season(title), "measure": None,
                "label_col": label_col, "header_row": head_i, "districts": len(found), "national_rows": [],
                "columns": [], "status": "recognised", "reason": ""}
    data = [rows[i] for i in found]
    for col in range(width):
        name = head[col] if col < len(head) else ""
        values = [r[col] for r in data if col < len(r) and r[col] is not None]
        column = {"col": col, "header": name, "role": "", "crop": "", "measure": "", "farmer_type": "all",
                  "basis": "farmers", "unit": "", "keep": False, "why": ""}
        proposal["columns"].append(column)
        if col == label_col:
            column.update(role="district", keep=True)
            continue
        role = next((r for r, words in LONG_ROLES if any(w in name for w in words)), "")
        if not role and values and all(isinstance(v, Decimal) and 1990 <= v <= 2100 and v == int(v) for v in values):
            role = "year"
        if not role and values and sum(1 for v in values if vocab.crop(v)) >= 0.6 * len(values):
            role = "crop"
        if role:
            column.update(role=role, keep=True)
            continue
        numeric = sum(1 for v in values if isinstance(v, Decimal))
        if not values or numeric < 0.5 * len(values):
            column["why"] = "not numeric"
            continue
        measure = vocab.title_measure(name)
        if measure in (None, PRACTICES):
            measure = vocab.group_measure(name)
        if measure is None:
            column["why"] = "the header names no measure the engine reads"
            continue
        column.update(role="measure", measure=measure, keep=True,
                      unit=vocab.yield_unit(name) if measure == "yield" else MEASURES[measure].unit,
                      farmer_type=vocab.farmer_type([name]) or "all")
    if not any(c["role"] == "measure" for c in proposal["columns"]) and not any(
            c["role"] == "value" for c in proposal["columns"]):
        proposal.update(status="unrecognised", reason="no column names a measure the engine reads")
    return proposal


def propose(sheets: dict[str, list[list]], default_year: int | None = None) -> list[dict]:
    out = []
    for sheet, rows in sheets.items():
        if not rows:
            continue
        title_i, title = find_title(rows, sheet)
        label_col, found, national, seen = district_rows(rows, title_i + 1)
        if len(seen) < MIN_DISTRICTS:
            out.append({"sheet": sheet, "title": title, "number": vocab.table_number(title), "layout": "",
                        "year": vocab.year(title) or default_year, "season": vocab.season(title), "measure": None,
                        "districts": len(seen), "columns": [], "status": "no_districts",
                        "reason": f"fewer than {MIN_DISTRICTS} district rows"})
            continue
        if max(seen.values()) > 1:
            out.append(propose_long(rows, sheet, title, label_col, found, default_year))
        else:
            out.append(propose_wide(rows, sheet, title_i, title, label_col, found, national, default_year))
    return out


def _row(proposal, district_id, geography, column, raw, year=None, season=None, crop=None, farmer=None,
         measure=None, unit=None, row=0):
    value, printed = classify(raw)
    return {
        "year": year if year is not None else proposal["year"],
        "season": season if season is not None else proposal["season"],
        "district_id": district_id, "geography": geography,
        "crop": crop if crop is not None else column["crop"],
        "measure": measure or column["measure"], "basis": column.get("basis", ""),
        "farmer_type": farmer or column["farmer_type"], "unit": unit or column["unit"],
        "value": value, "printed": printed, "raw": "" if raw is None else str(raw),
        "row": row + 1, "col": column["col"] + 1,
    }


def extract(sheets: dict[str, list[list]], proposal: dict) -> list[dict]:
    rows = sheets[proposal["sheet"]]
    columns = [c for c in proposal["columns"] if c["keep"]]
    out = []
    if proposal["layout"] == "wide":
        for i, row in enumerate(rows):
            label = text(row[proposal["label_col"]]) if proposal["label_col"] < len(row) else ""
            place = vocab.district(label)
            national = norm(label) in vocab.NATIONAL_LABELS and not place
            if not place and not national:
                continue
            for column in columns:
                raw = row[column["col"]] if column["col"] < len(row) else None
                if place:
                    out.append(_row(proposal, place["district_id"], place["district"], column, raw, row=i))
                    continue
                label_farmer = vocab.NATIONAL_LABELS[norm(label)]
                if MEASURES[column["measure"]].kind == "crop":
                    farmer = column["farmer_type"] if column["farmer_type"] == "lsf" else label_farmer
                elif label_farmer != "all":
                    continue
                else:
                    farmer = column["farmer_type"]
                out.append(_row(proposal, "", vocab.NATIONAL, column, raw, farmer=farmer, row=i))
        return dedupe(out)
    roles = {c["role"]: c for c in columns if c["role"] not in ("measure", "")}
    measures = [c for c in columns if c["role"] == "measure"]
    for i, row in enumerate(rows):
        if i <= (proposal.get("header_row") or -1):
            continue
        get = lambda c: row[c["col"]] if c and c["col"] < len(row) else None  # noqa: E731
        place = vocab.district(text(get(roles.get("district"))))
        if not place:
            continue
        year = get(roles.get("year"))
        year = int(year) if isinstance(year, Decimal) else (vocab.year(year) if year else proposal["year"])
        season = vocab.season(f"season {text(get(roles.get('season')))}") if roles.get("season") else proposal["season"]
        crop = vocab.crop(get(roles.get("crop"))) or "" if roles.get("crop") else None
        farmer = vocab.farmer_type([norm(get(roles.get("farmer_type")))]) if roles.get("farmer_type") else None
        for column in measures:
            out.append(_row(proposal, place["district_id"], place["district"], column, get(column), year=year,
                            season=season, crop=crop, farmer=farmer, row=i))
        if roles.get("indicator") and roles.get("value"):
            measure = vocab.title_measure(text(get(roles["indicator"])))
            if measure in MEASURES:
                column = roles["value"] | {"basis": "farmers", "farmer_type": "all", "crop": "", "measure": measure,
                                           "unit": MEASURES[measure].unit}
                out.append(_row(proposal, place["district_id"], place["district"], column, get(roles["value"]),
                                year=year, season=season, crop=crop, farmer=farmer, row=i))
    return dedupe(out)


def key(r: dict) -> tuple:
    return (r["year"], r["season"], r["geography"], r["crop"], r["measure"], r["basis"], r["farmer_type"])


def dedupe(rows: list[dict]) -> list[dict]:
    """One value per key: the first copy is kept; a later copy with another value is noted on it."""
    seen, out = {}, []
    for r in rows:
        k = key(r)
        if k in seen:
            if seen[k]["value"] != r["value"]:
                seen[k].setdefault("conflicts", []).append(f"row {r['row']} col {r['col']}: {r['raw'] or 'blank'}")
            continue
        seen[k] = r
        out.append(r)
    return out


def checks(rows: list[dict]) -> list[str]:
    """Warnings a reviewer must see. They do not stop a read; the reviewer decides."""
    warnings = []
    for r in rows:
        for other in r.get("conflicts", []):
            warnings.append(f"{r['geography']} {r['crop']} {r['measure']}: kept {r['raw'] or 'blank'}, "
                            f"another copy at {other}")
        if r["value"] is None:
            if r["printed"] == "text":
                warnings.append(f"{r['geography']} {r['crop']} {r['measure']}: text '{r['raw']}' read as blank")
            continue
        if r["unit"] == "%" and not 0 <= r["value"] <= 100:
            warnings.append(f"{r['geography']} {r['crop']} {r['measure']}: {r['value']}% is outside 0 to 100")
        if r["measure"] in ("yield", "production", "cultivated_area", "harvested_area") and r["value"] < 0:
            warnings.append(f"{r['geography']} {r['crop']} {r['measure']}: negative value {r['value']}")
    return warnings
