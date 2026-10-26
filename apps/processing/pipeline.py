import hashlib
import logging
from typing import Optional
from django.db import transaction
from django.utils import timezone

from apps.sources.models import Source, Document, DocumentChunk
from apps.processing.models import ProcessingJob
from apps.processing.extractors import get_extractor_for_source, ExtractionResult
from apps.processing.cleaners import TextCleaner
from apps.processing.chunking import TextChunker, ChunkingConfig

logger = logging.getLogger("brofessor")


class IngestionPipeline:
    """
    Coordinates the full content ingestion pipeline:
    Source -> Extractor -> Cleaner -> Chunker -> Document / DocumentChunk persistence
    """

    @classmethod
    def compute_hash(cls, text: str) -> str:
        """Calculate SHA-256 digest of normalized text."""
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    @classmethod
    def process_source(
        cls,
        source_id: str,
        chunking_config: Optional[ChunkingConfig] = None,
        job_id: Optional[str] = None,
    ) -> Document:
        """
        Execute the end-to-end ingestion pipeline for a single Source instance.
        """
        if hasattr(source_id, "id"):
            source_id = getattr(source_id, "id")

        try:
            source = Source.objects.get(id=source_id)
        except Source.DoesNotExist as e:
            logger.error(f"Ingestion failed: Source with id {source_id} does not exist.")
            raise

        # Track processing job
        job = None
        if job_id:
            job = ProcessingJob.objects.filter(id=job_id).first()
        if not job:
            job = ProcessingJob.objects.create(
                source=source,
                job_type=ProcessingJob.JobType.INGESTION,
                status=ProcessingJob.JobStatus.RUNNING,
                started_at=timezone.now(),
            )
        else:
            job.status = ProcessingJob.JobStatus.RUNNING
            job.started_at = timezone.now()
            job.save(update_fields=["status", "started_at"])

        source.status = Source.ProcessingStatus.PROCESSING
        source.error_message = ""
        source.save(update_fields=["status", "error_message"])

        try:
            # 1. Content Extraction
            logger.info(f"Extracting content for source '{source.name}' ({source.source_type})")
            extractor = get_extractor_for_source(source.source_type)
            extraction_result: ExtractionResult = extractor.extract(source)

            # 2. Cleaning & Normalization
            logger.info(f"Normalizing text for source '{source.name}'")
            cleaned_text = TextCleaner.clean(extraction_result.text)
            if not cleaned_text:
                raise ValueError(f"Extracted content for Source '{source.name}' was empty after cleaning.")

            content_hash = cls.compute_hash(cleaned_text)

            # 3. Document Chunking
            logger.info(f"Chunking content for source '{source.name}'")
            chunker = TextChunker(config=chunking_config)
            base_meta = {
                "source_id": str(source.id),
                "source_type": source.source_type,
                "source_name": source.name,
                "uri": source.uri,
                **extraction_result.metadata,
            }
            chunks_data = chunker.chunk(
                text=cleaned_text,
                base_metadata=base_meta,
                segments=extraction_result.segments,
            )

            # 4. Atomic Database Persistence
            with transaction.atomic():
                document, created = Document.objects.update_or_create(
                    source=source,
                    defaults={
                        "title": extraction_result.title,
                        "content": cleaned_text,
                        "content_hash": content_hash,
                        "metadata": {
                            **extraction_result.metadata,
                            "chunk_count": len(chunks_data),
                            "total_chars": len(cleaned_text),
                        },
                    },
                )

                # Replace old chunks if re-processing
                DocumentChunk.objects.filter(document=document).delete()

                chunk_objects = [
                    DocumentChunk(
                        document=document,
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        token_count=chunk.token_count,
                        metadata=chunk.metadata,
                    )
                    for chunk in chunks_data
                ]
                DocumentChunk.objects.bulk_create(chunk_objects)

                # Generate embeddings for the newly created chunks
                try:
                    from apps.rag.services.embedding import EmbeddingService
                    embedded_count = EmbeddingService.embed_document(document.id)
                except Exception as emb_exc:
                    logger.warning(
                        f"Automatic embedding deferred or failed for document {document.id}: {emb_exc}"
                    )
                    embedded_count = 0

                # Mark completed
                source.status = Source.ProcessingStatus.COMPLETED
                source.metadata = {
                    **(source.metadata or {}),
                    "document_id": str(document.id),
                    "chunk_count": len(chunk_objects),
                    "embedded_chunk_count": embedded_count,
                    "last_processed_at": timezone.now().isoformat(),
                }
                source.save(update_fields=["status", "metadata"])


                job.status = ProcessingJob.JobStatus.COMPLETED
                job.finished_at = timezone.now()
                job.payload = {
                    "document_id": str(document.id),
                    "chunk_count": len(chunk_objects),
                    "total_characters": len(cleaned_text),
                }
                job.save(update_fields=["status", "finished_at", "payload"])

            logger.info(
                f"Successfully ingested source '{source.name}' into document '{document.id}' with {len(chunk_objects)} chunks."
            )
            return document

        except Exception as e:
            error_message = str(e)
            logger.error(f"Ingestion failed for source '{source.name}' ({source.id}): {error_message}", exc_info=True)

            source.status = Source.ProcessingStatus.FAILED
            source.error_message = error_message
            source.save(update_fields=["status", "error_message"])

            job.status = ProcessingJob.JobStatus.FAILED
            job.error_message = error_message
            job.finished_at = timezone.now()
            job.save(update_fields=["status", "error_message", "finished_at"])

            raise
