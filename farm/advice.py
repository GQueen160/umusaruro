"""Plain advice for one district and the crops a farmer named.

Numbers come from the Season A 2026 cell file and the CHIRPS rainfall
gate. A blank cell stays blank. The survey does not name a seed variety
and does not publish a soil test, so the advice does not invent either.
"""

from __future__ import annotations

from decimal import Decimal
from functools import lru_cache

from umusaruro.cells import load as load_cells
from umusaruro.rainfall import load as load_rainfall
from umusaruro.rules import classify

SAS_A = (
    "https://statistics.gov.rw/sites/default/files/documents/2026-04/"
    "SAS%202026%20Season%20A%20_Final%20Report.pdf"
)
CHIRPS = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/africa_monthly/tifs/"

# Keys are the crop names in data/season_a_2026/cells.csv.
CROPS = (
    ("maize", "Ibigori", "Maize", ("ibigori", "maize", "corn")),
    ("beans", "Ibishyimbo", "Beans", ("ibishyimbo", "beans", "bean")),
    ("paddy_rice", "Umuceri", "Rice", ("umuceri", "rice", "paddy")),
    ("irish_potatoes", "Ibirayi", "Potato", ("ibirayi", "potato", "potatoes")),
    ("sweet_potatoes", "Ibijumba", "Sweet potato", ("ibijumba", "sweet potato", "sweet potatoes")),
    ("cassava", "Imyumbati", "Cassava", ("imyumbati", "cassava")),
    ("sorghum", "Amasaka", "Sorghum", ("amasaka", "sorghum")),
    ("bananas", "Ibitoki", "Banana", ("ibitoki", "banana", "bananas")),
    ("vegetables", "Imboga", "Vegetables", ("imboga", "vegetables", "vegetable")),
    ("soya_beans", "Soya", "Soybean", ("soya", "soybean", "soybeans")),
    ("ground_nuts", "Ubunyobwa", "Groundnut", ("ubunyobwa", "groundnut", "groundnuts")),
    ("wheat", "Ingano", "Wheat", ("ingano", "wheat")),
)


def crop_list() -> list[dict]:
    return [{"id": key, "rw": rw, "en": en} for key, rw, en, _ in CROPS]


def crop_label(key: str) -> tuple[str, str]:
    for item, rw, en, _ in CROPS:
        if item == key:
            return rw, en
    return key, key


def crops_in(text: str) -> list[str]:
    found = []
    for key, _, _, words in CROPS:
        if any(_word(word, text) for word in words):
            found.append(key)
    return found[:4]


def _word(word: str, text: str) -> bool:
    import re
    return re.search(rf"(?<![\w]){re.escape(word)}(?![\w])", text) is not None


@lru_cache(maxsize=1)
def _cells():
    return load_cells()


@lru_cache(maxsize=1)
def _rain():
    return load_rainfall()


def _read(table: str, geography: str, farmer_type: str, crop: str, measure: str):
    try:
        cell = _cells().get(table, geography, farmer_type, crop, measure)
    except KeyError:
        return None
    if cell.blank or cell.value is None:
        return None
    return cell.value


def pretty(value: Decimal | None) -> str | None:
    if value is None:
        return None
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    whole, dot, frac = text.partition(".")
    sign = ""
    if whole.startswith("-"):
        sign, whole = "-", whole[1:]
    groups = []
    while whole:
        groups.append(whole[-3:])
        whole = whole[:-3]
    body = sign + ",".join(reversed(groups))
    return body if not frac else body + dot + frac


def _fact(value: Decimal | None, unit: str, table: str, label: str) -> dict | None:
    shown = pretty(value)
    if shown is None:
        return None
    return {
        "label": label,
        "value": shown,
        "unit": unit,
        "table": table,
        "survey": "SAS A 2026",
        "url": SAS_A,
    }


def _yields(district: str, crop: str) -> dict:
    return {
        "all": _read("13", district, "all", crop, "yield"),
        "large": _read("14", district, "lsf", crop, "yield"),
        "national": _read("13", "National", "all", crop, "yield"),
    }


