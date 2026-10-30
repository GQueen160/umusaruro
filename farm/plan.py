"""A farmer's plan after the place, the crop, and three answers.

The harvest figures are the printed survey cells. A blank district cell
is not replaced with the national harvest. The survey does not name a
seed variety, a litre amount, or a fertilizer measure, so the plan does
not invent them.
"""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from farm.advice import CROPS, _cells, _rain, _read, _yields, crop_label, pretty
from umusaruro.rules import MAIZE_MILESTONE_KG, classify

SEED_KEY = {
    "maize": "maize",
    "paddy_rice": "paddy_rice",
    "wheat": "wheat",
    "irish_potatoes": "irish_potato",
    "cassava": "cassava",
    "vegetables": "vegetables",
    "soya_beans": "soybean",
}
LOSS_KEY = {
    "maize": "maize",
    "paddy_rice": "paddy_rice",
    "wheat": "wheat",
    "irish_potatoes": "irish_potato",
    "sweet_potatoes": "sweet_potato",
    "cassava": "cassava",
    "sorghum": "sorghum",
    "vegetables": "vegetables",
    "soya_beans": "soybean",
    "ground_nuts": "groundnut",
}
ANSWERS = {
    "seed": {"improved", "saved", "unset"},
    "water": {"rain", "add"},
    "purpose": {"food", "sell", "both"},
}


def country_rates(crops: list[str]) -> list[dict]:
    rows = []
    for crop in _known(crops):
        rw, en, fr = crop_label(crop)
        if crop == "maize":
            value = MAIZE_MILESTONE_KG
            kind = "goal"
        else:
            value = _read("13", "National", "all", crop, "yield")
            kind = "harvest"
        rows.append({
            "crop": crop,
            "kind": kind,
            "kg_ha": None if value is None else _plain(value),
            "shown": pretty(value),
            "rw": rw,
            "en": en,
            "fr": fr,
        })
    return rows


def portion_kg(kg_per_ha: Decimal, amount: Decimal, unit: str) -> int:
    ha = amount / Decimal("10000") if unit == "m2" else amount
    return int((ha * kg_per_ha).quantize(Decimal("1"), rounding=ROUND_HALF_UP))


