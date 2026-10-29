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
    ("maize", "Ibigori", "Maize", "Maïs", ("ibigori", "maize", "corn")),
    ("beans", "Ibishyimbo", "Beans", "Haricots", ("ibishyimbo", "beans", "bean")),
    ("paddy_rice", "Umuceri", "Rice", "Riz", ("umuceri", "rice", "paddy")),
    ("irish_potatoes", "Ibirayi", "Potato", "Pomme de terre", ("ibirayi", "potato", "potatoes")),
    ("sweet_potatoes", "Ibijumba", "Sweet potato", "Patate douce", ("ibijumba", "sweet potato", "sweet potatoes")),
    ("cassava", "Imyumbati", "Cassava", "Manioc", ("imyumbati", "cassava")),
    ("sorghum", "Amasaka", "Sorghum", "Sorgho", ("amasaka", "sorghum")),
    ("bananas", "Ibitoki", "Banana", "Banane", ("ibitoki", "banana", "bananas")),
    ("vegetables", "Imboga", "Vegetables", "Légumes", ("imboga", "vegetables", "vegetable")),
    ("soya_beans", "Soya", "Soybean", "Soja", ("soya", "soybean", "soybeans")),
    ("ground_nuts", "Ubunyobwa", "Groundnut", "Arachide", ("ubunyobwa", "groundnut", "groundnuts")),
    ("wheat", "Ingano", "Wheat", "Blé", ("ingano", "wheat")),
)

FARM = {
    "small": {"rw": "Abahinzi bato", "en": "Small farms", "fr": "Petites exploitations"},
    "large": {"rw": "Abahinzi binini", "en": "Large farms", "fr": "Grandes exploitations"},
    "rain": {"rw": "Imvura", "en": "Rainfall", "fr": "Pluie"},
    "district": {"rw": "Akarere", "en": "District", "fr": "District"},
    "national": {"rw": "Igihugu", "en": "National", "fr": "National"},
    "maize_national": {"rw": "Igihugu, ibigori", "en": "National, maize", "fr": "National, maïs"},
}


def crop_list() -> list[dict]:
    return [{"id": key, "rw": rw, "en": en, "fr": fr} for key, rw, en, fr, _ in CROPS]


def crop_label(key: str) -> tuple[str, str, str]:
    for item, rw, en, fr, _ in CROPS:
        if item == key:
            return rw, en, fr
    return key, key, key


def crops_in(text: str) -> list[str]:
    found = []
    for key, _, _, _, words in CROPS:
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


