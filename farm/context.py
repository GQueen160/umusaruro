from farm.role import current
from umusaruro.lang import LABELS, current_lang, pack


def reader(request):
    lang = current_lang(request)
    return {"reader": current(request), "lang": lang, "languages": LABELS, "ui": pack(lang)}
