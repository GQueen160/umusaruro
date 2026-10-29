"""Interface language: English, French, Kinyarwanda.

The cited survey sentences on the district and method pages stay in
English. The choice screen, the field sheet, and the planner chrome follow
the language stored in the session.
"""

from __future__ import annotations

LANGS = ("en", "fr", "rw")
LABELS = (("en", "en"), ("fr", "fra"), ("rw", "kin"))

COPY = {
    "who_title": {"en": "Who is reading?", "fr": "Qui lit ?", "rw": "Ni nde usoma?"},
    "who_lead": {"en": "Choose once.", "fr": "Choisissez une fois.", "rw": "Hitamo inshuro imwe."},
    "farmer": {"en": "Farmer", "fr": "Agriculteur", "rw": "Umuhinzi"},
    "planner": {"en": "Planner", "fr": "Planificateur", "rw": "Umuyobozi"},
    "nav_field": {"en": "Farmer map", "fr": "Carte du champ", "rw": "Ikarita y'umuhinzi"},
    "nav_crops": {"en": "Crops", "fr": "Cultures", "rw": "Ibihingwa"},
    "nav_districts": {"en": "District map", "fr": "Carte des districts", "rw": "Ikarita y'uturere"},
    "nav_method": {"en": "Method", "fr": "Méthode", "rw": "Uburyo"},
    "nav_sector": {"en": "Your sector", "fr": "Votre secteur", "rw": "Umurenge wawe"},
    "change": {"en": "Change", "fr": "Changer", "rw": "Hindura"},
    "change_long": {"en": "Change who is reading", "fr": "Changer le lecteur", "rw": "Hindura uwisoma"},
    "search": {"en": "Search a village", "fr": "Chercher un village", "rw": "Shakisha umudugudu"},
    "where": {"en": "Where I am", "fr": "Où je suis", "rw": "Aho ndi"},
    "voice": {"en": "Speak", "fr": "Parler", "rw": "Vuga"},
    "hearing": {"en": "Listening…", "fr": "J'écoute…", "rw": "Ndumva…"},
    "brand_farmer": {"en": "Advice for your field", "fr": "Conseil pour votre champ", "rw": "Inama ku murima wawe"},
    "brand_sector": {"en": "The district's advice", "fr": "Le conseil du district", "rw": "Inama y'akarere"},
    "prompt_farmer": {
        "en": "Tap the map where you will plant.",
        "fr": "Touchez la carte là où vous allez cultiver.",
        "rw": "Kanda ku karita aho uzahinga.",
    },
    "prompt_sector": {
        "en": "Find your sector. No sector table. The numbers are the district's.",
        "fr": "Trouvez votre secteur. Pas de tableau par secteur. Les chiffres sont ceux du district.",
        "rw": "Shaka umurenge wawe. Nta mibare y'umurenge. Imibare ni iy'akarere.",
    },
    "ladder": {"en": "Choose the place", "fr": "Choisir le lieu", "rw": "Hindura ahantu"},
    "ladder_hint": {
        "en": "District, sector, cell, village",
        "fr": "District, secteur, cellule, village",
        "rw": "Akarere, umurenge, akagari, umudugudu",
    },
    "pick_district": {"en": "District", "fr": "District", "rw": "Akarere"},
    "pick_sector": {"en": "Sector", "fr": "Secteur", "rw": "Umurenge"},
    "pick_cell": {"en": "Cell", "fr": "Cellule", "rw": "Akagari"},
    "pick_village": {"en": "Village", "fr": "Village", "rw": "Umudugudu"},
    "opt_district": {"en": "Choose a district", "fr": "Choisir un district", "rw": "Hitamo akarere"},
    "opt_sector": {"en": "Choose a sector", "fr": "Choisir un secteur", "rw": "Hitamo umurenge"},
    "opt_cell": {"en": "Choose a cell", "fr": "Choisir une cellule", "rw": "Hitamo akagari"},
    "opt_village": {"en": "Choose a village", "fr": "Choisir un village", "rw": "Hitamo umudugudu"},
    "tap_village": {"en": "Tap your village.", "fr": "Touchez votre village.", "rw": "Kanda umudugudu wawe."},
    "open_district": {"en": "Read {name}.", "fr": "Lire {name}.", "rw": "Soma akarere ka {name}."},
    "plans": {"en": "Saved aims", "fr": "Objectifs enregistrés", "rw": "Intego wabitse"},
    "you": {"en": "You", "fr": "Vous", "rw": "Wowe"},
    "us": {"en": "Umusaruro", "fr": "Umusaruro", "rw": "Umusaruro"},
    "need_village": {
        "en": "Tap the village on the map first.",
        "fr": "Touchez d'abord le village sur la carte.",
        "rw": "Banza ukande umudugudu ku karita.",
    },
    "saved": {"en": "Aim saved", "fr": "Objectif enregistré", "rw": "Intego yabitswe"},
    "no_geo": {
        "en": "This device cannot show where you are. Tap the map.",
        "fr": "Cet appareil ne montre pas où vous êtes. Touchez la carte.",
        "rw": "Iyi mudasobwa ntayerekana aho uri. Kanda ku karita.",
    },
    "no_fix": {
        "en": "Where you are could not be found. Tap the map.",
        "fr": "L'endroit n'a pas été trouvé. Touchez la carte.",
        "rw": "Ntabwo nabonye aho uri. Kanda ku karita.",
    },
    "no_voice": {
        "en": "This device does not hear speech. Type or tap the map.",
        "fr": "Cet appareil n'entend pas la voix. Écrivez ou touchez la carte.",
        "rw": "Iyi mudasobwa ntumva ijwi. Koresha amagambo cyangwa kanda ku karita.",
    },
    "not_heard": {
        "en": "That was not heard. Say it again, or type the village.",
        "fr": "Ce n'était pas entendu. Répétez, ou écrivez le village.",
        "rw": "Ntabwo numvise. Ongera uvuge, cyangwa andika izina ry'umudugudu.",
    },
    "failed": {"en": "That did not save.", "fr": "L'enregistrement a échoué.", "rw": "Ntibyakunze."},
    "no_place": {"en": "That tap is outside Rwanda.", "fr": "Cet endroit est hors du Rwanda.", "rw": "Aho wakandagiye ntibirimo mu Rwanda."},
    "need_crop": {"en": "Choose a district and a crop.", "fr": "Choisissez un district et une culture.", "rw": "Hitamo akarere n'igihingwa."},
    "unknown_district": {"en": "That district was not found.", "fr": "Ce district est introuvable.", "rw": "Aka karere ntikabonetse."},
    "empty_voice": {"en": "No words were heard.", "fr": "Aucun mot n'a été entendu.", "rw": "Ntabwo navunikiwe ijambo."},
    "need_crop_only": {"en": "Choose a crop.", "fr": "Choisissez une culture.", "rw": "Hitamo igihingwa."},
    "bad_target": {"en": "Write the aim in kg per hectare.", "fr": "Écrivez l'objectif en kg par hectare.", "rw": "Andika intego mu kg kuri hegitari."},
    "rejected_target": {"en": "That aim is not accepted.", "fr": "Cet objectif n'est pas accepté.", "rw": "Intego ntiyemewe."},
    "advisor_h1": {"en": "Every crop. Three stages.", "fr": "Chaque culture. Trois étapes.", "rw": "Igihingwa cyose. Intambwe eshatu."},
    "overview_h1": {"en": "The field, beside the reading.", "fr": "Le terrain, à côté de la lecture.", "rw": "Umurima, hafi y'isosomo."},
    "tag": {"en": "Cultivation advisor", "fr": "Conseil de culture", "rw": "Umujyanama w'ubuhinzi"},
    "lang_name": {"en": "Language", "fr": "Langue", "rw": "Ururimi"},
    "flag_name": {"en": "What to do", "fr": "Quoi faire", "rw": "Icyo gukora"},
    "flag_plant": {"en": "Plant", "fr": "Cultiver", "rw": "Hinga"},
    "flag_check": {"en": "Check", "fr": "Vérifier", "rw": "Reba"},
    "flag_stop": {"en": "Stop", "fr": "Arrêt", "rw": "Hagarara"},
    "flag_wait": {
        "en": "Choose a crop. The color will say what to do.",
        "fr": "Choisissez une culture. La couleur dira quoi faire.",
        "rw": "Hitamo igihingwa. Ibara rizakubwira icyo gukora.",
    },
    "flag_plant_line": {
        "en": "The survey printed a harvest for this crop in this district. You can set an aim.",
        "fr": "L'enquête a imprimé une récolte pour cette culture dans ce district. Vous pouvez fixer un objectif.",
        "rw": "Raporo yanditse umusaruro w'iki gihingwa muri aka karere. Ushobora gushyiraho intego.",
    },
    "flag_check_line": {
        "en": "Read the card. Water, seed, or fertilizer needs a look in this district.",
        "fr": "Lisez la carte. L'eau, la semence ou l'engrais demande un regard dans ce district.",
        "rw": "Soma ikarita. Amazi, imbuto, cyangwa ifumbire bisaba kureba muri aka karere.",
    },
    "flag_stop_line": {
        "en": "This crop was not printed for this district. A blank is not zero.",
        "fr": "Cette culture n'a pas été imprimée pour ce district. Une case vide n'est pas zéro.",
        "rw": "Iki gihingwa ntikanditswe muri aka karere. Ahatagira umubare si zeru.",
    },
}


def current_lang(request) -> str:
    lang = request.session.get("lang")
    return lang if lang in LANGS else "en"


def text(request, key: str) -> str:
    row = COPY[key]
    return row.get(current_lang(request)) or row["en"]


def pack(lang: str) -> dict:
    return {key: row.get(lang) or row["en"] for key, row in COPY.items()}


def safe_next(value: str | None) -> str:
    if not value or not value.startswith("/") or value.startswith("//"):
        return "/"
    return value
