from django.http import Http404
from django.shortcuts import render

from sheet import sheet
from sheet.mapsvg import outline


def overview(request):
    data = sheet.overview()
    shapes = outline()
    regions = [(row, shapes.shapes[row.name]) for row in data["rows"]]
    return render(request, "sheet/overview.html", {**data, "map": shapes, "regions": regions})


def district(request, slug):
    name = sheet.by_slug(slug)
    if name is None:
        raise Http404("No such district")
    return render(request, "sheet/district.html", {"s": sheet.district_sheet(name), "districts": sheet.districts()})


def method(request):
    return render(request, "sheet/method.html", sheet.method())
