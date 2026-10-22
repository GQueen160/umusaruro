"""What the pages show, built from the cell files, the rainfall file, and the rules.

Nothing here reads a number that is not in a cell file, the rainfall file,
the PSTA 5 milestones, or the rules module. Sentences are lists of strings
and Stats, so a number never sits in prose without its citation. Actions
come from Season A only; Season B is read beside it as a check.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

from umusaruro import cells as cell_file
from umusaruro import footers
from umusaruro import history as history_file
from umusaruro import rainfall as rainfall_file
from umusaruro import rules
from umusaruro.cells import Cell, Cells
from umusaruro.rules import Decision
from umusaruro.signoff import screen_cells, season_b_screen_cells

from sheet import charts
from sheet.stats import (CHIRPS, CONTRACT, FOOTER_CHECK, HISTORY, RULES, RULES_B, SIGNOFF, SIGNOFF_B, Ref, Stat,
                         in_tonnes, psta, sas, sas_workbook)

NATIONAL = "National"
MILESTONES = [("2025/26", Decimal("2.06")), ("2026/27", Decimal("2.26"))]
ACTION_LABELS = {"irrigation": "Irrigation", "seed": "All-crop improved seed", None: "No action from these rules"}


def cell_stat(cell: Cell, unit: str) -> Stat:
    return Stat(cell.value, unit, sas(cell.season, cell.table), cell.printed, cell.checked)


def gap_stat(large: Cell, small: Cell) -> Stat:
    source = sas(large.season, large.table)
    if large.value is None or small.value is None:
        return Stat(None, "points", source, "derived", large.checked and small.checked)
    return Stat(large.value - small.value, "points", source, "derived", large.checked and small.checked)


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
class SeasonBRow:
    key: str
    label: str
    withheld: bool
    small: Stat | None
    large: Stat | None
    gap: Stat | None
    season_a_gap: Stat
    cutoff: Stat
    passes: bool | None


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
    season_b: list[SeasonBRow]
    season_b_note: list | None
    trend: "Trend"
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


@lru_cache(maxsize=1)
def season_b() -> tuple[Cells, bool]:
    """Season B cells, and whether the Table 29 footer has been resolved by a person."""
    return cell_file.load(cell_file.SEASON_B_PATH), footers.resolved("29")


def districts() -> list[str]:
    return list(data()[2])


LEVER_TABLES = {
    "A": {"irrigation": ("31", "", "irrigation"), "seed": ("20", "all_crops", "farmers"),
          "fertilizer": ("25", "all_crops", "farmers")},
    "B": {"irrigation": ("29", "", "irrigation"), "seed": ("18", "all_crops", "farmers"),
          "fertilizer": ("23", "all_crops", "farmers")},
}


def _lever_cells(cells: Cells, name: str, season: str = "A"):
    return {
        key: (cells.get(table, name, "ssf", crop, measure), cells.get(table, name, "lsf", crop, measure))
        for key, (table, crop, measure) in LEVER_TABLES[season].items()
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


def season_b_passes(key: str, small: Cell, large: Cell) -> bool | None:
    """The Season A cutoffs applied to Season B cells. No rainfall gate: the rainfall window is Season A's."""
    if small.value is None or large.value is None:
        return None
    gap = large.value - small.value
    if key == "irrigation":
        return gap >= rules.IRRIGATION_GAP and small.value < rules.IRRIGATION_SSF_MAX
    return gap >= {"seed": rules.SEED_GAP, "fertilizer": rules.FERTILIZER_GAP}[key]


def _season_b_rows(name: str, season_a: dict[str, Lever]) -> list[SeasonBRow]:
    cells_b, irrigation_resolved = season_b()
    rows = []
    for key, (small, large) in _lever_cells(cells_b, name, "B").items():
        label, cutoff = LEVER_LABELS[key]
        withheld = key == "irrigation" and not irrigation_resolved
        rows.append(SeasonBRow(
            key=key,
            label=label,
            withheld=withheld,
            small=None if withheld else cell_stat(small, "%"),
            large=None if withheld else cell_stat(large, "%"),
            gap=None if withheld else gap_stat(large, small),
            season_a_gap=season_a[key].gap,
            cutoff=constant(cutoff, "points"),
            passes=None if withheld else season_b_passes(key, small, large),
        ))
    return rows


