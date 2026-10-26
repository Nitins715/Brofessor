from dataclasses import dataclass
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from django.utils import timezone
from apps.knowledge.models import (
    Concept,
    KnowledgeGap,
    Recommendation,
)
from apps.roadmap.models import Skill, Topic
from apps.sources.models import Source
from apps.assessments.models import Assessment
from apps.rag.llm import get_llm_provider

logger = logging.getLogger("brofessor")


class RecommendationService:
    """
    Generates actionable, prioritized recommendations based on active knowledge gaps.
    Optionally enriches recommendations using LLM / RAG context when available.
    """

    @classmethod
    def generate_recommendations_for_gap(
        cls,
        gap: KnowledgeGap,
        use_llm: bool = False,
    ) -> List[Recommendation]:
        """
        Generate and persist concrete recommendations to resolve a specific KnowledgeGap.
        """
        skill = gap.skill
        topic = gap.topic or (skill.topic if skill else None)
        recommendations: List[Recommendation] = []

        priority_map = {
            KnowledgeGap.Severity.CRITICAL: Recommendation.Priority.URGENT,
            KnowledgeGap.Severity.HIGH: Recommendation.Priority.HIGH,
            KnowledgeGap.Severity.MEDIUM: Recommendation.Priority.MEDIUM,
            KnowledgeGap.Severity.LOW: Recommendation.Priority.LOW,
        }
        rec_priority = priority_map.get(gap.severity, Recommendation.Priority.MEDIUM)

        # 1. Action based on gap type
        if gap.gap_type == KnowledgeGap.GapType.NO_EVIDENCE:
            # Check for existing sources or concepts
            concept = Concept.objects.filter(skills=skill).first() if skill else None
            source = Source.objects.filter(status=Source.ProcessingStatus.COMPLETED).first()
            assessment = Assessment.objects.filter(skill=skill, is_active=True).first() if skill else None

            if concept:
                r1, _ = Recommendation.objects.update_or_create(
                    gap=gap,
                    skill=skill,
                    action_type=Recommendation.ActionType.STUDY_CONCEPT,
                    defaults={
                        "topic": topic,
                        "priority": rec_priority,
                        "title": f"Study core concept: {concept.name}",
                        "description": f"Learn foundational fundamentals of '{concept.name}' mapped to {skill.name}.",
                        "suggested_action": f"Review definition and relationships for {concept.name}.",
                        "concept": concept,
                    },
                )
                recommendations.append(r1)

            if assessment:
                r2, _ = Recommendation.objects.update_or_create(
                    gap=gap,
                    skill=skill,
                    action_type=Recommendation.ActionType.PRACTICE_QUESTIONS,
                    defaults={
                        "topic": topic,
                        "priority": rec_priority,
                        "title": f"Take initial assessment for {skill.name}",
                        "description": f"Benchmark your baseline understanding on '{assessment.title}'.",
                        "suggested_action": f"Start assessment '{assessment.title}' to record baseline evidence.",
                        "assessment": assessment,
                    },
                )
                recommendations.append(r2)
            else:
                r2, _ = Recommendation.objects.update_or_create(
                    gap=gap,
                    skill=skill,
                    action_type=Recommendation.ActionType.READ_SOURCE,
                    defaults={
                        "topic": topic,
                        "priority": rec_priority,
                        "title": f"Ingest or study materials for {skill.name}",
                        "description": f"Add an article, documentation, or note covering {skill.name}.",
                        "suggested_action": f"Add reading material or watch a technical breakdown on {skill.name}.",
                        "source": source,
                    },
                )
                recommendations.append(r2)

        elif gap.gap_type == KnowledgeGap.GapType.WEAK_ASSESSMENT:
            assessment = Assessment.objects.filter(skill=skill, is_active=True).first() if skill else None
            r_reassess, _ = Recommendation.objects.update_or_create(
                gap=gap,
                skill=skill,
                action_type=Recommendation.ActionType.REASSESS_SKILL,
                defaults={
                    "topic": topic,
                    "priority": rec_priority,
                    "title": f"Reassess and verify {skill.name}",
                    "description": f"Recent score ({gap.current_score}%) fell below target ({gap.target_score}%). Review incorrect questions and retest.",
                    "suggested_action": f"Review test feedback and take another attempt on {skill.name}.",
                    "assessment": assessment,
                },
            )
            recommendations.append(r_reassess)

            if topic:
                r_revise, _ = Recommendation.objects.update_or_create(
                    gap=gap,
                    skill=skill,
                    action_type=Recommendation.ActionType.REVISE_TOPIC,
                    defaults={
                        "topic": topic,
                        "priority": Recommendation.Priority.MEDIUM,
                        "title": f"Revise topic: {topic.name}",
                        "description": f"Review core principles of '{topic.name}' before retaking the assessment.",
                        "suggested_action": f"Re-read key notes and summaries under {topic.name}.",
                    },
                )
                recommendations.append(r_revise)

        elif gap.gap_type == KnowledgeGap.GapType.WEAK_COVERAGE:
            r_project, _ = Recommendation.objects.update_or_create(
                gap=gap,
                skill=skill,
                action_type=Recommendation.ActionType.BUILD_PROJECT,
                defaults={
                    "topic": topic,
                    "priority": rec_priority,
                    "title": f"Build practical project for {skill.name}",
                    "description": f"Demonstrated coverage is only {gap.current_score}%. Deepen understanding with hands-on implementation.",
                    "suggested_action": f"Build a code script or mini-project implementing {skill.name} and record practical evidence.",
                },
            )
            recommendations.append(r_project)

        elif gap.gap_type == KnowledgeGap.GapType.BELOW_ROADMAP_LEVEL:
            r_practice, _ = Recommendation.objects.update_or_create(
                gap=gap,
                skill=skill,
                action_type=Recommendation.ActionType.PRACTICE_QUESTIONS,
                defaults={
                    "topic": topic,
                    "priority": rec_priority,
                    "title": f"Target {gap.expected_level} mastery for {skill.name}",
                    "description": f"Current level is '{gap.current_level}' vs required '{gap.expected_level}'. Solve intermediate/advanced challenges.",
                    "suggested_action": f"Tackle advanced questions or practical exercises to level up {skill.name}.",
                },
            )
            recommendations.append(r_practice)

        # Contextual LLM enhancement if requested
        if use_llm and recommendations:
            try:
                llm = get_llm_provider()
                prompt = (
                    f"Given a learner who has a knowledge gap in '{skill.name if skill else topic.name}' "
                    f"(Gap: {gap.title}, Score: {gap.current_score}%). "
                    f"Suggest a concise 1-sentence actionable study tip."
                )
                response = llm.generate_response(prompt)
                if response and response.content:
                    tip = response.content.strip()
                    for r in recommendations:
                        r.suggested_action = f"{r.suggested_action} AI Tip: {tip}"
                        r.save(update_fields=["suggested_action"])
            except Exception as e:
                logger.warning(f"Contextual LLM recommendation enrichment skipped: {e}")

        return recommendations

    @classmethod
    def generate_all_recommendations(
        cls,
        use_llm: bool = False,
    ) -> List[Recommendation]:
        """Generate recommendations for all active KnowledgeGaps."""
        active_gaps = KnowledgeGap.objects.filter(status=KnowledgeGap.Status.ACTIVE)
        all_recs = []
        for gap in active_gaps:
            recs = cls.generate_recommendations_for_gap(gap, use_llm=use_llm)
            all_recs.extend(recs)
        return all_recs
