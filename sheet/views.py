from django.http import Http404
from django.shortcuts import render

from sheet import advisor as advisor_data
from sheet import sheet
from sheet.mapsvg import outline


def overview(request):
    data = sheet.overview()
    shapes = outline()
    regions = [(row, shapes.shapes[row.name]) for row in data["rows"]]
    return render(request, "sheet/overview.html", {**data, "map": shapes, "regions": regions})


def _name(slug):
    name = sheet.by_slug(slug)
    if name is None:
        raise Http404("No such district")
    return name


def district(request, slug):
    return render(request, "sheet/district.html",
                  {"s": sheet.district_sheet(_name(slug)), "districts": sheet.districts()})


def district_panel(request, slug):
    """The district sheet as a fragment for the map's side panel."""
    return render(request, "sheet/panel.html", {"s": sheet.district_sheet(_name(slug))})


def method(request):
    return render(request, "sheet/method.html", sheet.method())


def advisor(request):
    return render(request, "sheet/advisor.html", advisor_data.home())


def crop(request, key):
    page = advisor_data.crop_page(key)
    if page is None:
        raise Http404("No such crop")
    return render(request, "sheet/crop.html", page)
