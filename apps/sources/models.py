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
    """Semantically split chunk of a Document with vector embedding and hierarchical relations."""
    class ChunkLevel(models.TextChoices):
        PARENT = "parent", "Parent"
        CHILD = "child", "Child"

    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="chunks")
    parent_chunk = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="child_chunks",
        help_text="Parent chunk reference for hierarchical small-to-big retrieval.",
    )
    chunk_level = models.CharField(
        max_length=16,
        choices=ChunkLevel.choices,
        default=ChunkLevel.CHILD,
        db_index=True,
        help_text="Hierarchy level: parent section or child sub-chunk.",
    )
    chunk_index = models.PositiveIntegerField()
    heading = models.CharField(
        max_length=512,
        blank=True,
        default="",
        db_index=True,
        help_text="Hierarchical section heading breadcrumb (e.g. 'DBMS > Transactions > ACID Properties').",
    )
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
            models.Index(fields=["document", "chunk_level"]),
        ]

    def __str__(self):
        return f"{self.document.title or 'Doc'} - Chunk #{self.chunk_index}"


class Entity(BaseModel):
    """Knowledge Graph Entity / Node representing a concept, tool, algorithm, or fact."""
    class EntityType(models.TextChoices):
        CONCEPT = "concept", "Concept"
        TECHNOLOGY = "technology", "Technology/Tool"
        ALGORITHM = "algorithm", "Algorithm/Method"
        FRAMEWORK = "framework", "Framework/Library"
        ARCHITECTURE = "architecture", "Architecture/Design"
        OTHER = "other", "Other"

    name = models.CharField(max_length=255, db_index=True)
    canonical_name = models.CharField(max_length=255, db_index=True, help_text="Normalized lowercase identifier for deduplication.")
    entity_type = models.CharField(max_length=32, choices=EntityType.choices, default=EntityType.CONCEPT, db_index=True)
    description = models.TextField(blank=True, help_text="Summary description of the entity.")
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Knowledge Entity"
        verbose_name_plural = "Knowledge Entities"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["canonical_name"]),
            models.Index(fields=["entity_type"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_entity_type_display()})"


class Relationship(BaseModel):
    """Knowledge Graph Edge representing a directed semantic connection between entities."""
    class RelationType(models.TextChoices):
        PREREQUISITE_OF = "prerequisite_of", "Prerequisite Of"
        PART_OF = "part_of", "Part Of"
        IMPLEMENTS = "implements", "Implements"
        USES = "uses", "Uses / Depends On"
        ENABLES = "enables", "Enables"
        COMPARED_TO = "compared_to", "Compared To"
        RELATION = "relates_to", "Relates To"

    source_entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="outgoing_relationships",
    )
    target_entity = models.ForeignKey(
        Entity,
        on_delete=models.CASCADE,
        related_name="incoming_relationships",
    )
    relation_type = models.CharField(
        max_length=32,
        choices=RelationType.choices,
        default=RelationType.RELATION,
        db_index=True,
    )
    description = models.TextField(blank=True, help_text="Explanation of how the entities are related.")
    weight = models.FloatField(default=1.0, help_text="Relationship strength or confidence.")
    source_chunk = models.ForeignKey(
        DocumentChunk,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="provenance_relationships",
        help_text="Origin chunk establishing this relationship.",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Knowledge Relationship"
        verbose_name_plural = "Knowledge Relationships"
        unique_together = [("source_entity", "target_entity", "relation_type")]
        indexes = [
            models.Index(fields=["source_entity", "relation_type"]),
            models.Index(fields=["target_entity", "relation_type"]),
        ]

    def __str__(self):
        return f"{self.source_entity.name} --[{self.relation_type}]--> {self.target_entity.name}"


class EntityChunkMapping(BaseModel):
    """Associates Entities with DocumentChunks where they are referenced or discussed."""
    entity = models.ForeignKey(Entity, on_delete=models.CASCADE, related_name="chunk_mappings")
    chunk = models.ForeignKey(DocumentChunk, on_delete=models.CASCADE, related_name="entity_mappings")
    mention_count = models.PositiveIntegerField(default=1)

    class Meta:
        verbose_name = "Entity Chunk Mapping"
        verbose_name_plural = "Entity Chunk Mappings"
        unique_together = [("entity", "chunk")]
        indexes = [
            models.Index(fields=["entity", "chunk"]),
        ]

    def __str__(self):
        return f"{self.entity.name} in Chunk #{self.chunk.chunk_index}"
