from django.contrib import admin
from .models import Concept, Evidence, CalculatedMastery


@admin.register(Concept)
class ConceptAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "domain", "topic", "created_at")
    search_fields = ("name", "slug")


@admin.register(Evidence)
class EvidenceAdmin(admin.ModelAdmin):
    list_display = ("title", "evidence_type", "skill", "topic", "recorded_at")
    list_filter = ("evidence_type",)
    search_fields = ("title", "description")


@admin.register(CalculatedMastery)
class CalculatedMasteryAdmin(admin.ModelAdmin):
    list_display = ("skill", "concept", "mastery_score", "confidence_score", "evidence_count", "last_calculated_at")
