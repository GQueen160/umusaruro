import csv
import shutil
import tempfile
from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.management import call_command
from django.test import TestCase, override_settings

from engine import ingest
from engine.models import Dataset, Observation

ROOT = Path(settings.BASE_DIR)
SAS_2026_A = ROOT / "data/raw/sas/sas_2026_season_a_tables.xlsx"


class IngestTests(TestCase):
    def setUp(self):
        self.var = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.var)
        self.settings = override_settings(VAR_DIR=Path(self.var), UPLOAD_DIR=Path(self.var) / "uploads")
        self.settings.enable()
        self.addCleanup(self.settings.disable)

    def register(self, path=SAS_2026_A, **extra):
        return ingest.register(path, filename=path.name, title="SAS 2026 A", default_year=2026, **extra)

    def test_register_proposes_and_publishes_nothing(self):
        dataset = self.register()
        self.assertEqual(dataset.status, Dataset.REVIEW)
        self.assertEqual(dataset.path, "data/raw/sas/sas_2026_season_a_tables.xlsx")
        self.assertTrue(dataset.tables.filter(include=True, measure="yield").exists())
        self.assertFalse(Observation.objects.exists())

    def test_publish_needs_a_person(self):
        dataset = self.register()
        with self.assertRaisesRegex(ValueError, "signed-in person or a name"):
            ingest.publish(dataset, confirmed_as="  ")

    def test_published_values_match_the_back_series(self):
        dataset = self.register()
        count = ingest.publish(dataset, confirmed_as="Reviewer Name")
        self.assertEqual(Observation.objects.count(), count)
        dataset.refresh_from_db()
        self.assertEqual((dataset.status, dataset.confirmer), (Dataset.PUBLISHED, "Reviewer Name"))
        with (ROOT / "data/history/season_a.csv").open(encoding="utf-8") as handle:
            history = [h for h in csv.DictReader(handle)
                       if h["year"] == "2026" and h["lever"] == "maize_yield" and h["printed"] == "number"]
        self.assertGreater(len(history), 30)
        for h in history:
            ob = Observation.objects.get(year=2026, season="A", crop="maize", measure="yield",
                                         farmer_type=h["farmer_type"], geography=h["geography"],
                                         table__number=h["table"])
            self.assertEqual(ob.value, Decimal(h["workbook_value"]), h["geography"])

    def test_the_same_file_twice_is_refused(self):
        self.register()
        with self.assertRaises(ingest.AlreadyHeld):
            self.register()

    def test_upload_is_copied_under_var(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "upload.xlsx"
            shutil.copyfile(SAS_2026_A, copy)
            dataset = self.register(copy)
        self.assertTrue(dataset.path.startswith("var:uploads/"))
        self.assertTrue(ingest.file_path(dataset).exists())

    def test_unreadable_file_is_kept_with_the_reason(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "notes.pdf"
            bad.write_bytes(b"%PDF-1.4")
            dataset = self.register(bad)
        self.assertEqual(dataset.status, Dataset.FAILED)
        self.assertIn("unsupported file type .pdf", dataset.error)


class LoadSasTests(TestCase):
    def test_loads_every_workbook_once(self):
        call_command("engine_load_sas", confirm_as="Reviewer Name", stdout=open("/dev/null", "w"))
        self.assertEqual(Dataset.objects.filter(status=Dataset.PUBLISHED).count(), 9)
        crops = set(Observation.objects.filter(measure="yield").values_list("crop", flat=True))
        self.assertTrue({"maize", "cassava", "irish_potato", "climbing_bean", "paddy_rice"} <= crops)
        before = Observation.objects.count()
        call_command("engine_load_sas", confirm_as="Reviewer Name", stdout=open("/dev/null", "w"))
        self.assertEqual(Observation.objects.count(), before)