def holding_routine(district: str, crops: list[str], unit: str, farm, portions) -> dict:
    """Daily and weekly figures for the land the farmer typed.

    One millimetre of rain on one square metre is one litre. A dry
    district's daily litres are the millimetres it got less than the
    middle district, spread over the months in the rainfall file, on
    the square metres the farmer entered. The survey prints neither a
    litre nor a fertilizer measure, so those are not added.
    """
    known = _known(crops)
    chosen = unit if unit in {"ha", "m2"} else "ha"
    unit_names = {
        "ha": ("hectares", "hectares", "hegitari"),
        "m2": ("square metres", "mètres carrés", "metero kare"),
    }[chosen]
    rates = {row["crop"]: row for row in country_rates(known)}
    rain = _rain().get(district)
    days = _season_days(rain.months) if rain is not None else 0
    span = _season_span(rain.months) if rain is not None else ""
    farm_amount = _amount(farm)
    summary = []
    daily = []
    weekly = []
    if farm_amount is not None:
        summary.append(_line(
            f"The farm is {_plain(farm_amount)} {unit_names[0]}.",
            f"La ferme fait {_plain(farm_amount)} {unit_names[1]}.",
            f"Umurima ni {_plain(farm_amount)} {unit_names[2]}.",
        ))
    planted = False
    for crop in known:
        row = portions.get(crop) if isinstance(portions, dict) else None
        if not isinstance(row, dict):
            continue
        area = _amount(row.get("area"))
        if area is None:
            continue
        planted = True
        rw, en, fr = crop_label(crop)
        area_text = _plain(area)
        target = _amount(row.get("target"))
        rate = rates.get(crop)
        max_kg = None
        if rate and rate["kg_ha"]:
            max_kg = portion_kg(Decimal(rate["kg_ha"]), area, chosen)
        goal = ""
        goal_fr = ""
        goal_rw = ""
        if target is not None:
            shown = pretty(target)
            goal = f" Your goal is {shown} kg."
            goal_fr = f" Votre objectif est {shown} kg."
            goal_rw = f" Intego yawe ni kg {shown}."
        country = ""
        country_fr = ""
        country_rw = ""
        if max_kg is not None:
            shown = pretty(Decimal(max_kg))
            country = f" Country figure on this land: {shown} kg."
            country_fr = f" Chiffre du pays sur cette terre : {shown} kg."
            country_rw = f" Umubare w'igihugu kuri ubu butaka: kg {shown}."
        summary.append(_line(
            f"{en}: {area_text} {unit_names[0]}.{goal}{country}",
            f"{fr} : {area_text} {unit_names[1]}.{goal_fr}{country_fr}",
            f"{rw}: {area_text} {unit_names[2]}.{goal_rw}{country_rw}",
        ))
        if rain is None or not days:
            daily.append(_line(
                f"{district} has no rainfall figure, so there is no litre for {en}.",
                f"{district} n'a pas de chiffre de pluie, donc il n'y a pas de litre pour {fr}.",
                f"{district} nta mubare w'imvura ifite, nta litiro rya {rw} rero.",
            ))
        else:
            metres = area * Decimal("10000") if chosen == "ha" else area
            if rain.below_median:
                gap = rain.median_mm - rain.total_mm
                total = (gap * metres).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                per_day = (total / Decimal(days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                daily.append(_line(
                    f"Each morning: {pretty(per_day)} litres on the {area_text} {unit_names[0]} of {en}. {district} received {pretty(gap)} mm less rain than the middle district. Over {days} days, {span}, that is {pretty(total)} litres on this land.",
                    f"Chaque matin : {pretty(per_day)} litres sur les {area_text} {unit_names[1]} de {fr}. {district} a reçu {pretty(gap)} mm de pluie de moins que le district du milieu. Sur {days} jours, {span}, cela fait {pretty(total)} litres sur cette terre.",
                    f"Buri gitondo: litiro {pretty(per_day)} ku {area_text} {unit_names[2]} za {rw}. {district} yagize imvura nkeya ku mm {pretty(gap)} kurusha akarere k'hagati. Mu minsi {days}, {span}, ni litiro {pretty(total)} kuri ubu butaka.",
                ))
            else:
                total = (rain.total_mm * metres).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
                daily.append(_line(
                    f"Each morning: add no extra litres on the {area_text} {unit_names[0]} of {en}. Rain on this land was {pretty(total)} litres ({pretty(rain.total_mm)} mm) from {span}, at or above the middle district.",
                    f"Chaque matin : n'ajoutez aucun litre sur les {area_text} {unit_names[1]} de {fr}. La pluie sur cette terre était de {pretty(total)} litres ({pretty(rain.total_mm)} mm) de {span}, au milieu des districts ou au-dessus.",
                    f"Buri gitondo: ntongeramo litiro ku {area_text} {unit_names[2]} za {rw}. Imvura kuri ubu butaka yari litiro {pretty(total)} (mm {pretty(rain.total_mm)}) kuva {span}, ku giciro cy'hagati cyangwa hejuru.",
                ))
        if target is None or not days:
            weekly.append(_line(
                f"Each week: there is no kilogram yet, because the goal for {en} is empty.",
                f"Chaque semaine : il n'y a pas encore de kilogramme, parce que l'objectif pour {fr} est vide.",
                f"Buri cyumweru: nta kilogramo iraboneka, kuko intego ya {rw} irimo ubusa.",
            ))
        else:
            per_week = (target * Decimal(7) / Decimal(days)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            weekly.append(_line(
                f"Each week: {pretty(per_week)} kg of {en}, so the {pretty(target)} kg goal is met by {span}.",
                f"Chaque semaine : {pretty(per_week)} kg de {fr}, pour que l'objectif de {pretty(target)} kg soit atteint d'ici {span}.",
                f"Buri cyumweru: kg {pretty(per_week)} za {rw}, kugira ngo intego ya kg {pretty(target)} igerwe kugeza {span}.",
            ))
        weekly.append(_line(
            f"Each week: weed the whole {area_text} {unit_names[0]} of {en} once.",
            f"Chaque semaine : désherbez une fois les {area_text} {unit_names[1]} de {fr}.",
            f"Buri cyumweru: kuraho ibyatsi inshuro imwe ku {area_text} {unit_names[2]} byose bya {rw}.",
        ))
    if not planted:
        summary.append(_line(
            "Enter the land for a crop before the plan.",
            "Entrez la terre d'une culture avant le plan.",
            "Andika ubutaka bw'igihingwa mbere y'igahunda.",
        ))
    return {"summary": summary, "daily": daily, "weekly": weekly}


def _amount(value):
    text = str(value or "").strip().replace(",", ".")
    if not text:
        return None
    try:
        number = Decimal(text)
    except InvalidOperation:
        return None
    if number <= 0:
        return None
    return number


def _season_days(months: str) -> int:
    import calendar

    start, end = months.split("/")
    year, month = (int(part) for part in start.split("-"))
    end_year, end_month = (int(part) for part in end.split("-"))
    total = 0
    while (year, month) <= (end_year, end_month):
        total += calendar.monthrange(year, month)[1]
        month += 1
        if month == 13:
            month = 1
            year += 1
    return total


def _season_span(months: str) -> str:
    names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    start, end = months.split("/")

    def one(part: str) -> str:
        year, month = part.split("-")
        return f"{names[int(month) - 1]} {year}"

    return f"{one(start)} to {one(end)}"


def season_window(today: date, months: str) -> tuple[date, date]:
    """The rainfall months, placed on the year that contains today.

    Season A runs from September into February. A day between those
    months starts its own journey of the same length.
    """
    import calendar

    start_part, end_part = months.split("/")
    start_month = int(start_part.split("-")[1])
    end_month = int(end_part.split("-")[1])
    if end_month < start_month:
        if today.month >= start_month:
            start = date(today.year, start_month, 1)
            end_year = today.year + 1
        elif today.month <= end_month:
            start = date(today.year - 1, start_month, 1)
            end_year = today.year
        else:
            start = today
            return start, today + timedelta(days=_season_days(months) - 1)
        end = date(end_year, end_month, calendar.monthrange(end_year, end_month)[1])
        return start, end
    if start_month <= today.month <= end_month:
        start = date(today.year, start_month, 1)
        end = date(today.year, end_month, calendar.monthrange(today.year, end_month)[1])
        return start, end
    start = today
    return start, today + timedelta(days=_season_days(months) - 1)


def week_key(day: date) -> str:
    iso = day.isocalendar()
    return f"{iso.year}-W{iso.week:02d}"


def journey_calendar(district: str, crops: list[str], holding, today: date | None = None) -> dict:
    today = today or date.today()
    rain = _rain().get(district)
    months = rain.months if rain is not None else "2025-09/2026-02"
    start, end = season_window(today, months)
    routine = {"daily": [], "weekly": []}
    if isinstance(holding, dict):
        routine = holding_routine(
            district,
            list(crops or []),
            holding.get("unit") or "ha",
            holding.get("farm"),
            holding.get("portions") or {},
        )
    inside = start <= today <= end
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "today": today.isoformat(),
        "day": (today - start).days + 1 if inside else None,
        "total": (end - start).days + 1,
        "daily": routine.get("daily") or [],
        "weekly": routine.get("weekly") or [],
    }


def empty_checks() -> dict:
    return {"days": {}, "weeks": {}}


def mark_check(checks, day: date, item: str, on: bool) -> dict:
    stored = empty_checks()
    if isinstance(checks, dict):
        stored["days"] = dict(checks.get("days") or {})
        stored["weeks"] = dict(checks.get("weeks") or {})
    bucket = stored["days"] if item.startswith("d") else stored["weeks"]
    key = day.isoformat() if item.startswith("d") else week_key(day)
    current = [str(piece) for piece in (bucket.get(key) or [])]
    if on and item not in current:
        current.append(item)
    if not on and item in current:
        current.remove(item)
    if current:
        bucket[key] = current
    else:
        bucket.pop(key, None)
    return stored


def mark_count(checks) -> int:
    if not isinstance(checks, dict):
        return 0
    total = 0
    for group in ("days", "weeks"):
        for items in (checks.get(group) or {}).values():
            total += len(items)
    return total


def domestic_brief(district: str, crops: list[str]) -> dict:
    known = _known(crops)
    lines = [_climate(district), _line(
        "No soil type is published for this village. This note cannot name the soil.",
        "Aucun type de sol n'est publié pour ce village. Cette note ne peut pas nommer le sol.",
        "Nta bwoko bw'ubutaka bwanditswe kuri uyu mudugudu. Iyi nyandiko ntishobora kwita ubutaka.",
    )]
    for crop in known:
        lines.append(_breed(crop))
    lines.append(_line(
        f"The rain is for {district} district, not for one village. A breed that survives here is not printed.",
        f"La pluie est celle du district de {district}, pas d'un village. Une variété qui survit ici n'est pas imprimée.",
        f"Imvura ni iy'akarere ka {district}, si iy'umudugudu rumwe. Nta bwoko bw'imbuto bwanditswe ko bwakwera hano.",
    ))
    return {"lines": lines}


def _plain(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text


def _known(crops: list[str]) -> list[str]:
    allowed = {key for key, *_ in CROPS}
    return [crop for crop in crops if crop in allowed]


def _climate(district: str) -> dict:
    rain = _rain().get(district)
    if rain is None:
        return _line(
            f"{district} has no rainfall figure in this file.",
            f"{district} n'a pas de chiffre de pluie dans ce fichier.",
            f"{district} nta mubare w'imvura ufite muri iyi dosiye.",
        )
    shown = pretty(rain.total_mm)
    if rain.below_median:
        return _line(
            f"In {district}, this season's rain was {shown} mm. It was drier than most districts.",
            f"À {district}, la pluie de cette saison était de {shown} mm. Elle était plus sèche que dans la plupart des districts.",
            f"Muri {district}, imvura y'iki gihembwe yari {shown} mm. Yari yumye kurusha uturere twinshi.",
        )
    return _line(
        f"In {district}, this season's rain was {shown} mm. It sat at or above the middle of the 30 districts.",
        f"À {district}, la pluie de cette saison était de {shown} mm. Elle était au milieu des 30 districts, ou au-dessus.",
        f"Muri {district}, imvura y'iki gihembwe yari {shown} mm. Yari ku giciro cy'hagati cy'uturere 30, cyangwa hejuru.",
    )


def _breed(crop: str) -> dict:
    rw, en, fr = crop_label(crop)
    key = SEED_KEY.get(crop)
    share = _read("21", "National", "all", key, "improved") if key else None
    if share is None:
        return _line(
            f"No breed of {en} is published for this place.",
            f"Aucune variété de {fr} n'est publiée pour cet endroit.",
            f"Nta bwoko bwa {rw} bwanditswe kuri aha hantu.",
        )
    shown = pretty(share)
    return _line(
        f"No breed of {en} is published for this place. Nationally, {shown}% of this seed is improved. That is the country, not this village.",
        f"Aucune variété de {fr} n'est publiée pour cet endroit. Au niveau national, {shown} % de cette semence est améliorée. C'est le pays, pas ce village.",
        f"Nta bwoko bwa {rw} bwanditswe kuri aha hantu. Ku gihugu, {shown}% by'iyi mbuto ni iy'ingeri. Ni umubare w'igihugu, si uwa uyu mudugudu.",
    )


def farmer_plan(district: str, crops: list[str], reader: str, answers: dict | None) -> dict | None:
    if not _answers(answers):
        return None
    known = [crop for crop in crops if crop in {key for key, *_ in CROPS}]
    if not known:
        return None
    yields = {crop: _yields(district, crop) for crop in known}
    printed = [crop for crop in known if yields[crop]["all"] is not None]
    if len(printed) >= 2:
        lead = max(printed, key=lambda crop: yields[crop]["all"])
    elif printed:
        lead = printed[0]
    else:
        lead = known[0]
    rain = _rain().get(district)
    decision = classify(_cells(), district, None if rain is None else rain.below_median)
    dry = decision.action == "irrigation" or (rain is not None and rain.below_median)
    aim, aim_kind = _aim(yields[lead], reader)
    names = {code: crop_label(lead)[index] for index, code in enumerate(("rw", "en", "fr"))}
    return {
        "crop": lead,
        "goals": _goals(district, known, lead, names, yields, aim, aim_kind, reader),
        "seed": _seed(lead, names, answers["seed"]),
        "daily": _daily(names, answers, decision, dry, yields[lead]["all"] is None),
        "weekly": _weekly(lead, names, answers["purpose"], yields[lead]["all"] is None),
    }


def _answers(answers: dict | None) -> bool:
    if not isinstance(answers, dict):
        return False
    return all(answers.get(key) in allowed for key, allowed in ANSWERS.items())


def _aim(yields: dict, reader: str) -> tuple[Decimal | None, str | None]:
    if reader == "farmer-mini":
        if yields["all"] is not None:
            return yields["all"], "all"
        return None, None
    if yields["large"] is not None:
        return yields["large"], "large"
    if yields["all"] is not None:
        return yields["all"], "all"
    return None, None


def _line(en: str, fr: str, rw: str) -> dict:
    return {"en": en, "fr": fr, "rw": rw}


def _goals(district, known, lead, names, yields, aim, aim_kind, reader) -> list[dict]:
    lines = []
    row = yields[lead]
    if row["all"] is None:
        lines.append(_line(
            f"{names['en']} was not printed for {district}. A blank is not zero, so there is no harvest to aim at here.",
            f"{names['fr']} n'a pas été imprimé pour {district}. Une case vide n'est pas zéro, donc il n'y a pas de récolte à viser ici.",
            f"{names['rw']} ntikanditswe muri {district}. Ahatagira umubare si zeru, nta musaruro wo kwifashisha hano.",
        ))
    elif aim is not None:
        shown = pretty(aim)
        if aim_kind == "large":
            lines.append(_line(
                f"Your aim is {shown} kg from one hectare of {names['en']}. That is what large farms harvested in {district}.",
                f"Votre objectif est {shown} kg pour un hectare de {names['fr']}. C'est ce que les grandes exploitations ont récolté à {district}.",
                f"Intego yawe ni {shown} kg kuri hegitari ya {names['rw']}. Ni umusaruro w'abahinzi binini muri {district}.",
            ))
        else:
            lines.append(_line(
                f"Your aim is {shown} kg from one hectare of {names['en']}. That is the harvest printed for all farms in {district}.",
                f"Votre objectif est {shown} kg pour un hectare de {names['fr']}. C'est la récolte imprimée pour toutes les exploitations à {district}.",
                f"Intego yawe ni {shown} kg kuri hegitari ya {names['rw']}. Ni umusaruro wanditswe ku bahinzi bose muri {district}.",
            ))
    if row["all"] is not None and row["large"] is not None and row["large"] > row["all"] and reader == "farmer-mini":
        lines.append(_line(
            f"Large farms in {district} harvested {pretty(row['large'])} kg per hectare. That is a higher printed harvest, not another seed.",
            f"Les grandes exploitations à {district} ont récolté {pretty(row['large'])} kg par hectare. C'est une récolte imprimée plus haute, pas une autre semence.",
            f"Abahinzi binini muri {district} basaruye {pretty(row['large'])} kg kuri hegitari. Ni umusaruro wanditswe uri hejuru, si indi mbuto.",
        ))
    if row["all"] is not None and aim_kind == "large":
        lines.append(_line(
            f"All farms in {district} harvested {pretty(row['all'])} kg per hectare. Your aim stays with the large-farm figure.",
            f"Toutes les exploitations à {district} ont récolté {pretty(row['all'])} kg par hectare. Votre objectif reste le chiffre des grandes exploitations.",
            f"Abahinzi bose muri {district} basaruye {pretty(row['all'])} kg kuri hegitari. Intego yawe igumana umubare w'abahinzi binini.",
        ))
    if row["national"] is not None and (aim is None or row["national"] != aim):
        lines.append(_line(
            f"The country harvest for {names['en']} is {pretty(row['national'])} kg per hectare. That is the national figure, not {district}.",
            f"La récolte du pays pour {names['fr']} est {pretty(row['national'])} kg par hectare. C'est le chiffre national, pas celui de {district}.",
            f"Umusaruro w'igihugu wa {names['rw']} ni {pretty(row['national'])} kg kuri hegitari. Ni umubare w'igihugu, si uwa {district}.",
        ))
    if lead == "maize" and row["all"] is not None:
        lines.append(_line(
            f"The country goal for maize is {pretty(MAIZE_MILESTONE_KG)} kg per hectare. That is the national milestone, not the harvest of {district}. Keep your aim when it is already higher. Climb toward the milestone when your aim is lower.",
            f"L'objectif du pays pour le maïs est {pretty(MAIZE_MILESTONE_KG)} kg par hectare. C'est le jalon national, pas la récolte de {district}. Gardez votre objectif s'il est déjà plus haut. Montez vers le jalon s'il est plus bas.",
            f"Intego y'igihugu ku bigori ni {pretty(MAIZE_MILESTONE_KG)} kg kuri hegitari. Ni intego y'igihugu, si umusaruro wa {district}. Komeza intego yawe niba isanzwe iri hejuru. Jya bugufi niba iri hasi.",
        ))
    others = [crop for crop in known if crop != lead]
    if others:
        other_en = ", ".join(crop_label(crop)[1] for crop in others)
        other_fr = ", ".join(crop_label(crop)[2] for crop in others)
        other_rw = ", ".join(crop_label(crop)[0] for crop in others)
        lines.append(_line(
            f"This plan follows {names['en']}. You also chose {other_en}. On another plot, read one crop at a time.",
            f"Ce plan suit {names['fr']}. Vous avez aussi choisi {other_fr}. Sur un autre champ, lisez une culture à la fois.",
            f"Iyi gahunda ikurikiza {names['rw']}. Wahisemo kandi {other_rw}. Ku wundi murima, soma igihingwa kimwe.",
        ))
    lines.append(_line(
        f"These numbers are for {district} district, not for one village.",
        f"Ces chiffres sont ceux du district de {district}, pas d'un village.",
        f"Izi mibare ni iz'akarere ka {district}, si iz'umudugudu rumwe.",
    ))
    return lines


def _seed(lead: str, names: dict, choice: str) -> list[dict]:
    lines = [_line(
        f"The survey does not name a variety of {names['en']}. The class it separates is improved seed. Ask the sector agronomist which improved variety is sold for this district, and keep that name.",
        f"L'enquête ne nomme pas une variété de {names['fr']}. La classe qu'elle sépare est la semence améliorée. Demandez à l'agronome du secteur quelle variété améliorée est vendue pour ce district, et gardez ce nom.",
        f"Raporo ntivuga izina ry'imbuto ya {names['rw']}. Icyo itandukanya ni imbuto y'ingeri. Baza umujyanama w'ubuhinzi w'umurenge izina ry'imbuto y'ingeri igurishwa muri aka karere, ukabike iryo zina.",
    )]
    if choice == "improved":
        lines.append(_line(
            f"You will plant improved seed. Use that same seed on the whole plot, so the harvest can be compared with your aim.",
            f"Vous planterez de la semence améliorée. Utilisez la même semence sur tout le champ, pour comparer la récolte à votre objectif.",
            f"Uzahinga imbuto y'ingeri. Koresha iyo mbuto imwe ku murima wose, kugira ngo umusaruro ugereranywe n'intego yawe.",
        ))
    elif choice == "saved":
        lines.append(_line(
            f"Seed kept from the last harvest is traditional seed. Before you plant, ask the sector agronomist for improved seed of {names['en']} if you want to follow that class.",
            f"La semence gardée de la dernière récolte est une semence traditionnelle. Avant de planter, demandez à l'agronome du secteur de la semence améliorée de {names['fr']} si vous voulez suivre cette classe.",
            f"Imbuto wabitse ku musaruro ushize ni imbuto isanzwe. Mbere yo guhinga, baza umujyanama w'umurenge imbuto y'ingeri ya {names['rw']} niba ushaka gukurikiza iyo tsinda.",
        ))
    else:
        lines.append(_line(
            f"You have not chosen the seed. Choose one improved packet of {names['en']}. Do not mix packets on the same plot.",
            f"Vous n'avez pas choisi la semence. Choisissez un seul sachet amélioré de {names['fr']}. Ne mélangez pas les sachets sur le même champ.",
            f"Ntabwo wahisemo imbuto. Hitamo igipfunyuzo kimwe cy'imbuto y'ingeri ya {names['rw']}. Ntuhinge ibipfunyuzo bitandukanye ku murima umwe.",
        ))
    seed_key = SEED_KEY.get(lead)
    if seed_key:
        share = _read("21", "National", "all", seed_key, "improved")
        if share is not None:
            lines.append(_line(
                f"Nationally, {pretty(share)}% of {names['en']} seed is improved. That is the country, not this district.",
                f"Au niveau national, {pretty(share)} % de la semence de {names['fr']} est améliorée. C'est le pays, pas ce district.",
                f"Ku gihugu, {pretty(share)}% by'imbuto za {names['rw']} ni iz'ingeri. Ni umubare w'igihugu, si uwa aka karere.",
            ))
    elif lead == "beans":
        bush = _read("21", "National", "all", "bush_bean", "improved")
        climbing = _read("21", "National", "all", "climbing_bean", "improved")
        if bush is not None and climbing is not None:
            lines.append(_line(
                f"The survey does not print one seed figure for all beans. Nationally, bush bean seed is {pretty(bush)}% improved and climbing bean seed is {pretty(climbing)}% improved. Those are country figures, not this district.",
                f"L'enquête n'imprime pas un seul chiffre de semence pour tous les haricots. Au niveau national, la semence de haricot nain est améliorée à {pretty(bush)} % et celle de haricot volubile à {pretty(climbing)} %. Ce sont des chiffres du pays, pas de ce district.",
                f"Raporo nta mubare umwe yandika ku bishyimbo byose. Ku gihugu, imbuto z'ibishyimbo byo hasi z'ingeri ni {pretty(bush)}%, n'iz'ibishyimbo byo kuzamuka ni {pretty(climbing)}%. Iyo mibare ni iy'igihugu, si iy'aka karere.",
            ))
    elif lead == "bananas":
        lines.append(_line(
            "The survey splits banana into cooking, dessert, and beer. It does not print one improved-seed share for all bananas.",
            "L'enquête sépare la banane en banane à cuire, banane dessert et banane à bière. Elle n'imprime pas une seule part de semence améliorée pour toutes les bananes.",
            "Raporo itandukanya ibitoki byo guteka, ibyo kurya, n'iby'inzoga. Nta migabane imwe y'imbuto y'ingeri yandika ku bitoki byose.",
        ))
    else:
        lines.append(_line(
            f"The survey does not print an improved-seed share for {names['en']}.",
            f"L'enquête n'imprime pas une part de semence améliorée pour {names['fr']}.",
            f"Raporo nta migabane y'imbuto y'ingeri yandika kuri {names['rw']}.",
        ))
    return lines


def _daily(names, answers, decision, dry: bool, missing: bool) -> list[dict]:
    if missing:
        return [_line(
            f"Do not start a watering and fertilizer routine for {names['en']}. This district did not print it. Ask the sector agronomist whether it is grown here.",
            f"Ne commencez pas une routine d'eau et d'engrais pour {names['fr']}. Ce district ne l'a pas imprimé. Demandez à l'agronome du secteur s'il se cultive ici.",
            f"Ntutangire gahunda y'amazi n'ifumbire kuri {names['rw']}. Aka karere ntikakanditse. Baza umujyanama w'umurenge niba gihingwa hano.",
        )]
    lines = [_line(
        "The steps below follow the printed harvest. The survey does not print a litre amount or a spoon of fertilizer.",
        "Les étapes suivent la récolte imprimée. L'enquête n'imprime ni un nombre de litres ni une cuillerée d'engrais.",
        "Intambwe zikurikira umusaruro wanditswe. Raporo nta litiro cyangwa akanya k'ifumbire yandika.",
    )]
    if answers["water"] == "add" and dry:
        lines.append(_line(
            "Each morning, press a finger into the soil beside the plant. If it is dry, water the root until the soil is moist, then stop. Do this before the sun is high.",
            "Chaque matin, enfoncez un doigt dans le sol près du plant. S'il est sec, arrosez la racine jusqu'à ce que le sol soit humide, puis arrêtez. Faites-le avant que le soleil soit haut.",
            "Buri gitondo, shira urutoki mu butaka hafi y'igihimba. Niba bwumye, voma ku mizi kugeza ubutaka bufunze, hanyuma uhagarare. Kora bikiri kare, mbere y'izuba rikabije.",
        ))
    elif answers["water"] == "add":
        lines.append(_line(
            "Add water only when the soil is dry a finger deep. Water on the root. Extra water every day can rot the roots.",
            "Ajoutez de l'eau seulement quand le sol est sec à un doigt de profondeur. Arrosez la racine. Trop d'eau chaque jour peut pourrir les racines.",
            "Ongeramo amazi gusa iyo ubutaka bwumye ku rutoki. Voma ku mizi. Amazi menshi buri munsi ashobora kuboza imizi.",
        ))
    elif dry and decision.action == "irrigation":
        lines.append(_line(
            "You chose rain only. Small farms here irrigate much less than large farms, and this season was drier than most districts. Each morning, look at the leaves. If they fold, the crop needs water. Ask the sector agronomist about water before you count on this field.",
            "Vous avez choisi la pluie seulement. Les petites exploitations ici irriguent beaucoup moins que les grandes, et la saison a été plus sèche que dans la plupart des districts. Chaque matin, regardez les feuilles. Si elles se replient, la culture manque d'eau. Demandez à l'agronome du secteur de l'eau avant de compter sur ce champ.",
            "Wahisemo imvura gusa. Abahinzi bato bavoma bike kurusha abahinzi binini hano, kandi iki gihembwe cyari cyumye kurusha uturere twinshi. Buri gitondo reba amababi. Niba afunze, igihingwa gikeneye amazi. Baza umujyanama w'umurenge amazi mbere yo kwiringira uyu murima.",
        ))
    elif dry:
        lines.append(_line(
            "You chose rain only. This season was drier than most districts. Each morning, look at the leaves. If they fold, ask the sector agronomist about water.",
            "Vous avez choisi la pluie seulement. La saison a été plus sèche que dans la plupart des districts. Chaque matin, regardez les feuilles. Si elles se replient, demandez à l'agronome du secteur de l'eau.",
            "Wahisemo imvura gusa. Iki gihembwe cyari cyumye kurusha uturere twinshi. Buri gitondo reba amababi. Niba afunze, baza umujyanama w'umurenge amazi.",
        ))
    else:
        lines.append(_line(
            "Rain is the water. Each morning, look once. If water is sitting in the row, open a small drain so the roots are not in a pool.",
            "La pluie est l'eau. Chaque matin, regardez une fois. Si l'eau reste dans le rang, ouvrez un petit drain pour que les racines ne restent pas dans une flaque.",
            "Imvura ni amazi. Buri gitondo reba inshuro imwe. Niba amazi ameze mu murongo, fungura umuyoboro muto kugira ngo imizi itaguma mu mazi.",
        ))
    if decision.fertilizer_named:
        lines.append(_line(
            f"Do not stir a spoon of chemical into the watering can. The survey does not name the product or the measure. In this district, small farms use inorganic fertilizer less often than large farms, for all crops. Ask the sector agronomist for the fertilizer for {names['en']} and the measure for your field. Put it on moist soil beside the plant, then water the soil, not the leaves.",
            f"Ne mélangez pas une cuillerée de produit dans l'arrosoir. L'enquête ne nomme ni le produit ni la dose. Dans ce district, les petites exploitations utilisent moins souvent l'engrais minéral que les grandes, pour toutes les cultures. Demandez à l'agronome du secteur l'engrais pour {names['fr']} et la dose pour votre champ. Posez-le sur un sol humide près du plant, puis arrosez le sol, pas les feuilles.",
            f"Ntushyire akanya k'imiti mu mazi yo kuvoma. Raporo ntivuga izina ry'imiti cyangwa ingano. Muri aka karere, abahinzi bato bakoresha ifumbire mvaruganda bike kurusha abahinzi binini, ku bihingwa byose. Baza umujyanama w'umurenge ifumbire ya {names['rw']} n'ingano y'umurima wawe. Ishyire ku butaka bufunze hafi y'igihimba, hanyuma uvome ubutaka, si amababi.",
        ))
    else:
        lines.append(_line(
            "Do not add a chemical to the water each day. The figures for this district do not put fertilizer first.",
            "N'ajoutez pas un produit chimique à l'eau chaque jour. Les chiffres de ce district ne mettent pas l'engrais en premier.",
            "Ntongeramo imiti mu mazi buri munsi. Imibare y'aka karere ntisaba ifumbire mbere y'ibindi.",
        ))
    return lines


def _weekly(lead: str, names: dict, purpose: str, missing: bool) -> list[dict]:
    if missing:
        return [_line(
            "If this crop is already in the ground, walk it once a week. Pull small weeds, and take one marked leaf to the sector agronomist if many plants look the same.",
            "Si cette culture est déjà en terre, parcourez-la une fois par semaine. Arrachez les petites herbes, et portez une feuille marquée à l'agronome du secteur si beaucoup de plants se ressemblent.",
            "Niba iki gihingwa gisanzwe kiri mu butaka, kigemure inshuro imwe mu cyumweru. Kuraho ibyatsi bito, hanyuma ujyanane ikibabi kimwe kwa mujyanama w'umurenge niba ibihimba byinshi bisa kimwe.",
        )]
    lines = [
        _line(
            "Once a week, pull weeds while they are small, before they shade the crop.",
            "Une fois par semaine, arrachez les herbes tant qu'elles sont petites, avant qu'elles ne fassent de l'ombre à la culture.",
            "Buri cyumweru, kuraho ibyatsi bikiri bito, mbere yuko byitwikira igihingwa.",
        ),
        _line(
            "Once a week, look under the leaves for spots, holes, or insects. If several plants show the same mark, take one leaf to the sector agronomist. Do not spray a product the survey does not name.",
            "Une fois par semaine, regardez sous les feuilles les taches, les trous ou les insectes. Si plusieurs plants montrent la même marque, portez une feuille à l'agronome du secteur. Ne pulvérisez pas un produit que l'enquête ne nomme pas.",
            "Buri cyumweru, reba munsi y'amababi ibibara, utwobo, cyangwa udukoko. Niba ibihimba byinshi yerekana ikimenyetso kimwe, jyana ikibabi kimwe kwa mujyanama w'umurenge. Nturashe imiti raporo itavuga izina.",
        ),
    ]
    loss = None
    loss_key = LOSS_KEY.get(lead)
    if loss_key:
        loss = _read("16", "National", "all", loss_key, "post_harvest_loss")
    if purpose in {"sell", "both"} and loss is not None and loss > 0:
        lines.append(_line(
            f"The country printed that {pretty(loss)}% of {names['en']} is lost after harvest. That is national, not this district. As it ripens, pick what is ready, dry it, and keep it off the soil.",
            f"Le pays a imprimé que {pretty(loss)} % de {names['fr']} est perdu après la récolte. C'est national, pas ce district. Quand ça mûrit, cueillez ce qui est prêt, séchez-le, et gardez-le hors du sol.",
            f"Igihugu cyanditse ko {pretty(loss)}% bya {names['rw']} birapfa nyuma y'isarura. Ni umubare w'igihugu, si uwa aka karere. Iyo bikuruye, sarura ibiteguye, byumye, hanyuma ubibike kure y'ubutaka.",
        ))
    elif purpose == "food":
        lines.append(_line(
            "You want food at home. Each week, pick what is ready so it does not spoil in the field. Dry it before you store it.",
            "Vous voulez de la nourriture à la maison. Chaque semaine, cueillez ce qui est prêt pour que ça ne pourrisse pas au champ. Séchez-le avant de le garder.",
            "Ushaka ibiryo mu rugo. Buri cyumweru sarura ibiteguye, kugira ngo bitabora mu murima. Byumye mbere yo kubibika.",
        ))
    else:
        lines.append(_line(
            "You want to sell the harvest. Each week, pick what is ready so it does not spoil in the field. Dry it before you store it.",
            "Vous voulez vendre la récolte. Chaque semaine, cueillez ce qui est prêt pour que ça ne pourrisse pas au champ. Séchez-le avant de le garder.",
            "Ushaka kugurisha umusaruro. Buri cyumweru sarura ibiteguye, kugira ngo bitabora mu murima. Byumye mbere yo kubibika.",
        ))
    return lines
