"""The engine's reader and detector, without Django.

The strongest check: read every NISR workbook in data/raw the way an
upload is read, and every value in the verified back-series
(data/history/season_a.csv) must come out the same, blank reason included.
"""

import csv
import re
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from engine import detect, reader, vocab

ROOT = Path(__file__).resolve().parents[1]
DISTRICTS = [r["district"] for r in csv.DictReader((ROOT / "data/reference/districts.csv").open(encoding="utf-8"))]


def wide_table(title, header_rows, cells):
    rows = [[None, title]] + [[None, *h] for h in header_rows]
    for i, name in enumerate(DISTRICTS):
        rows.append([None, name, *cells(i)])
    rows.append([None, "National", *cells(99)])
    return rows


class VocabTests(unittest.TestCase):
    def test_seasons_written_without_a_space(self):
        self.assertEqual(vocab.season("Table 37: Season A2019_Use of inorganic fertilizer"), "A")
        self.assertEqual(vocab.season("2024 Season A_Use of seeds"), "A")
        self.assertEqual(vocab.season("Season C, Source of water"), "C")
        self.assertEqual(vocab.season("Seasonal Agricultural Survey"), "")

    def test_crop_names(self):
        self.assertEqual(vocab.crop("Taro & Yams"), "yams_taro")
        self.assertEqual(vocab.crop(" Irish  potatoes "), "irish_potato")
        self.assertIsNone(vocab.crop("Cereals"))

    def test_type_tables_are_not_read_as_use(self):
        self.assertIsNone(vocab.title_measure("Percentage of plots by type of inorganic fertilizer"))
        self.assertIsNone(vocab.title_measure("Source of improved seeds per district"))
        self.assertEqual(vocab.title_measure("Use of Inorganic fertilizer by farmer type"), "inorganic_fertilizer")
        self.assertEqual(vocab.title_measure("Use of organic fertilizer by farmer type"), "organic_fertilizer")


class WideTableTests(unittest.TestCase):
    def setUp(self):
        def cells(i):
            if i == 0:
                return ["-", None, Decimal(0)]
            return [Decimal(1000 + i), Decimal(500 + i), Decimal(7)]
        rows = wide_table("Table 5: Season B 2031_Average yield by crop type per district (Kg/Ha)",
                          [["District", "Maize", "Cereals", "Climbing bean"]], cells)
        self.sheets = {"Table 5": rows}
        [self.proposal] = detect.propose(self.sheets, default_year=2030)

    def test_proposal(self):
        p = self.proposal
        self.assertEqual((p["status"], p["layout"], p["year"], p["season"], p["measure"]),
                         ("recognised", "wide", 2031, "B", "yield"))
        kept = {c["header"]: c for c in p["columns"] if c["keep"]}
        self.assertEqual(sorted(kept), ["climbing bean", "maize"])
        skipped = next(c for c in p["columns"] if c["header"] == "cereals")
        self.assertEqual(skipped["why"], "a total of several crops")

    def test_blanks_keep_their_reason(self):
        rows = detect.extract(self.sheets, self.proposal)
        first = {r["crop"]: r for r in rows if r["geography"] == DISTRICTS[0]}
        self.assertEqual((first["maize"]["value"], first["maize"]["printed"]), (None, "dash"))
        self.assertEqual((first["climbing_bean"]["value"], first["climbing_bean"]["printed"]), (None, "zero"))
        national = [r for r in rows if r["geography"] == "National" and r["crop"] == "maize"]
        self.assertEqual(national[0]["value"], Decimal(1099))
        self.assertEqual(len(rows), 2 * (len(DISTRICTS) + 1))

    def test_input_table_keeps_only_the_yes_share(self):
        header = [["District", "Overall", "Overall", "SSF", "SSF"],
                  ["", "Percentage of farmers", "Percentage of farmers", "Percentage of farmers",
                   "Percentage of farmers"],
                  ["", "Yes", "No", "Yes", "No"]]
        rows = wide_table("Table 9: Season A 2031_Use of pesticides by farmer type per district", header,
                          lambda i: [Decimal(40), Decimal(60), Decimal(30), Decimal(70)])
        [p] = detect.propose({"T": rows})
        kept = [(c["measure"], c["farmer_type"], c["basis"]) for c in p["columns"] if c["keep"]]
        self.assertEqual(kept, [("pesticides", "all", "farmers"), ("pesticides", "ssf", "farmers")])

    def test_unknown_title_is_listed_not_guessed(self):
        rows = wide_table("Table 2: Number of sampled segments per district", [["District", "Segments"]],
                          lambda i: [Decimal(5)])
        [p] = detect.propose({"T": rows})
        self.assertEqual(p["status"], "unrecognised")
        self.assertEqual(detect.extract({"T": rows}, p), [])


