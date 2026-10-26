import logging
from typing import List, Optional, Union
import uuid
from django.conf import settings
from django.utils import timezone

from apps.sources.models import Source, Document, DocumentChunk
from apps.processing.models import ProcessingJob
from apps.rag.embeddings import get_embedding_provider, BaseEmbeddingProvider

logger = logging.getLogger("brofessor")


class EmbeddingService:
    """
    Service responsible for converting DocumentChunk text into dense vectors
    and storing them in PostgreSQL with pgvector.
    """

    @classmethod
    def get_provider(cls, provider: Optional[BaseEmbeddingProvider] = None) -> BaseEmbeddingProvider:
        return provider or get_embedding_provider()

    @classmethod
    def embed_document(
        cls,
        document_id: Union[str, uuid.UUID],
        batch_size: Optional[int] = None,
        force: bool = False,
        provider: Optional[BaseEmbeddingProvider] = None,
    ) -> int:
        """
        Embed all chunks of a document and persist them to PostgreSQL / pgvector.
        Returns count of embedded chunks.
        """
        doc = Document.objects.select_related("source").get(id=document_id)
        active_provider = cls.get_provider(provider)
        active_batch_size = batch_size or getattr(settings, "EMBEDDING_BATCH_SIZE", 32)

        # Track job
        job = ProcessingJob.objects.create(
            source=doc.source,
            job_type=ProcessingJob.JobType.EMBEDDING,
            status=ProcessingJob.JobStatus.RUNNING,
            started_at=timezone.now(),
            payload={"document_id": str(doc.id), "model": active_provider.model_name},
        )

        try:
            chunks_qs = doc.chunks.all().order_by("chunk_index")
            if not force:
                chunks_qs = chunks_qs.filter(embedding__isnull=True)

            chunks_list: List[DocumentChunk] = list(chunks_qs)
            if not chunks_list:
                job.status = ProcessingJob.JobStatus.COMPLETED
                job.finished_at = timezone.now()
                job.payload["embedded_count"] = 0
                job.save(update_fields=["status", "finished_at", "payload"])
                return 0

            logger.info(
                f"Generating embeddings for {len(chunks_list)} chunks in document '{doc.title}' "
                f"using {active_provider.model_name} ({active_provider.dimension}d)"
            )

            total_embedded = 0
            for i in range(0, len(chunks_list), active_batch_size):
                batch = chunks_list[i : i + active_batch_size]
                texts = [chunk.content for chunk in batch]

                vectors = active_provider.embed_batch(texts)
                for chunk, vec in zip(batch, vectors):
                    chunk.embedding = vec

                DocumentChunk.objects.bulk_update(batch, ["embedding"])
                total_embedded += len(batch)

            # Update job and source metadata
            job.status = ProcessingJob.JobStatus.COMPLETED
            job.finished_at = timezone.now()
            job.payload["embedded_count"] = total_embedded
            job.save(update_fields=["status", "finished_at", "payload"])

            if doc.source:
                doc.source.metadata = {
                    **(doc.source.metadata or {}),
                    "embeddings_model": active_provider.model_name,
                    "embedded_chunks_count": total_embedded,
                    "last_embedded_at": timezone.now().isoformat(),
                }
                doc.source.save(update_fields=["metadata"])

            return total_embedded

        except Exception as e:
            error_msg = f"Failed to generate embeddings for document {document_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            job.status = ProcessingJob.JobStatus.FAILED
            job.error_message = error_msg
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])
            raise

    @classmethod
    def embed_source(
        cls,
        source_id: Union[str, uuid.UUID],
        batch_size: Optional[int] = None,
        force: bool = False,
        provider: Optional[BaseEmbeddingProvider] = None,
    ) -> int:
        """Embed all documents and chunks for a given Source."""
        source = Source.objects.get(id=source_id)
        total = 0
        for doc in source.documents.all():
            total += cls.embed_document(
                document_id=doc.id,
                batch_size=batch_size,
                force=force,
                provider=provider,
            )
        return total

    @classmethod
    def retry_failed_embeddings(
        cls,
        source_id: Optional[Union[str, uuid.UUID]] = None,
        provider: Optional[BaseEmbeddingProvider] = None,
    ) -> int:
        """Find and embed any chunks that do not currently have a vector stored."""
        qs = DocumentChunk.objects.filter(embedding__isnull=True)
        if source_id:
            qs = qs.filter(document__source_id=source_id)

        document_ids = qs.values_list("document_id", flat=True).distinct()
        total_embedded = 0
        for doc_id in document_ids:
            total_embedded += cls.embed_document(doc_id, force=False, provider=provider)
        return total_embedded
