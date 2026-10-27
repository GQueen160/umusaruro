import unittest
from decimal import Decimal

from umusaruro.cells import load
from umusaruro.rules import (
    FERTILIZER_GAP,
    IRRIGATION_GAP,
    IRRIGATION_SSF_MAX,
    SEED_GAP,
    SEED_LEAD,
    _action,
    classify,
)


class RulesTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = load()

    def decision(self, geography, rainfall=None):
        return classify(self.cells, geography, rainfall)

    def test_constants_match_the_contract(self):
        self.assertEqual(IRRIGATION_GAP, Decimal("30"))
        self.assertEqual(IRRIGATION_SSF_MAX, Decimal("15"))
        self.assertEqual(SEED_GAP, Decimal("25"))
        self.assertEqual(SEED_LEAD, Decimal("5"))
        self.assertEqual(FERTILIZER_GAP, Decimal("15"))

    def test_nyagatare_waits_on_rainfall(self):
        waiting = self.decision("Nyagatare")
        self.assertTrue(waiting.above_milestone)
        self.assertEqual(waiting.irrigation_gap, Decimal("43.6"))
        self.assertTrue(waiting.irrigation_candidate)
        self.assertEqual(waiting.seed_gap, Decimal("39.1"))
        self.assertTrue(waiting.seed_fires)
        self.assertEqual(waiting.fertilizer_gap, Decimal("23.8"))
        self.assertTrue(waiting.fertilizer_named)
        self.assertTrue(waiting.unresolved)
        self.assertIsNone(waiting.action)

        wet = self.decision("Nyagatare", rainfall=False)
        self.assertEqual(wet.action, "seed")
        self.assertFalse(wet.unresolved)

        dry = self.decision("Nyagatare", rainfall=True)
        self.assertEqual(dry.action, "irrigation")
        self.assertTrue(dry.fertilizer_named)

    def test_kirehe_is_one_tenth_under_the_irrigation_line(self):
        decision = self.decision("Kirehe", rainfall=True)
        self.assertTrue(decision.above_milestone)
        self.assertEqual(decision.irrigation_gap, Decimal("63.7"))
        self.assertTrue(decision.irrigation_candidate)
        self.assertEqual(decision.seed_gap, Decimal("36.9"))
        self.assertEqual(decision.fertilizer_gap, Decimal("16.9"))
        self.assertTrue(decision.fertilizer_named)
        self.assertEqual(decision.action, "irrigation")

    def test_kamonyi_is_seed_and_fertilizer(self):
        decision = self.decision("Kamonyi")
        self.assertFalse(decision.above_milestone)
        self.assertFalse(decision.irrigation_candidate)
        self.assertEqual(decision.seed_gap, Decimal("54.7"))
        self.assertEqual(decision.fertilizer_gap, Decimal("46.1"))
        self.assertEqual(decision.action, "seed")
        self.assertTrue(decision.fertilizer_named)
        self.assertFalse(decision.unresolved)

    def test_gakenke_is_seed_only(self):
        decision = self.decision("Gakenke")
        self.assertFalse(decision.irrigation_candidate)
        self.assertEqual(decision.irrigation_gap, Decimal("28.7"))
        self.assertEqual(decision.seed_gap, Decimal("29.2"))
        self.assertTrue(decision.seed_fires)
        self.assertFalse(decision.fertilizer_named)
        self.assertEqual(decision.action, "seed")

    def test_ngoma_is_irrigation_only_if_rainfall_passes(self):
        waiting = self.decision("Ngoma")
        self.assertTrue(waiting.irrigation_candidate)
        self.assertFalse(waiting.seed_fires)
        self.assertEqual(waiting.seed_gap, Decimal("12.2"))
        self.assertEqual(waiting.fertilizer_gap, Decimal("18.2"))
        self.assertTrue(waiting.fertilizer_named)
        self.assertTrue(waiting.unresolved)

        dry = self.decision("Ngoma", rainfall=True)
        self.assertEqual(dry.action, "irrigation")
        wet = self.decision("Ngoma", rainfall=False)
        self.assertIsNone(wet.action)
        self.assertTrue(wet.fertilizer_named)

    def test_blank_large_farm_cell_cannot_fire_a_gap(self):
        gicumbi = self.decision("Gicumbi")
        self.assertIsNone(gicumbi.irrigation_gap)
        self.assertFalse(gicumbi.irrigation_candidate)

        nyarugenge = self.decision("Nyarugenge")
        self.assertIsNone(nyarugenge.seed_gap)
        self.assertFalse(nyarugenge.seed_fires)
        self.assertIsNone(nyarugenge.irrigation_gap)

    def test_boundaries_beside_the_constants(self):
        muhanga = self.decision("Muhanga")
        self.assertFalse(muhanga.irrigation_candidate)
        rwamagana = self.decision("Rwamagana", rainfall=True)
        self.assertEqual(rwamagana.seed_gap, Decimal("24.5"))
        self.assertFalse(rwamagana.seed_fires)
        self.assertEqual(rwamagana.action, "irrigation")

    def test_a_seed_lead_under_five_points_keeps_irrigation(self):
        short_lead, unresolved = _action(Decimal("40"), True, Decimal("43"), True, True)
        self.assertEqual(short_lead, "irrigation")
        self.assertFalse(unresolved)
        long_lead, _ = _action(Decimal("40"), True, Decimal("45"), True, True)
        self.assertEqual(long_lead, "seed")


if __name__ == "__main__":
    unittest.main()
