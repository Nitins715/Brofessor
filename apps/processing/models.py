from django.db import models
from apps.core.models import BaseModel


class ProcessingJob(BaseModel):
    """Tracks background processing tasks (document parsing, chunking, embedding generation)."""
    class JobType(models.TextChoices):
        INGESTION = "ingestion", "Document Ingestion"
        CHUNKING = "chunking", "Document Chunking"
        EMBEDDING = "embedding", "Vector Embedding"
        MASTERY_CALC = "mastery_calc", "Mastery Calculation"
        KNOWLEDGE_EXTRACTION = "knowledge_extraction", "Knowledge Extraction"

    class JobStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    job_type = models.CharField(max_length=32, choices=JobType.choices)
    status = models.CharField(
        max_length=32,
        choices=JobStatus.choices,
        default=JobStatus.PENDING,
        db_index=True,
    )
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="processing_jobs",
    )
    celery_task_id = models.CharField(max_length=255, blank=True, db_index=True)
    payload = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Processing Job"
        verbose_name_plural = "Processing Jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.get_job_type_display()}] {self.status} ({self.id})"
