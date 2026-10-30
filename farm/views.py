import json
from decimal import Decimal, InvalidOperation

from datetime import date

from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_GET, require_POST

from farm.advice import advise, crop_list, sector_board
from farm.plan import country_rates, domestic_brief, holding_routine, journey_calendar, mark_check, mark_count
from farm.models import FieldPlan
from farm.role import READERS, by_group, current, known, office
from farm.chat import answer
from umusaruro.lang import LANGS, current_lang, safe_next, text
from farm.places import (
    BOUNDARIES,
    by_id,
    cells,
    district_place,
    districts,
    locate,
    search,
    sector_place,
    sectors,
    villages_in,
)
from farm.talk import hear


def _place_gate(request, role, district=""):
    picked = district if district_place(district) else ""
    return render(request, "farm/home.html", {
        "crops": crop_list(),
        "gate": True,
        "place_for": role,
        "districts": districts(),
        "picked_district": picked,
        "sectors": sectors(picked) if role == "sector" and picked else [],
        "farmers": by_group("farmer"),
        "planners": by_group("planner"),
    })


def entrance(request):
    found = current(request)
    if found is not None:
        if found["id"] in {"district", "sector"} and office(request) is None:
            return _place_gate(request, found["id"])
        if found["id"] == "district":
            return redirect("district", slug=office(request)["district"].lower())
        return redirect(found["home"])
    return render(request, "farm/home.html", {
        "crops": crop_list(),
        "gate": True,
        "farmers": by_group("farmer"),
        "planners": by_group("planner"),
    })


def field(request):
    found = current(request)
    if found is None:
        return redirect("entrance")
    if found["id"] == "district":
        bound = office(request)
        if bound is None:
            return redirect("entrance")
        return redirect("district", slug=bound["district"].lower())
    if found["id"] == "sector" and office(request) is None:
        return redirect("entrance")
    return render(request, "farm/home.html", {"crops": crop_list(), "gate": False})


@require_POST
def choose_role(request):
    role = known(request.POST.get("role"))
    if role is None:
        return redirect("entrance")
    if role not in {"district", "sector"}:
        request.session["reader"] = role
        request.session.pop("office", None)
        return redirect(READERS[role]["home"])
    request.session["reader"] = role
    district_name = (request.POST.get("district") or "").strip()
    if district_place(district_name) is None:
        request.session.pop("office", None)
        return _place_gate(request, role)
    if role == "district":
        request.session["office"] = {"district": district_name}
        return redirect("district", slug=district_name.lower())
    if request.POST.get("step") != "open":
        request.session.pop("office", None)
        return _place_gate(request, role, district_name)
    chosen = sector_place((request.POST.get("sector_id") or "").strip())
    if chosen is None or chosen["district"] != district_name:
        request.session.pop("office", None)
        return _place_gate(request, role, district_name)
    request.session["office"] = {
        "district": district_name,
        "sector": chosen["sector"],
        "sector_id": chosen["sector_id"],
        "lat": chosen["lat"],
        "lon": chosen["lon"],
    }
    return redirect("field")


@require_POST
def clear_role(request):
    request.session.pop("reader", None)
    request.session.pop("office", None)
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


@require_POST
def chat_view(request):
    body = _body(request)
    message = " ".join(str(body.get("message") or "").split())
    if not message:
        return JsonResponse({"about": False, "ready": True, "answer": text(request, "chat_name_place")}, status=400)
    if len(message) > 500:
        message = message[:500]
    try:
        turns = int(request.session.get("chat_turns") or 0)
    except (TypeError, ValueError):
        turns = 0
    if turns >= 40:
        return JsonResponse({"about": False, "ready": True, "answer": text(request, "chat_later")})
    raw_place = body.get("place") if isinstance(body.get("place"), dict) else {}
    raw_crops = body.get("crops") if isinstance(body.get("crops"), list) else []
    found = current(request)
    result = answer(
        message,
        lang=current_lang(request),
        reader=found["id"] if found else "farmer-large",
        office=office(request),
        page={
            "district": str(raw_place.get("district") or "")[:80],
            "sector": str(raw_place.get("sector") or "")[:80],
            "cell": str(raw_place.get("cell") or "")[:80],
            "village": str(raw_place.get("village") or "")[:80],
        },
        crops=[str(item)[:40] for item in raw_crops[:8]],
    )
    if result["status"] == 200:
        request.session["chat_turns"] = turns + 1
    return JsonResponse(
        {"about": result["about"], "ready": result["ready"], "answer": result["answer"]},
        status=result["status"],
    )


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
    reader = _reader(request, body)
    bound = office(request)
    if bound and reader in {"district", "sector"}:
        district = bound["district"]
    advice = advise(district, [str(crop) for crop in crops], reader=reader)
    known = advice["crops"]
    if reader == "farmer-domestic":
        advice["domestic"] = domestic_brief(district, known)
    elif reader in {"farmer-mini", "farmer-large"}:
        advice["rates"] = country_rates(known)
    elif reader == "sector":
        advice["board"] = sector_board(district, known)
        advice["note_en"] = f"No sector table. These bars are {district} district."
        advice["note_fr"] = f"Pas de tableau par secteur. Ces barres sont celles du district de {district}."
        advice["note_rw"] = f"Nta mibare y'umurenge. Imirongo ni iya karere ka {district}."
    return JsonResponse({"advice": advice})


