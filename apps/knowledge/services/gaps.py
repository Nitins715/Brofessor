from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from django.utils import timezone
from apps.knowledge.models import CalculatedMastery, KnowledgeGap, MasteryLevel
from apps.roadmap.models import Skill, Topic
from .mastery import MasteryEngineService, MasteryScoringConfig, DEFAULT_MASTERY_CONFIG

logger = logging.getLogger("brofessor")

DIFFICULTY_RANK = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
}

MASTERY_RANK = {
    MasteryLevel.BEGINNER: 1,
    MasteryLevel.INTERMEDIATE: 2,
    MasteryLevel.ADVANCED: 3,
    MasteryLevel.EXPERT: 4,
}


class KnowledgeGapService:
    """
    Identifies, updates, and tracks gaps between Required Roadmap Skills
    and User Demonstrated Knowledge.
    """

    @classmethod
    def evaluate_skill_gaps(
        cls,
        skill: Skill,
        config: Optional[MasteryScoringConfig] = None,
        refresh_mastery: bool = True,
    ) -> List[KnowledgeGap]:
        """
        Evaluate and persist knowledge gaps for a single Skill.
        Resolves outdated gaps if performance or coverage has improved.
        """
        cfg = config or DEFAULT_MASTERY_CONFIG
        if refresh_mastery:
            mastery = MasteryEngineService.recalculate_skill_mastery(skill.id, cfg)
        else:
            mastery = CalculatedMastery.objects.filter(skill=skill).first() or MasteryEngineService.recalculate_skill_mastery(skill.id, cfg)


        score = float(mastery.mastery_score)
        coverage = float(mastery.knowledge_coverage)
        evidence_count = mastery.evidence_count
        metadata = mastery.calculation_metadata or {}
        recent_assessments = metadata.get("recent_assessments", [])
        avg_assessment_pct = metadata.get("avg_assessment_pct", 0.0)

        active_gaps: List[Dict[str, Any]] = []

        # 1. No evidence gap
        if evidence_count == 0:
            if skill.difficulty_level == "advanced":
                severity = KnowledgeGap.Severity.CRITICAL
            elif skill.difficulty_level == "intermediate":
                severity = KnowledgeGap.Severity.HIGH
            else:
                severity = KnowledgeGap.Severity.MEDIUM

            active_gaps.append({
                "gap_type": KnowledgeGap.GapType.NO_EVIDENCE,
                "severity": severity,
                "title": f"No evidence recorded for {skill.name}",
                "description": f"Skill '{skill.name}' in topic '{skill.topic.name}' has no learning, practical, or assessment evidence.",
                "expected_level": skill.difficulty_level,
                "current_level": mastery.mastery_level,
                "current_score": Decimal("0.00"),
                "target_score": Decimal("70.00"),
            })

        # 2. Weak coverage gap
        elif coverage < cfg.weak_coverage_threshold:
            severity = (
                KnowledgeGap.Severity.HIGH
                if skill.difficulty_level == "advanced"
                else KnowledgeGap.Severity.MEDIUM
            )
            active_gaps.append({
                "gap_type": KnowledgeGap.GapType.WEAK_COVERAGE,
                "severity": severity,
                "title": f"Weak knowledge coverage for {skill.name}",
                "description": (
                    f"Demonstrated coverage for '{skill.name}' is only {coverage}%. "
                    f"Broader modalities (e.g. practical implementations or tests) are required."
                ),
                "expected_level": skill.difficulty_level,
                "current_level": mastery.mastery_level,
                "current_score": Decimal(str(coverage)),
                "target_score": Decimal(str(cfg.weak_coverage_threshold)),
            })

        # 3. Weak assessment performance gap
        if recent_assessments and avg_assessment_pct < cfg.weak_assessment_threshold:
            severity = (
                KnowledgeGap.Severity.HIGH
                if avg_assessment_pct < 40.0
                else KnowledgeGap.Severity.MEDIUM
            )
            active_gaps.append({
                "gap_type": KnowledgeGap.GapType.WEAK_ASSESSMENT,
                "severity": severity,
                "title": f"Weak assessment scores on {skill.name}",
                "description": (
                    f"Latest assessment average for '{skill.name}' is {avg_assessment_pct}%, "
                    f"which falls below the target threshold of {cfg.weak_assessment_threshold}%."
                ),
                "expected_level": skill.difficulty_level,
                "current_level": mastery.mastery_level,
                "current_score": Decimal(str(avg_assessment_pct)),
                "target_score": Decimal(str(cfg.weak_assessment_threshold)),
            })

        # 4. Mastery below expected roadmap level
        skill_rank = DIFFICULTY_RANK.get(skill.difficulty_level, 1)
        user_rank = MASTERY_RANK.get(mastery.mastery_level, 1)
        if skill_rank > user_rank and evidence_count > 0:
            rank_delta = skill_rank - user_rank
            severity = KnowledgeGap.Severity.HIGH if rank_delta >= 2 else KnowledgeGap.Severity.MEDIUM
            active_gaps.append({
                "gap_type": KnowledgeGap.GapType.BELOW_ROADMAP_LEVEL,
                "severity": severity,
                "title": f"{skill.name} mastery below roadmap target ({skill.difficulty_level})",
                "description": (
                    f"Expected roadmap level is '{skill.difficulty_level}', but current demonstrated "
                    f"mastery is '{mastery.mastery_level}' (Score: {score}%)."
                ),
                "expected_level": skill.difficulty_level,
                "current_level": mastery.mastery_level,
                "current_score": Decimal(str(score)),
                "target_score": Decimal("70.00" if skill.difficulty_level != "advanced" else "85.00"),
            })

        # Synchronize database records: resolve old gaps not in active_gaps
        active_types = {g["gap_type"] for g in active_gaps}
        KnowledgeGap.objects.filter(
            skill=skill,
            status=KnowledgeGap.Status.ACTIVE,
        ).exclude(gap_type__in=active_types).update(
            status=KnowledgeGap.Status.RESOLVED,
            resolved_at=timezone.now(),
        )

        persisted_gaps = []
        for g_data in active_gaps:
            gap_obj, _ = KnowledgeGap.objects.update_or_create(
                skill=skill,
                gap_type=g_data["gap_type"],
                status=KnowledgeGap.Status.ACTIVE,
                defaults={
                    "topic": skill.topic,
                    "severity": g_data["severity"],
                    "title": g_data["title"],
                    "description": g_data["description"],
                    "expected_level": g_data["expected_level"],
                    "current_level": g_data["current_level"],
                    "current_score": g_data["current_score"],
                    "target_score": g_data["target_score"],
                    "metadata": {
                        "evaluated_at": timezone.now().isoformat(),
                        "mastery_score": score,
                        "coverage": coverage,
                    },
                },
            )
            persisted_gaps.append(gap_obj)

        return persisted_gaps

    @classmethod
    def evaluate_all_gaps(cls, topic_id: Optional[Union[str, uuid.UUID]] = None) -> List[KnowledgeGap]:
        """Scan all roadmap skills (or skills under a Topic) and regenerate active gaps."""
        qs = Skill.objects.select_related("topic").all()
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        all_gaps = []
        for skill in qs:
            gaps = cls.evaluate_skill_gaps(skill)
            all_gaps.extend(gaps)

        return all_gaps
