import os
import uuid
from pathlib import Path
from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from drf_spectacular.utils import extend_schema, OpenApiParameter

from .models import Source, Document, DocumentChunk
from .serializers import (
    SourceSerializer,
    SourceStatusSerializer,
    DocumentSerializer,
    DocumentChunkSerializer,
    TextSourceCreateSerializer,
    ArticleSourceCreateSerializer,
    YouTubeSourceCreateSerializer,
    PDFUploadSerializer,
)
from apps.processing.pipeline import IngestionPipeline
from apps.processing.tasks import ingest_source_task


import threading


def dispatch_ingestion(source: Source, run_async: bool = False) -> None:
    """Helper to dispatch source processing asynchronously via Celery or background thread."""
    if run_async:
        # If Celery worker/broker is available and not in eager mode, try Celery first
        if not getattr(settings, "CELERY_TASK_ALWAYS_EAGER", True):
            try:
                ingest_source_task.delay(str(source.id))
                return
            except Exception:
                pass

        # In standalone local mode, run non-blocking in background thread
        def _run_in_background():
            from django.db import connections
            try:
                connections.close_all()
                IngestionPipeline.process_source(str(source.id))
            except Exception:
                pass
            finally:
                connections.close_all()

        t = threading.Thread(target=_run_in_background, daemon=True)
        t.start()
        return

    # Synchronous processing
    try:
        IngestionPipeline.process_source(str(source.id))
    except Exception:
        # Errors are captured and recorded in Source.status and Source.error_message
        pass



class SourceListView(APIView):
    """List knowledge sources or filter by type/status."""

    @extend_schema(
        summary="List Sources",
        description="Retrieve all knowledge sources with optional filtering.",
        parameters=[
            OpenApiParameter(name="source_type", description="Filter by source type (note, article, pdf, youtube, manual)", required=False, type=str),
            OpenApiParameter(name="status", description="Filter by status (pending, processing, completed, failed)", required=False, type=str),
        ],
        responses={200: SourceSerializer(many=True)},
    )
    def get(self, request):
        queryset = Source.objects.all().order_by("-created_at")
        source_type = request.query_params.get("source_type")
        source_status = request.query_params.get("status")

        if source_type:
            queryset = queryset.filter(source_type=source_type.lower())
        if source_status:
            queryset = queryset.filter(status=source_status.lower())

        serializer = SourceSerializer(queryset, many=True)
        return Response(serializer.data)


