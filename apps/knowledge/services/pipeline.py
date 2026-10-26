from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional, Union
import uuid
from django.utils import timezone

from apps.sources.models import Source
from apps.processing.models import ProcessingJob
from apps.knowledge.models import Concept, Evidence
from apps.roadmap.models import Skill
from apps.rag.llm import BaseLLMProvider
from apps.rag.embeddings import BaseEmbeddingProvider
from .extraction import ConceptExtractionService, ExtractedConceptResult
from .mapping import RoadmapMappingService, MappingResult
from .evidence import EvidenceService
from .knowledge_model import PersonalKnowledgeModelService

logger = logging.getLogger("brofessor")


@dataclass
class KnowledgeExtractionResult:
    """Summary of the full source knowledge extraction pipeline run."""
    source_id: str
    concepts_extracted: int
    concepts_mapped: int
    evidence_recorded: int
    affected_skills: List[str]
    status: str
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "concepts_extracted": self.concepts_extracted,
            "concepts_mapped": self.concepts_mapped,
            "evidence_recorded": self.evidence_recorded,
            "affected_skills": self.affected_skills,
            "status": self.status,
            "error": self.error,
            "metadata": self.metadata,
        }


class KnowledgePipeline:
    """
    End-to-end Knowledge Extraction & Personal Knowledge Model pipeline.
    Flow: Source -> Extract Concepts -> Map to Roadmap Skills -> Record Learning Evidence -> Update Mastery.
    Tracks status via ProcessingJob with failure handling and retry support.
    """

    @classmethod
    def process_source(
        cls,
        source_id: Union[str, uuid.UUID, Source],
        llm_provider: Optional[BaseLLMProvider] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        job_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> KnowledgeExtractionResult:
        start_time = time.time()
        if hasattr(source_id, "id"):
            source_id = source_id.id

        source = Source.objects.get(id=source_id)

        # 1. Initialize or update ProcessingJob
        job = None
        if job_id:
            job = ProcessingJob.objects.filter(id=job_id).first()
        if not job:
            job = ProcessingJob.objects.create(
                source=source,
                job_type=ProcessingJob.JobType.KNOWLEDGE_EXTRACTION,
                status=ProcessingJob.JobStatus.RUNNING,
                started_at=timezone.now(),
            )
        else:
            job.status = ProcessingJob.JobStatus.RUNNING
            job.started_at = timezone.now()
            job.error_message = ""
            job.save(update_fields=["status", "started_at", "error_message"])

        logger.info(f"Starting Knowledge Extraction pipeline for Source '{source.name}' (Job {job.id})")

        try:
            # 2. Extract concepts from Source content
            extracted_items: List[ExtractedConceptResult] = ConceptExtractionService.extract_from_source(
                source=source,
                llm_provider=llm_provider,
            )

            mapped_count = 0
            evidence_count = 0
            affected_skills = set()

            # 3. Map extracted concepts to Roadmap Skills and record learning evidence
            for item in extracted_items:
                concept = item.concept
                mapping_res = RoadmapMappingService.map_concept(
                    concept=concept,
                    embedding_provider=embedding_provider,
                )

                matched_skill = mapping_res.skill if mapping_res.mapped else None
                matched_topic = mapping_res.topic if mapping_res.mapped else None

                if mapping_res.mapped and matched_skill:
                    mapped_count += 1
                    affected_skills.add(matched_skill)

                # Record learning evidence
                ev = EvidenceService.record_learning_evidence(
                    title=f"Studied {concept.name}",
                    source=source,
                    concept=concept,
                    skill=matched_skill,
                    topic=matched_topic,
                    snippet=item.evidence_snippet or concept.description,
                    confidence_weight=mapping_res.confidence if mapping_res.mapped else 0.60,
                    raw_data={
                        "category": item.category,
                        "importance": item.importance,
                        "mapped": mapping_res.mapped,
                        "mapping_method": mapping_res.method,
                    },
                )
                evidence_count += 1

            # 4. Update derived mastery scores for all affected skills
            for skill in affected_skills:
                PersonalKnowledgeModelService.recalculate_skill_mastery(skill.id)

            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # 5. Mark Job Completed
            job.status = ProcessingJob.JobStatus.COMPLETED
            job.finished_at = timezone.now()
            job.payload = {
                "concepts_extracted": len(extracted_items),
                "concepts_mapped": mapped_count,
                "evidence_recorded": evidence_count,
                "affected_skills_count": len(affected_skills),
                "duration_ms": elapsed_ms,
            }
            job.save(update_fields=["status", "finished_at", "payload"])

            logger.info(
                f"Knowledge Extraction completed for Source '{source.name}': "
                f"{len(extracted_items)} concepts ({mapped_count} mapped), {evidence_count} evidence items in {elapsed_ms}ms"
            )

            return KnowledgeExtractionResult(
                source_id=str(source.id),
                concepts_extracted=len(extracted_items),
                concepts_mapped=mapped_count,
                evidence_recorded=evidence_count,
                affected_skills=[s.name for s in affected_skills],
                status="completed",
                metadata={"duration_ms": elapsed_ms},
            )

        except Exception as e:
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.error(f"Knowledge Extraction failed for Source '{source.name}': {e}", exc_info=True)
            job.status = ProcessingJob.JobStatus.FAILED
            job.finished_at = timezone.now()
            job.error_message = str(e)
            job.payload = {"duration_ms": elapsed_ms}
            job.save(update_fields=["status", "finished_at", "error_message", "payload"])

            return KnowledgeExtractionResult(
                source_id=str(source.id),
                concepts_extracted=0,
                concepts_mapped=0,
                evidence_recorded=0,
                affected_skills=[],
                status="failed",
                error=str(e),
                metadata={"duration_ms": elapsed_ms},
            )

    @classmethod
    def retry_failed(
        cls,
        source_id: Optional[Union[str, uuid.UUID]] = None,
        job_id: Optional[Union[str, uuid.UUID]] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
    ) -> List[KnowledgeExtractionResult]:
        """
        Retry failed knowledge extraction jobs for a specific source, job, or all failed jobs.
        """
        job_qs = ProcessingJob.objects.filter(
            job_type=ProcessingJob.JobType.KNOWLEDGE_EXTRACTION,
            status=ProcessingJob.JobStatus.FAILED,
        )

        if job_id:
            job_qs = job_qs.filter(id=job_id)
        elif source_id:
            job_qs = job_qs.filter(source_id=source_id)

        results = []
        for job in list(job_qs):
            if job.source:
                res = cls.process_source(
                    source_id=job.source.id,
                    job_id=job.id,
                    llm_provider=llm_provider,
                    embedding_provider=embedding_provider,
                )
                results.append(res)

        return results
