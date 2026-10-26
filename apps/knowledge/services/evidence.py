from decimal import Decimal
import logging
from typing import Any, Dict, Optional, Union
from django.utils import timezone

from apps.knowledge.models import Concept, Evidence
from apps.roadmap.models import Topic, Skill
from apps.sources.models import Source

logger = logging.getLogger("brofessor")


class EvidenceService:
    """
    Service for recording immutable knowledge evidence items across all 4 modalities:
    Learning (content ingestion), Declared (self-reported), Practical (projects/repos),
    and Assessment (tests/quizzes).
    """

    @classmethod
    def record_learning_evidence(
        cls,
        title: str,
        source: Optional[Source] = None,
        concept: Optional[Concept] = None,
        skill: Optional[Skill] = None,
        topic: Optional[Topic] = None,
        snippet: str = "",
        document_id: Optional[str] = None,
        confidence_weight: float = 1.0,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> Evidence:
        """Record evidence from reading/ingesting learning materials."""
        payload = raw_data or {}
        if snippet:
            payload["snippet"] = snippet
        if document_id:
            payload["document_id"] = document_id

        return cls._create_evidence(
            evidence_type=Evidence.EvidenceType.LEARNING,
            title=title,
            description=snippet[:500] if snippet else f"Encountered in {source.name if source else 'learning material'}",
            source=source,
            concept=concept,
            skill=skill,
            topic=topic,
            raw_data=payload,
            confidence_weight=confidence_weight,
        )

    @classmethod
    def record_declared_evidence(
        cls,
        title: str,
        skill: Skill,
        rating: Optional[int] = None,
        note: str = "",
        concept: Optional[Concept] = None,
        confidence_weight: float = 0.70,
    ) -> Evidence:
        """Record self-declared knowledge or prior experience."""
        payload = {
            "declared_rating": rating,
            "note": note,
        }
        return cls._create_evidence(
            evidence_type=Evidence.EvidenceType.DECLARED,
            title=title,
            description=note or f"Self-declared knowledge for {skill.name}",
            skill=skill,
            topic=skill.topic,
            concept=concept,
            raw_data=payload,
            confidence_weight=confidence_weight,
        )

    @classmethod
    def record_declared_topic_evidence(
        cls,
        title: str,
        topic: Topic,
        rating: Optional[int] = None,
        note: str = "",
        confidence_weight: float = 0.70,
    ) -> Evidence:
        """Record self-declared knowledge or prior experience at the topic level."""
        payload = {
            "declared_rating": rating,
            "note": note,
        }
        return cls._create_evidence(
            evidence_type=Evidence.EvidenceType.DECLARED,
            title=title,
            description=note or f"Self-declared knowledge for topic {topic.name}",
            topic=topic,
            raw_data=payload,
            confidence_weight=confidence_weight,
        )

    @classmethod
    def record_practical_evidence(
        cls,
        title: str,
        skill: Skill,
        description: str = "",
        repo_url: str = "",
        raw_data: Optional[Dict[str, Any]] = None,
        confidence_weight: float = 0.90,
    ) -> Evidence:
        """Record evidence from practical implementations, projects, or repositories."""
        payload = raw_data or {}
        if repo_url:
            payload["repo_url"] = repo_url

        return cls._create_evidence(
            evidence_type=Evidence.EvidenceType.PRACTICAL,
            title=title,
            description=description or f"Applied project evidence for {skill.name}",
            skill=skill,
            topic=skill.topic,
            raw_data=payload,
            confidence_weight=confidence_weight,
        )

    @classmethod
    def record_assessment_evidence(
        cls,
        title: str,
        skill: Optional[Skill] = None,
        topic: Optional[Topic] = None,
        score: float = 0.0,
        max_score: float = 100.0,
        assessment_id: Optional[str] = None,
        confidence_weight: float = 1.00,
        raw_data: Optional[Dict[str, Any]] = None,
    ) -> Evidence:
        """Record evidence from formal assessments, quizzes, or test results."""
        percentage = round((score / max_score) * 100, 2) if max_score > 0 else 0.0
        payload = {
            **(raw_data or {}),
            "score": score,
            "max_score": max_score,
            "percentage": percentage,
            "assessment_id": assessment_id,
        }
        resolved_topic = topic or (skill.topic if skill else None)
        return cls._create_evidence(
            evidence_type=Evidence.EvidenceType.ASSESSMENT,
            title=title,
            description=f"Scored {score}/{max_score} ({percentage}%) on assessment",
            skill=skill,
            topic=resolved_topic,
            raw_data=payload,
            confidence_weight=confidence_weight,
        )

    @classmethod
    def _create_evidence(
        cls,
        evidence_type: str,
        title: str,
        description: str = "",
        source: Optional[Source] = None,
        concept: Optional[Concept] = None,
        skill: Optional[Skill] = None,
        topic: Optional[Topic] = None,
        raw_data: Optional[Dict[str, Any]] = None,
        confidence_weight: float = 1.0,
    ) -> Evidence:
        # If skill is provided but topic is None, derive topic from skill
        resolved_skill = skill
        resolved_topic = topic
        if resolved_skill and not resolved_topic:
            resolved_topic = resolved_skill.topic

        # If concept is provided but skill is None, check if concept is mapped to a skill
        if concept and not resolved_skill:
            mapped_skill = concept.skills.first()
            if mapped_skill:
                resolved_skill = mapped_skill
                resolved_topic = mapped_skill.topic
            elif concept.topic and not resolved_topic:
                resolved_topic = concept.topic

        evidence = Evidence.objects.create(
            evidence_type=evidence_type,
            title=title,
            description=description,
            source=source,
            concept=concept,
            skill=resolved_skill,
            topic=resolved_topic,
            raw_data=raw_data or {},
            confidence_weight=Decimal(str(round(confidence_weight, 2))),
            recorded_at=timezone.now(),
        )

        logger.info(
            f"Recorded {evidence.get_evidence_type_display()} '{title}' "
            f"(Skill: {resolved_skill.name if resolved_skill else 'Unassigned'})"
        )
        return evidence
