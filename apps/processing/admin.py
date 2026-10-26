from django.contrib import admin
from .models import ProcessingJob


@admin.register(ProcessingJob)
class ProcessingJobAdmin(admin.ModelAdmin):
    list_display = ("job_type", "status", "source", "celery_task_id", "created_at")
    list_filter = ("job_type", "status")
