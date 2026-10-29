"""The crop hierarchy.

Each crop keeps the findings the Season A 2026 report actually prints for it.
District yield is Tables 13 and 14. Improved seed is Table 21, and only where
that table names the crop; it is national. Post-harvest loss is Table 16,
national. Irrigation, all-crop seed, and inorganic fertilizer are not split
by crop, so they stay on the district map. A blank cell stays blank. A
national rate is never copied onto a district.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from functools import lru_cache

from sheet.sheet import cell_stat, data, districts, slug
from sheet.stats import Stat, sas_a

NATIONAL = "National"


@dataclass(frozen=True)
class Crop:
    key: str
    en: str
    rw: str
    family: str
    yield_key: str
    use_key: str | None
    seed_key: str | None
    milestone: bool = False
    trend: bool = False
    group: bool = False


@dataclass(frozen=True)
class Family:
    key: str
    en: str
    rw: str
    crops: tuple[Crop, ...]


FAMILIES = (
    Family("cereals", "Cereals", "Impeke", (
        Crop("maize", "Maize", "Ibigori", "cereals", "maize", "maize", "maize", milestone=True, trend=True),
        Crop("sorghum", "Sorghum", "Amasaka", "cereals", "sorghum", "sorghum", None),
        Crop("paddy_rice", "Rice", "Umuceri", "cereals", "paddy_rice", "paddy_rice", "paddy_rice"),
        Crop("wheat", "Wheat", "Ingano", "cereals", "wheat", "wheat", "wheat"),
        Crop("other_cereals", "Other cereals", "Izindi mpeke", "cereals", "other_cereals", "other_cereals", None, group=True),
    )),
    Family("roots", "Roots and tubers", "Imizi", (
        Crop("cassava", "Cassava", "Imyumbati", "roots", "cassava", "cassava", "cassava"),
        Crop("sweet_potatoes", "Sweet potato", "Ibijumba", "roots", "sweet_potatoes", "sweet_potato", None),
        Crop("irish_potatoes", "Irish potato", "Ibirayi", "roots", "irish_potatoes", "irish_potato", "irish_potato"),
        Crop("yams_taro", "Yams and taro", "Ibikoro n'amateke", "roots", "yams_taro", "yam_taro", None),
    )),
    Family("banana", "Banana", "Ibitoki", (
        Crop("bananas", "Banana, all types", "Ibitoki", "banana", "bananas", None, None, group=True),
        Crop("cooking_banana", "Cooking banana", "Ibitoki byo guteka", "banana", "cooking_banana", "cooking_banana", "cooking_banana"),
        Crop("dessert_banana", "Dessert banana", "Ibitoki byo kurya", "banana", "dessert_banana", "dessert_banana", "dessert_banana"),
        Crop("banana_for_beer", "Banana for beer", "Ibitoki by'inzoga", "banana", "banana_for_beer", "banana_for_beer", "banana_for_beer"),
    )),
    Family("legumes", "Legumes", "Ibishyimbo", (
        Crop("beans", "Beans, all types", "Ibishyimbo", "legumes", "beans", None, None, group=True),
        Crop("bush_bean", "Bush bean", "Ibishyimbo byo hasi", "legumes", "bush_bean", "bush_bean", "bush_bean"),
        Crop("climbing_bean", "Climbing bean", "Ibishyimbo byo kuzamuka", "legumes", "climbing_bean", "climbing_bean", "climbing_bean"),
        Crop("peas", "Peas", "Amashaza", "legumes", "peas", "pea", "pea"),
        Crop("ground_nuts", "Groundnut", "Ubunyobwa", "legumes", "ground_nuts", "groundnut", None),
        Crop("soya_beans", "Soybean", "Soya", "legumes", "soya_beans", "soybean", "soybean"),
    )),
    Family("garden", "Garden and other crops", "Ibindi bihingwa", (
        Crop("vegetables", "Vegetables", "Imboga", "garden", "vegetables", "vegetables", "vegetables", group=True),
        Crop("fruits", "Fruits", "Imbuto z'ibiti", "garden", "fruits", "fruits", "fruits", group=True),
        Crop("fodder_crops", "Fodder", "Ibihingwa by'amatungo", "garden", "fodder_crops", "fodder_crops", "fodder_crops", group=True),
        Crop("other_crops", "Other crops", "Ibindi", "garden", "other_crops", "other_crops", "other_crops", group=True),
    )),
)

CROPS = {crop.key: crop for family in FAMILIES for crop in family.crops}


@dataclass(frozen=True)
class PlaceYield:
    name: str
    slug: str
    all_farms: Stat
    large_farms: Stat
    share: int = 0


def _yield(cells, table: str, geography: str, crop: str) -> Stat:
    farmer = "lsf" if table == "14" else "all"
    return cell_stat(cells.get(table, geography, farmer, crop, "yield"), "kg/ha")


def _percent(cells, table: str, crop: str, measure: str) -> Stat:
    return cell_stat(cells.get(table, NATIONAL, "all", crop, measure), "%")


def _count(value: int, checked: bool) -> Stat:
    return Stat(Decimal(value), "districts", sas_a("13"), checked=checked)


def _crop_count(value: int) -> Stat:
    return Stat(Decimal(value), "crops", sas_a("13"), checked=False)


def _share(value: Decimal | None, peak: Decimal | None) -> int:
    """0–100 against the highest printed value in the same picture. Not shown as a number."""
    if value is None or peak is None or peak == 0:
        return 0
    return max(1, int((value / peak) * Decimal(100)))


@lru_cache(maxsize=1)
def _built() -> dict[str, dict]:
    cells, _rain, _decisions = data()
    pages = {}
    for crop in CROPS.values():
        draft = []
        for name in districts():
            draft.append((name, _yield(cells, "13", name, crop.yield_key), _yield(cells, "14", name, crop.yield_key)))
        peak = max((all_farms.value for _name, all_farms, _large in draft if all_farms.value is not None), default=None)
        places = [
            PlaceYield(name, slug(name), all_farms, large_farms, _share(all_farms.value, peak))
            for name, all_farms, large_farms in draft
        ]
        national = _yield(cells, "13", NATIONAL, crop.yield_key)
        large = _yield(cells, "14", NATIONAL, crop.yield_key)
        printed = [place for place in places if place.all_farms.value is not None]
        leaders = []
        if printed:
            highest = max(place.all_farms.value for place in printed)
            leaders = [place for place in printed if place.all_farms.value == highest]
        pages[crop.key] = {
            "crop": crop,
            "family": next(family for family in FAMILIES if family.key == crop.family),
            "national": national,
            "national_large": large,
            "places": places,
            "printed": _count(len(printed), all(place.all_farms.checked for place in places)),
            "has_blanks": len(printed) < len(places),
            "leaders": leaders,
            "large_is_lower": (
                national.value is not None and large.value is not None and large.value < national.value
            ),
            "seed": _percent(cells, "21", crop.seed_key, "improved") if crop.seed_key else None,
            "loss": _percent(cells, "16", crop.use_key, "post_harvest_loss") if crop.use_key else None,
            "sold": _percent(cells, "16", crop.use_key, "sold") if crop.use_key else None,
            "stored": _percent(cells, "16", crop.use_key, "stored") if crop.use_key else None,
        }
    return pages


def crop_page(key: str) -> dict | None:
    return _built().get(key)


def home() -> dict:
    pages = _built()
    families = []
    for family in FAMILIES:
        peak = max(
            (pages[crop.key]["national"].value for crop in family.crops if pages[crop.key]["national"].value is not None),
            default=None,
        )
        families.append({
            "key": family.key,
            "en": family.en,
            "rw": family.rw,
            "crops": [
                {
                    "key": crop.key,
                    "en": crop.en,
                    "rw": crop.rw,
                    "national": pages[crop.key]["national"],
                    "printed": pages[crop.key]["printed"],
                    "share": _share(pages[crop.key]["national"].value, peak),
                    "milestone": crop.milestone,
                    "trend": crop.trend,
                }
                for crop in family.crops
            ],
        })
    return {"families": families, "crop_count": _crop_count(len(CROPS))}
