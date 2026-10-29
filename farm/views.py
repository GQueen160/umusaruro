import json
from decimal import Decimal, InvalidOperation

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from farm.advice import advise, crop_list
from farm.models import FieldPlan
from farm.role import READERS, by_group, current, known
from umusaruro.lang import LANGS, safe_next, text
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


def entrance(request):
    found = current(request)
    if found is not None:
        return redirect(found["home"])
    return render(request, "farm/home.html", {
        "crops": crop_list(),
        "gate": True,
        "farmers": by_group("farmer"),
        "planners": by_group("planner"),
    })


def field(request):
    if current(request) is None:
        return redirect("entrance")
    return render(request, "farm/home.html", {"crops": crop_list(), "gate": False})


@require_POST
def choose_role(request):
    role = known(request.POST.get("role"))
    if role is None:
        return redirect("entrance")
    request.session["reader"] = role
    return redirect(READERS[role]["home"])


@require_POST
def clear_role(request):
    request.session.pop("reader", None)
    return redirect("entrance")


@require_POST
def set_lang(request):
    lang = request.POST.get("lang")
    if lang in LANGS:
        request.session["lang"] = lang
    return redirect(safe_next(request.POST.get("next")))


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
        return JsonResponse({"error": text(request, "need_village")}, status=400)
    place = locate(lon, lat)
    if place is None:
        return JsonResponse({"error": text(request, "no_place")}, status=404)
    return JsonResponse({"place": place})


@require_POST
def advice_view(request):
    body = _body(request)
    district = (body.get("district") or "").strip()
    crops = body.get("crops") or []
    if not district or not isinstance(crops, list):
        return JsonResponse({"error": text(request, "need_crop")}, status=400)
    place = district_place(district)
    if place is None:
        return JsonResponse({"error": text(request, "unknown_district")}, status=404)
    return JsonResponse({"advice": advise(district, [str(crop) for crop in crops], reader=_reader(request, body))})


@require_POST
def hear_view(request):
    body = _body(request)
    heard = str(body.get("text") or "").strip()
    if not heard:
        return JsonResponse({"error": text(request, "empty_voice")}, status=400)
    return JsonResponse(hear(heard, reader=_reader(request, body)))


@require_GET
def plans(request):
    return JsonResponse({"plans": [_plan(row) for row in FieldPlan.objects.all()[:8]]})


@require_POST
def save_plan(request):
    body = _body(request)
    place = by_id(str(body.get("village_id") or ""))
    if place is None:
        return JsonResponse({"error": text(request, "need_village")}, status=400)
    crops = body.get("crops") or []
    if not isinstance(crops, list) or not crops:
        return JsonResponse({"error": text(request, "need_crop_only")}, status=400)
    try:
        target = Decimal(str(body.get("target_kg"))).quantize(Decimal("0.1"))
    except (InvalidOperation, TypeError):
        return JsonResponse({"error": text(request, "bad_target")}, status=400)
    if target <= 0 or target > Decimal("100000"):
        return JsonResponse({"error": text(request, "rejected_target")}, status=400)
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


def _reader(request, body: dict) -> str:
    picked = known(str(body.get("reader") or "")) or known(request.session.get("reader"))
    return picked or "farmer-large"


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