LEVER_NOUNS = {"irrigation": "irrigation", "seed": "all-crop seed"}


def _season_b_note(d: Decision, rows: list[SeasonBRow]) -> list | None:
    if d.action is None:
        return None
    row = next(r for r in rows if r.key == d.action)
    noun = LEVER_NOUNS[d.action]
    if row.withheld:
        return ["Season B irrigation is not shown until a second person confirms the footer of the irrigation table "
                "(see the method page)."]
    if row.passes is None:
        return [f"In Season B the {noun} gap cannot be computed: ", row.large, " for large farms."]
    if row.passes:
        return [f"Season B agrees: the {noun} gap is ", row.gap, ", which also reaches ", row.cutoff, "."]
    if d.action == "irrigation" and row.small.value >= rules.IRRIGATION_SSF_MAX:
        return ["Season B differs: ", row.small, " of smallholders irrigated, at or above the ",
                constant(rules.IRRIGATION_SSF_MAX, "%"), " line."]
    return [f"Season B differs: the {noun} gap is ", row.gap, ", under ", row.cutoff, "."]


HISTORY_UNITS = {"kg_per_ha": "kg/ha", "t_per_ha": "t/ha", "percent": "%"}
LATEST = 2026


@lru_cache(maxsize=1)
def history() -> history_file.History:
    return history_file.load()


def point_stat(point: history_file.Point) -> Stat:
    return Stat(point.value, HISTORY_UNITS[point.unit], sas_workbook(point.year, point.table, point.source_url),
                "number" if point.value is not None else point.printed)


def by_year(lever: str, geography: str, farmer_type: str) -> dict[int, Stat]:
    return {p.year: point_stat(p) for p in history().series(lever, geography, farmer_type)}


def trend_band(name: str) -> str | None:
    """Season A 2026 maize yield against the district's own 2019 to 2025 results: high, low, within, or None."""
    series = by_year("maize_yield", name, "all")
    latest = series[LATEST].value
    earlier = [s.value for year, s in series.items() if year < LATEST and s.value is not None]
    if latest is None or not earlier:
        return None
    if latest > max(earlier):
        return "high"
    if latest < min(earlier):
        return "low"
    return "within"


@dataclass(frozen=True)
class LeverTrend:
    key: str
    label: str
    chart: charts.Chart
    rows: list[tuple[str, list[Stat]]]


@dataclass(frozen=True)
class Trend:
    years: list[int]
    band: str | None
    sentence: list
    maize: charts.Chart
    maize_rows: list[tuple[str, list[Stat]]]
    levers: list[LeverTrend]


def _trend_sentence(name: str, band: str | None, series: dict[int, Stat]) -> list:
    latest = series[LATEST]
    first = Ref(str(min(series)))
    season = Ref(f"Season A {LATEST}")
    if band is None:
        return ["Maize yield in ", season, " is ", latest, ", so it cannot be set against earlier seasons."]
    if band == "high":
        return [latest, " in ", season, " is the highest maize yield in ", name, " since the series starts in ", first, "."]
    if band == "low":
        return [latest, " in ", season, " is the lowest maize yield in ", name, " since the series starts in ", first, "."]
    earlier = {y: s for y, s in series.items() if y < LATEST and s.value is not None}
    low = min(earlier.values(), key=lambda s: s.value)
    high = max(earlier.values(), key=lambda s: s.value)
    return [latest, " in ", season, " sits inside ", name, "'s earlier range, from ", low, " to ", high, "."]


