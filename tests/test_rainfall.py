import unittest
from decimal import Decimal

from tools.transcribe_season_a import DISTRICTS
from umusaruro.cells import load as load_cells
from umusaruro.rainfall import load as load_rainfall
from umusaruro.rules import classify_all


class RainfallGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.rainfall = load_rainfall()
        cls.decisions = classify_all(load_cells(), cls.rainfall)

    def test_every_district_has_one_total(self):
        self.assertEqual(list(self.rainfall), DISTRICTS)
        for gate in self.rainfall.values():
            self.assertEqual(gate.version, "CHIRPS v2.0")
            self.assertEqual(gate.months, "2025-09/2026-02")
            self.assertGreater(gate.cells, 0)

    def test_half_the_districts_sit_below_the_median(self):
        below = [name for name, gate in self.rainfall.items() if gate.below_median]
        self.assertEqual(len(below), 15)
        self.assertEqual({gate.median_mm for gate in self.rainfall.values()}, {Decimal("689.25")})

    def test_kicukiro_rests_on_seven_cells(self):
        self.assertEqual(self.rainfall["Kicukiro"].cells, 7)
        self.assertTrue(self.rainfall["Kicukiro"].below_median)

    def test_seven_irrigation_districts(self):
        irrigation = sorted(name for name, decision in self.decisions.items() if decision.action == "irrigation")
        self.assertEqual(
            irrigation,
            ["Gatsibo", "Kayonza", "Kicukiro", "Kirehe", "Ngoma", "Nyagatare", "Rwamagana"],
        )

    def test_rainfall_removes_three_candidates(self):
        candidates = sorted(name for name, decision in self.decisions.items() if decision.irrigation_candidate)
        self.assertEqual(len(candidates), 10)
        for name in ("Karongi", "Nyamasheke", "Nyamagabe"):
            self.assertFalse(self.rainfall[name].below_median)
            self.assertNotEqual(self.decisions[name].action, "irrigation")
        self.assertEqual(self.decisions["Nyamasheke"].action, "seed")
        self.assertEqual(self.decisions["Nyamagabe"].action, "seed")
        self.assertIsNone(self.decisions["Karongi"].action)
        self.assertIsNone(self.decisions["Karongi"].seed_gap)

    def test_no_decision_is_left_waiting(self):
        self.assertFalse(any(decision.unresolved for decision in self.decisions.values()))

    def test_gatsibo_keeps_irrigation_when_seed_gap_is_smaller(self):
        gatsibo = self.decisions["Gatsibo"]
        self.assertEqual(gatsibo.irrigation_gap, Decimal("55.5"))
        self.assertEqual(gatsibo.seed_gap, Decimal("51.8"))
        self.assertEqual(gatsibo.action, "irrigation")


if __name__ == "__main__":
    unittest.main()
