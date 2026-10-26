from django.contrib import admin
from .models import Assessment, Question, Attempt, Answer


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ("title", "skill", "topic", "passing_score", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("title",)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("assessment", "order", "question_type", "points")
    list_filter = ("question_type", "assessment")


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("assessment", "score", "passed", "started_at", "completed_at")
    list_filter = ("passed", "assessment")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ("attempt", "question", "is_correct", "score_awarded")
