"""What the engine recognises: places, crops, measures, farm types.

Every rule here is a plain list of words, so a reviewer can read why a
column was read as maize yield or a table as inorganic fertilizer use. A
column or table that matches nothing is not guessed at; it is listed as
unrecognised and a person maps it on the review screen.
"""

from __future__ import annotations

import csv
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DISTRICTS_CSV = Path(__file__).resolve().parents[1] / "data" / "reference" / "districts.csv"
NATIONAL = "National"
NATIONAL_LABELS = {"national": "all", "total": "all", "rwanda": "all", "national_lsf": "lsf",
                   "ssf": "ssf", "small scale farmer": "ssf", "small scale farmers": "ssf",
                   "lsf": "lsf", "larger scale farmer": "lsf", "large scale farmer": "lsf", "large scale farmers": "lsf"}


def norm(text) -> str:
    return " ".join(str(text).replace("\u00a0", " ").split()).strip().lower() if text is not None else ""


@lru_cache(maxsize=1)
def districts() -> dict[str, dict]:
    """Normalised name -> {district_id, district, province}."""
    with DISTRICTS_CSV.open(newline="", encoding="utf-8") as handle:
        return {norm(r["district"]): r for r in csv.DictReader(handle)}


def district(label) -> dict | None:
    return districts().get(norm(label))


# Canonical crop key -> label, then the words that name it in a header.
CROPS = {
    "maize": ("Maize", ["maize", "corn"]),
    "sorghum": ("Sorghum", ["sorghum"]),
    "paddy_rice": ("Paddy rice", ["paddy rice", "rice", "paddy"]),
    "wheat": ("Wheat", ["wheat"]),
    "other_cereals": ("Other cereals", ["other cereals"]),
    "cassava": ("Cassava", ["cassava"]),
    "sweet_potato": ("Sweet potato", ["sweet potato", "sweet potatoes", "sweet potatoe"]),
    "irish_potato": ("Irish potato", ["irish potato", "irish potatoes", "irish potatoe", "potato", "potatoes"]),
    "yams_taro": ("Yams and taro", ["yams & taro", "yams and taro", "yam & taro", "taro & yams", "taro and yams",
                                         "yams", "taro"]),
    "banana": ("Banana, all types", ["banana", "bananas"]),
    "cooking_banana": ("Cooking banana", ["cooking banana", "cooking bananas"]),
    "dessert_banana": ("Dessert banana", ["dessert banana", "dessert bananas"]),
    "beer_banana": ("Banana for beer", ["banana for beer", "beer banana", "for beer"]),
    "beans": ("Beans, all types", ["beans", "bean"]),
    "bush_bean": ("Bush bean", ["bush bean", "bush beans"]),
    "climbing_bean": ("Climbing bean", ["climbing bean", "climbing beans"]),
    "peas": ("Peas", ["peas", "pea"]),
    "groundnut": ("Groundnut", ["groundnut", "groundnuts", "ground nuts", "ground nut"]),
    "soybean": ("Soybean", ["soybean", "soybeans", "soya beans", "soya bean", "soy beans"]),
    "vegetables": ("Vegetables", ["vegetables", "vegetable"]),
    "fruits": ("Fruits", ["fruits", "fruit"]),
    "fodder": ("Fodder crops", ["fodder crops", "fodder"]),
    "other_crops": ("Other crops", ["other crops"]),
}
CROP_WORDS = {word: key for key, (_label, words) in CROPS.items() for word in words}
AGGREGATES = {"cereals", "tubers and roots", "tubers & roots", "legumes and pulses", "legumes", "total", "all crops"}


def crop(label) -> str | None:
    return CROP_WORDS.get(norm(label))


@dataclass(frozen=True)
class Measure:
    key: str
    label: str
    unit: str
    kind: str  # "crop" measures need a crop; "input" measures describe all crops in a district


