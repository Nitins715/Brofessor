from django.contrib import admin
from .models import Domain, Topic, Skill, RoadmapNode, RoadmapProgress, LearningResource, SkillResourceMapping


class SkillResourceMappingInline(admin.TabularInline):
    model = SkillResourceMapping
    extra = 1
    autocomplete_fields = ["resource"]


@admin.register(LearningResource)
class LearningResourceAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "resource_type", "verification_status", "last_verified_date", "created_at")
    list_filter = ("resource_type", "verification_status", "source")
    search_fields = ("title", "url", "source", "description")


@admin.register(SkillResourceMapping)
class SkillResourceMappingAdmin(admin.ModelAdmin):
    list_display = ("skill", "resource", "is_primary", "order", "created_at")
    list_filter = ("is_primary", "resource__resource_type", "resource__verification_status")
    search_fields = ("skill__name", "resource__title", "resource__url")
    autocomplete_fields = ["skill", "resource"]


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("name", "topic", "difficulty_level", "order", "created_at")
    list_filter = ("difficulty_level", "topic__domain")
    search_fields = ("name", "slug")
    inlines = [SkillResourceMappingInline]


@admin.register(RoadmapNode)
class RoadmapNodeAdmin(admin.ModelAdmin):
    list_display = ("skill", "domain", "topic", "order", "created_at")
    list_filter = ("domain",)


@admin.register(RoadmapProgress)
class RoadmapProgressAdmin(admin.ModelAdmin):
    list_display = ("node", "status", "is_current", "completed_at", "updated_at")
    list_filter = ("status", "is_current")
