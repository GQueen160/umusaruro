"""A farmer's plan for one place and one harvest.

The survey numbers stay in the CSV files. This row only remembers where
the farmer tapped, what they will grow, and the yield they are aiming for.
"""

from django.db import models


class FieldPlan(models.Model):
    village_id = models.CharField(max_length=12)
    district = models.CharField(max_length=40)
    sector = models.CharField(max_length=40)
    cell = models.CharField(max_length=40)
    village = models.CharField(max_length=60)
    lat = models.DecimalField(max_digits=8, decimal_places=5)
    lon = models.DecimalField(max_digits=8, decimal_places=5)
    crops = models.JSONField()
    season = models.CharField(max_length=1, default="A")
    year = models.PositiveSmallIntegerField(default=2026)
    target_crop = models.CharField(max_length=30)
    target_kg = models.DecimalField(max_digits=12, decimal_places=1)
    holding = models.JSONField(null=True, blank=True)
    checks = models.JSONField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self) -> str:
        return f"{self.village} {self.target_crop} {self.target_kg}"
