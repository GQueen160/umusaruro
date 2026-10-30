from farm.role import current, office
from umusaruro.lang import LABELS, current_lang, pack


def reader(request):
    lang = current_lang(request)
    return {
        "reader": current(request),
        "office": office(request),
        "lang": lang,
        "languages": LABELS,
        "ui": pack(lang),
    }