def _fact(value: Decimal | None, unit: str, table: str, label) -> dict | None:
    shown = pretty(value)
    if shown is None:
        return None
    labels = label if isinstance(label, dict) else {"rw": label, "en": label, "fr": label}
    return {
        "label": labels["rw"],
        "labels": labels,
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


def _why(rw: str, en: str, fr: str) -> dict:
    return {"rw": rw, "en": en, "fr": fr}


def _target(yields: dict, reader: str = "farmer-large") -> tuple[Decimal | None, dict]:
    # Table 14 prints large farms. It does not print a mini-farm yield for one
    # district, and the national smallholder rate is not copied onto a district.
    blank = _why("Nta mubare wo gushyiraho. Si zeru.", "There is no number to aim at. That is not zero.", "Il n'y a pas de chiffre à viser. Ce n'est pas zéro.")
    national = _why(
        "Ni umusaruro w'igihugu. Aka karere ntikagaragaje umubare.",
        "This is the national harvest. This district's number was not printed.",
        "C'est la récolte nationale. Le chiffre de ce district n'a pas été imprimé.",
    )
    if reader == "farmer-mini":
        if yields["all"] is not None:
            return yields["all"], _why(
                "Ni umusaruro w'akarere, abahinzi bose. Raporo nta musaruro w'umuhinzi muto isohora ku karere.",
                "This is the district harvest for all farms. The survey does not print a mini-farm yield for one district.",
                "C'est la récolte du district, toutes les exploitations. L'enquête n'imprime pas une récolte de petite exploitation pour un district.",
            )
        if yields["national"] is not None:
            return yields["national"], national
        return None, blank
    if yields["large"] is not None:
        return yields["large"], _why(
            "Ni umusaruro w'abahinzi binini muri aka karere.",
            "This is what large farms harvested in this district.",
            "C'est ce que les grandes exploitations ont récolté dans ce district.",
        )
    if yields["all"] is not None:
        return yields["all"], _why(
            "Ni umusaruro w'akarere. Umubare w'abahinzi binini ntubonetse.",
            "This is the district harvest. The large-farm number was not printed.",
            "C'est la récolte du district. Le chiffre des grandes exploitations n'a pas été imprimé.",
        )
    if yields["national"] is not None:
        return yields["national"], national
    return None, blank


def advise(district: str, crops: list[str], reader: str = "farmer-large") -> dict:
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
            "title_fr": "Irriguer",
            "body_rw": (
                f"Muri {district}, abahinzi bato bavoma bike kurusha abahinzi binini, "
                "kandi imvura y'iki gihembwe yari munsi y'ibindi bice. Tegura amazi kare."
            ),
            "body_en": "Small farms irrigate much less than large farms here, and this season was drier than most districts. Prepare water early.",
            "body_fr": "Les petites exploitations irriguent beaucoup moins que les grandes ici, et la saison a été plus sèche que dans la plupart des districts. Préparez l'eau tôt.",
            "facts": [item for item in (
                _fact(small, "%", "31", FARM["small"]),
                _fact(large, "%", "31", FARM["large"]),
                None if rain is None else {
                    "label": FARM["rain"]["rw"],
                    "labels": FARM["rain"],
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
            "title_fr": "Continuer",
            "body_rw": f"Ibi bipimo bya {district} ntibisaba kuvoma cyangwa imbuto zizungu mbere y'ibindi.",
            "body_en": "These district figures do not put irrigation or improved seed first.",
            "body_fr": "Ces chiffres du district ne mettent pas l'irrigation ou la semence améliorée en premier.",
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
            "title_fr": "Engrais",
            "body_rw": "Ifumbire mvaruganda ikoreshwa n'abahinzi bato bike kurusha abahinzi binini. Yishyire ukurikije uburyo bwemewe.",
            "body_en": "Small farms use inorganic fertilizer less often than large farms. Apply it the way the extension service teaches.",
            "body_fr": "Les petites exploitations utilisent moins souvent l'engrais minéral que les grandes. Appliquez-le comme le service de vulgarisation l'enseigne.",
            "facts": [item for item in (
                _fact(small, "%", "25", FARM["small"]),
                _fact(large, "%", "25", FARM["large"]),
            ) if item],
        })

    crop_cards = []
    comparable = []
    for crop in known:
        yields = _yields(district, crop)
        rw, en, fr = crop_label(crop)
        target, why = _target(yields, reader)
        if yields["all"] is not None:
            comparable.append((yields["all"], crop, rw))
        sentence = _yield_sentence(district, rw, yields)
        crop_cards.append({
            "kind": "crop",
            "crop": crop,
            "title_rw": rw,
            "title_en": en,
            "title_fr": fr,
            "body_rw": sentence,
            "body_en": _yield_sentence_en(district, en, yields),
            "body_fr": _yield_sentence_fr(district, fr, yields),
            "facts": [item for item in (
                _fact(yields["all"], "kg/ha", "13", FARM["district"]),
                _fact(yields["large"], "kg/ha", "14", FARM["large"]),
                _fact(yields["national"], "kg/ha", "13", FARM["national"]),
            ) if item],
            "target_kg": None if target is None else str(target),
            "target_rw": why["rw"],
            "target_en": why["en"],
            "target_fr": why["fr"],
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
            "title_fr": f"{crop_label(crop)[2]} rend plus ici",
            "body_rw": (
                f"Muri ibyo wahisemo, {rw} ni cyo gifite umusaruro munini muri {district}: {shown} kg kuri hegitari. "
                "Iki si izina ry'imbuto. Raporo ntivuga imbuto imwe iruta iyindi."
            ),
            "body_en": "Among the crops you chose, this one has the higher published yield in the district. The survey does not name a seed variety.",
            "body_fr": "Parmi les cultures choisies, celle-ci a le rendement publié le plus élevé dans le district. L'enquête ne nomme pas une variété.",
            "facts": [],
        })

    if "maize" in known:
        national_improved = _read("21", "National", "all", "maize", "improved")
        fact = _fact(national_improved, "%", "21", FARM["maize_national"])
        if fact:
            cards.append({
                "kind": "seed",
                "first": False,
                "title_rw": "Ibigori ku gihugu",
                "title_en": "Maize seed, national",
                "title_fr": "Semence de maïs, nationale",
                "body_rw": "Ku gihugu, imbuto z'ibigori zizungu ni zimwe mu mbuto zikoreshwa. Iyi mibare nta karere ifite.",
                "body_en": "Nationally, this share of maize seed is improved. The table has no district column.",
                "body_fr": "Au niveau national, cette part de la semence de maïs est améliorée. Le tableau n'a pas de colonne par district.",
                "facts": [fact],
            })

    cards.extend(crop_cards)
    cards.append({
        "kind": "soil",
        "first": False,
        "title_rw": "Ubutaka",
        "title_en": "Soil",
        "title_fr": "Sol",
        "body_rw": "Iyi raporo nta mpuzandengo y'ubutaka ifite, kandi ntivuga izina ry'imbuto. Inama ikoresha umusaruro, imbuto zizungu, ifumbire, n'imvura by'akarere.",
        "body_en": "This report has no soil test and no seed-variety name. The advice uses the district harvest, improved seed, fertilizer, and rainfall.",
        "body_fr": "Ce rapport n'a pas d'analyse de sol et ne nomme pas de variété. Le conseil utilise la récolte du district, la semence améliorée, l'engrais et la pluie.",
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
                "fr": card["title_fr"],
                "kg": card["target_kg"],
                "why_rw": card["target_rw"],
                "why_en": card["target_en"],
                "why_fr": card["target_fr"],
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
        "note_fr": f"Ces chiffres sont ceux du district de {district}, pas d'un village. L'enquête n'est pas publiée par village.",
    }


def _seed_card(district: str, first: bool) -> dict:
    small = _read("20", district, "ssf", "all_crops", "farmers")
    large = _read("20", district, "lsf", "all_crops", "farmers")
    return {
        "kind": "seed",
        "first": first,
        "title_rw": "Imbuto zizungu",
        "title_en": "Improved seed",
        "title_fr": "Semence améliorée",
        "body_rw": (
            f"Muri {district}, abahinzi bato bakoresha imbuto zizungu bike kurusha abahinzi binini. "
            "Ibi ni ibihingwa byose, si ibigori gusa. Raporo ntivuga izina ry'imbuto."
        ),
        "body_en": "Small farms use improved seed less often than large farms. This is all crops, not one variety name. The survey does not name the variety.",
        "body_fr": "Les petites exploitations utilisent moins souvent la semence améliorée que les grandes. C'est toutes les cultures, pas un nom de variété. L'enquête ne nomme pas la variété.",
        "facts": [item for item in (
            _fact(small, "%", "20", FARM["small"]),
            _fact(large, "%", "20", FARM["large"]),
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


def _yield_sentence_fr(district: str, name: str, yields: dict) -> str:
    shown = pretty(yields["all"])
    if shown is None:
        return f"La récolte de {name} à {district} n'a pas été imprimée. Ce n'est pas zéro."
    large = pretty(yields["large"])
    extra = "" if large is None else f" Les grandes exploitations ont récolté {large} kg par hectare."
    return f"À {district}, {name} a rendu {shown} kg par hectare.{extra}"