def _target(yields: dict) -> tuple[Decimal | None, str, str]:
    if yields["large"] is not None:
        return yields["large"], "Ni umusaruro w'abahinzi binini muri aka karere.", "This is what large farms harvested in this district."
    if yields["all"] is not None:
        return yields["all"], "Ni umusaruro w'akarere. Umubare w'abahinzi binini ntubonetse.", "This is the district harvest. The large-farm number was not printed."
    if yields["national"] is not None:
        return yields["national"], "Ni umusaruro w'igihugu. Aka karere ntikagaragaje umubare.", "This is the national harvest. This district's number was not printed."
    return None, "Nta mubare wo gushyiraho. Si zeru.", "There is no number to aim at. That is not zero."


def advise(district: str, crops: list[str]) -> dict:
    known = [crop for crop in crops if crop in {key for key, *_ in CROPS}]
    rain = _rain().get(district)
    decision = classify(_cells(), district, None if rain is None else rain.below_median)
    cards = []

    if decision.action == "irrigation":
        small = _read("31", district, "ssf", "", "irrigation")
        large = _read("31", district, "lsf", "", "irrigation")
        cards.append({
            "kind": "water",
            "first": True,
            "title_rw": "Voma",
            "title_en": "Irrigate",
            "body_rw": (
                f"Muri {district}, abahinzi bato bavoma bike kurusha abahinzi binini, "
                "kandi imvura y'iki gihembwe yari munsi y'ibindi bice. Tegura amazi kare."
            ),
            "body_en": "Small farms irrigate much less than large farms here, and this season was drier than most districts. Prepare water early.",
            "facts": [item for item in (
                _fact(small, "%", "31", "Abahinzi bato"),
                _fact(large, "%", "31", "Abahinzi binini"),
                None if rain is None else {
                    "label": "Imvura",
                    "value": pretty(rain.total_mm),
                    "unit": "mm",
                    "table": "Sep 2025–Feb 2026",
                    "survey": rain.version,
                    "url": CHIRPS,
                },
            ) if item],
        })
    elif decision.action == "seed":
        cards.append(_seed_card(district, first=True))
    elif decision.action is None and not decision.unresolved:
        cards.append({
            "kind": "note",
            "first": True,
            "title_rw": "Komeza",
            "title_en": "Keep going",
            "body_rw": f"Ibi bipimo bya {district} ntibisaba kuvoma cyangwa imbuto zizungu mbere y'ibindi.",
            "body_en": "These district figures do not put irrigation or improved seed first.",
            "facts": [],
        })

    if decision.action != "seed" and decision.seed_fires:
        cards.append(_seed_card(district, first=False))
    if decision.fertilizer_named:
        small = _read("25", district, "ssf", "all_crops", "farmers")
        large = _read("25", district, "lsf", "all_crops", "farmers")
        cards.append({
            "kind": "fertilizer",
            "first": False,
            "title_rw": "Ifumbire",
            "title_en": "Fertilizer",
            "body_rw": "Ifumbire mvaruganda ikoreshwa n'abahinzi bato bike kurusha abahinzi binini. Yishyire ukurikije uburyo bwemewe.",
            "body_en": "Small farms use inorganic fertilizer less often than large farms. Apply it the way the extension service teaches.",
            "facts": [item for item in (
                _fact(small, "%", "25", "Abahinzi bato"),
                _fact(large, "%", "25", "Abahinzi binini"),
            ) if item],
        })

    crop_cards = []
    comparable = []
    for crop in known:
        yields = _yields(district, crop)
        rw, en = crop_label(crop)
        target, why_rw, why_en = _target(yields)
        if yields["all"] is not None:
            comparable.append((yields["all"], crop, rw))
        sentence = _yield_sentence(district, rw, yields)
        crop_cards.append({
            "kind": "crop",
            "crop": crop,
            "title_rw": rw,
            "title_en": en,
            "body_rw": sentence,
            "body_en": _yield_sentence_en(district, en, yields),
            "facts": [item for item in (
                _fact(yields["all"], "kg/ha", "13", "Akarere"),
                _fact(yields["large"], "kg/ha", "14", "Abahinzi binini"),
                _fact(yields["national"], "kg/ha", "13", "Igihugu"),
            ) if item],
            "target_kg": None if target is None else str(target),
            "target_rw": why_rw,
            "target_en": why_en,
        })

    stronger = None
    if len(comparable) >= 2:
        _, crop, rw = max(comparable)
        stronger = crop
        amount = next(card for card in crop_cards if card["crop"] == crop)
        shown = next(fact["value"] for fact in amount["facts"] if fact["label"] == "Akarere")
        cards.insert(0, {
            "kind": "stronger",
            "first": True,
            "title_rw": f"{rw} nirwo riruta",
            "title_en": f"{crop_label(crop)[1]} yields more here",
            "body_rw": (
                f"Muri ibyo wahisemo, {rw} ni cyo gifite umusaruro munini muri {district}: {shown} kg kuri hegitari. "
                "Iki si izina ry'imbuto. Raporo ntivuga imbuto imwe iruta iyindi."
            ),
            "body_en": "Among the crops you chose, this one has the higher published yield in the district. The survey does not name a seed variety.",
            "facts": [],
        })

    if "maize" in known:
        national_improved = _read("21", "National", "all", "maize", "improved")
        fact = _fact(national_improved, "%", "21", "Igihugu, ibigori")
        if fact:
            cards.append({
                "kind": "seed",
                "first": False,
                "title_rw": "Ibigori ku gihugu",
                "title_en": "Maize seed, national",
                "body_rw": "Ku gihugu, imbuto z'ibigori zizungu ni zimwe mu mbuto zikoreshwa. Iyi mibare nta karere ifite.",
                "body_en": "Nationally, this share of maize seed is improved. The table has no district column.",
                "facts": [fact],
            })

    cards.extend(crop_cards)
    cards.append({
        "kind": "soil",
        "first": False,
        "title_rw": "Ubutaka",
        "title_en": "Soil",
        "body_rw": "Iyi raporo nta mpuzandengo y'ubutaka ifite, kandi ntivuga izina ry'imbuto. Inama ikoresha umusaruro, imbuto zizungu, ifumbire, n'imvura by'akarere.",
        "body_en": "This report has no soil test and no seed-variety name. The advice uses the district harvest, improved seed, fertilizer, and rainfall.",
        "facts": [],
    })

    suggested = None
    ordered = crop_cards
    if stronger:
        ordered = [card for card in crop_cards if card["crop"] == stronger] + [
            card for card in crop_cards if card["crop"] != stronger
        ]
    for card in ordered:
        if card["target_kg"] is not None:
            suggested = {
                "crop": card["crop"],
                "rw": card["title_rw"],
                "en": card["title_en"],
                "kg": card["target_kg"],
                "why_rw": card["target_rw"],
                "why_en": card["target_en"],
            }
            break

    return {
        "district": district,
        "action": decision.action,
        "crops": known,
        "stronger": stronger,
        "cards": cards,
        "target": suggested,
        "level": "district",
        "note_rw": f"Imibare ni iya karere ka {district}, si iy'umudugudu. Raporo ntisoza umudugudu.",
        "note_en": f"These numbers are for {district} district, not for one village. The survey is not published per village.",
    }