class LongTableTests(unittest.TestCase):
    def test_csv_with_one_row_per_district_and_year(self):
        lines = ["province,district,year,crop,yield (kg/ha),improved seed use (%)"]
        for year in (2030, 2031):
            for name in DISTRICTS:
                lines.append(f"Somewhere,{name},{year},Maize,\"1,250.5\",12")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "panel.csv"
            path.write_text("\n".join(lines), encoding="utf-8")
            sheets = reader.read(path)
        [p] = detect.propose(sheets)
        self.assertEqual((p["status"], p["layout"]), ("recognised", "long"))
        roles = {c["header"]: c["role"] for c in p["columns"] if c["keep"]}
        self.assertEqual(roles, {"district": "district", "year": "year", "crop": "crop",
                                 "yield (kg/ha)": "measure", "improved seed use (%)": "measure"})
        rows = detect.extract(sheets, p)
        self.assertEqual(len(rows), 2 * 2 * len(DISTRICTS))
        maize = next(r for r in rows if r["measure"] == "yield" and r["year"] == 2031)
        self.assertEqual((maize["crop"], maize["value"], maize["unit"]), ("maize", Decimal("1250.5"), "kg/ha"))


class ReaderTests(unittest.TestCase):
    def test_old_excel_is_refused_with_a_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "old.xls"
            path.write_bytes(b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1" + b"\0" * 100)
            with self.assertRaisesRegex(reader.UnreadableFile, "save the file as .xlsx or .csv"):
                reader.read(path)

    def test_semicolon_csv_and_thousands(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.csv"
            path.write_text("a;b\n1,234;-\n", encoding="utf-8")
            self.assertEqual(reader.read(path), {"x": [["a", "b"], [Decimal(1234), "-"]]})


class NisrWorkbookTests(unittest.TestCase):
    LEVER = {"seed": ("improved_seed", "", "farmers"), "fertilizer": ("inorganic_fertilizer", "", "farmers"),
             "irrigation": ("irrigation", "", "farmers"), "maize_yield": ("yield", "maize", ""),
             "maize_yield_lsf": ("yield", "maize", "")}

    @classmethod
    def setUpClass(cls):
        cls.obs, cls.proposals = {}, {}
        for path in sorted((ROOT / "data/raw/sas").glob("*.xlsx")):
            year = int(re.search(r"20\d\d", path.name).group())
            sheets = reader.read(path)
            cls.proposals[path.name] = detect.propose(sheets, year)
            for p in cls.proposals[path.name]:
                if p["status"] != "recognised":
                    continue
                for r in detect.extract(sheets, p):
                    k = (r["year"], r["season"], p["number"], r["measure"], r["crop"], r["geography"],
                         r["farmer_type"], r["basis"])
                    cls.obs[k] = r

    def test_every_back_series_value_is_read_the_same(self):
        checked = 0
        with (ROOT / "data/history/season_a.csv").open(encoding="utf-8") as handle:
            for h in csv.DictReader(handle):
                measure, crop, basis = self.LEVER[h["lever"]]
                k = (int(h["year"]), "A", h["table"], measure, crop, h["geography"], h["farmer_type"], basis)
                if h["printed"] == "absent":
                    self.assertNotIn(k, self.obs)
                    continue
                r = self.obs[k]
                expected = Decimal(h["workbook_value"]) if h["printed"] == "number" else None
                self.assertEqual((r["value"], r["printed"]), (expected, h["printed"]), k)
                checked += 1
        self.assertGreater(checked, 2700)

    def test_every_season_is_known(self):
        for name, proposals in self.proposals.items():
            for p in proposals:
                if p["status"] == "recognised":
                    self.assertIn(p["season"], "ABC", f"{name} {p['title']}")
                    self.assertTrue(p["season"], f"{name} {p['title']}")


if __name__ == "__main__":
    unittest.main()
