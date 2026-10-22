"""What the engine stores.

A Dataset is one file as it was received, identified by its SHA-256. Each
sheet in it becomes a SourceTable holding the detector's proposal. Once a
person confirms the proposals, every cell read becomes an Observation,
carrying its year, season, place, crop, measure, farm type, the value or
the reason it is blank, and the row and column it came from.
"""

from __future__ import annotations

from django.conf import settings
from django.db import models

from engine import vocab


class Dataset(models.Model):
    REVIEW, PUBLISHED, FAILED = "review", "published", "failed"
    STATUS = [(REVIEW, "Waiting for review"), (PUBLISHED, "Published"), (FAILED, "Could not be read")]

    title = models.CharField(max_length=200)
    publisher = models.CharField(max_length=200, blank=True)
    license = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(max_length=500, blank=True)
    landing_page = models.URLField(max_length=500, blank=True)
    filename = models.CharField(max_length=255)
    path = models.CharField(max_length=500, help_text="File location, relative to the project or var/ folder")
    sha256 = models.CharField(max_length=64, unique=True)
    bytes = models.PositiveBigIntegerField()
    default_year = models.PositiveSmallIntegerField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=STATUS, default=REVIEW)
    error = models.TextField(blank=True)
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name="uploads")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    confirmed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
                                     related_name="confirmations")
    confirmed_as = models.CharField(max_length=200, blank=True, help_text="Name of the person who confirmed")
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-uploaded_at", "-id"]

    def __str__(self) -> str:
        return self.title

    @property
    def confirmer(self) -> str:
        if self.confirmed_by:
            return self.confirmed_by.get_full_name() or self.confirmed_by.get_username()
        return self.confirmed_as


class SourceTable(models.Model):
    RECOGNISED, UNRECOGNISED, NO_DISTRICTS = "recognised", "unrecognised", "no_districts"
    STATUS = [(RECOGNISED, "Recognised"), (UNRECOGNISED, "Not recognised"), (NO_DISTRICTS, "No district rows")]

    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="tables")
    sheet = models.CharField(max_length=100)
    title = models.TextField()
    number = models.CharField(max_length=10, blank=True)
    layout = models.CharField(max_length=10, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    season = models.CharField(max_length=1, blank=True)
    measure = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=15, choices=STATUS)
    reason = models.CharField(max_length=200, blank=True)
    include = models.BooleanField(default=False)
    proposal = models.JSONField()
    warnings = models.JSONField(default=list)
    cells = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["dataset", "id"]

    def __str__(self) -> str:
        return f"{self.dataset} / {self.sheet}"

    @property
    def measure_label(self) -> str:
        if self.measure == vocab.PRACTICES:
            return "Agricultural practices"
        return vocab.MEASURES[self.measure].label if self.measure in vocab.MEASURES else ""


class Observation(models.Model):
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE, related_name="observations")
    table = models.ForeignKey(SourceTable, on_delete=models.CASCADE, related_name="observations")
    year = models.PositiveSmallIntegerField()
    season = models.CharField(max_length=1, blank=True)
    district_id = models.CharField(max_length=2, blank=True, help_text="NISR code; blank for national rows")
    geography = models.CharField(max_length=40)
    crop = models.CharField(max_length=30, blank=True, help_text="Blank for inputs that are not crop-specific")
    measure = models.CharField(max_length=30)
    basis = models.CharField(max_length=10, blank=True, help_text="Share of farmers, plots, or land")
    farmer_type = models.CharField(max_length=3, help_text="all, ssf (small scale), or lsf (large scale)")
    value = models.DecimalField(max_digits=30, decimal_places=15, null=True, blank=True)
    unit = models.CharField(max_length=10)
    printed = models.CharField(max_length=10, help_text="number, or why the value is blank: empty, dash, zero, text")
    raw = models.CharField(max_length=60, blank=True)
    row = models.PositiveIntegerField()
    col = models.PositiveIntegerField()

    class Meta:
        indexes = [
            models.Index(fields=["measure", "crop", "season", "year"]),
            models.Index(fields=["district_id", "measure"]),
        ]

    def __str__(self) -> str:
        return f"{self.year}{self.season} {self.geography} {self.crop} {self.measure}"


class CropTarget(models.Model):
    """A yield target a person sets for a crop, with where it comes from."""

    crop = models.CharField(max_length=30)
    season = models.CharField(max_length=1, blank=True)
    year = models.PositiveSmallIntegerField(null=True, blank=True)
    value = models.DecimalField(max_digits=12, decimal_places=2)
    unit = models.CharField(max_length=10, default="kg/ha")
    source = models.CharField(max_length=300, help_text="Document and page the target comes from")
    set_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    set_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("crop", "season", "year")]

    def __str__(self) -> str:
        return f"{self.crop} {self.season} {self.value} {self.unit}"
