from decimal import Decimal

from django.test import TestCase

import re

from farm.advice import advise
from farm.plan import farmer_plan
from farm.models import FieldPlan
from farm.places import locate
from farm.talk import hear


class PlaceTests(TestCase):
    def test_a_tap_in_gitega_names_the_village(self):
        place = locate(30.05251, -1.94856)
        self.assertEqual(place["village"], "Gihanga")
        self.assertEqual(place["sector"], "Gitega")
        self.assertEqual(place["district"], "Nyarugenge")

    def test_the_first_screen_is_the_map_and_the_choice(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Who is reading?")
        self.assertContains(response, ">en<")
        self.assertContains(response, ">fra<")
        self.assertContains(response, ">kin<")
        self.assertContains(response, "id=\"map\"")
        self.assertContains(response, "id=\"search\" role=\"search\" hidden")
        self.assertContains(response, "Mini farm")
        self.assertContains(response, "Domestic")
        self.assertContains(response, "Sector agricultural officer")


class AdviceTests(TestCase):
    def test_the_color_follows_the_printed_harvest(self):
        self.assertEqual(advise("Nyarugenge", ["maize"])["flag"], "plant")
        self.assertEqual(advise("Nyagatare", ["maize"])["flag"], "check")
        self.assertEqual(advise("Nyarugenge", ["sorghum"])["flag"], "stop")

    def test_a_mini_farm_aims_at_the_district_harvest(self):
        advice = advise("Nyagatare", ["maize"], reader="farmer-mini")
        self.assertEqual(advice["target"]["kg"], "2887")
        self.assertIn("abahinzi bose", advice["target"]["why_rw"])
        large = advise("Nyagatare", ["maize"], reader="farmer-large")
        self.assertEqual(large["target"]["kg"], "5292")

    def test_nyagatare_maize_says_irrigate_and_aims_at_large_farms(self):
        advice = advise("Nyagatare", ["maize"])
        self.assertEqual(advice["action"], "irrigation")
        self.assertEqual(advice["target"]["kg"], "5292")
        self.assertIn("Voma", advice["cards"][0]["title_rw"])
        self.assertNotIn("0 kg", advice["cards"][0]["body_rw"])

    def test_a_blank_large_farm_cell_is_not_zero(self):
        advice = advise("Karongi", ["maize"])
        self.assertEqual(advice["target"]["kg"], "1517")
        text = " ".join(card["body_rw"] for card in advice["cards"])
        self.assertNotIn("0 kg", text)
        self.assertIn("1,517", text)

    def test_two_crops_name_the_higher_yield_without_a_variety(self):
        advice = advise("Nyagatare", ["maize", "beans"])
        self.assertEqual(advice["stronger"], "maize")
        lead = advice["cards"][0]["body_rw"]
        self.assertIn("izina ry'imbuto", lead)


_ANSWERS = {"seed": "improved", "water": "add", "purpose": "both"}


def _lines(plan, *keys):
    return " ".join(line["en"] for key in keys for line in plan[key])


class PlanTests(TestCase):
    def test_the_plan_names_the_aim_the_country_and_the_day(self):
        plan = farmer_plan("Nyagatare", ["maize"], "farmer-mini", {
            "seed": "saved", "water": "add", "purpose": "both",
        })
        text = _lines(plan, "goals", "seed", "daily", "weekly")
        self.assertIn("2,887", text)
        self.assertIn("2,260", text)
        self.assertIn("not the harvest of Nyagatare", text)
        self.assertIn("traditional seed", text)
        self.assertIn("does not name a variety", text)
        self.assertIn("64.3%", text)
        self.assertIn("press a finger", text)
        self.assertIn("Do not stir a spoon", text)
        self.assertIn("pull weeds", text.lower())
        self.assertIsNone(re.search(r"\d+(\.\d+)?\s*(L|litres|ml)\b", text))
        self.assertIsNone(farmer_plan("Nyagatare", ["maize"], "farmer-mini", {"seed": "improved"}))

    def test_a_blank_crop_does_not_become_a_national_aim(self):
        plan = farmer_plan("Nyarugenge", ["sorghum"], "farmer-mini", _ANSWERS)
        goals = _lines(plan, "goals")
        self.assertIn("not printed", goals)
        self.assertIn("not zero", goals)
        self.assertNotIn("Your aim", goals)
        self.assertIn("Do not start", plan["daily"][0]["en"])

    def test_rain_only_does_not_invent_a_daily_litre(self):
        plan = farmer_plan("Nyagatare", ["maize"], "farmer-large", {
            "seed": "unset", "water": "rain", "purpose": "food",
        })
        self.assertIn("5,292", _lines(plan, "goals"))
        self.assertIn("rain only", _lines(plan, "daily").lower())
        self.assertIn("food at home", _lines(plan, "weekly").lower())

    def test_beans_keep_the_two_seed_figures_apart(self):
        plan = farmer_plan("Nyagatare", ["beans"], "farmer-mini", _ANSWERS)
        text = _lines(plan, "seed")
        self.assertIn("bush bean", text)
        self.assertIn("climbing bean", text)
        self.assertIn("0.5%", text)
        self.assertIn("0.2%", text)
        self.assertNotIn("variety name is", text)


class VoiceTests(TestCase):
    def test_a_district_name_is_the_district(self):
        heard = hear("nhinge ibigori i nyagatare")
        self.assertEqual(heard["crops"], ["maize"])
        self.assertEqual(heard["place"]["district"], "Nyagatare")
        self.assertEqual(heard["place"]["village_id"], "")
        self.assertEqual(heard["advice"]["action"], "irrigation")
        self.assertIn("Voma", heard["reply_rw"])

    def test_the_same_village_name_in_two_places_is_not_guessed(self):
        heard = hear("umudugudu wa nyagatare")
        self.assertGreater(len(heard["choices"]), 1)
        self.assertIsNone(heard["place"])


class ReaderTests(TestCase):
    def test_the_field_map_waits_for_a_reader(self):
        self.assertRedirects(self.client.get("/field/"), "/")

    def test_a_mini_farm_opens_the_field(self):
        response = self.client.post("/role/", {"role": "farmer-mini"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/field/")
        self.assertContains(response, "Select the village where you will plant.")
        self.assertContains(response, "Mini farm")
        self.assertContains(response, 'id="crops" hidden')
        self.assertContains(response, "How big is the farm?")
        self.assertContains(response, "On what scale, in {unit}, will you plant {name}?")
        self.assertContains(response, "Country goal on the farm")
        self.assertContains(response, "max on this land: {kg} kg.")
        self.assertContains(response, "You are exceeding the size of the farm.")
        self.assertNotContains(response, 'role="dialog"')
        self.assertNotContains(response, "Ibihingwa byose")

    def test_a_large_farm_keeps_the_large_farm_aim(self):
        self.client.post("/role/", {"role": "farmer-large"})
        response = self.client.post(
            "/api/advice/",
            data={"district": "Nyagatare", "crops": ["maize"]},
            content_type="application/json",
        )
        self.assertEqual(response.json()["advice"]["target"]["kg"], "5292")

    def test_the_field_sends_the_mini_aim(self):
        self.client.post("/role/", {"role": "farmer-mini"})
        response = self.client.post(
            "/api/advice/",
            data={"district": "Nyagatare", "crops": ["maize"]},
            content_type="application/json",
        )
        self.assertEqual(response.json()["advice"]["target"]["kg"], "2887")
        self.assertIsNone(response.json()["advice"].get("plan"))
        maize = response.json()["advice"]["rates"][0]
        self.assertEqual(maize["crop"], "maize")
        self.assertEqual(maize["kind"], "goal")
        self.assertEqual(maize["kg_ha"], "2260")

    def test_the_country_goal_scales_to_the_portion(self):
        from decimal import Decimal

        from farm.plan import portion_kg

        self.assertEqual(portion_kg(Decimal("2260"), Decimal("0.5"), "ha"), 1130)
        self.assertEqual(portion_kg(Decimal("2260"), Decimal("2000"), "m2"), 452)

    def test_a_dry_field_turns_missed_rain_into_litres(self):
        from farm.plan import holding_routine

        routine = holding_routine("Nyagatare", ["maize"], "ha", "5", {
            "maize": {"area": "5", "target": "20000"},
        })
        daily = routine["daily"][0]["en"]
        self.assertIn("35,787 litres", daily)
        self.assertIn("6,477,500 litres", daily)
        self.assertIn("129.55 mm", daily)
        self.assertNotIn("spoon", daily.lower())
        weekly = " ".join(line["en"] for line in routine["weekly"])
        self.assertIn("773 kg", weekly)
        self.assertIn("weed the whole 5 hectares", weekly)
        self.assertIn("11,300 kg", routine["summary"][1]["en"])

    def test_a_wet_field_adds_no_extra_litres(self):
        from farm.plan import holding_routine

        routine = holding_routine("Gisagara", ["beans"], "ha", "1", {
            "beans": {"area": "1", "target": "700"},
        })
        daily = routine["daily"][0]["en"]
        self.assertIn("add no extra litres", daily)
        self.assertIn("7,560,000 litres", daily)

    def test_a_domestic_note_names_the_rain_and_no_breed(self):
        self.client.post("/role/", {"role": "farmer-domestic"}, follow=True)
        response = self.client.post(
            "/api/advice/",
            data={"district": "Nyagatare", "crops": ["maize"]},
            content_type="application/json",
        )
        lines = " ".join(line["en"] for line in response.json()["advice"]["domestic"]["lines"])
        self.assertIn("Nyagatare", lines)
        self.assertIn("mm", lines)
        self.assertIn("No soil type", lines)
        self.assertIn("No breed", lines)
        lowered = lines.lower()
        for banned in ("clay", "loam", "sand", "ferral", "rhm"):
            self.assertNotIn(banned, lowered)
        page = self.client.get("/field/")
        self.assertContains(page, "Select the village where you will plant.")
        self.assertContains(page, "Domestic")

    def test_ministry_opens_the_crop_advisor(self):
        response = self.client.post("/role/", {"role": "ministry"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/advisor/")
        self.assertContains(response, "Ministry")
        self.assertContains(response, "Country tables.")
        self.assertNotContains(response, "Farmer map")

    def test_a_district_officer_stays_in_one_district(self):
        chooser = self.client.post("/role/", {"role": "district"})
        self.assertContains(chooser, "Which district do you read?")
        self.assertContains(chooser, "District agricultural officer")
        response = self.client.post(
            "/role/", {"role": "district", "district": "Nyagatare"}, follow=True,
        )
        self.assertEqual(response.request["PATH_INFO"], "/district/nyagatare/")
        self.assertContains(response, "Your district only.")
        self.assertNotContains(response, 'href="/district/gasabo/"')
        self.assertNotContains(response, "Farmer map")
        self.assertNotContains(response, "No sector table")
        other = self.client.get("/district/gasabo/", follow=True)
        self.assertEqual(other.request["PATH_INFO"], "/district/nyagatare/")
        overview = self.client.get("/sheet/", follow=True)
        self.assertEqual(overview.request["PATH_INFO"], "/district/nyagatare/")
        self.client.post("/role/clear/")
        open_again = self.client.get("/district/gasabo/")
        self.assertContains(open_again, 'href="/district/nyagatare/"')

    def test_a_sector_officer_stays_in_one_sector(self):
        from farm.places import sectors

        chooser = self.client.post("/role/", {"role": "sector"})
        self.assertContains(chooser, "Which sector do you read?")
        self.assertContains(chooser, "Sector agricultural officer")
        listed = self.client.post("/role/", {
            "role": "sector", "district": "Kicukiro", "step": "list",
        })
        row = next(item for item in sectors("Kicukiro") if item["name"] == "Gahanga")
        self.assertContains(listed, "Gahanga")
        opened = self.client.post("/role/", {
            "role": "sector",
            "district": "Kicukiro",
            "sector_id": row["id"],
            "step": "open",
        }, follow=True)
        self.assertEqual(opened.request["PATH_INFO"], "/field/")
        self.assertContains(opened, "Gahanga")
        self.assertContains(opened, "No sector table")
        self.assertNotContains(opened, 'id="pick-district"')
        self.assertNotContains(opened, 'id="target"')
        self.assertNotContains(opened, "Ibihingwa byose")
        other = self.client.get("/district/nyagatare/", follow=True)
        self.assertEqual(other.request["PATH_INFO"], "/field/")
        own = self.client.get("/district/kicukiro/")
        self.assertEqual(own.status_code, 200)
        self.assertNotContains(own, 'href="/district/gasabo/"')
        moved = self.client.post(
            "/api/advice/",
            data={"district": "Nyagatare", "crops": ["maize"]},
            content_type="application/json",
        )
        self.assertIn("Kicukiro", moved.json()["advice"]["note_en"])

    def test_a_sector_board_draws_the_district(self):
        from farm.advice import sector_board
        from sheet.sheet import bar_width

        board = sector_board("Nyagatare", ["maize"])
        self.assertEqual(board["action"], "irrigation")
        kinds = [row["kind"] for row in board["rows"]]
        self.assertIn("water", kinds)
        self.assertIn("rain", kinds)
        self.assertIn("maize", kinds)
        maize = next(row for row in board["rows"] if row["kind"] == "maize")
        self.assertEqual(maize["bars"][0]["label_en"], "District")
        self.assertGreater(maize["bars"][0]["width"], 0)
        self.assertTrue(maize["bars"][0]["url"].startswith("https://"))
        water = next(row for row in sector_board("Kicukiro", [])["rows"] if row["kind"] == "water")
        shown = Decimal(water["bars"][0]["value"].replace(",", ""))
        self.assertEqual(water["bars"][0]["width"], bar_width(shown, Decimal(100)))
        self.assertEqual(water["bars"][0]["table"], "31")
        sorghum = next(row for row in sector_board("Nyarugenge", ["sorghum"])["rows"] if row["kind"] == "sorghum")
        self.assertTrue(sorghum["bars"][0]["blank"])
        self.assertEqual(sorghum["bars"][0]["width"], 0)
        for row in board["rows"]:
            for bar in row["bars"]:
                self.assertLessEqual(bar["width"], 100)
                self.assertNotIn("sector", bar["label_en"].lower())

    def test_choosing_again_returns_to_the_map(self):
        self.client.post("/role/", {"role": "farmer-large"})
        response = self.client.post("/role/clear/", follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/")
        self.assertContains(response, "Who is reading?")

    def test_the_language_control_switches_the_choice_screen(self):
        french = self.client.post("/lang/", {"lang": "fr", "next": "/"}, follow=True)
        self.assertContains(french, "Qui lit ?")
        self.assertContains(french, "Petite exploitation")
        self.assertContains(french, 'lang="fr"')
        kinyarwanda = self.client.post("/lang/", {"lang": "rw", "next": "/"}, follow=True)
        self.assertContains(kinyarwanda, "Ni nde usoma?")
        self.assertContains(kinyarwanda, "Umuhinzi muto")
        english = self.client.post("/lang/", {"lang": "en", "next": "/"}, follow=True)
        self.assertContains(english, "Who is reading?")
        self.assertContains(english, "Mini farm")

    def test_a_language_outside_the_three_is_ignored(self):
        response = self.client.post("/lang/", {"lang": "de", "next": "https://example.com"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/")
        self.assertContains(response, "Who is reading?")

    def test_an_unknown_choice_is_not_stored(self):
        response = self.client.post("/role/", {"role": "admin"})
        self.assertRedirects(response, "/")
        self.assertNotIn("reader", self.client.session)


class PlanTests(TestCase):
    def test_a_target_is_kept_for_the_village(self):
        place = locate(30.05251, -1.94856)
        response = self.client.post(
            "/api/plans/save/",
            data={"village_id": place["village_id"], "crops": ["maize"], "target_crop": "maize", "target_kg": "1800"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        saved = FieldPlan.objects.get()
        self.assertEqual(saved.village, "Gihanga")
        self.assertEqual(saved.target_kg, Decimal("1800.0"))
        self.assertIsNone(saved.holding)

    def test_the_farm_plan_keeps_the_land_and_the_goal(self):
        place = locate(30.05251, -1.94856)
        response = self.client.post(
            "/api/plans/save/",
            data={
                "village_id": place["village_id"],
                "crops": ["paddy_rice"],
                "unit": "ha",
                "farm": "12",
                "portions": {"paddy_rice": {"area": "11", "target": "31000"}},
            },
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        saved = FieldPlan.objects.get()
        self.assertEqual(saved.target_crop, "paddy_rice")
        self.assertEqual(saved.target_kg, Decimal("31000.0"))
        self.assertEqual(saved.holding["farm"], "12")
        self.assertEqual(saved.holding["portions"]["paddy_rice"]["area"], "11")
        self.client.post("/role/", {"role": "farmer-mini"})
        page = self.client.get("/field/")
        self.assertContains(page, "Save my plan")

    def test_october_is_day_60_of_the_season(self):
        from datetime import date

        from farm.plan import season_window

        start, end = season_window(date(2026, 10, 30), "2025-09/2026-02")
        self.assertEqual(start.isoformat(), "2026-09-01")
        self.assertEqual(end.isoformat(), "2027-02-28")
        self.assertEqual((date(2026, 10, 30) - start).days + 1, 60)
        outside, outside_end = season_window(date(2026, 5, 1), "2025-09/2026-02")
        self.assertEqual(outside.isoformat(), "2026-05-01")
        self.assertEqual((outside_end - outside).days + 1, 181)

    def test_a_day_can_be_marked_and_cleared(self):
        place = locate(30.05251, -1.94856)
        saved = self.client.post(
            "/api/plans/save/",
            data={
                "village_id": place["village_id"],
                "crops": ["paddy_rice"],
                "unit": "ha",
                "farm": "12",
                "portions": {"paddy_rice": {"area": "11", "target": "31000"}},
            },
            content_type="application/json",
        )
        plan = saved.json()["plan"]
        day = plan["journey"]["today"]
        marked = self.client.post(
            f"/api/plans/{plan['id']}/check/",
            data={"date": day, "item": "d0", "on": True},
            content_type="application/json",
        )
        self.assertEqual(marked.status_code, 200)
        self.assertEqual(marked.json()["plan"]["marked"], 1)
        week = self.client.post(
            f"/api/plans/{plan['id']}/check/",
            data={"date": day, "item": "w0", "on": True},
            content_type="application/json",
        )
        self.assertEqual(week.json()["plan"]["marked"], 2)
        cleared = self.client.post(
            f"/api/plans/{plan['id']}/check/",
            data={"date": day, "item": "d0", "on": False},
            content_type="application/json",
        )
        self.assertEqual(cleared.json()["plan"]["marked"], 1)
        self.assertEqual(FieldPlan.objects.get().target_kg, Decimal("31000.0"))

    def test_a_target_needs_a_village(self):
        response = self.client.post(
            "/api/plans/save/",
            data={"village_id": "", "crops": ["maize"], "target_kg": "1800"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)


class ChatTests(TestCase):
    def _model(self, replies):
        import os
        from unittest.mock import patch

        calls = []

        def transport(payload, key):
            calls.append(payload)
            return replies[len(calls) - 1]

        return calls, patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key", "NVIDIA_MODEL": ""}), transport

    def test_a_question_outside_the_survey_is_turned_away(self):
        from farm.chat import answer

        calls, env, transport = self._model(['{"about": false, "place": "", "crops": []}'])
        with env:
            result = answer("What is the capital of France?", lang="en", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertFalse(result["about"])
        self.assertIn("cannot answer", result["answer"])
        self.assertIn("Kicukiro", result["answer"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["model"], "nvidia/nemotron-3.5-bolt-e4b")

    def test_a_yield_question_is_read_from_the_district(self):
        from farm.chat import answer

        replies = [
            '{"about": true, "place": "", "crops": []}',
            "Kicukiro printed a maize harvest for the district.",
        ]
        calls, env, transport = self._model(replies)
        with env:
            result = answer(
                "What did maize yield in Kicukiro?",
                lang="en", reader="farmer-mini", office=None, page={}, crops=[], transport=transport,
            )
        self.assertTrue(result["about"])
        self.assertEqual(result["answer"], replies[1])
        facts = calls[1]["messages"][1]["content"].split("FACTS:\n", 1)[1]
        self.assertIn("Kicukiro", facts)
        self.assertIn("kg/ha", facts)
        self.assertNotIn("99999", facts)

    def test_a_number_the_survey_did_not_print_is_dropped(self):
        from farm.chat import answer

        replies = [
            '{"about": true, "place": "Kicukiro", "crops": ["maize"]}',
            "The maize yield in Kicukiro is 99999 kg.",
        ]
        calls, env, transport = self._model(replies)
        with env:
            result = answer("maize in Kicukiro", lang="en", reader="farmer-large", office=None, page={}, crops=[], transport=transport)
        self.assertNotIn("99999", result["answer"])
        self.assertIn("Kicukiro", result["answer"])
        self.assertIn("kg/ha", result["answer"])

    def test_a_shared_village_name_asks_for_the_district(self):
        from farm.chat import answer

        replies = ['{"about": true, "place": "Mukoni", "crops": ["maize"]}']
        calls, env, transport = self._model(replies)
        with env:
            result = answer("Tell me about Mukoni maize", lang="en", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertTrue(result["about"])
        self.assertIn("Mukoni", result["answer"])
        self.assertIn("Name the district", result["answer"])
        self.assertEqual(len(calls), 1)

    def test_an_officer_stays_inside_the_chosen_district(self):
        from farm.chat import answer

        replies = [
            '{"about": true, "place": "Nyagatare", "crops": ["maize"]}',
            "You read Kicukiro only. Maize there is the printed district harvest.",
        ]
        calls, env, transport = self._model(replies)
        with env:
            result = answer(
                "What did maize yield in Nyagatare?",
                lang="en",
                reader="district",
                office={"district": "Kicukiro"},
                page={},
                crops=[],
                transport=transport,
            )
        facts = calls[1]["messages"][1]["content"].split("FACTS:\n", 1)[1]
        self.assertIn("You read Kicukiro only.", facts)
        self.assertTrue(result["answer"].startswith("You read Kicukiro only."))
        self.assertNotIn("99999", result["answer"])

    def test_the_chat_stays_quiet_without_a_key(self):
        import os
        from unittest.mock import patch
        from farm.chat import answer

        with patch.dict(os.environ, {"NVIDIA_API_KEY": ""}):
            result = answer("What did maize yield in Kicukiro?", lang="en", reader="farmer-mini", office=None, page={}, crops=[])
        self.assertEqual(result["status"], 503)
        self.assertIn("NVIDIA", result["answer"])

    def test_the_field_offers_the_chat_and_the_gate_does_not(self):
        gate = self.client.get("/")
        self.assertNotContains(gate, 'id="chat-open"')
        self.client.post("/role/", {"role": "farmer-mini"})
        field = self.client.get("/field/")
        self.assertContains(field, 'id="chat-open"')
        self.assertContains(field, "Ask about a village")

    def test_the_endpoint_turns_away_a_question_outside_the_survey(self):
        from unittest.mock import patch

        def fake(messages, max_tokens=200, timeout=20, transport=None):
            return '{"about": false, "place": "", "crops": []}'

        with patch("farm.chat.complete", side_effect=fake):
            response = self.client.post(
                "/api/chat/",
                data={"message": "What is the capital of France?"},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["about"])
        self.assertIn("cannot answer", response.json()["answer"])

    def test_a_kinyarwanda_crop_question_stays_inside_the_survey(self):
        from farm.chat import answer

        calls, env, transport = self._model(['{"about": false, "place": "", "crops": []}'])
        with env:
            result = answer("Nshaka guhinga umuceri", lang="rw", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertTrue(result["about"])
        self.assertIn("umudugudu", result["answer"])
        self.assertEqual(len(calls), 1)

    def test_a_greeting_explains_what_the_chat_can_do(self):
        from farm.chat import answer

        calls, env, transport = self._model(['{"about": false, "greeting": true, "place": "", "crops": []}'])
        with env:
            result = answer("How are you today?", lang="en", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertTrue(result["about"])
        self.assertIn("Hello.", result["answer"])
        self.assertIn("harvest", result["answer"])
        self.assertNotIn("cannot answer", result["answer"])
        self.assertEqual(len(calls), 1)

        calls, env, transport = self._model(['{"about": false, "greeting": false, "place": "", "crops": []}'])
        with env:
            result = answer("Muraho", lang="rw", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertTrue(result["about"])
        self.assertIn("Muraho.", result["answer"])
        self.assertIn("umusaruro", result["answer"])

    def test_a_greeting_still_explains_when_the_model_fails(self):
        import os
        from unittest.mock import patch
        from farm.chat import answer
        from farm.nvidia import NvidiaError

        def transport(payload, key):
            raise NvidiaError("failed")

        with patch.dict(os.environ, {"NVIDIA_API_KEY": "test-key"}):
            result = answer("Muraho", lang="rw", reader="farmer-mini", office=None, page={}, crops=[], transport=transport)
        self.assertEqual(result["status"], 200)
        self.assertIn("Muraho.", result["answer"])
