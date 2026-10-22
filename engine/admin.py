from django.contrib import admin

from engine.models import CropTarget, Dataset, Observation, SourceTable


@admin.register(Dataset)
class DatasetAdmin(admin.ModelAdmin):
    list_display = ["title", "status", "uploaded_at", "confirmed_at"]
    list_filter = ["status"]
    readonly_fields = ["sha256", "bytes", "path", "uploaded_by", "uploaded_at", "confirmed_by", "confirmed_at"]


@admin.register(SourceTable)
class SourceTableAdmin(admin.ModelAdmin):
    list_display = ["sheet", "dataset", "year", "season", "measure", "status", "include", "cells"]
    list_filter = ["status", "include", "measure", "season", "year"]
    search_fields = ["title", "sheet"]


@admin.register(Observation)
class ObservationAdmin(admin.ModelAdmin):
    list_display = ["year", "season", "geography", "crop", "measure", "farmer_type", "basis", "value", "printed"]
    list_filter = ["measure", "season", "year", "farmer_type"]
    search_fields = ["geography", "crop"]


@admin.register(CropTarget)
class CropTargetAdmin(admin.ModelAdmin):
    list_display = ["crop", "season", "year", "value", "unit", "source"]
