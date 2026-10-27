import unittest

from umusaruro.cells import load
from umusaruro.signoff import PAGES, blank_sheet, key_of, read_sheet, review, typed_matches


class SignoffTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = load()
        cls.sheet = read_sheet()

    def test_sheet_lists_every_screen_cell_once(self):
        expected = [key_of(row) for row in blank_sheet()]
        found = [key_of(row) for row in self.sheet]
        self.assertEqual(found, expected)
        self.assertEqual(len(set(found)), len(found))
        for key in found:
            self.cells.get(key.table, key.geography, key.farmer_type, key.crop, key.measure)

    def test_pages_match_the_report(self):
        for row in self.sheet:
            self.assertEqual(int(row["pdf_page"]), PAGES[row["table"]])

    def test_no_typed_value_disagrees(self):
        result = review(self.cells, self.sheet)
        self.assertEqual(result.mismatched, [])
        self.assertEqual(result.incomplete, [])

    def test_checked_only_where_signed(self):
        matched = {
            (k.table, k.geography, k.farmer_type, k.crop, k.measure)
            for k in review(self.cells, self.sheet).matched
        }
        for cell in self.cells.rows:
            key = (cell.table, cell.geography, cell.farmer_type, cell.crop, cell.measure)
            self.assertEqual(cell.checked, key in matched, key)

    def test_typed_values(self):
        nyagatare = self.cells.get("13", "Nyagatare", "all", "maize", "yield")
        self.assertTrue(typed_matches("2,887", nyagatare))
        self.assertTrue(typed_matches("2887", nyagatare))
        self.assertFalse(typed_matches("2877", nyagatare))
        self.assertFalse(typed_matches("-", nyagatare))
        fifty = self.cells.get("31", "Nyagatare", "lsf", "", "irrigation")
        self.assertTrue(typed_matches("50", fifty))
        dash = self.cells.get("14", "Karongi", "lsf", "maize", "yield")
        self.assertTrue(typed_matches("-", dash))
        self.assertFalse(typed_matches("0", dash))
        absent = self.cells.get("14", "Nyarugenge", "lsf", "maize", "yield")
        self.assertTrue(typed_matches("-", absent))


if __name__ == "__main__":
    unittest.main()