def _seed_card(district: str, first: bool) -> dict:
    small = _read("20", district, "ssf", "all_crops", "farmers")
    large = _read("20", district, "lsf", "all_crops", "farmers")
    return {
        "kind": "seed",
        "first": first,
        "title_rw": "Imbuto zizungu",
        "title_en": "Improved seed",
        "body_rw": (
            f"Muri {district}, abahinzi bato bakoresha imbuto zizungu bike kurusha abahinzi binini. "
            "Ibi ni ibihingwa byose, si ibigori gusa. Raporo ntivuga izina ry'imbuto."
        ),
        "body_en": "Small farms use improved seed less often than large farms. This is all crops, not one variety name. The survey does not name the variety.",
        "facts": [item for item in (
            _fact(small, "%", "20", "Abahinzi bato"),
            _fact(large, "%", "20", "Abahinzi binini"),
        ) if item],
    }


def _yield_sentence(district: str, name: str, yields: dict) -> str:
    shown = pretty(yields["all"])
    if shown is None:
        return f"Umusaruro wa {name} muri {district} ntubonetse muri raporo. Si zeru."
    large = pretty(yields["large"])
    extra = "" if large is None else f" Abahinzi binini basaruye {large} kg kuri hegitari."
    return f"Muri {district}, umusaruro wa {name} ni {shown} kg kuri hegitari.{extra}"


def _yield_sentence_en(district: str, name: str, yields: dict) -> str:
    shown = pretty(yields["all"])
    if shown is None:
        return f"The {name} harvest in {district} was not printed. It is not zero."
    large = pretty(yields["large"])
    extra = "" if large is None else f" Large farms harvested {large} kg per hectare."
    return f"In {district}, {name} yielded {shown} kg per hectare.{extra}"
