"""Who is reading, for this browser only.

This is not an account. The choice picks a screen and is kept in the
session until the reader chooses again.
"""

from __future__ import annotations

from farm.places import district_place, sector_place

READERS = {
    "farmer-domestic": {
        "group": "farmer",
        "title_rw": "Ubuhinzi bw'urugo",
        "title_en": "Domestic",
        "title_fr": "Jardin familial",
        "home": "field",
        "use_en": "A garden at home. The note follows the district rain.",
        "use_fr": "Un jardin à la maison. La note suit la pluie du district.",
        "use_rw": "Urugo. Inama ikurikiza imvura y'akarere.",
        "note_en": "",
        "note_fr": "",
        "note_rw": "",
    },
    "farmer-mini": {
        "group": "farmer",
        "title_rw": "Umuhinzi muto",
        "title_en": "Mini farm",
        "title_fr": "Petite exploitation",
        "home": "field",
        "use_en": "Name the farm, the land for each crop, and your target.",
        "use_fr": "Indiquez la ferme, la terre de chaque culture, et votre objectif.",
        "use_rw": "Vuga ubunini bw'umurima, ubutaka bw'igihingwa, n'intego yawe.",
        "note_en": "",
        "note_fr": "",
        "note_rw": "",
    },
    "farmer-large": {
        "group": "farmer",
        "title_rw": "Umuhinzi munini",
        "title_en": "Large farm",
        "title_fr": "Grande exploitation",
        "home": "field",
        "use_en": "Name the farm, the land for each crop, and your target.",
        "use_fr": "Indiquez la ferme, la terre de chaque culture, et votre objectif.",
        "use_rw": "Vuga ubunini bw'umurima, ubutaka bw'igihingwa, n'intego yawe.",
        "note_en": "",
        "note_fr": "",
        "note_rw": "",
    },
    "ministry": {
        "group": "planner",
        "title_rw": "Minisiteri",
        "title_en": "Ministry",
        "title_fr": "Ministère",
        "home": "advisor",
        "use_en": "Open a crop. Shared levers are on the district map.",
        "use_fr": "Ouvrez une culture. Les leviers communs sont sur la carte des districts.",
        "use_rw": "Fungura igihingwa. Ibikoresho rusange biri ku ikarita y'uturere.",
        "note_en": "Country tables.",
        "note_fr": "Tableaux du pays.",
        "note_rw": "Imibare y'igihugu.",
    },
    "district": {
        "group": "planner",
        "title_rw": "Umukozi w'akarere",
        "title_en": "District agricultural officer",
        "title_fr": "Agent agricole de district",
        "home": "overview",
        "use_en": "Your district only. The color is the action.",
        "use_fr": "Votre district seulement. La couleur est l'action.",
        "use_rw": "Akarere kawe gusa. Ibara ni igikorwa.",
        "note_en": "",
        "note_fr": "",
        "note_rw": "",
    },
    "sector": {
        "group": "planner",
        "title_rw": "Umukozi w'umurenge",
        "title_en": "Sector agricultural officer",
        "title_fr": "Agent agricole de secteur",
        "home": "field",
        "use_en": "Your sector only. The numbers are the district's.",
        "use_fr": "Votre secteur seulement. Les chiffres sont ceux du district.",
        "use_rw": "Umurenge wawe gusa. Imibare ni iy'akarere.",
        "note_en": "No sector table.",
        "note_fr": "Pas de tableau par secteur.",
        "note_rw": "Nta mibare y'umurenge.",
    },
}


def current(request) -> dict | None:
    key = request.session.get("reader")
    row = READERS.get(key)
    if row is None:
        return None
    return {"id": key, **row}


def by_group(group: str) -> list[dict]:
    return [{"id": key, **row} for key, row in READERS.items() if row["group"] == group]


def known(value: str | None) -> str | None:
    if value in READERS:
        return value
    return None


def office(request) -> dict | None:
    """The one district, or the one sector, this browser chose."""
    raw = request.session.get("office")
    role = request.session.get("reader")
    if not isinstance(raw, dict) or role not in {"district", "sector"}:
        return None
    district = str(raw.get("district") or "")
    if district_place(district) is None:
        return None
    if role == "district":
        return {"district": district}
    place = sector_place(str(raw.get("sector_id") or ""))
    if place is None or place["district"] != district:
        return None
    return {
        "district": district,
        "sector": place["sector"],
        "sector_id": place["sector_id"],
        "lat": place["lat"],
        "lon": place["lon"],
    }


def bound_district(request) -> str | None:
    found = current(request)
    place = office(request)
    if found is None or place is None or found["id"] not in {"district", "sector"}:
        return None
    return place["district"]
