from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema
from django.db.models import Count

from apps.sources.models import Source, Document, DocumentChunk
from apps.knowledge.models import Concept, Evidence
from apps.processing.pipeline import IngestionPipeline
from apps.rag.services.embedding import EmbeddingService


class ProcessingOverviewView(APIView):
    """Unified system processing health and telemetry overview."""

    @extend_schema(summary="Processing System Overview")
    def get(self, request):
        source_counts = {
            Source.ProcessingStatus.PENDING: 0,
            Source.ProcessingStatus.PROCESSING: 0,
            Source.ProcessingStatus.COMPLETED: 0,
            Source.ProcessingStatus.FAILED: 0,
        }
        for item in Source.objects.values("status").annotate(count=Count("id")):
            source_counts[item["status"]] = item["count"]

        total_chunks = DocumentChunk.objects.count()
        embedded_chunks = DocumentChunk.objects.filter(embedding__isnull=False).count()
        missing_embeddings = total_chunks - embedded_chunks

        total_concepts = Concept.objects.count()
        mapped_concepts = Concept.objects.filter(skills__isnull=False).distinct().count()

        failed_sources_count = source_counts[Source.ProcessingStatus.FAILED]

        return Response({
            "module": "processing",
            "status": "healthy" if failed_sources_count == 0 else "attention_needed",
            "sources": {
                "total": Source.objects.count(),
                "breakdown": source_counts,
                "failed_count": failed_sources_count,
            },
            "embeddings": {
                "total_chunks": total_chunks,
                "embedded_chunks": embedded_chunks,
                "missing_embeddings": missing_embeddings,
                "coverage_pct": round((embedded_chunks / total_chunks * 100), 2) if total_chunks > 0 else 100.0,
            },
            "knowledge_extraction": {
                "total_concepts": total_concepts,
                "mapped_concepts": mapped_concepts,
                "unmapped_concepts": total_concepts - mapped_concepts,
                "total_evidence": Evidence.objects.count(),
            },
        }, status=status.HTTP_200_OK)


class SourceProcessingStatusListView(APIView):
    """List processing statuses and diagnostics across all knowledge sources."""

    @extend_schema(summary="List Sources Processing Status")
    def get(self, request):
        status_filter = request.query_params.get("status")
        qs = Source.objects.all().order_by("-updated_at")
        if status_filter:
            qs = qs.filter(status=status_filter.lower())

        results = []
        for s in qs[:100]:
            doc = s.documents.first()
            chunks_count = doc.chunks.count() if doc else 0
            results.append({
                "source_id": str(s.id),
                "name": s.name,
                "source_type": s.source_type,
                "status": s.status,
                "error_message": s.error_message,
                "document_created": doc is not None,
                "chunks_count": chunks_count,
                "created_at": s.created_at,
                "updated_at": s.updated_at,
            })

        return Response(results, status=status.HTTP_200_OK)


class SourceProcessingDetailView(APIView):
    """Detailed processing breakdown and chunk embedding state for a single Source."""

    @extend_schema(summary="Get Source Processing Details")
    def get(self, request, pk):
        source = Source.objects.filter(id=pk).first()
        if not source:
            raise NotFound(detail=f"Source {pk} not found")

        doc = source.documents.first()
        chunks_data = []
        if doc:
            for c in doc.chunks.all().order_by("chunk_index"):
                chunks_data.append({
                    "chunk_id": str(c.id),
                    "chunk_index": c.chunk_index,
                    "token_count": c.token_count,
                    "is_embedded": c.embedding is not None,
                })

        return Response({
            "source_id": str(source.id),
            "name": source.name,
            "source_type": source.source_type,
            "status": source.status,
            "error_message": source.error_message,
            "document": {
                "id": str(doc.id) if doc else None,
                "title": doc.title if doc else None,
                "chunk_count": len(chunks_data),
            } if doc else None,
            "chunks": chunks_data,
        }, status=status.HTTP_200_OK)


