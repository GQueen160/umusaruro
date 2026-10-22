import csv
import sys
import unittest
from decimal import Decimal
from pathlib import Path

from umusaruro import history
from umusaruro.cells import BlankCell

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_history  # noqa: E402
import raw_manifest  # noqa: E402


class RawFilesTest(unittest.TestCase):
    def test_every_raw_file_matches_the_manifest(self):
        self.assertEqual(raw_manifest.verify(), [])

    def test_every_raw_file_names_nisr_and_the_licence(self):
        for row in raw_manifest.read():
            self.assertTrue(row["url"].startswith("https://statistics.gov.rw/"), row["path"])
            self.assertTrue(row["landing_page"].startswith("https://statistics.gov.rw/"), row["path"])
            self.assertIn("CC BY 4.0", row["license"])
            self.assertEqual(len(row["sha256"]), 64)


class ReferenceTest(unittest.TestCase):
    def test_thirty_districts_with_nisr_codes(self):
        with (ROOT / "data" / "reference" / "districts.csv").open(encoding="utf-8") as handle:
            rows = list(csv.DictReader(handle))
        self.assertEqual(len(rows), 30)
        self.assertEqual(sum(int(r["sectors"]) for r in rows), 416)
        for r in rows:
            self.assertTrue(r["district_id"].startswith(r["province_id"]))


class HistoryTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.history = history.load()

    def test_the_committed_file_is_what_the_builder_writes(self):
        rows, _quality, compared = build_history.build()
        with history.PATH.open(newline="", encoding="utf-8") as handle:
            self.assertEqual(list(csv.DictReader(handle)), rows)
        self.assertEqual(compared, 343)

    def test_eight_years_of_season_a(self):
        self.assertEqual(self.history.years, list(range(2019, 2027)))
        for year in self.history.years:
            for lever in history.LEVERS:
                farmers = ["lsf"] if lever == "maize_yield_lsf" else ["all"] if lever == "maize_yield" else ["all", "ssf", "lsf"]
                for farmer in farmers:
                    districts = [p for p in self.history.points
                                 if (p.year, p.lever, p.farmer_type) == (year, lever, farmer) and p.geography != "National"]
                    self.assertEqual(len(districts), 30, (year, lever, farmer))

    def test_national_rows_match_the_workbooks(self):
        expect = {
            (2019, "seed", "all"): "22.4", (2019, "fertilizer", "all"): "26.1", (2019, "irrigation", "all"): "3.1",
            (2019, "maize_yield", "all"): "1539", (2019, "maize_yield_lsf", "lsf"): "1.9",
            (2020, "irrigation", "all"): "6.5", (2023, "fertilizer", "all"): "59.6",
            (2026, "maize_yield", "all"): "1994", (2026, "irrigation", "ssf"): "12.6",
        }
        for (year, lever, farmer), value in expect.items():
            self.assertEqual(str(self.history.get(year, lever, "National", farmer).number()), value)

    def test_2019_large_farm_yield_stays_in_tonnes(self):
        point = self.history.get(2019, "maize_yield_lsf", "National", "lsf")
        self.assertEqual(point.unit, "t_per_ha")
        self.assertEqual(self.history.get(2020, "maize_yield_lsf", "National", "lsf").unit, "kg_per_ha")

    def test_a_workbook_zero_is_a_blank(self):
        point = self.history.get(2026, "maize_yield_lsf", "Nyarugenge", "lsf")
        self.assertTrue(point.blank)
        self.assertEqual(point.printed, "zero")
        with self.assertRaises(BlankCell):
            point.number()

    def test_a_missing_district_row_is_absent(self):
        point = self.history.get(2020, "maize_yield_lsf", "Nyarugenge", "lsf")
        self.assertEqual(point.printed, "absent")

    def test_series_runs_in_year_order_with_codes(self):
        series = self.history.series("maize_yield", "Nyagatare", "all")
        self.assertEqual([p.year for p in series], list(range(2019, 2027)))
        self.assertTrue(all(p.district_id == "52" for p in series))
        self.assertEqual(series[-1].number(), Decimal(self.history.get(2026, "maize_yield", "Nyagatare", "all").value))

    def test_every_point_cites_a_manifest_workbook(self):
        urls = {row["url"] for row in raw_manifest.read()}
        for p in self.history.points:
            self.assertIn(p.source_url, urls)
            self.assertTrue(p.table.isdigit())


if __name__ == "__main__":
    unittest.main()