class SourceDetailView(APIView):
    """Retrieve full details of a single knowledge source."""

    @extend_schema(
        summary="Get Source Details",
        responses={200: SourceSerializer},
    )
    def get(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        return Response(SourceSerializer(source).data)

    @extend_schema(summary="Delete Source")
    def delete(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        source.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SourceStatusView(APIView):
    """Check processing status and error diagnostics for a knowledge source."""

    @extend_schema(
        summary="Get Source Processing Status",
        responses={200: SourceStatusSerializer},
    )
    def get(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        return Response(SourceStatusSerializer(source).data)


class RetrySourceView(APIView):
    """Retry ingestion and processing for a failed or pending source."""

    @extend_schema(
        summary="Retry Source Processing",
        responses={200: SourceSerializer},
    )
    def post(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        source.status = Source.ProcessingStatus.PENDING
        source.error_message = ""
        source.save(update_fields=["status", "error_message", "updated_at"])

        run_async = request.data.get("run_async", True) if isinstance(request.data, dict) else True
        dispatch_ingestion(source, run_async=run_async)
        source.refresh_from_db()
        return Response(SourceSerializer(source).data, status=status.HTTP_200_OK)



class SourceDocumentView(APIView):
    """Retrieve the normalized document generated for a source."""

    @extend_schema(
        summary="Get Source Document",
        responses={200: DocumentSerializer},
    )
    def get(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        document = source.documents.first()
        if not document:
            return Response(
                {"detail": "No processed document available for this source yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(DocumentSerializer(document).data)


class SourceChunksView(APIView):
    """Retrieve all chunks generated for a source's document."""

    @extend_schema(
        summary="Get Document Chunks",
        responses={200: DocumentChunkSerializer(many=True)},
    )
    def get(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        document = source.documents.first()
        if not document:
            return Response(
                {"detail": "No processed document available for this source yet."},
                status=status.HTTP_404_NOT_FOUND,
            )
        chunks = document.chunks.all().order_by("chunk_index")
        return Response(DocumentChunkSerializer(chunks, many=True).data)


class AddTextSourceView(APIView):
    """Ingest user-provided text, note, or manual knowledge."""
    parser_classes = [JSONParser]

    @extend_schema(
        summary="Add Text/Manual Source",
        request=TextSourceCreateSerializer,
        responses={201: SourceSerializer},
    )
    def post(self, request):
        serializer = TextSourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        title = data.get("title") or (data["content"][:40] + "...")
        source = Source.objects.create(
            name=title,
            source_type=data["source_type"],
            metadata={
                **data.get("metadata", {}),
                "content": data["content"],
                "title": title,
            },
        )

        dispatch_ingestion(source, run_async=data.get("run_async", False))
        source.refresh_from_db()
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


class AddArticleSourceView(APIView):
    """Ingest a web article or blog post via URL."""
    parser_classes = [JSONParser]

    @extend_schema(
        summary="Add Web Article Source",
        request=ArticleSourceCreateSerializer,
        responses={201: SourceSerializer},
    )
    def post(self, request):
        serializer = ArticleSourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        url = data["url"]
        title = data.get("title") or url
        source = Source.objects.create(
            name=title,
            source_type=Source.SourceType.ARTICLE,
            uri=url,
            metadata=data.get("metadata", {}),
        )

        dispatch_ingestion(source, run_async=data.get("run_async", True))
        source.refresh_from_db()
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


class AddYouTubeSourceView(APIView):
    """Ingest a YouTube video transcript via URL."""
    parser_classes = [JSONParser]

    @extend_schema(
        summary="Add YouTube Video Source",
        request=YouTubeSourceCreateSerializer,
        responses={201: SourceSerializer},
    )
    def post(self, request):
        serializer = YouTubeSourceCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        url = data["url"]
        title = data.get("title") or f"YouTube: {url}"
        source = Source.objects.create(
            name=title,
            source_type=Source.SourceType.YOUTUBE,
            uri=url,
            metadata=data.get("metadata", {}),
        )

        dispatch_ingestion(source, run_async=data.get("run_async", True))
        source.refresh_from_db()
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


class UploadPDFSourceView(APIView):
    """Upload a local PDF document for text extraction and chunking."""
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(
        summary="Upload PDF Source",
        request=PDFUploadSerializer,
        responses={201: SourceSerializer},
    )
    def post(self, request):
        serializer = PDFUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        uploaded_file = data["file"]
        title = data.get("title") or Path(uploaded_file.name).stem

        # Save to media/uploads/pdfs/
        upload_dir = Path(settings.MEDIA_ROOT) / "uploads" / "pdfs"
        upload_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{uuid.uuid4()}_{uploaded_file.name}"
        save_path = upload_dir / filename

        with open(save_path, "wb+") as destination:
            for chunk in uploaded_file.chunks():
                destination.write(chunk)

        rel_file_path = str(save_path.relative_to(settings.MEDIA_ROOT))

        source = Source.objects.create(
            name=title,
            source_type=Source.SourceType.PDF,
            file_path=rel_file_path,
            metadata={
                **data.get("metadata", {}),
                "original_filename": uploaded_file.name,
                "file_size": uploaded_file.size,
            },
        )

        dispatch_ingestion(source, run_async=data.get("run_async", True))
        source.refresh_from_db()
        return Response(SourceSerializer(source).data, status=status.HTTP_201_CREATED)


class EmbedSourceView(APIView):
    """Trigger or re-generate dense vector embeddings for all chunks in a Source."""

    @extend_schema(
        summary="Generate/Regenerate Embeddings for Source",
        responses={200: {"type": "object", "properties": {"embedded_chunks": {"type": "integer"}}}},
    )
    def post(self, request, pk):
        source = get_object_or_404(Source, pk=pk)
        from apps.rag.services.embedding import EmbeddingService

        force = request.data.get("force", False) if isinstance(request.data, dict) else False
        embedded_count = EmbeddingService.embed_source(source.id, force=force)
        return Response(
            {
                "source_id": str(source.id),
                "embedded_chunks": embedded_count,
                "status": "completed",
            },
            status=status.HTTP_200_OK,
        )


class RetryEmbeddingsView(APIView):
    """Retry embedding generation for all document chunks that lack vectors."""

    @extend_schema(
        summary="Retry Missing Embeddings Across All Sources",
        responses={200: {"type": "object", "properties": {"total_embedded": {"type": "integer"}}}},
    )
    def post(self, request):
        from apps.rag.services.embedding import EmbeddingService

        total_embedded = EmbeddingService.retry_failed_embeddings()
        return Response(
            {
                "total_embedded": total_embedded,
                "status": "completed",
            },
            status=status.HTTP_200_OK,
        )

