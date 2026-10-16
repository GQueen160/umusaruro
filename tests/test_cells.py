import unittest
from decimal import Decimal

from umusaruro.cells import BlankCell, load


class SeasonACellsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = load()

    def cell(self, table, geography, farmer_type, crop, measure):
        return self.cells.get(table, geography, farmer_type, crop, measure)

    def test_national_maize_yield_reproduces(self):
        self.assertEqual(self.cell("13", "National", "ssf", "maize", "yield").number(), Decimal("1897"))
        self.assertEqual(self.cell("13", "National", "all", "maize", "yield").number(), Decimal("1994"))
        self.assertEqual(self.cell("13", "National", "lsf", "maize", "yield").number(), Decimal("4337"))
        self.assertEqual(self.cell("14", "National", "lsf", "maize", "yield").number(), Decimal("4337"))

    def test_national_irrigation_reproduces(self):
        self.assertEqual(self.cell("31", "National", "ssf", "", "irrigation").number(), Decimal("12.6"))
        self.assertEqual(self.cell("31", "National", "lsf", "", "irrigation").number(), Decimal("60.3"))

    def test_contract_districts(self):
        self.assertEqual(self.cell("13", "Nyagatare", "all", "maize", "yield").number(), Decimal("2887"))
        self.assertEqual(self.cell("13", "Kirehe", "all", "maize", "yield").number(), Decimal("2515"))
        self.assertEqual(self.cell("13", "Kamonyi", "all", "maize", "yield").number(), Decimal("1863"))
        self.assertEqual(self.cell("14", "Kamonyi", "lsf", "maize", "yield").number(), Decimal("6470"))
        self.assertEqual(self.cell("31", "Nyagatare", "ssf", "", "irrigation").number(), Decimal("6.4"))
        self.assertEqual(self.cell("31", "Nyagatare", "lsf", "", "irrigation").number(), Decimal("50.0"))
        self.assertEqual(self.cell("20", "Kamonyi", "ssf", "all_crops", "farmers").number(), Decimal("45.3"))
        self.assertEqual(self.cell("20", "National", "ssf", "all_crops", "farmers").number(), Decimal("35.2"))
        self.assertEqual(self.cell("21", "National", "all", "maize", "improved").number(), Decimal("64.3"))
        self.assertEqual(self.cell("16", "National", "all", "maize", "post_harvest_loss").number(), Decimal("0.3"))

    def test_only_two_districts_reach_the_2026_27_milestone(self):
        above = sorted(
            row.geography
            for row in self.cells.rows
            if row.table == "13"
            and row.crop == "maize"
            and row.measure == "yield"
            and row.farmer_type == "all"
            and row.geography != "National"
            and row.number() >= Decimal("2260")
        )
        self.assertEqual(above, ["Kirehe", "Nyagatare"])

    def test_blanks_are_not_zero(self):
        blanks = [
            self.cell("14", "Karongi", "lsf", "maize", "yield"),
            self.cell("14", "Nyarugenge", "lsf", "maize", "yield"),
            self.cell("20", "Nyarugenge", "lsf", "all_crops", "farmers"),
            self.cell("31", "Gicumbi", "lsf", "", "irrigation"),
        ]
        for row in blanks:
            self.assertTrue(row.blank)
            self.assertIsNone(row.value)
            with self.assertRaises(BlankCell):
                row.number()

    def test_every_cell_names_its_source_and_is_unchecked(self):
        for row in self.cells.rows:
            self.assertEqual(row.survey, "SAS")
            self.assertEqual(row.season, "A")
            self.assertEqual(row.year, "2026")
            self.assertTrue(row.source_url.startswith("https://statistics.gov.rw/"))
            self.assertFalse(row.checked)
            self.assertIn(row.printed, {"number", "dash", "empty", "absent"})


if __name__ == "__main__":
    unittest.main()