@require_POST
def routine_view(request):
    body = _body(request)
    reader = _reader(request, body)
    if reader not in {"farmer-mini", "farmer-large"}:
        return JsonResponse({"error": text(request, "need_crop")}, status=400)
    district = (body.get("district") or "").strip()
    crops = body.get("crops") or []
    if not district or not isinstance(crops, list):
        return JsonResponse({"error": text(request, "need_crop")}, status=400)
    if district_place(district) is None:
        return JsonResponse({"error": text(request, "unknown_district")}, status=404)
    portions = body.get("portions") if isinstance(body.get("portions"), dict) else {}
    routine = holding_routine(district, [str(crop) for crop in crops], body.get("unit") or "ha", body.get("farm"), portions)
    return JsonResponse({"routine": routine})


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
    holding = _holding(body)
    if holding is not None:
        crop, target = _holding_target(crops, holding)
        if target is None:
            return JsonResponse({"error": text(request, "bad_target")}, status=400)
    else:
        try:
            target = Decimal(str(body.get("target_kg"))).quantize(Decimal("0.1"))
        except (InvalidOperation, TypeError):
            return JsonResponse({"error": text(request, "bad_target")}, status=400)
        crop = str(body.get("target_crop") or crops[0])
    if target <= 0 or target > Decimal("100000"):
        return JsonResponse({"error": text(request, "rejected_target")}, status=400)
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
        holding=holding,
    )
    return JsonResponse({"plan": _plan(row)})


@require_POST
def check_plan(request, plan_id):
    row = FieldPlan.objects.filter(pk=plan_id).first()
    if row is None or not row.holding:
        return JsonResponse({"error": text(request, "need_village")}, status=404)
    body = _body(request)
    item = str(body.get("item") or "")
    if item[:1] not in {"d", "w"} or not item[1:].isdigit():
        return JsonResponse({"error": text(request, "bad_target")}, status=400)
    try:
        day = date.fromisoformat(str(body.get("date") or ""))
    except ValueError:
        return JsonResponse({"error": text(request, "bad_target")}, status=400)
    window = journey_calendar(row.district, row.crops, row.holding)
    start = date.fromisoformat(window["start"])
    end = date.fromisoformat(window["end"])
    if day < start or day > end:
        return JsonResponse({"error": text(request, "bad_target")}, status=400)
    kind = "daily" if item.startswith("d") else "weekly"
    if int(item[1:]) >= len(window[kind]):
        return JsonResponse({"error": text(request, "bad_target")}, status=400)
    row.checks = mark_check(row.checks, day, item, bool(body.get("on")))
    row.save(update_fields=["checks"])
    return JsonResponse({"plan": _plan(row)})


def _holding(body: dict):
    portions = body.get("portions")
    if not isinstance(portions, dict) or not portions:
        return None
    unit = body.get("unit") if body.get("unit") in {"ha", "m2"} else "ha"
    clean = {}
    for crop, row in portions.items():
        if not isinstance(row, dict):
            continue
        clean[str(crop)] = {
            "area": str(row.get("area") or ""),
            "target": str(row.get("target") or ""),
        }
    if not clean:
        return None
    return {"unit": unit, "farm": str(body.get("farm") or ""), "portions": clean}


def _holding_target(crops, holding):
    for crop in crops:
        row = holding["portions"].get(str(crop)) or {}
        try:
            number = Decimal(str(row.get("target") or "").replace(",", "."))
        except InvalidOperation:
            continue
        if number > 0:
            return str(crop), number.quantize(Decimal("0.1"))
    return None, None


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
    payload = {
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
        "holding": row.holding,
        "checks": row.checks or {"days": {}, "weeks": {}},
        "marked": mark_count(row.checks),
        "season": row.season,
        "year": row.year,
    }
    if row.holding:
        payload["journey"] = journey_calendar(row.district, row.crops, row.holding)
    return payload
