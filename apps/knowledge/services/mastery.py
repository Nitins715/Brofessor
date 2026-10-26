from dataclasses import dataclass
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from django.db.models import Avg
from apps.knowledge.models import CalculatedMastery, Evidence, MasteryLevel
from apps.roadmap.models import Skill, Topic
from apps.assessments.models import Attempt

logger = logging.getLogger("brofessor")


@dataclass
class MasteryScoringConfig:
    """
    Configurable contribution weights, scoring caps, and mastery level thresholds.
    Allows empirical scoring formulas to be updated without code rewrites.
    """
    # Maximum points contributed by each evidence modality towards 100-point mastery score
    learning_weight: float = 30.0     # Material exposure, readings, notes
    declared_weight: float = 15.0     # Self-declared competence / self-ratings
    practical_weight: float = 35.0    # Real-world implementations, projects, commits
    assessment_weight: float = 20.0   # Formal assessments / quiz verifications

    # Points granted per evidence item until weight cap is reached
    pts_per_learning_item: float = 10.0
    pts_per_declared_item: float = 7.5
    pts_per_practical_item: float = 17.5

    # Mastery Level Thresholds (0.0 to 100.0 scale)
    beginner_max: float = 39.99
    intermediate_min: float = 40.0
    intermediate_max: float = 69.99
    advanced_min: float = 70.0
    advanced_max: float = 89.99
    expert_min: float = 90.0

    # Assessment window & thresholds
    max_assessment_history: int = 3
    weak_assessment_threshold: float = 60.0
    weak_coverage_threshold: float = 40.0


DEFAULT_MASTERY_CONFIG = MasteryScoringConfig()