def district_trend(name: str) -> Trend:
    years = history().years
    maize = by_year("maize_yield", name, "all")
    national = by_year("maize_yield", NATIONAL, "all")
    milestone_column, milestone_t = MILESTONES[-1]
    guide = Stat((milestone_t * 1000).quantize(Decimal(1)), "kg/ha", psta(milestone_column), checked=True)
    band = trend_band(name)
    levers = []
    for key in ("seed", "fertilizer", "irrigation"):
        small, large = by_year(key, name, "ssf"), by_year(key, name, "lsf")
        series = [("ssf", "Smallholders", small), ("lsf", "Large farms", large)]
        levers.append(LeverTrend(
            key=key,
            label=LEVER_LABELS[key][0],
            chart=charts.chart(years, series, top=Decimal(100)),
            rows=[(label, [values[y] for y in years]) for _k, label, values in series],
        ))
    return Trend(
        years=years,
        band=band,
        sentence=_trend_sentence(name, band, maize),
        maize=charts.chart(years, [("district", name, maize), ("national", "Rwanda", national)],
                           guides=[(f"PSTA 5 milestone {milestone_column}", guide)]),
        maize_rows=[(name, [maize[y] for y in years]), ("Rwanda", [national[y] for y in years])],
        levers=levers,
    )


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
    b_rows = _season_b_rows(name, levers)
    stats = [maize, large_maize] + [s for lever in levers.values() for s in (lever.small, lever.large)]
    stats += [s for row in b_rows if not row.withheld for s in (row.small, row.large)]
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
        season_b=b_rows,
        season_b_note=_season_b_note(d, b_rows),
        trend=district_trend(name),
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
    milestone_band: str
    trend_band: str
    rain_band: str


@dataclass(frozen=True)
class LayerItem:
    key: str
    label: list
    count: Stat


@dataclass(frozen=True)
class Layer:
    key: str
    name: str
    title: list
    items: list[LayerItem]
    note: list


def milestone_band(maize_kg: Decimal | None) -> str:
    if maize_kg is None:
        return "unknown"
    (_first, early), (_second, late) = MILESTONES
    if maize_kg >= late * 1000:
        return "late"
    if maize_kg >= early * 1000:
        return "early"
    return "below"


def _count(rows: list[Row], attr: str, key: str, source) -> Stat:
    return Stat(Decimal(sum(1 for r in rows if getattr(r, attr) == key)), "districts", source, checked=True)


def layers(rows: list[Row]) -> list[Layer]:
    (early_col, _e), (late_col, _l) = MILESTONES
    first = Ref(str(min(history().years)))
    latest = Ref(f"Season A {LATEST}")
    return [
        Layer("action", "Action", ["Action named by the rules, ", latest], [
            LayerItem("irrigation", [ACTION_LABELS["irrigation"]], _count(rows, "action", "irrigation", RULES)),
            LayerItem("seed", [ACTION_LABELS["seed"]], _count(rows, "action", "seed", RULES)),
            LayerItem("none", [ACTION_LABELS[None]], _count(rows, "action", None, RULES)),
        ], ["Click a district for its sheet."]),
        Layer("milestone", "Milestones", ["Maize yield, ", latest, ", against the ", Ref("PSTA 5"), " milestones"], [
            LayerItem("late", ["At or above the ", Ref(late_col), " milestone"], _count(rows, "milestone_band", "late", RULES)),
            LayerItem("early", ["At or above ", Ref(early_col), ", below ", Ref(late_col)],
                      _count(rows, "milestone_band", "early", RULES)),
            LayerItem("below", ["Below the ", Ref(early_col), " milestone"], _count(rows, "milestone_band", "below", RULES)),
        ], ["Yield from ", Ref("SAS Season A 2026 Table 13"), "; milestones from the ", Ref("PSTA 5"),
            " results framework."]),
        Layer("trend", "Trend", [latest, " against each district's own record since ", first], [
            LayerItem("high", ["Highest maize yield since ", first], _count(rows, "trend_band", "high", HISTORY)),
            LayerItem("within", ["Inside the earlier range"], _count(rows, "trend_band", "within", HISTORY)),
            LayerItem("low", ["Lowest since ", first], _count(rows, "trend_band", "low", HISTORY)),
        ], ["Each district is compared only with itself, across the eight Season A surveys. Survey estimates move "
            "from year to year by sampling alone, so a single record is a reason to look, not a proven trend."]),
        Layer("rain", "Rainfall", ["September to February rainfall, ", latest], [
            LayerItem("below", ["Below the median of the districts"], _count(rows, "rain_band", "below", CHIRPS)),
            LayerItem("above", ["At or above the median"], _count(rows, "rain_band", "above", CHIRPS)),
        ], ["Rainfall from ", Ref("CHIRPS v2.0"), ". It decides only whether irrigation can be named first."]),
    ]


