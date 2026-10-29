"""Who is reading, for this browser only.

This is not an account. The choice picks a screen and is kept in the
session until the reader chooses again.
"""

from __future__ import annotations

READERS = {
    "farmer-mini": {
        "group": "farmer",
        "title_rw": "Umuhinzi muto",
        "title_en": "Mini farm",
        "title_fr": "Petite exploitation",
        "home": "field",
        "use_en": "One field. Aim at the district harvest.",
        "use_fr": "Un champ. Viser la récolte du district.",
        "use_rw": "Umurima umwe. Intego ni umusaruro w'akarere.",
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
        "use_en": "One field. Aim at the large-farm harvest.",
        "use_fr": "Un champ. Viser la récolte des grandes exploitations.",
        "use_rw": "Umurima umwe. Intego ni umusaruro w'abahinzi binini.",
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
        "use_en": "Click a district. The color is the action.",
        "use_fr": "Cliquez un district. La couleur est l'action.",
        "use_rw": "Kanda akarere. Ibara ni igikorwa.",
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
        "use_en": "Find the sector. Read its district.",
        "use_fr": "Trouvez le secteur. Lisez son district.",
        "use_rw": "Shaka umurenge. Soma akarere karyo.",
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
