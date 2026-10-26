from rest_framework import serializers
from .models import Source, Document, DocumentChunk


class DocumentChunkSerializer(serializers.ModelSerializer):
    """Serializer for individual document chunks."""
    class Meta:
        model = DocumentChunk
        fields = [
            "id",
            "chunk_index",
            "content",
            "token_count",
            "metadata",
            "created_at",
        ]


class DocumentSerializer(serializers.ModelSerializer):
    """Serializer for processed documents."""
    chunks_count = serializers.IntegerField(source="chunks.count", read_only=True)

    class Meta:
        model = Document
        fields = [
            "id",
            "title",
            "content",
            "content_hash",
            "metadata",
            "chunks_count",
            "created_at",
            "updated_at",
        ]


class SourceSerializer(serializers.ModelSerializer):
    """Serializer for Source overview and detail."""
    document = DocumentSerializer(source="documents.first", read_only=True)

    class Meta:
        model = Source
        fields = [
            "id",
            "name",
            "source_type",
            "uri",
            "file_path",
            "status",
            "metadata",
            "error_message",
            "document",
            "created_at",
            "updated_at",
        ]


class SourceStatusSerializer(serializers.ModelSerializer):
    """Status serializer for polling ingestion progress."""
    document_id = serializers.SerializerMethodField()
    chunk_count = serializers.SerializerMethodField()

    class Meta:
        model = Source
        fields = [
            "id",
            "name",
            "source_type",
            "status",
            "error_message",
            "document_id",
            "chunk_count",
            "updated_at",
        ]

    def get_document_id(self, obj):
        doc = obj.documents.first()
        return str(doc.id) if doc else None

    def get_chunk_count(self, obj):
        doc = obj.documents.first()
        return doc.chunks.count() if doc else 0


class TextSourceCreateSerializer(serializers.Serializer):
    """Payload for submitting text, notes, or manual knowledge."""
    title = serializers.CharField(max_length=255, required=False, default="")
    content = serializers.CharField(required=True, allow_blank=False)
    source_type = serializers.ChoiceField(
        choices=["note", "manual"],
        default="note",
    )
    metadata = serializers.DictField(required=False, default=dict)
    run_async = serializers.BooleanField(required=False, default=False)


class ArticleSourceCreateSerializer(serializers.Serializer):
    """Payload for submitting web article or blog URL."""
    url = serializers.URLField(required=True)
    title = serializers.CharField(max_length=255, required=False, default="")
    metadata = serializers.DictField(required=False, default=dict)
    run_async = serializers.BooleanField(required=False, default=True)


class YouTubeSourceCreateSerializer(serializers.Serializer):
    """Payload for submitting YouTube video URL."""
    url = serializers.CharField(required=True)
    title = serializers.CharField(max_length=255, required=False, default="")
    metadata = serializers.DictField(required=False, default=dict)
    run_async = serializers.BooleanField(required=False, default=True)


class PDFUploadSerializer(serializers.Serializer):
    """Payload for uploading a local PDF document."""
    file = serializers.FileField(required=True)
    title = serializers.CharField(max_length=255, required=False, default="")
    metadata = serializers.DictField(required=False, default=dict)
    run_async = serializers.BooleanField(required=False, default=True)
