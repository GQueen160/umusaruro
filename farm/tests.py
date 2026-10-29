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
        self.assertContains(response, "Tap the map where you will plant.")
        self.assertContains(response, "Aim at the district harvest.")
        self.assertContains(response, "Mini farm")
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

    def test_ministry_opens_the_crop_advisor(self):
        response = self.client.post("/role/", {"role": "ministry"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/advisor/")
        self.assertContains(response, "Ministry")
        self.assertContains(response, "Country tables.")
        self.assertNotContains(response, "Farmer map")

    def test_a_district_officer_opens_the_district_map(self):
        response = self.client.post("/role/", {"role": "district"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/sheet/")
        self.assertContains(response, "District agricultural officer")
        self.assertContains(response, "Click a district.")
        self.assertNotContains(response, "Farmer map")
        self.assertNotContains(response, "No sector table")

    def test_a_sector_officer_finds_the_sector_then_its_district(self):
        response = self.client.post("/role/", {"role": "sector"}, follow=True)
        self.assertEqual(response.request["PATH_INFO"], "/field/")
        self.assertContains(response, "Find your sector")
        self.assertContains(response, "No sector table")
        self.assertContains(response, "Sector agricultural officer")
        self.assertNotContains(response, 'id="target"')
        self.assertNotContains(response, "Ibihingwa byose")

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

    def test_a_target_needs_a_village(self):
        response = self.client.post(
            "/api/plans/save/",
            data={"village_id": "", "crops": ["maize"], "target_kg": "1800"},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
