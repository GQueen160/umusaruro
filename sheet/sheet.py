"""What the pages show, built from the cell file, the rainfall file, and the rules.

Nothing here reads a number that is not in `cells.csv`, the rainfall file,
the PSTA 5 milestones, or the rules module. Sentences are lists of strings
and Stats, so a number never sits in prose without its citation.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

from umusaruro import cells as cell_file
from umusaruro import rainfall as rainfall_file
from umusaruro import rules
from umusaruro.cells import Cell, Cells
from umusaruro.rules import Decision
from umusaruro.signoff import screen_cells

from sheet.stats import CHIRPS, CONTRACT, RULES, SIGNOFF, Stat, in_tonnes, psta, sas_a

NATIONAL = "National"
MILESTONES = [("2025/26", Decimal("2.06")), ("2026/27", Decimal("2.26"))]
ACTION_LABELS = {"irrigation": "Irrigation", "seed": "All-crop improved seed", None: "No action from these rules"}


def cell_stat(cell: Cell, unit: str) -> Stat:
    return Stat(cell.value, unit, sas_a(cell.table), cell.printed, cell.checked)


def gap_stat(large: Cell, small: Cell) -> Stat:
    if large.value is None or small.value is None:
        return Stat(None, "points", sas_a(large.table), "derived", large.checked and small.checked)
    return Stat(large.value - small.value, "points", sas_a(large.table), "derived", large.checked and small.checked)


def constant(value: Decimal, unit: str) -> Stat:
    return Stat(value, unit, CONTRACT, checked=True)


def ranks(gaps: dict[str, Decimal | None]) -> dict[str, int]:
    """1 is the largest gap. Equal gaps share a rank. Blank gaps are not ranked."""
    known = sorted((g for g in gaps.values() if g is not None), reverse=True)
    return {name: known.index(g) + 1 for name, g in gaps.items() if g is not None}


@dataclass(frozen=True)
class Lever:
    key: str
    label: str
    small: Stat
    large: Stat
    gap: Stat
    rank: Stat | None
    cutoff: Stat
    fires: bool


@dataclass(frozen=True)
class Milestone:
    column: str
    target: Stat
    above: bool | None


@dataclass(frozen=True)
class DistrictSheet:
    name: str
    slug: str
    decision: Decision
    action_label: str
    maize_kg: Stat
    maize_t: Stat
    large_maize_kg: Stat
    large_maize_t: Stat
    milestones: list[Milestone]
    levers: list[Lever]
    rain_total: Stat
    rain_median: Stat
    rain_cells: Stat
    rain_below: bool
    reason: list[list]
    fertilizer: list
    shown: Stat
    checked: Stat


def slug(name: str) -> str:
    return name.lower()


@lru_cache(maxsize=1)
def data():
    cells = cell_file.load()
    rain = rainfall_file.load()
    decisions = rules.classify_all(cells, rain)
    return cells, rain, decisions


def districts() -> list[str]:
    return list(data()[2])


def _lever_cells(cells: Cells, name: str):
    return {
        "irrigation": (cells.get("31", name, "ssf", "", "irrigation"), cells.get("31", name, "lsf", "", "irrigation")),
        "seed": (cells.get("20", name, "ssf", "all_crops", "farmers"), cells.get("20", name, "lsf", "all_crops", "farmers")),
        "fertilizer": (cells.get("25", name, "ssf", "all_crops", "farmers"), cells.get("25", name, "lsf", "all_crops", "farmers")),
    }


@lru_cache(maxsize=1)
def lever_ranks() -> dict[str, dict[str, int]]:
    cells, _rain, decisions = data()
    gaps = {"irrigation": {}, "seed": {}, "fertilizer": {}}
    for name, decision in decisions.items():
        gaps["irrigation"][name] = decision.irrigation_gap
        gaps["seed"][name] = decision.seed_gap
        gaps["fertilizer"][name] = decision.fertilizer_gap
    return {key: ranks(values) for key, values in gaps.items()}


LEVER_LABELS = {
    "irrigation": ("Irrigation", rules.IRRIGATION_GAP),
    "seed": ("Improved seed, all crops", rules.SEED_GAP),
    "fertilizer": ("Inorganic fertilizer, all crops", rules.FERTILIZER_GAP),
}


def _reason(d: Decision, levers: dict[str, Lever], total: Stat, median: Stat) -> list[list]:
    irr, seed = levers["irrigation"], levers["seed"]
    ssf_max = constant(rules.IRRIGATION_SSF_MAX, "%")
    out: list[list] = []
    if d.action == "irrigation":
        out.append([irr.small, " of smallholders irrigated, under the ", ssf_max, " line, against ", irr.large,
                    " of large farms: a gap of ", irr.gap, ", at least ", irr.cutoff, "."])
        out.append(["September to February rainfall was ", total, ", below the median of the districts, ", median, "."])
        if d.seed_fires and d.seed_gap > d.irrigation_gap:
            out.append(["The seed gap, ", seed.gap, ", also passes its cutoff, but it leads the irrigation gap by less than ",
                        constant(rules.SEED_LEAD, "points"), ", so irrigation stays first."])
        elif d.seed_fires:
            out.append(["The seed gap, ", seed.gap, ", also passes its cutoff, but the irrigation gap is wider, ",
                        "so irrigation stays first."])
        return out
    if d.action == "seed":
        out.append([seed.small, " of smallholders used improved seed on any crop, against ", seed.large,
                    " of large farms: a gap of ", seed.gap, ", at least ", seed.cutoff, "."])
        if d.irrigation_candidate and d.rainfall_below_median:
            out.append(["Irrigation also qualifies with a gap of ", irr.gap, ", but the seed gap leads it by at least ",
                        constant(rules.SEED_LEAD, "points"), "."])
        elif d.irrigation_candidate:
            out.append(["The irrigation numbers are met, but September to February rainfall was ", total,
                        ", above the median of the districts, ", median, ", so irrigation is not named first."])
        return out
    if d.seed_gap is None:
        out.append(["No seed gap can be computed: ", seed.large, " for large farms."])
    else:
        out.append(["The seed gap, ", seed.gap, ", is under ", seed.cutoff, "."])
    if d.irrigation_gap is None:
        out.append(["No irrigation gap can be computed: ", irr.large, " for large farms."])
    elif not d.irrigation_candidate:
        if irr.small.value is not None and irr.small.value >= rules.IRRIGATION_SSF_MAX:
            out.append([irr.small, " of smallholders already irrigate, at or above the ", ssf_max, " line."])
        else:
            out.append(["The irrigation gap, ", irr.gap, ", is under ", irr.cutoff, "."])
    else:
        out.append(["The irrigation numbers are met, but rainfall was ", total, ", above the median of the districts, ",
                    median, "."])
    return out


def _fertilizer(d: Decision, lever: Lever) -> list:
    if d.fertilizer_gap is None:
        return ["Inorganic fertilizer: ", lever.large, " for large farms, so no gap is computed."]
    if d.fertilizer_named:
        return ["Inorganic fertilizer also lags: ", lever.small, " of smallholders against ", lever.large,
                " of large farms, a gap of ", lever.gap, ", at least ", lever.cutoff, "."]
    return ["Inorganic fertilizer is not named: the gap, ", lever.gap, ", is under ", lever.cutoff, "."]


def district_sheet(name: str) -> DistrictSheet:
    cells, rain, decisions = data()
    d = decisions[name]
    gate = rain[name]
    all_ranks = lever_ranks()
    levers: dict[str, Lever] = {}
    for key, (small, large) in _lever_cells(cells, name).items():
        label, cutoff = LEVER_LABELS[key]
        ranked = all_ranks[key]
        rank = None
        if name in ranked:
            rank = Stat(Decimal(ranked[name]), f"of {len(ranked)} districts", RULES, "number",
                        small.checked and large.checked)
        levers[key] = Lever(
            key=key,
            label=label,
            small=cell_stat(small, "%"),
            large=cell_stat(large, "%"),
            gap=gap_stat(large, small),
            rank=rank,
            cutoff=constant(cutoff, "points"),
            fires={"irrigation": d.irrigation_candidate, "seed": d.seed_fires, "fertilizer": d.fertilizer_named}[key],
        )
    maize = cell_stat(cells.get("13", name, "all", "maize", "yield"), "kg/ha")
    large_maize = cell_stat(cells.get("14", name, "lsf", "maize", "yield"), "kg/ha")
    total = Stat(gate.total_mm, "mm", CHIRPS, checked=True)
    median = Stat(gate.median_mm, "mm", CHIRPS, checked=True)
    milestones = [
        Milestone(column, Stat(target, "t/ha", psta(column), checked=True),
                  None if maize.value is None else maize.value >= target * 1000)
        for column, target in MILESTONES
    ]
    stats = [maize, large_maize] + [s for lever in levers.values() for s in (lever.small, lever.large)]
    return DistrictSheet(
        name=name,
        slug=slug(name),
        decision=d,
        action_label=ACTION_LABELS[d.action],
        maize_kg=maize,
        maize_t=in_tonnes(maize),
        large_maize_kg=large_maize,
        large_maize_t=in_tonnes(large_maize),
        milestones=milestones,
        levers=list(levers.values()),
        rain_total=total,
        rain_median=median,
        rain_cells=Stat(Decimal(gate.cells), "grid cells", CHIRPS, checked=True),
        rain_below=gate.below_median,
        reason=_reason(d, levers, total, median),
        fertilizer=_fertilizer(d, levers["fertilizer"]),
        shown=Stat(Decimal(len(stats)), "survey cells", SIGNOFF, checked=True),
        checked=Stat(Decimal(sum(1 for s in stats if s.checked)), "", SIGNOFF, checked=True),
    )


def by_slug(value: str) -> str | None:
    return {slug(name): name for name in districts()}.get(value)


@dataclass(frozen=True)
class Row:
    name: str
    slug: str
    action: str | None
    action_label: str
    maize_t: Stat
    above: bool | None
    fertilizer_named: bool
    irrigation_gap: Stat
    seed_gap: Stat
    fertilizer_gap: Stat


def overview() -> dict:
    cells, rain, decisions = data()
    rows = []
    for name, d in decisions.items():
        levers = _lever_cells(cells, name)
        rows.append(Row(
            name=name,
            slug=slug(name),
            action=d.action,
            action_label=ACTION_LABELS[d.action],
            maize_t=in_tonnes(cell_stat(cells.get("13", name, "all", "maize", "yield"), "kg/ha")),
            above=d.above_milestone,
            fertilizer_named=d.fertilizer_named,
            irrigation_gap=gap_stat(levers["irrigation"][1], levers["irrigation"][0]),
            seed_gap=gap_stat(levers["seed"][1], levers["seed"][0]),
            fertilizer_gap=gap_stat(levers["fertilizer"][1], levers["fertilizer"][0]),
        ))
    counts = {}
    for key in ("irrigation", "seed", None):
        counts[key] = Stat(Decimal(sum(1 for d in decisions.values() if d.action == key)), "districts", RULES, checked=True)
    national = {
        farm: cell_stat(cells.get("13", NATIONAL, farm, "maize", "yield"), "kg/ha")
        for farm in ("all", "ssf", "lsf")
    }
    return {
        "rows": rows,
        "counts": [(ACTION_LABELS[k], k or "none", v) for k, v in counts.items()],
        "fertilizer_count": Stat(Decimal(sum(1 for d in decisions.values() if d.fertilizer_named)), "districts",
                                 RULES, checked=True),
        "fertilizer_alone": Stat(Decimal(sum(1 for d in decisions.values() if d.fertilizer_named and not d.action)),
                                 "", RULES, checked=True),
        "national": {farm: (s, in_tonnes(s)) for farm, s in national.items()},
        "milestones": [Stat(t, "t/ha", psta(c), checked=True) for c, t in MILESTONES],
        "milestone_columns": [c for c, _t in MILESTONES],
        "above_count": Stat(Decimal(sum(1 for d in decisions.values() if d.above_milestone)), "districts",
                            RULES, checked=True),
    }


@dataclass(frozen=True)
class NearCut:
    district: str
    slug: str
    what: str
    value: Stat
    cutoff: Stat


def near_cutoffs(within: Decimal = Decimal("2")) -> list[NearCut]:
    cells, _rain, decisions = data()
    out = []
    for name, d in decisions.items():
        levers = _lever_cells(cells, name)
        checks = [
            ("smallholder irrigation", cell_stat(levers["irrigation"][0], "%"), constant(rules.IRRIGATION_SSF_MAX, "%")),
            ("irrigation gap", gap_stat(levers["irrigation"][1], levers["irrigation"][0]), constant(rules.IRRIGATION_GAP, "points")),
            ("seed gap", gap_stat(levers["seed"][1], levers["seed"][0]), constant(rules.SEED_GAP, "points")),
            ("fertilizer gap", gap_stat(levers["fertilizer"][1], levers["fertilizer"][0]), constant(rules.FERTILIZER_GAP, "points")),
        ]
        for what, value, cutoff in checks:
            if value.value is not None and abs(value.value - cutoff.value) <= within:
                out.append(NearCut(name, slug(name), what, value, cutoff))
    return out


def method() -> dict:
    cells, rain, _decisions = data()
    keys = [key for *_place, key in screen_cells()]
    checked = sum(
        1 for k in keys if cells.get(k.table, k.geography, k.farmer_type, k.crop, k.measure).checked
    )
    thin = [(name, Stat(Decimal(g.cells), "grid cells", CHIRPS, checked=True))
            for name, g in rain.items() if g.cells < 10]
    any_gate = next(iter(rain.values()))
    return {
        "constants": [
            ("Irrigation gap, large farms minus smallholders", constant(rules.IRRIGATION_GAP, "points")),
            ("Smallholder irrigation must be under", constant(rules.IRRIGATION_SSF_MAX, "%")),
            ("Seed gap, all crops", constant(rules.SEED_GAP, "points")),
            ("Seed must lead irrigation by at least", constant(rules.SEED_LEAD, "points")),
            ("Fertilizer gap that names fertilizer", constant(rules.FERTILIZER_GAP, "points")),
            ("Maize milestone used for above or below", constant(rules.MAIZE_MILESTONE_KG, "kg/ha")),
        ],
        "near": near_cutoffs(),
        "maize_improved": cell_stat(cells.get("21", NATIONAL, "all", "maize", "improved"), "%"),
        "maize_loss": cell_stat(cells.get("16", NATIONAL, "all", "maize", "post_harvest_loss"), "%"),
        "median": Stat(any_gate.median_mm, "mm", CHIRPS, checked=True),
        "thin": thin,
        "screen_total": Stat(Decimal(len(keys)), "cells", SIGNOFF, checked=True),
        "screen_checked": Stat(Decimal(checked), "", SIGNOFF, checked=True),
    }