class MasteryEngineService:
    """
    Computes multi-modal knowledge contribution, knowledge coverage,
    and 4-tier mastery levels based on accumulated evidence and recent assessments.
    """

    @classmethod
    def determine_mastery_level(cls, score: float, config: Optional[MasteryScoringConfig] = None) -> str:
        """Map numeric score (0-100) to one of the 4 mastery levels: Beginner, Intermediate, Advanced, Expert."""
        cfg = config or DEFAULT_MASTERY_CONFIG
        if score >= cfg.expert_min:
            return MasteryLevel.EXPERT
        elif score >= cfg.advanced_min:
            return MasteryLevel.ADVANCED
        elif score >= cfg.intermediate_min:
            return MasteryLevel.INTERMEDIATE
        return MasteryLevel.BEGINNER

    @classmethod
    def calculate_knowledge_coverage(
        cls,
        skill: Skill,
        evidence_items: List[Evidence],
    ) -> float:
        """
        Calculate knowledge coverage percentage (0.0 to 100.0) reflecting:
        1. Modality diversity (up to 60 pts: 15 pts per active modality)
        2. Concept coverage (up to 25 pts: ratio of skill's concepts with evidence)
        3. Evidence density (up to 15 pts: item volume capped at 5)
        """
        if not evidence_items:
            return 0.0

        modalities = {e.evidence_type for e in evidence_items}
        modality_score = min(60.0, len(modalities) * 15.0)

        # Concept coverage
        skill_concepts = list(skill.concepts.all())
        if skill_concepts:
            covered_concept_ids = {e.concept_id for e in evidence_items if e.concept_id}
            concept_ratio = len(covered_concept_ids.intersection({c.id for c in skill_concepts})) / len(skill_concepts)
            concept_score = min(25.0, concept_ratio * 25.0)
        else:
            concept_score = 15.0 if len(evidence_items) >= 2 else 10.0

        density_score = min(15.0, (len(evidence_items) / 5.0) * 15.0)
        total_coverage = round(min(100.0, modality_score + concept_score + density_score), 2)
        return total_coverage

    @classmethod
    def get_latest_assessments_for_skill(
        cls,
        skill: Skill,
        max_history: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve up to the latest 3 assessment results for the skill.
        Prioritizes completed Attempt models, with fallback to Evidence records.
        """
        attempts = (
            Attempt.objects.filter(assessment__skill=skill, completed_at__isnull=False)
            .select_related("assessment")
            .order_by("-completed_at")[:max_history]
        )

        results = []
        for att in attempts:
            results.append({
                "attempt_id": str(att.id),
                "assessment_id": str(att.assessment.id),
                "assessment_title": att.assessment.title,
                "score_pct": float(att.score) if att.score is not None else 0.0,
                "completed_at": att.completed_at.isoformat() if att.completed_at else None,
                "passed": att.passed,
            })

        if not results:
            # Fallback to Evidence records of type assessment
            assessment_evs = Evidence.objects.filter(
                skill=skill,
                evidence_type=Evidence.EvidenceType.ASSESSMENT,
            ).order_by("-recorded_at")[:max_history]

            for ev in assessment_evs:
                pct = float(ev.raw_data.get("percentage", 100.0 * float(ev.confidence_weight)))
                results.append({
                    "attempt_id": str(ev.raw_data.get("attempt_id", ev.id)),
                    "assessment_id": str(ev.raw_data.get("assessment_id", "")),
                    "assessment_title": ev.title,
                    "score_pct": pct,
                    "completed_at": ev.recorded_at.isoformat() if ev.recorded_at else None,
                    "passed": pct >= 70.0,
                })

        return results

    @classmethod
    def recalculate_skill_mastery(
        cls,
        skill_id: Union[str, uuid.UUID],
        config: Optional[MasteryScoringConfig] = None,
    ) -> CalculatedMastery:
        """
        Recalculate knowledge score, coverage, confidence, and 4-tier mastery level for a Skill.
        Uses accumulated evidence and up to latest 3 assessments.
        """
        cfg = config or DEFAULT_MASTERY_CONFIG
        skill = Skill.objects.filter(id=skill_id).select_related("topic").first()
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        evidence_items = list(Evidence.objects.filter(skill=skill).order_by("-recorded_at"))

        counts = {
            Evidence.EvidenceType.LEARNING: 0,
            Evidence.EvidenceType.DECLARED: 0,
            Evidence.EvidenceType.PRACTICAL: 0,
            Evidence.EvidenceType.ASSESSMENT: 0,
        }
        for ev in evidence_items:
            counts[ev.evidence_type] = counts.get(ev.evidence_type, 0) + 1

        # 1. Modality contributions
        learning_pts = min(cfg.learning_weight, counts[Evidence.EvidenceType.LEARNING] * cfg.pts_per_learning_item)
        declared_pts = min(cfg.declared_weight, counts[Evidence.EvidenceType.DECLARED] * cfg.pts_per_declared_item)
        practical_pts = min(cfg.practical_weight, counts[Evidence.EvidenceType.PRACTICAL] * cfg.pts_per_practical_item)

        # 2. Assessment influence (up to latest 3 assessments)
        recent_assessments = cls.get_latest_assessments_for_skill(skill, max_history=cfg.max_assessment_history)
        if recent_assessments:
            avg_assessment_pct = sum(a["score_pct"] for a in recent_assessments) / len(recent_assessments)
            assessment_pts = min(cfg.assessment_weight, (avg_assessment_pct / 100.0) * cfg.assessment_weight)
        else:
            avg_assessment_pct = 0.0
            assessment_pts = 0.0

        # Total mastery score
        total_score = round(min(100.0, learning_pts + declared_pts + practical_pts + assessment_pts), 2)
        mastery_level = cls.determine_mastery_level(total_score, cfg)
        coverage_score = cls.calculate_knowledge_coverage(skill, evidence_items)

        # Confidence: evidence volume + modality diversity
        active_modalities = sum(1 for c in counts.values() if c > 0)
        volume_factor = min(1.0, len(evidence_items) / 5.0)
        diversity_factor = active_modalities / 4.0
        confidence = round((volume_factor * 0.5) + (diversity_factor * 0.5), 2)

        mastery_obj, _ = CalculatedMastery.objects.update_or_create(
            skill=skill,
            defaults={
                "mastery_score": Decimal(str(total_score)),
                "mastery_level": mastery_level,
                "knowledge_coverage": Decimal(str(coverage_score)),
                "confidence_score": Decimal(str(confidence)),
                "evidence_count": len(evidence_items),
                "calculation_metadata": {
                    "breakdown": counts,
                    "learning_pts": learning_pts,
                    "declared_pts": declared_pts,
                    "practical_pts": practical_pts,
                    "assessment_pts": round(assessment_pts, 2),
                    "avg_assessment_pct": round(avg_assessment_pct, 2),
                    "recent_assessments_count": len(recent_assessments),
                    "recent_assessments": recent_assessments,
                    "modalities_covered": active_modalities,
                    "algorithm": "v1_multi_modal_mastery",
                    "config": {
                        "learning_weight": cfg.learning_weight,
                        "declared_weight": cfg.declared_weight,
                        "practical_weight": cfg.practical_weight,
                        "assessment_weight": cfg.assessment_weight,
                        "thresholds": {
                            "beginner_max": cfg.beginner_max,
                            "intermediate_min": cfg.intermediate_min,
                            "advanced_min": cfg.advanced_min,
                            "expert_min": cfg.expert_min,
                        },
                    },
                },
            },
        )

        logger.info(
            f"Calculated mastery for Skill '{skill.name}': {mastery_obj.mastery_score}% [{mastery_obj.mastery_level}] "
            f"(Coverage: {mastery_obj.knowledge_coverage}%, Assessments: {len(recent_assessments)})"
        )
        return mastery_obj

    @classmethod
    def recalculate_topic_mastery(
        cls,
        topic_id: Union[str, uuid.UUID],
        config: Optional[MasteryScoringConfig] = None,
    ) -> CalculatedMastery:
        """
        Aggregate and persist mastery and knowledge coverage across all skills under a Topic.
        """
        cfg = config or DEFAULT_MASTERY_CONFIG
        topic = Topic.objects.filter(id=topic_id).prefetch_related("skills").first()
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        skills = list(topic.skills.all())
        if not skills:
            mastery_obj, _ = CalculatedMastery.objects.update_or_create(
                topic=topic,
                skill=None,
                concept=None,
                defaults={
                    "mastery_score": Decimal("0.00"),
                    "mastery_level": MasteryLevel.BEGINNER,
                    "knowledge_coverage": Decimal("0.00"),
                    "confidence_score": Decimal("0.00"),
                    "evidence_count": 0,
                    "calculation_metadata": {"skills_count": 0},
                },
            )
            return mastery_obj

        # Calculate or load mastery for each skill
        skill_scores = []
        skill_coverages = []
        skill_confidences = []
        total_ev_count = 0

        for skill in skills:
            sm = CalculatedMastery.objects.filter(skill=skill).first()
            if not sm:
                sm = cls.recalculate_skill_mastery(skill.id, cfg)
            skill_scores.append(float(sm.mastery_score))
            skill_coverages.append(float(sm.knowledge_coverage))
            skill_confidences.append(float(sm.confidence_score))
            total_ev_count += sm.evidence_count

        avg_score = round(sum(skill_scores) / len(skill_scores), 2)
        avg_coverage = round(sum(skill_coverages) / len(skill_coverages), 2)
        avg_confidence = round(sum(skill_confidences) / len(skill_confidences), 2)
        mastery_level = cls.determine_mastery_level(avg_score, cfg)

        mastery_obj, _ = CalculatedMastery.objects.update_or_create(
            topic=topic,
            skill=None,
            concept=None,
            defaults={
                "mastery_score": Decimal(str(avg_score)),
                "mastery_level": mastery_level,
                "knowledge_coverage": Decimal(str(avg_coverage)),
                "confidence_score": Decimal(str(avg_confidence)),
                "evidence_count": total_ev_count,
                "calculation_metadata": {
                    "skills_count": len(skills),
                    "skills_summary": [
                        {"skill_id": str(s.id), "name": s.name, "score": skill_scores[idx]}
                        for idx, s in enumerate(skills)
                    ],
                },
            },
        )
        return mastery_obj
