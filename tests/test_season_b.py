import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from umusaruro import footers
from umusaruro.cells import BlankCell, load, CSV_PATH, SEASON_B_PATH
from umusaruro.signoff import DISTRICTS, SEASONS, key_of, read_sheet, review

SEASON_B = next(season for season in SEASONS if season.name == "B")


class SeasonBCellsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cells = load(SEASON_B_PATH)

    def test_every_cell_is_season_b_from_the_report(self):
        self.assertEqual(len(self.cells.rows), 930)
        for cell in self.cells.rows:
            self.assertEqual((cell.survey, cell.season, cell.year), ("SAS", "B", "2026"))
            self.assertIn("SAS%202026B_Main%20report.pdf", cell.source_url)
            self.assertIn(cell.table, {"18", "23", "29"})

    def test_season_a_file_holds_no_season_b_cell(self):
        for cell in load(CSV_PATH).rows:
            self.assertEqual(cell.season, "A")

    def test_national_rows_match_the_report_text(self):
        expect = {
            ("18", "all", "all_crops", "farmers"): "20.9",
            ("18", "ssf", "all_crops", "farmers"): "19.4",
            ("18", "lsf", "all_crops", "farmers"): "65.0",
            ("23", "all", "all_crops", "farmers"): "57.5",
            ("29", "all", "", "irrigation"): "13.1",
            ("29", "ssf", "", "irrigation"): "11.5",
            ("29", "lsf", "", "irrigation"): "56.2",
        }
        for (table, farmer, crop, measure), value in expect.items():
            self.assertEqual(self.cells.get(table, "National", farmer, crop, measure).number(), Decimal(value))

    def test_a_printed_dash_stays_blank_although_the_workbook_says_zero(self):
        for district in ("Nyarugenge", "Ngororero"):
            cell = self.cells.get("18", district, "lsf", "all_crops", "farmers")
            self.assertEqual(cell.printed, "dash")
            with self.assertRaises(BlankCell):
                cell.number()

    def test_every_district_has_the_screen_cells(self):
        for district in DISTRICTS:
            for farmer in ("ssf", "lsf"):
                self.cells.get("18", district, farmer, "all_crops", "farmers")
                self.cells.get("23", district, farmer, "all_crops", "farmers")
                self.cells.get("29", district, farmer, "", "irrigation")


class SeasonBSignoffTest(unittest.TestCase):
    def test_sheet_lists_every_screen_cell_once(self):
        cells = load(SEASON_B_PATH)
        sheet = read_sheet(SEASON_B.sheet_path)
        self.assertEqual([key_of(r) for r in sheet], [key_of(r) for r in SEASON_B.blank_sheet()])
        self.assertEqual(len(sheet), 189)
        for row in sheet:
            self.assertEqual(int(row["pdf_page"]), SEASON_B.pages[row["table"]])
        result = review(cells, sheet)
        self.assertEqual(result.mismatched, [])
        self.assertEqual(result.incomplete, [])

    def test_checked_only_where_signed(self):
        cells = load(SEASON_B_PATH)
        matched = {(k.table, k.geography, k.farmer_type, k.crop, k.measure)
                   for k in review(cells, read_sheet(SEASON_B.sheet_path)).matched}
        for cell in cells.rows:
            key = (cell.table, cell.geography, cell.farmer_type, cell.crop, cell.measure)
            self.assertEqual(cell.checked, key in matched, key)


class FooterTest(unittest.TestCase):
    def write(self, footer_on_page, checker="A. Person", checked_on="2026-10-23"):
        handle = tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False, newline="", encoding="utf-8")
        with handle:
            writer = csv.DictWriter(handle, fieldnames=["table", "pdf_page", "pdf_footer", "workbook_footer",
                                                        "footer_on_page", "checker", "checked_on"])
            writer.writeheader()
            writer.writerow({"table": "29", "pdf_page": "57", "pdf_footer": footers.EXPECTED,
                             "workbook_footer": "Source: NISR, SAS 2025", "footer_on_page": footer_on_page,
                             "checker": checker, "checked_on": checked_on})
        self.addCleanup(Path(handle.name).unlink)
        return Path(handle.name)

    def test_the_committed_file_records_the_disagreement(self):
        row = footers.read()["29"]
        self.assertEqual(row["pdf_footer"], "Source: NISR, SAS 2026")
        self.assertEqual(row["workbook_footer"], "Source: NISR, SAS 2025")
        for table in ("18", "23"):
            self.assertEqual(footers.read()[table]["workbook_footer"], footers.read()[table]["pdf_footer"])

    def test_resolved_needs_the_typed_footer_a_name_and_a_date(self):
        self.assertTrue(footers.resolved("29", self.write("Source:  NISR, SAS 2026")))
        self.assertTrue(footers.resolved("29", self.write("Source : NISR, SAS 2026")))
        self.assertFalse(footers.resolved("29", self.write("Source: NISR, SAS 2025")))
        self.assertFalse(footers.resolved("29", self.write("")))
        self.assertFalse(footers.resolved("29", self.write("Source: NISR, SAS 2026", checker="")))
        self.assertFalse(footers.resolved("29", self.write("Source: NISR, SAS 2026", checked_on="23/10/2026")))
        self.assertFalse(footers.resolved("18", self.write("Source: NISR, SAS 2026")))


if __name__ == "__main__":
    unittest.main()
