import json
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_GET, require_POST

from farm.advice import advise, crop_list
from farm.models import FieldPlan
from farm.places import (
    BOUNDARIES,
    by_id,
    cells,
    district_place,
    districts,
    locate,
    search,
    sectors,
    villages_in,
)
from farm.talk import hear


def home(request):
    return render(request, "farm/home.html", {"crops": crop_list()})


@require_GET
def boundaries(request):
    return HttpResponse(BOUNDARIES.read_text(encoding="utf-8"), content_type="application/geo+json")


@require_GET
def search_places(request):
    return JsonResponse({"places": search(request.GET.get("q", ""))})


@require_GET
def place_children(request):
    district = request.GET.get("district", "").strip()
    sector_id = request.GET.get("sector_id", "").strip()
    cell_id = request.GET.get("cell_id", "").strip()
    if cell_id:
        return JsonResponse({"level": "village", "places": villages_in(cell_id)})
    if sector_id:
        return JsonResponse({"level": "cell", "places": cells(sector_id)})
    if district:
        return JsonResponse({"level": "sector", "places": sectors(district)})
    return JsonResponse({"level": "district", "places": districts()})


@require_GET
def locate_place(request):
    try:
        lat = float(request.GET["lat"])
        lon = float(request.GET["lon"])
    except (KeyError, TypeError, ValueError):
        return JsonResponse({"error": "Kanda ku karita."}, status=400)
    place = locate(lon, lat)
    if place is None:
        return JsonResponse({"error": "Aho wakandagiye ntibirimo mu Rwanda."}, status=404)
    return JsonResponse({"place": place})


@require_POST
def advice_view(request):
    body = _body(request)
    district = (body.get("district") or "").strip()
    crops = body.get("crops") or []
    if not district or not isinstance(crops, list):
        return JsonResponse({"error": "Hitamo akarere n'igihingwa."}, status=400)
    place = district_place(district)
    if place is None:
        return JsonResponse({"error": "Aka karere ntikabonetse."}, status=404)
    return JsonResponse({"advice": advise(district, [str(crop) for crop in crops])})


@require_POST
def hear_view(request):
    body = _body(request)
    text = str(body.get("text") or "").strip()
    if not text:
        return JsonResponse({"error": "Ntabwo navunikiwe ijambo."}, status=400)
    return JsonResponse(hear(text))


@require_GET
def plans(request):
    return JsonResponse({"plans": [_plan(row) for row in FieldPlan.objects.all()[:8]]})


@require_POST
def save_plan(request):
    body = _body(request)
    place = by_id(str(body.get("village_id") or ""))
    if place is None:
        return JsonResponse({"error": "Banza ukande umudugudu ku karita."}, status=400)
    crops = body.get("crops") or []
    if not isinstance(crops, list) or not crops:
        return JsonResponse({"error": "Hitamo igihingwa."}, status=400)
    try:
        target = Decimal(str(body.get("target_kg"))).quantize(Decimal("0.1"))
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": "Andika intego mu kg kuri hegitari."}, status=400)
    if target <= 0 or target > Decimal("100000"):
        return JsonResponse({"error": "Intego ntiyemewe."}, status=400)
    crop = str(body.get("target_crop") or crops[0])
    row = FieldPlan.objects.create(
        village_id=place["village_id"],
        district=place["district"],
        sector=place["sector"],
        cell=place["cell"],
        village=place["village"],
        lat=Decimal(str(place["lat"])),
        lon=Decimal(str(place["lon"])),
        crops=[str(item) for item in crops],
        target_crop=crop,
        target_kg=target,
    )
    return JsonResponse({"plan": _plan(row)})


def _body(request) -> dict:
    if request.content_type == "application/json":
        try:
            return json.loads(request.body.decode() or "{}")
        except json.JSONDecodeError:
            return {}
    return request.POST.dict()


def _plan(row: FieldPlan) -> dict:
    return {
        "id": row.id,
        "village": row.village,
        "cell": row.cell,
        "sector": row.sector,
        "district": row.district,
        "lat": str(row.lat),
        "lon": str(row.lon),
        "crops": row.crops,
        "target_crop": row.target_crop,
        "target_kg": format(row.target_kg, "f").rstrip("0").rstrip("."),
        "season": row.season,
        "year": row.year,
    }