MEASURES = {m.key: m for m in [
    Measure("yield", "Average yield", "kg/ha", "crop"),
    Measure("production", "Production", "t", "crop"),
    Measure("cultivated_area", "Cultivated area", "ha", "crop"),
    Measure("harvested_area", "Harvested area", "ha", "crop"),
    Measure("improved_seed", "Farmers using improved seed", "%", "input"),
    Measure("inorganic_fertilizer", "Farmers using inorganic fertilizer", "%", "input"),
    Measure("organic_fertilizer", "Farmers using organic fertilizer", "%", "input"),
    Measure("pesticides", "Farmers using pesticides", "%", "input"),
    Measure("irrigation", "Farmers practising irrigation", "%", "input"),
    Measure("erosion_control", "Farmers practising erosion control", "%", "input"),
    Measure("mechanization", "Farmers using mechanization", "%", "input"),
    Measure("agroforestry", "Farmers practising agroforestry", "%", "input"),
    Measure("rainfall", "Rainfall", "mm", "input"),
]}
PRACTICES = "practices"

# A title containing any of these is not a district measure the engine reads.
EXCLUDE = ["source of", "type of", "types of", "degree of", "share of", "use type", "sowing", "cropping system",
           "plot size", "land use", "ownership", "land source", "sampled", "segments", "stratum", "area under",
           "number of crops", "gross value", "list of", "summary", "irrigation type", "water used", "detailed", "categories of"]

# (measure, pattern) in order; the first match wins.
TITLE_RULES = [
    ("yield", r"\byield"),
    ("harvested_area", r"harvested area"),
    ("cultivated_area", r"cultivated area|area cultivated|planted area"),
    ("production", r"\bproduction\b"),
    ("organic_fertilizer", r"(?<!in)organic fertili[sz]er"),
    ("inorganic_fertilizer", r"inorganic fertili[sz]er"),
    ("improved_seed", r"use of seeds?|improved seeds?|seed use"),
    ("pesticides", r"pesticide"),
    ("irrigation", r"irrigation practice|practi[cs]ed irrigation|irrigation"),
    ("erosion_control", r"erosion control"),
    (PRACTICES, r"agricultural practices"),
    ("rainfall", r"rainfall|precipitation"),
]
GROUP_RULES = [
    ("erosion_control", r"erosion"),
    ("mechanization", r"mechani"),
    ("irrigation", r"irrigat"),
    ("agroforestry", r"agroforest"),
]


def title_measure(title: str) -> str | None:
    text = norm(title)
    if any(word in text for word in EXCLUDE):
        return None
    for key, pattern in TITLE_RULES:
        if re.search(pattern, text):
            return key
    return None


def group_measure(text: str) -> str | None:
    for key, pattern in GROUP_RULES:
        if re.search(pattern, norm(text)):
            return key
    return None


def yield_unit(title: str) -> str:
    return "t/ha" if re.search(r"\b(mt|t|tonnes?)\s*/\s*ha", norm(title)) else "kg/ha"


def season(text: str) -> str:
    match = re.search(r"season\s*([abc])(?![a-z])", norm(text))
    return match.group(1).upper() if match else ""


def year(text: str) -> int | None:
    match = re.search(r"(?<!\d)(20[0-9]{2})(?!\d)", str(text))
    return int(match.group(1)) if match else None


def table_number(text: str) -> str:
    match = re.search(r"table\s*(\d+)", norm(text))
    return match.group(1) if match else ""


FARMER_WORDS = {"overall": "all", "all": "all", "ssf": "ssf", "lsf": "lsf"}
BASIS_PATTERNS = [("farmers", r"farmers?"), ("plots", r"plots?"), ("land", r"\bland\b|area")]
ANSWERS = {"yes", "no", "traditional", "improved"}
KEEP_ANSWERS = {"yes", "improved"}


def farmer_type(parts: list[str]) -> str | None:
    for part in parts:
        if part in FARMER_WORDS:
            return FARMER_WORDS[part]
        if "large scale" in part or "large-scale" in part:
            return "lsf"
        if "small scale" in part or "small-scale" in part:
            return "ssf"
    return None


def basis(parts: list[str]) -> str:
    for part in parts:
        if part.startswith("percentage of") or part.startswith("farmers who"):
            for key, pattern in BASIS_PATTERNS:
                if re.search(pattern, part):
                    return key
    return ""