class RetrySourceProcessingView(APIView):
    """Retry ingestion and processing for a failed Source."""

    @extend_schema(summary="Retry Source Processing")
    def post(self, request, pk):
        source = Source.objects.filter(id=pk).first()
        if not source:
            raise NotFound(detail=f"Source {pk} not found")

        source.status = Source.ProcessingStatus.PENDING
        source.error_message = ""
        source.save(update_fields=["status", "error_message", "updated_at"])

        try:
            doc = IngestionPipeline.process_source(str(source.id))
            source.refresh_from_db()
            return Response({
                "status": "success",
                "source_id": str(source.id),
                "source_status": source.status,
                "document_id": str(doc.id) if doc else None,
            }, status=status.HTTP_200_OK)
        except Exception as e:
            source.refresh_from_db()
            return Response({
                "status": "failed",
                "source_id": str(source.id),
                "source_status": source.status,
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)


class EmbeddingProcessingStatusView(APIView):
    """Check embedding pipeline metrics and trigger retries."""

    @extend_schema(summary="Get Embedding Processing Status")
    def get(self, request):
        total_chunks = DocumentChunk.objects.count()
        embedded = DocumentChunk.objects.filter(embedding__isnull=False).count()
        missing = total_chunks - embedded

        return Response({
            "total_chunks": total_chunks,
            "embedded_chunks": embedded,
            "missing_chunks": missing,
            "coverage_percentage": round((embedded / total_chunks * 100), 2) if total_chunks > 0 else 100.0,
        }, status=status.HTTP_200_OK)

    @extend_schema(summary="Retry Failed/Missing Embeddings")
    def post(self, request):
        count = EmbeddingService.retry_failed_embeddings()
        return Response({
            "status": "completed",
            "embedded_chunks": count,
        }, status=status.HTTP_200_OK)


class ExtractionProcessingStatusView(APIView):
    """Inspect concepts extraction and mapping pipeline metrics."""

    @extend_schema(summary="Get Extraction Processing Status")
    def get(self, request):
        concepts_qs = Concept.objects.all()
        mapped_count = concepts_qs.filter(skills__isnull=False).distinct().count()
        total_concepts = concepts_qs.count()

        return Response({
            "total_concepts": total_concepts,
            "mapped_concepts": mapped_count,
            "unmapped_concepts": total_concepts - mapped_count,
            "evidence_count": Evidence.objects.count(),
        }, status=status.HTTP_200_OK)


class ProcessingFailuresView(APIView):
    """Unified failure diagnostics dashboard."""

    @extend_schema(summary="List Processing Failures & Diagnostics")
    def get(self, request):
        failed_sources = [
            {
                "source_id": str(s.id),
                "name": s.name,
                "source_type": s.source_type,
                "status": s.status,
                "error_message": s.error_message,
                "failed_at": s.updated_at,
            }
            for s in Source.objects.filter(status=Source.ProcessingStatus.FAILED)
        ]

        missing_embeddings_count = DocumentChunk.objects.filter(embedding__isnull=True).count()
        unmapped_concepts_count = Concept.objects.filter(skills__isnull=True, topic__isnull=True).count()

        return Response({
            "failed_sources_count": len(failed_sources),
            "failed_sources": failed_sources,
            "missing_embeddings_count": missing_embeddings_count,
            "unmapped_concepts_count": unmapped_concepts_count,
        }, status=status.HTTP_200_OK)


class JobStatusView(APIView):
    """Check asynchronous background Celery task status and result."""

    @extend_schema(summary="Get Background Task Status")
    def get(self, request, task_id):
        from celery.result import AsyncResult
        result = AsyncResult(task_id)
        data = {
            "task_id": task_id,
            "status": result.status,
            "ready": result.ready(),
            "successful": result.successful() if result.ready() else False,
            "failed": result.failed() if result.ready() else False,
        }
        if result.ready():
            if result.successful():
                data["result"] = result.result
            else:
                data["error"] = str(result.result)
        return Response(data, status=status.HTTP_200_OK)

