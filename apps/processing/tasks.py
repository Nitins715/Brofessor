import logging
from celery import shared_task
from apps.processing.pipeline import IngestionPipeline

logger = logging.getLogger("brofessor")


@shared_task(bind=True, name="apps.processing.tasks.ingest_source_task", max_retries=2)
def ingest_source_task(self, source_id: str, job_id: str = None):
    """
    Celery background worker task to process a knowledge source asynchronously.
    Executes extraction, normalization, and chunk generation.
    """
    logger.info(f"Celery task ingest_source_task started for source: {source_id} (Task ID: {self.request.id})")
    try:
        document = IngestionPipeline.process_source(source_id=source_id, job_id=job_id)
        return {
            "status": "success",
            "source_id": source_id,
            "document_id": str(document.id),
        }
    except Exception as exc:
        logger.error(f"Task ingest_source_task failed for source {source_id}: {exc}")
        # Re-raise so Celery marks task as failed
        raise exc


@shared_task(bind=True, name="apps.processing.tasks.embed_source_task", max_retries=2)
def embed_source_task(self, source_id: str, force: bool = False):
    """
    Celery background worker task to generate vector embeddings for all chunks in a Source.
    """
    logger.info(f"Celery task embed_source_task started for source: {source_id} (Task ID: {self.request.id})")
    try:
        from apps.rag.services.embedding import EmbeddingService
        embedded_count = EmbeddingService.embed_source(source_id=source_id, force=force)
        return {
            "status": "success",
            "source_id": source_id,
            "embedded_chunks": embedded_count,
        }
    except Exception as exc:
        logger.error(f"Task embed_source_task failed for source {source_id}: {exc}")
        raise exc


@shared_task(bind=True, name="apps.processing.tasks.retry_embeddings_task", max_retries=2)
def retry_embeddings_task(self):
    """
    Celery background worker task to retry missing embeddings across all document chunks.
    """
    logger.info(f"Celery task retry_embeddings_task started (Task ID: {self.request.id})")
    try:
        from apps.rag.services.embedding import EmbeddingService
        total_embedded = EmbeddingService.retry_failed_embeddings()
        return {
            "status": "success",
            "embedded_chunks": total_embedded,
        }
    except Exception as exc:
        logger.error(f"Task retry_embeddings_task failed: {exc}")
        raise exc