def overview() -> dict:
    cells, rain, decisions = data()
    rows = []
    for name, d in decisions.items():
        levers = _lever_cells(cells, name)
        maize_cell = cells.get("13", name, "all", "maize", "yield")
        rows.append(Row(
            name=name,
            slug=slug(name),
            action=d.action,
            action_label=ACTION_LABELS[d.action],
            maize_t=in_tonnes(cell_stat(maize_cell, "kg/ha")),
            above=d.above_milestone,
            fertilizer_named=d.fertilizer_named,
            irrigation_gap=gap_stat(levers["irrigation"][1], levers["irrigation"][0]),
            seed_gap=gap_stat(levers["seed"][1], levers["seed"][0]),
            fertilizer_gap=gap_stat(levers["fertilizer"][1], levers["fertilizer"][0]),
            milestone_band=milestone_band(maize_cell.value),
            trend_band=trend_band(name) or "unknown",
            rain_band="below" if rain[name].below_median else "above",
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
        "layers": layers(rows),
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


@dataclass(frozen=True)
class SeasonBAgreement:
    action: str
    label: str
    withheld: bool
    agree: Stat
    total: Stat
    differ: list[tuple[str, str]]
    blank: list[tuple[str, str]]


def season_b_agreement() -> list[SeasonBAgreement]:
    cells_a, _rain, decisions = data()
    cells_b, irrigation_resolved = season_b()
    out = []
    for action in ("irrigation", "seed"):
        named = [name for name, d in decisions.items() if d.action == action]
        withheld = action == "irrigation" and not irrigation_resolved
        verdicts = {} if withheld else {
            name: season_b_passes(action, *_lever_cells(cells_b, name, "B")[action]) for name in named
        }
        out.append(SeasonBAgreement(
            action=action,
            label=ACTION_LABELS[action],
            withheld=withheld,
            agree=Stat(Decimal(sum(1 for v in verdicts.values() if v)), "", RULES_B, checked=True),
            total=Stat(Decimal(len(named)), "districts", RULES, checked=True),
            differ=[(n, slug(n)) for n, v in verdicts.items() if v is False],
            blank=[(n, slug(n)) for n, v in verdicts.items() if v is None],
        ))
    return out


def method() -> dict:
    cells, rain, _decisions = data()
    cells_b, irrigation_resolved = season_b()
    keys_b = [key for *_place, key in season_b_screen_cells()]
    checked_b = sum(1 for k in keys_b if cells_b.get(k.table, k.geography, k.farmer_type, k.crop, k.measure).checked)
    footer = footers.read()["29"]
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
        "season_b": season_b_agreement(),
        "season_b_national": [
            (LEVER_LABELS[key][0], cell_stat(small, "%"), cell_stat(large, "%"))
            for key, (small, large) in _lever_cells(cells_b, NATIONAL, "B").items()
            if key != "irrigation" or irrigation_resolved
        ],
        "footer": footer,
        "footer_resolved": irrigation_resolved,
        "footer_source": FOOTER_CHECK,
        "screen_total_b": Stat(Decimal(len(keys_b)), "cells", SIGNOFF_B, checked=True),
        "screen_checked_b": Stat(Decimal(checked_b), "", SIGNOFF_B, checked=True),
        "history_levers": [label for label, _key in HISTORY_COLUMNS],
        "history_tables": history_tables(),
    }


HISTORY_COLUMNS = [("Maize yield", "maize_yield"), ("Large-farm maize yield", "maize_yield_lsf"),
                   ("Improved seed", "seed"), ("Inorganic fertilizer", "fertilizer"), ("Irrigation", "irrigation")]


def history_tables() -> list[tuple[int, str, list[str]]]:
    """For each year: the workbook URL and the table read for each measure."""
    tables, urls = {}, {}
    for p in history().points:
        tables[(p.year, p.lever)] = p.table
        urls[p.year] = p.source_url
    return [(year, urls[year], [tables[(year, key)] for _label, key in HISTORY_COLUMNS]) for year in history().years]
