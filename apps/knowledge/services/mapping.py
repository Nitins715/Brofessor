from dataclasses import dataclass
import logging
import math
from typing import List, Optional, Tuple
from django.conf import settings

from apps.knowledge.models import Concept
from apps.roadmap.models import Domain, Topic, Skill
from apps.rag.embeddings import BaseEmbeddingProvider, get_embedding_provider

logger = logging.getLogger("brofessor")


@dataclass
class MappingResult:
    """Outcome of attempting to map a Concept to a Roadmap Skill."""
    mapped: bool
    skill: Optional[Skill] = None
    topic: Optional[Topic] = None
    confidence: float = 0.0
    method: str = "none"


class RoadmapMappingService:
    """
    Maps extracted concepts to predefined roadmap Skills and Topics.
    Preserves existing roadmap hierarchy as immutable source of truth:
    never auto-creates new roadmap skills. Leaves low-confidence concepts unmapped.
    """

    MIN_CONFIDENCE_THRESHOLD = 0.65

    @classmethod
    def _cosine_similarity(cls, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two float vectors."""
        if not v1 or not v2 or len(v1) != len(v2):
            return 0.0
        dot = sum(a * b for a, b in zip(v1, v2))
        norm1 = math.sqrt(sum(a * a for a in v1))
        norm2 = math.sqrt(sum(b * b for b in v2))
        if norm1 == 0.0 or norm2 == 0.0:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))

    @classmethod
    def map_concept(
        cls,
        concept: Concept,
        domain: Optional[Domain] = None,
        embedding_provider: Optional[BaseEmbeddingProvider] = None,
        min_confidence: Optional[float] = None,
    ) -> MappingResult:
        """
        Attempt to map a Concept to an existing Skill.
        Uses exact name matching first, then semantic vector similarity.
        """
        threshold = min_confidence or cls.MIN_CONFIDENCE_THRESHOLD

        # Query existing skills
        skill_qs = Skill.objects.select_related("topic", "topic__domain")
        target_domain = domain or Domain.objects.filter(is_selected=True).first()
        if target_domain:
            # Prioritize skills under selected domain
            domain_skills = list(skill_qs.filter(topic__domain=target_domain))
            skills = domain_skills if domain_skills else list(skill_qs.all())
        else:
            skills = list(skill_qs.all())

        if not skills:
            logger.info("No roadmap skills available to map concept.")
            return MappingResult(mapped=False, confidence=0.0, method="empty_roadmap")

        concept_name_lower = concept.name.lower().strip()

        # 1. Exact / Substring Lexical Matching
        for skill in skills:
            skill_name_lower = skill.name.lower().strip()
            if concept_name_lower == skill_name_lower:
                return cls._apply_mapping(concept, skill, confidence=1.0, method="exact_lexical")
            elif (
                len(concept_name_lower) > 4
                and (concept_name_lower in skill_name_lower or skill_name_lower in concept_name_lower)
            ):
                return cls._apply_mapping(concept, skill, confidence=0.88, method="substring_lexical")

        # 2. Semantic Vector Similarity Matching
        active_provider = embedding_provider or get_embedding_provider()
        concept_text = f"{concept.name}: {concept.description or ''}".strip()
        concept_vec = active_provider.embed_text(concept_text)

        best_skill: Optional[Skill] = None
        best_similarity = 0.0

        for skill in skills:
            skill_text = f"{skill.name}: {skill.description or ''}".strip()
            skill_vec = active_provider.embed_text(skill_text)
            sim = cls._cosine_similarity(concept_vec, skill_vec)

            if sim > best_similarity:
                best_similarity = sim
                best_skill = skill

        # 3. Confidence Threshold Check
        if best_skill and best_similarity >= threshold:
            return cls._apply_mapping(
                concept,
                best_skill,
                confidence=round(best_similarity, 4),
                method="semantic_similarity",
            )

        # Unmapped when confidence is insufficient
        logger.info(
            f"Concept '{concept.name}' unmapped (Best match '{best_skill.name if best_skill else 'none'}' "
            f"similarity {best_similarity:.4f} < threshold {threshold})"
        )
        meta = concept.metadata or {}
        meta["mapping_attempted"] = True
        meta["highest_candidate_similarity"] = round(best_similarity, 4)
        if best_skill:
            meta["nearest_skill_id"] = str(best_skill.id)
            meta["nearest_skill_name"] = best_skill.name
        concept.metadata = meta
        concept.save(update_fields=["metadata"])

        return MappingResult(
            mapped=False,
            skill=best_skill,
            topic=best_skill.topic if best_skill else None,
            confidence=round(best_similarity, 4),
            method="insufficient_confidence",
        )

    @classmethod
    def _apply_mapping(
        cls,
        concept: Concept,
        skill: Skill,
        confidence: float,
        method: str,
    ) -> MappingResult:
        """Apply the matched skill and topic to the Concept model instance."""
        concept.topic = skill.topic
        concept.domain = skill.topic.domain
        meta = concept.metadata or {}
        meta["mapped_skill"] = {
            "id": str(skill.id),
            "name": skill.name,
            "topic": skill.topic.name,
            "confidence": confidence,
            "method": method,
        }
        concept.metadata = meta
        concept.save(update_fields=["topic", "domain", "metadata"])
        concept.skills.add(skill)

        logger.info(
            f"Mapped concept '{concept.name}' -> Skill '{skill.name}' "
            f"(Confidence: {confidence}, Method: {method})"
        )
        return MappingResult(
            mapped=True,
            skill=skill,
            topic=skill.topic,
            confidence=confidence,
            method=method,
        )
