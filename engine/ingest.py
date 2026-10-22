"""Register a file, keep the detector's proposals, publish on confirmation.

register()  hashes the file, refuses a file already held, keeps a copy,
            and stores one SourceTable per sheet with its proposal and
            the warnings a reviewer must see. Nothing is published.
publish()   reads every included table into Observations and records who
            confirmed it. Run again, it replaces the dataset's rows.
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from engine import detect, reader
from engine.models import Dataset, Observation, SourceTable

VAR_PREFIX = "var:"


class AlreadyHeld(ValueError):
    def __init__(self, dataset: Dataset):
        super().__init__(f"this file is already held as '{dataset.title}'")
        self.dataset = dataset


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def file_path(dataset: Dataset) -> Path:
    if dataset.path.startswith(VAR_PREFIX):
        return Path(settings.VAR_DIR) / dataset.path[len(VAR_PREFIX):]
    return Path(settings.BASE_DIR) / dataset.path


def keep(path: Path, digest: str, filename: str) -> str:
    """Files already in the repository stay where they are; uploads are copied under var/."""
    repo = Path(settings.BASE_DIR).resolve()
    if path.resolve().is_relative_to(repo / "data"):
        return str(path.resolve().relative_to(repo))
    target = Path(settings.UPLOAD_DIR) / f"{digest}{Path(filename).suffix.lower()}"
    target.parent.mkdir(parents=True, exist_ok=True)
    if not target.exists():
        shutil.copyfile(path, target)
    return VAR_PREFIX + str(target.relative_to(settings.VAR_DIR))


@transaction.atomic
def register(path: Path, *, filename: str, title: str, publisher: str = "", license: str = "",
             source_url: str = "", landing_page: str = "", default_year: int | None = None,
             user=None) -> Dataset:
    digest = sha256(path)
    held = Dataset.objects.filter(sha256=digest).first()
    if held:
        raise AlreadyHeld(held)
    dataset = Dataset.objects.create(
        title=title, publisher=publisher, license=license, source_url=source_url, landing_page=landing_page,
        filename=filename, path=keep(path, digest, filename), sha256=digest, bytes=path.stat().st_size,
        default_year=default_year, uploaded_by=user if user and user.is_authenticated else None)
    try:
        sheets = reader.read(file_path(dataset), filename)
    except reader.UnreadableFile as exc:
        dataset.status, dataset.error = Dataset.FAILED, str(exc)
        dataset.save(update_fields=["status", "error"])
        return dataset
    for proposal in detect.propose(sheets, default_year):
        save_table(dataset, sheets, proposal)
    if not dataset.tables.filter(status=SourceTable.RECOGNISED).exists():
        dataset.error = "no table with district rows and a measure the engine reads"
        dataset.save(update_fields=["error"])
    return dataset


def save_table(dataset: Dataset, sheets: dict, proposal: dict, table: SourceTable | None = None) -> SourceTable:
    recognised = proposal["status"] == SourceTable.RECOGNISED
    rows = detect.extract(sheets, proposal) if recognised else []
    fields = dict(
        sheet=proposal["sheet"], title=proposal["title"], number=proposal.get("number", ""),
        layout=proposal.get("layout", ""), year=proposal.get("year"), season=proposal.get("season", ""),
        measure=proposal.get("measure") or "", status=proposal["status"], reason=proposal.get("reason", ""),
        proposal=proposal, warnings=detect.checks(rows)[:200], cells=len(rows))
    if table is None:
        return SourceTable.objects.create(dataset=dataset, include=recognised and proposal.get("year") is not None,
                                          **fields)
    for name, value in fields.items():
        setattr(table, name, value)
    table.save()
    return table


@transaction.atomic
def publish(dataset: Dataset, *, user=None, confirmed_as: str = "") -> int:
    if not (user and user.is_authenticated) and not confirmed_as.strip():
        raise ValueError("a confirmation needs a signed-in person or a name")
    sheets = reader.read(file_path(dataset), dataset.filename)
    dataset.observations.all().delete()
    count = 0
    for table in dataset.tables.filter(include=True, status=SourceTable.RECOGNISED):
        if table.year is None:
            raise ValueError(f"{table.sheet}: no year; set one before publishing")
        proposal = table.proposal | {"year": table.year, "season": table.season}
        batch = [Observation(dataset=dataset, table=table, **{k: r[k] for k in OBSERVATION_FIELDS})
                 for r in detect.extract(sheets, proposal)]
        Observation.objects.bulk_create(batch, batch_size=2000)
        count += len(batch)
    dataset.status = Dataset.PUBLISHED
    dataset.confirmed_by = user if user and user.is_authenticated else None
    dataset.confirmed_as = confirmed_as.strip()
    dataset.confirmed_at = timezone.now()
    dataset.save(update_fields=["status", "confirmed_by", "confirmed_as", "confirmed_at"])
    return count


OBSERVATION_FIELDS = ["year", "season", "district_id", "geography", "crop", "measure", "basis", "farmer_type",
                      "value", "unit", "printed", "raw", "row", "col"]
