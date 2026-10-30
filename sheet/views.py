from django.http import Http404
from django.shortcuts import redirect, render

from farm.role import bound_district, current
from sheet import advisor as advisor_data
from sheet import sheet
from sheet.mapsvg import outline


def _keep_home(request):
    """Send a district or sector officer back to the one place they chose."""
    reader = current(request)
    if reader is None or reader["id"] not in {"district", "sector"}:
        return None
    own = bound_district(request)
    if own is None:
        return redirect("entrance")
    if reader["id"] == "sector":
        return redirect("field")
    return redirect("district", slug=own.lower())


def overview(request):
    away = _keep_home(request)
    if away is not None:
        return away
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
    name = _name(slug)
    reader = current(request)
    own = bound_district(request)
    if reader and reader["id"] in {"district", "sector"}:
        if own is None:
            return redirect("entrance")
        if own != name:
            if reader["id"] == "sector":
                return redirect("field")
            return redirect("district", slug=own.lower())
    page = sheet.district_sheet(name)
    return render(request, "sheet/district.html", {
        "s": page,
        "g": sheet.picture(page),
        "districts": sheet.districts(),
        "scoped": bool(own and own == name),
    })


def district_panel(request, slug):
    """The district sheet as a fragment for the map's side panel."""
    name = _name(slug)
    reader = current(request)
    own = bound_district(request)
    if reader and reader["id"] in {"district", "sector"} and (own is None or own != name):
        raise Http404("No such district")
    page = sheet.district_sheet(name)
    return render(request, "sheet/panel.html", {"s": page, "g": sheet.picture(page)})


def method(request):
    return render(request, "sheet/method.html", sheet.method())


def advisor(request):
    return render(request, "sheet/advisor.html", advisor_data.home())


def crop(request, key):
    page = advisor_data.crop_page(key)
    if page is None:
        raise Http404("No such crop")
    own = bound_district(request)
    if own:
        page = dict(page)
        page["places"] = [place for place in page["places"] if place.name == own]
        page["leaders"] = []
        page["has_blanks"] = False
        page["one_place"] = own
    return render(request, "sheet/crop.html", page)
