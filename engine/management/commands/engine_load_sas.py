"""Load the NISR Seasonal Agricultural Survey workbooks held in data/raw.

Each workbook is checked against data/raw/MANIFEST.csv (SHA-256), read by
the same detector an upload goes through, and published under the name of
the person who reviewed the proposals:

    python manage.py engine_load_sas --confirm-as "Full Name"

A workbook already held is skipped.
"""

import csv
import re
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from engine import ingest

TITLES = {
    "annual": "Seasonal Agricultural Survey {year}, annual tables",
    "season_a": "Seasonal Agricultural Survey {year}, Season A tables",
    "season_b": "Seasonal Agricultural Survey {year}, Season B tables",
    "tables": "Seasonal Agricultural Survey {year}, tables",
}


def title_of(name: str, year: int) -> str:
    kind = next((k for k in TITLES if k in name), "tables")
    return TITLES[kind].format(year=year)


class Command(BaseCommand):
    help = "Load and publish the SAS workbooks listed in data/raw/MANIFEST.csv."

    def add_arguments(self, parser):
        parser.add_argument("--confirm-as", required=True, help="Name of the person who reviewed the proposals")

    def handle(self, *args, confirm_as, **options):
        raw = Path(settings.BASE_DIR) / "data" / "raw"
        with (raw / "MANIFEST.csv").open(newline="", encoding="utf-8") as handle:
            entries = [e for e in csv.DictReader(handle) if e["path"].startswith("sas/")]
        for entry in entries:
            path = raw / entry["path"]
            if ingest.sha256(path) != entry["sha256"]:
                raise CommandError(f"{entry['path']}: SHA-256 differs from MANIFEST.csv")
            year = int(re.search(r"20\d\d", path.name).group())
            try:
                dataset = ingest.register(
                    path, filename=path.name, title=title_of(path.name, year), publisher=entry["publisher"],
                    license=entry["license"], source_url=entry["url"], landing_page=entry["landing_page"],
                    default_year=year)
            except ingest.AlreadyHeld as held:
                self.stdout.write(f"skip  {path.name}: {held}")
                continue
            count = ingest.publish(dataset, confirmed_as=confirm_as)
            tables = dataset.tables.filter(include=True).count()
            self.stdout.write(f"load  {path.name}: {tables} tables, {count} observations")
