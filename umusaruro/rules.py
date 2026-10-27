"""Team classification rules for one district.

The cutoffs are ours. They are not NISR thresholds. Irrigation is only
the action when a caller says the district's CHIRPS total sits below the
median of the 30 districts. Until that rainfall flag is known, a district
that meets the irrigation arithmetic stays unresolved.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from umusaruro.cells import BlankCell, Cells
from umusaruro.rainfall import Rainfall

IRRIGATION_GAP = Decimal("30")
IRRIGATION_SSF_MAX = Decimal("15")
SEED_GAP = Decimal("25")
SEED_LEAD = Decimal("5")
FERTILIZER_GAP = Decimal("15")
MAIZE_MILESTONE_KG = Decimal("2260")


@dataclass(frozen=True)
class Decision:
    geography: str
    maize_kg: Decimal | None
    above_milestone: bool | None
    irrigation_gap: Decimal | None
    irrigation_candidate: bool
    seed_gap: Decimal | None
    seed_fires: bool
    fertilizer_gap: Decimal | None
    fertilizer_named: bool
    rainfall_below_median: bool | None
    action: str | None
    unresolved: bool


def _read(cells: Cells, table: str, geography: str, farmer_type: str, crop: str, measure: str):
    cell = cells.get(table, geography, farmer_type, crop, measure)
    try:
        return cell.number()
    except BlankCell:
        return None


def _gap(large: Decimal | None, small: Decimal | None) -> Decimal | None:
    if large is None or small is None:
        return None
    return large - small


def _action(irrigation_gap, irrigation_candidate, seed_gap, seed_fires, rainfall_below_median):
    if not irrigation_candidate:
        return ("seed" if seed_fires else None), False
    if rainfall_below_median is None:
        return None, True
    if not rainfall_below_median:
        return ("seed" if seed_fires else None), False
    if not seed_fires:
        return "irrigation", False
    lead = seed_gap - irrigation_gap
    if lead >= SEED_LEAD:
        return "seed", False
    return "irrigation", False


def classify(cells: Cells, geography: str, rainfall_below_median: bool | None = None) -> Decision:
    maize = _read(cells, "13", geography, "all", "maize", "yield")
    irrigation_ssf = _read(cells, "31", geography, "ssf", "", "irrigation")
    irrigation_lsf = _read(cells, "31", geography, "lsf", "", "irrigation")
    seed_ssf = _read(cells, "20", geography, "ssf", "all_crops", "farmers")
    seed_lsf = _read(cells, "20", geography, "lsf", "all_crops", "farmers")
    fertilizer_ssf = _read(cells, "25", geography, "ssf", "all_crops", "farmers")
    fertilizer_lsf = _read(cells, "25", geography, "lsf", "all_crops", "farmers")

    irrigation_gap = _gap(irrigation_lsf, irrigation_ssf)
    seed_gap = _gap(seed_lsf, seed_ssf)
    fertilizer_gap = _gap(fertilizer_lsf, fertilizer_ssf)
    irrigation_candidate = (
        irrigation_gap is not None
        and irrigation_ssf is not None
        and irrigation_gap >= IRRIGATION_GAP
        and irrigation_ssf < IRRIGATION_SSF_MAX
    )
    seed_fires = seed_gap is not None and seed_gap >= SEED_GAP
    fertilizer_named = fertilizer_gap is not None and fertilizer_gap >= FERTILIZER_GAP
    action, unresolved = _action(
        irrigation_gap, irrigation_candidate, seed_gap, seed_fires, rainfall_below_median
    )
    return Decision(
        geography=geography,
        maize_kg=maize,
        above_milestone=None if maize is None else maize >= MAIZE_MILESTONE_KG,
        irrigation_gap=irrigation_gap,
        irrigation_candidate=irrigation_candidate,
        seed_gap=seed_gap,
        seed_fires=seed_fires,
        fertilizer_gap=fertilizer_gap,
        fertilizer_named=fertilizer_named,
        rainfall_below_median=rainfall_below_median,
        action=action,
        unresolved=unresolved,
    )


def classify_all(cells: Cells, rainfall: dict[str, Rainfall]) -> dict[str, Decision]:
    return {
        district: classify(cells, district, gate.below_median)
        for district, gate in rainfall.items()
    }
