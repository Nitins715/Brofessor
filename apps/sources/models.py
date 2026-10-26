from django.db import models
from django.conf import settings
from pgvector.django import VectorField, HnswIndex
from apps.core.models import BaseModel


class Source(BaseModel):
    """External or internal raw knowledge source."""
    class SourceType(models.TextChoices):
        NOTE = "note", "Note"
        ARTICLE = "article", "Article/Blog"
        PDF = "pdf", "PDF"
        YOUTUBE = "youtube", "YouTube"
        MANUAL = "manual", "Manual Knowledge"
        GITHUB = "github", "Project/GitHub"

    class ProcessingStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        PROCESSING = "processing", "Processing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=32, choices=SourceType.choices, db_index=True)
    uri = models.CharField(max_length=1024, blank=True, help_text="URL, repository link, or external identifier.")
    file_path = models.CharField(max_length=1024, blank=True, help_text="Local path if stored in media storage.")
    status = models.CharField(
        max_length=32,
        choices=ProcessingStatus.choices,
        default=ProcessingStatus.PENDING,
        db_index=True,
    )
    metadata = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        verbose_name = "Source"
        verbose_name_plural = "Sources"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source_type", "status"]),
        ]

    def __str__(self):
        return f"[{self.get_source_type_display()}] {self.name}"


class Document(BaseModel):
    """Normalized document extracted from a Source."""
    source = models.ForeignKey(Source, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=512, blank=True)
    content = models.TextField(help_text="Extracted text or markdown content.")
    content_hash = models.CharField(max_length=64, blank=True, db_index=True, help_text="SHA-256 for change detection.")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["source", "created_at"]),
        ]

    def __str__(self):
        return self.title or f"Document {self.id} ({self.source.name})"


class DocumentChunk(BaseModel):
    """Semantically split chunk of a Document with vector embedding."""
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    token_count = models.PositiveIntegerField(null=True, blank=True)
    embedding = VectorField(
        dimensions=getattr(settings, "EMBEDDING_DIMENSIONS", 384),
        null=True,
        blank=True,
        help_text="Dense vector representation (e.g. 384d BAAI/bge-small-en-v1.5).",
    )

    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Document Chunk"
        verbose_name_plural = "Document Chunks"
        ordering = ["document", "chunk_index"]
        unique_together = [("document", "chunk_index")]
        indexes = [
            HnswIndex(
                name="chunk_vector_hnsw_idx",
                fields=["embedding"],
                m=16,
                ef_construction=64,
                opclasses=["vector_cosine_ops"],
            ),
            models.Index(fields=["document", "chunk_index"]),
        ]

    def __str__(self):
        return f"{self.document.title or 'Doc'} - Chunk #{self.chunk_index}"
