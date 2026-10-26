from dataclasses import dataclass, field
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Union
import uuid
from django.db.models import Count, Max
from django.utils import timezone

from apps.knowledge.models import Concept, Evidence, CalculatedMastery
from apps.roadmap.models import Domain, Topic, Skill

logger = logging.getLogger("brofessor")


@dataclass
class SkillEvidenceSummary:
    """Consolidated knowledge state and evidence metrics for a Skill."""
    skill_id: str
    skill_name: str
    topic_id: str
    topic_name: str
    difficulty_level: str
    total_evidence_count: int
    evidence_breakdown: Dict[str, int]
    covered_concepts: List[Dict[str, Any]]
    last_supported_at: Optional[str]
    mastery_score: float
    mastery_level: str
    knowledge_coverage: float
    confidence_score: float
    evidence_items: List[Dict[str, Any]]


@dataclass
class KnowledgeProfileSummary:
    """User-wide or domain-wide personal knowledge overview."""
    total_encountered_skills: int
    total_roadmap_skills: int
    coverage_percentage: float
    total_concepts_extracted: int
    total_evidence_items: int
    evidence_by_type: Dict[str, int]
    encountered_skills: List[Dict[str, Any]]


class PersonalKnowledgeModelService:
    """
    Personal Knowledge Model service.
    Aggregates learning, declared, practical, and assessment evidence for roadmap skills.
    Keeps raw evidence records strictly separated from derived CalculatedMastery measurements.
    """

    @classmethod
    def get_skill_summary(cls, skill_id: Union[str, uuid.UUID]) -> Optional[SkillEvidenceSummary]:
        """
        Aggregate all evidence, covered concepts, and calculated mastery for a single Skill.
        """
        skill = Skill.objects.filter(id=skill_id).select_related("topic").first()
        if not skill:
            return None

        # 1. Fetch raw evidence items
        evidence_qs = Evidence.objects.filter(skill=skill).select_related("source", "concept").order_by("-recorded_at")
        total_count = evidence_qs.count()

        # Breakdown by evidence type
        breakdown = {
            Evidence.EvidenceType.LEARNING: 0,
            Evidence.EvidenceType.DECLARED: 0,
            Evidence.EvidenceType.PRACTICAL: 0,
            Evidence.EvidenceType.ASSESSMENT: 0,
        }
        evidence_list = []
        last_supported = None

        for ev in evidence_qs:
            if not last_supported:
                last_supported = ev.recorded_at.isoformat() if ev.recorded_at else None
            breakdown[ev.evidence_type] = breakdown.get(ev.evidence_type, 0) + 1
            evidence_list.append({
                "id": str(ev.id),
                "type": ev.evidence_type,
                "title": ev.title,
                "description": ev.description,
                "source_name": ev.source.name if ev.source else None,
                "concept_name": ev.concept.name if ev.concept else None,
                "confidence_weight": float(ev.confidence_weight),
                "recorded_at": ev.recorded_at.isoformat() if ev.recorded_at else None,
                "raw_data": ev.raw_data,
            })

        # 2. Fetch covered concepts linked to this skill
        concepts = skill.concepts.all()
        covered_concepts = [
            {
                "id": str(c.id),
                "name": c.name,
                "slug": c.slug,
                "description": c.description,
                "category": (c.metadata or {}).get("category", "concept"),
            }
            for c in concepts
        ]

        # 3. Fetch derived mastery
        mastery = CalculatedMastery.objects.filter(skill=skill).first()
        if not mastery:
            from .mastery import MasteryEngineService
            mastery = MasteryEngineService.recalculate_skill_mastery(skill.id)

        mastery_score = float(mastery.mastery_score)
        mastery_level = getattr(mastery, "mastery_level", "beginner")
        knowledge_coverage = float(getattr(mastery, "knowledge_coverage", 0.0))
        confidence_score = float(mastery.confidence_score)

        return SkillEvidenceSummary(
            skill_id=str(skill.id),
            skill_name=skill.name,
            topic_id=str(skill.topic.id),
            topic_name=skill.topic.name,
            difficulty_level=skill.difficulty_level,
            total_evidence_count=total_count,
            evidence_breakdown=breakdown,
            covered_concepts=covered_concepts,
            last_supported_at=last_supported,
            mastery_score=mastery_score,
            mastery_level=mastery_level,
            knowledge_coverage=knowledge_coverage,
            confidence_score=confidence_score,
            evidence_items=evidence_list,
        )

    @classmethod
    def get_topic_summary(cls, topic_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """Summarize skills, evidence counts, and concepts under a Topic."""
        topic = Topic.objects.filter(id=topic_id).prefetch_related("skills").first()
        if not topic:
            return None

        skills_data = []
        total_topic_evidence = 0

        for skill in topic.skills.all():
            ev_count = Evidence.objects.filter(skill=skill).count()
            total_topic_evidence += ev_count
            mastery = CalculatedMastery.objects.filter(skill=skill).first()
            skills_data.append({
                "id": str(skill.id),
                "name": skill.name,
                "evidence_count": ev_count,
                "mastery_score": float(mastery.mastery_score) if mastery else 0.0,
                "mastery_level": getattr(mastery, "mastery_level", "beginner") if mastery else "beginner",
                "knowledge_coverage": float(getattr(mastery, "knowledge_coverage", 0.0)) if mastery else 0.0,
                "concepts_count": skill.concepts.count(),
            })

        topic_mastery = CalculatedMastery.objects.filter(topic=topic).first()

        return {
            "topic_id": str(topic.id),
            "topic_name": topic.name,
            "total_skills": len(skills_data),
            "encountered_skills": sum(1 for s in skills_data if s["evidence_count"] > 0),
            "total_evidence_count": total_topic_evidence,
            "mastery_score": float(topic_mastery.mastery_score) if topic_mastery else 0.0,
            "mastery_level": getattr(topic_mastery, "mastery_level", "beginner") if topic_mastery else "beginner",
            "skills": skills_data,
        }

    @classmethod
    def get_profile_summary(cls, domain_id: Optional[Union[str, uuid.UUID]] = None) -> KnowledgeProfileSummary:
        """
        Aggregate high-level Personal Knowledge Model profile across encountered skills,
        concepts, and evidence items.
        """
        skill_qs = Skill.objects.all()
        evidence_qs = Evidence.objects.all()
        concept_qs = Concept.objects.all()

        if domain_id:
            skill_qs = skill_qs.filter(topic__domain_id=domain_id)
            evidence_qs = evidence_qs.filter(skill__topic__domain_id=domain_id)
            concept_qs = concept_qs.filter(domain_id=domain_id)

        total_roadmap_skills = skill_qs.count()

        # Find skills that have >= 1 evidence record
        encountered_skill_ids = list(
            set(evidence_qs.filter(skill__isnull=False).values_list("skill_id", flat=True))
        )
        encountered_count = len(encountered_skill_ids)
        coverage_pct = (
            round((encountered_count / total_roadmap_skills) * 100, 2)
            if total_roadmap_skills > 0
            else 0.0
        )

        # Evidence breakdown
        breakdown = {
            Evidence.EvidenceType.LEARNING: 0,
            Evidence.EvidenceType.DECLARED: 0,
            Evidence.EvidenceType.PRACTICAL: 0,
            Evidence.EvidenceType.ASSESSMENT: 0,
        }
        for item in evidence_qs.values("evidence_type").annotate(count=Count("id")):
            breakdown[item["evidence_type"]] = item["count"]

        # Encountered skills summary list
        encountered_skills_data = []
        for s_id in encountered_skill_ids:
            skill = Skill.objects.filter(id=s_id).select_related("topic").first()
            if skill:
                count = evidence_qs.filter(skill_id=s_id).count()
                last_ev = evidence_qs.filter(skill_id=s_id).aggregate(latest=Max("recorded_at"))["latest"]
                mastery = CalculatedMastery.objects.filter(skill=skill).first()
                encountered_skills_data.append({
                    "id": str(skill.id),
                    "name": skill.name,
                    "topic_name": skill.topic.name,
                    "evidence_count": count,
                    "last_supported_at": last_ev.isoformat() if last_ev else None,
                    "mastery_score": float(mastery.mastery_score) if mastery else 0.0,
                    "mastery_level": getattr(mastery, "mastery_level", "beginner") if mastery else "beginner",
                    "knowledge_coverage": float(getattr(mastery, "knowledge_coverage", 0.0)) if mastery else 0.0,
                })

        encountered_skills_data.sort(key=lambda x: x["evidence_count"], reverse=True)

        return KnowledgeProfileSummary(
            total_encountered_skills=encountered_count,
            total_roadmap_skills=total_roadmap_skills,
            coverage_percentage=coverage_pct,
            total_concepts_extracted=concept_qs.count(),
            total_evidence_items=evidence_qs.count(),
            evidence_by_type=breakdown,
            encountered_skills=encountered_skills_data,
        )

    @classmethod
    def recalculate_skill_mastery(cls, skill_id: Union[str, uuid.UUID]) -> CalculatedMastery:
        """
        Recalculate mastery using the multi-modal MasteryEngineService,
        and update associated knowledge gaps and recommendations.
        """
        from .mastery import MasteryEngineService
        from .gaps import KnowledgeGapService
        from .recommendations import RecommendationService

        mastery = MasteryEngineService.recalculate_skill_mastery(skill_id)
        skill = Skill.objects.filter(id=skill_id).first()
        if skill:
            gaps = KnowledgeGapService.evaluate_skill_gaps(skill)
            for gap in gaps:
                RecommendationService.generate_recommendations_for_gap(gap)

        return mastery

    @classmethod
    def recalculate_all(cls, domain_id: Optional[Union[str, uuid.UUID]] = None) -> Dict[str, Any]:
        """
        Full system recalculation:
        Refreshes mastery across all skills, recalculates topic masteries,
        evaluates active knowledge gaps, and regenerates actionable recommendations.
        """
        from .mastery import MasteryEngineService
        from .gaps import KnowledgeGapService
        from .recommendations import RecommendationService

        skills_qs = Skill.objects.select_related("topic").all()
        topics_qs = Topic.objects.all()

        if domain_id:
            skills_qs = skills_qs.filter(topic__domain_id=domain_id)
            topics_qs = topics_qs.filter(domain_id=domain_id)

        skill_count = 0
        for skill in skills_qs:
            MasteryEngineService.recalculate_skill_mastery(skill.id)
            skill_count += 1

        topic_count = 0
        for topic in topics_qs:
            MasteryEngineService.recalculate_topic_mastery(topic.id)
            topic_count += 1

        all_gaps = KnowledgeGapService.evaluate_all_gaps()
        all_recs = RecommendationService.generate_all_recommendations()

        return {
            "status": "success",
            "skills_recalculated": skill_count,
            "topics_recalculated": topic_count,
            "active_gaps_count": len(all_gaps),
            "recommendations_generated": len(all_recs),
        }

    @classmethod
    def get_integrated_skill_summary(cls, skill_id: Union[str, uuid.UUID]) -> Optional[Dict[str, Any]]:
        """
        Frontend-ready integration pipeline:
        Skill -> Evidence -> Score -> Mastery -> Gap -> Recommendation -> Roadmap Progress
        """
        from apps.knowledge.models import KnowledgeGap, Recommendation
        from apps.roadmap.services import RoadmapProgressService

        summary = cls.get_skill_summary(skill_id)
        if not summary:
            return None

        skill = Skill.objects.filter(id=skill_id).first()
        gaps = KnowledgeGap.objects.filter(skill=skill, status=KnowledgeGap.Status.ACTIVE)
        recs = Recommendation.objects.filter(skill=skill, status=Recommendation.Status.PENDING)
        progress = RoadmapProgressService.get_skill_progress(skill_id)

        return {
            "skill": {
                "id": summary.skill_id,
                "name": summary.skill_name,
                "topic_id": summary.topic_id,
                "topic_name": summary.topic_name,
                "difficulty_level": summary.difficulty_level,
            },
            "evidence": {
                "total_count": summary.total_evidence_count,
                "breakdown": summary.evidence_breakdown,
                "items": summary.evidence_items,
            },
            "score": {
                "mastery_score": summary.mastery_score,
                "knowledge_coverage": summary.knowledge_coverage,
                "confidence_score": summary.confidence_score,
            },
            "mastery": {
                "level": summary.mastery_level,
                "is_proficient": summary.mastery_score >= 70.0,
            },
            "gaps": [
                {
                    "id": str(g.id),
                    "gap_type": g.gap_type,
                    "severity": g.severity,
                    "title": g.title,
                    "description": g.description,
                    "current_score": float(g.current_score),
                    "target_score": float(g.target_score),
                }
                for g in gaps
            ],
            "recommendations": [
                {
                    "id": str(r.id),
                    "action_type": r.action_type,
                    "priority": r.priority,
                    "title": r.title,
                    "description": r.description,
                    "suggested_action": r.suggested_action,
                }
                for r in recs
            ],
            "roadmap_progress": progress,
        }

    @classmethod
    def get_overall_knowledge_summary(cls, domain_id: Optional[Union[str, uuid.UUID]] = None) -> Dict[str, Any]:
        """
        Dashboard-level overview returning the complete skill knowledge summary across all skills.
        """
        from apps.roadmap.services import RoadmapProgressService

        skills_qs = Skill.objects.select_related("topic").all()
        if domain_id:
            skills_qs = skills_qs.filter(topic__domain_id=domain_id)

        skills_summary = []
        for s in skills_qs:
            item = cls.get_integrated_skill_summary(s.id)
            if item:
                skills_summary.append(item)

        domain_progress = RoadmapProgressService.get_domain_progress(domain_id)
        level_progress = RoadmapProgressService.get_roadmap_level_progress(domain_id)

        return {
            "domain_progress": domain_progress,
            "roadmap_level_progress": level_progress,
            "total_skills": len(skills_summary),
            "skills": skills_summary,
        }

