"""Turn a spoken Kinyarwanda or English sentence into a place and crops.

A district name is the district, even when a village somewhere shares that
name, unless the farmer also says umudugudu. Several villages with the
same name stay as choices. The system does not guess.
"""

from __future__ import annotations

from farm.advice import advise, crops_in
from farm.places import district_place, norm, sector_place, spoken, villages


def hear(text: str, reader: str = "farmer-large") -> dict:
    cleaned = norm(text)
    crops = crops_in(cleaned)
    place, choices = _place(cleaned)
    advice = None
    if place and place.get("district") and crops:
        advice = advise(place["district"], crops, reader=reader)
    return {
        "heard": text.strip(),
        "crops": crops,
        "place": place,
        "choices": choices,
        "advice": advice,
        "reply_rw": _reply(place, choices, crops, advice),
        "reply_en": _reply_en(place, choices, crops, advice),
        "reply_fr": _reply_fr(place, choices, crops, advice),
    }


def _place(text: str) -> tuple[dict | None, list[dict]]:
    named_districts = [row["district"] for row in _unique_districts() if spoken(row["district"], text)]
    scope = set(named_districts)
    want_village = "umudugudu" in text
    hits = []
    for row in villages():
        if scope and row["district"] not in scope:
            continue
        if not spoken(row["village"], text):
            continue
        if row["village"] in named_districts and not want_village:
            continue
        hits.append(dict(row))
    hits = _unique_villages(hits)
    if len(hits) == 1:
        return hits[0], []
    if len(hits) > 1:
        narrowed = _narrow(hits, text)
        if len(narrowed) == 1:
            return narrowed[0], []
        return None, narrowed[:6]
    if len(named_districts) == 1:
        return district_place(named_districts[0]), []
    sectors = _sectors(text, scope)
    if len(sectors) == 1:
        return sector_place(sectors[0]), []
    return None, []


def _unique_districts() -> list[dict]:
    seen = {}
    for row in villages():
        seen.setdefault(row["district"], row)
    return list(seen.values())


def _unique_villages(rows: list[dict]) -> list[dict]:
    found = {}
    for row in rows:
        found.setdefault(row["village_id"], row)
    return list(found.values())


def _narrow(hits: list[dict], text: str) -> list[dict]:
    by_sector = [row for row in hits if spoken(row["sector"], text)]
    if by_sector:
        hits = by_sector
    by_cell = [row for row in hits if spoken(row["cell"], text)]
    if by_cell:
        hits = by_cell
    return hits


def _sectors(text: str, scope: set[str]) -> list[str]:
    found = {}
    for row in villages():
        if scope and row["district"] not in scope:
            continue
        if spoken(row["sector"], text):
            found.setdefault(row["sector_id"], row["sector_id"])
    return list(found)


def _reply(place, choices, crops, advice) -> str:
    if choices:
        names = ", ".join(f"{row['village']} ({row['district']})" for row in choices)
        return f"Nabonye umudugudu utandukanye. Hitamo umwe: {names}."
    if place is None:
        return "Ntabwo numvise ahantu. Kanda ku karita, cyangwa vuga izina ry'umudugudu."
    where = _where(place)
    if not crops:
        return f"Nahageze: {where}. Hitamo igihingwa."
    if advice and advice.get("cards"):
        lead = next((card["title_rw"] for card in advice["cards"] if card.get("first")), advice["cards"][0]["title_rw"])
        return f"{where}. {lead}. {advice['note_rw']}"
    return f"{where}. Nta nama nshoboye kuvana muri raporo."


def _reply_en(place, choices, crops, advice) -> str:
    if choices:
        return "More than one village has that name. Choose one."
    if place is None:
        return "I did not hear a place. Tap the map, or say the village."
    if not crops:
        return "Place found. Choose the crop."
    if advice and advice.get("cards"):
        lead = next((card["title_en"] for card in advice["cards"] if card.get("first")), "")
        return f"{lead}. {advice['note_en']}"
    return "No advice could be read from the report."


def _reply_fr(place, choices, crops, advice) -> str:
    if choices:
        return "Plusieurs villages portent ce nom. Choisissez-en un."
    if place is None:
        return "Je n'ai pas entendu de lieu. Touchez la carte, ou dites le village."
    if not crops:
        return "Lieu trouvé. Choisissez la culture."
    if advice and advice.get("cards"):
        lead = next((card.get("title_fr") for card in advice["cards"] if card.get("first")), "")
        return f"{lead}. {advice.get('note_fr', '')}"
    return "Aucun conseil n'a pu être lu dans le rapport."


def _where(place: dict) -> str:
    parts = [place.get("village"), place.get("cell"), place.get("sector"), place.get("district")]
    parts = [part for part in parts if part]
    if place.get("village"):
        return ", ".join(parts)
    if place.get("sector"):
        return f"Umurenge wa {place['sector']}, {place['district']}. Kanda umudugudu wawe."
    return f"Akarere ka {place['district']}. Kanda umudugudu wawe."

