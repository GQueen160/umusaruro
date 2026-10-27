from decimal import Decimal

from django.test import TestCase

from farm.advice import advise
from farm.models import FieldPlan
from farm.places import locate
from farm.talk import hear


class PlaceTests(TestCase):
    def test_a_tap_in_gitega_names_the_village(self):
        place = locate(30.05251, -1.94856)
        self.assertEqual(place["village"], "Gihanga")
        self.assertEqual(place["sector"], "Gitega")
        self.assertEqual(place["district"], "Nyarugenge")

    def test_home_is_the_farmer_map(self):
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Kanda ku karita")
        self.assertContains(response, "id=\"map\"")


class AdviceTests(TestCase):
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

    def test_a_target_needs_a_village(self):
        response = self.client.post(
            "/api/plans/save/",
            data={"village_id": "", "crops": ["maize"], "target_kg": "1800"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
