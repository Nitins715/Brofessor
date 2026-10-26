import logging
from celery import shared_task
from apps.knowledge.services.pipeline import KnowledgePipeline

logger = logging.getLogger("brofessor")


@shared_task(bind=True, name="apps.knowledge.tasks.extract_knowledge_for_source_task", max_retries=2)
def extract_knowledge_for_source_task(self, source_id: str, job_id: str = None):
    """
    Celery background worker task to extract concepts, map to roadmap skills,
    record learning evidence, and update personal knowledge model.
    """
    logger.info(
        f"Celery task extract_knowledge_for_source_task started for source: {source_id} (Task ID: {self.request.id})"
    )
    try:
        result = KnowledgePipeline.process_source(source_id=source_id, job_id=job_id)
        return result.to_dict()
    except Exception as exc:
        logger.error(f"Task extract_knowledge_for_source_task failed for source {source_id}: {exc}")
        raise exc
