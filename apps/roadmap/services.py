from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Union
import uuid

from django.utils import timezone
from apps.roadmap.models import Domain, Topic, Skill, RoadmapNode, RoadmapProgress

logger = logging.getLogger("brofessor")

STATUS_WEIGHTS = {
    RoadmapProgress.ProgressStatus.NOT_STARTED: 0.0,
    RoadmapProgress.ProgressStatus.IN_PROGRESS: 50.0,
    RoadmapProgress.ProgressStatus.COMPLETED: 100.0,
    RoadmapProgress.ProgressStatus.MASTERED: 100.0,
}


class RoadmapProgressService:
    """
    Calculates curriculum progression for Domain, Topic, Skill, and Roadmap levels.
    Maintains strict separation between completion workflow progress and demonstrated mastery.
    """

    @classmethod
    def get_or_create_node_progress(cls, node: RoadmapNode) -> RoadmapProgress:
        """Fetch or initialize the progress record for a RoadmapNode."""
        progress, _ = RoadmapProgress.objects.get_or_create(
            node=node,
            defaults={"status": RoadmapProgress.ProgressStatus.NOT_STARTED},
        )
        return progress

    @classmethod
    def get_skill_progress(cls, skill_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Calculate progress details for a single Skill."""
        skill = Skill.objects.filter(id=skill_id).select_related("topic", "roadmap_node").first()
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        node = getattr(skill, "roadmap_node", None)
        if not node:
            # Create node if missing
            node, _ = RoadmapNode.objects.get_or_create(
                skill=skill,
                domain=skill.topic.domain,
                topic=skill.topic,
            )

        progress = cls.get_or_create_node_progress(node)
        progress_pct = STATUS_WEIGHTS.get(progress.status, 0.0)

        return {
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "topic_id": str(skill.topic.id),
            "topic_name": skill.topic.name,
            "difficulty_level": skill.difficulty_level,
            "status": progress.status,
            "progress_percentage": progress_pct,
            "is_current": progress.is_current,
            "completed_at": progress.completed_at.isoformat() if progress.completed_at else None,
            "notes": progress.notes,
        }

    @classmethod
    def update_skill_progress(
        cls,
        skill_id: Union[str, uuid.UUID],
        status: str,
        is_current: bool = False,
        notes: str = "",
    ) -> RoadmapProgress:
        """Update progression status for a Skill."""
        skill = Skill.objects.filter(id=skill_id).select_related("topic", "roadmap_node").first()
        if not skill:
            raise ValueError(f"Skill {skill_id} not found")

        node = getattr(skill, "roadmap_node", None)
        if not node:
            node, _ = RoadmapNode.objects.get_or_create(
                skill=skill,
                domain=skill.topic.domain,
                topic=skill.topic,
            )

        progress = cls.get_or_create_node_progress(node)
        progress.status = status
        progress.is_current = is_current
        if notes:
            progress.notes = notes

        if status in (RoadmapProgress.ProgressStatus.COMPLETED, RoadmapProgress.ProgressStatus.MASTERED):
            if not progress.completed_at:
                progress.completed_at = timezone.now()
        else:
            progress.completed_at = None

        progress.save()
        return progress

    @classmethod
    def get_topic_progress(cls, topic_id: Union[str, uuid.UUID]) -> Dict[str, Any]:
        """Calculate curriculum progress across all skills in a Topic."""
        topic = Topic.objects.filter(id=topic_id).prefetch_related("skills").first()
        if not topic:
            raise ValueError(f"Topic {topic_id} not found")

        skills = list(topic.skills.all())
        if not skills:
            return {
                "topic_id": str(topic.id),
                "topic_name": topic.name,
                "total_skills": 0,
                "completed_skills": 0,
                "in_progress_skills": 0,
                "not_started_skills": 0,
                "progress_percentage": 0.0,
                "skills": [],
            }

        skill_progress_list = []
        completed_count = 0
        in_progress_count = 0
        not_started_count = 0
        total_pct = 0.0

        for skill in skills:
            sp = cls.get_skill_progress(skill.id)
            skill_progress_list.append(sp)
            st = sp["status"]
            if st in (RoadmapProgress.ProgressStatus.COMPLETED, RoadmapProgress.ProgressStatus.MASTERED):
                completed_count += 1
            elif st == RoadmapProgress.ProgressStatus.IN_PROGRESS:
                in_progress_count += 1
            else:
                not_started_count += 1

            total_pct += sp["progress_percentage"]

        avg_pct = round(total_pct / len(skills), 2)

        return {
            "topic_id": str(topic.id),
            "topic_name": topic.name,
            "total_skills": len(skills),
            "completed_skills": completed_count,
            "in_progress_skills": in_progress_count,
            "not_started_skills": not_started_count,
            "progress_percentage": avg_pct,
            "skills": skill_progress_list,
        }

    @classmethod
    def get_domain_progress(cls, domain_id: Optional[Union[str, uuid.UUID]] = None) -> Dict[str, Any]:
        """Calculate overall curriculum progress across all topics and skills in a Domain."""
        if domain_id:
            domain = Domain.objects.filter(id=domain_id).first()
        else:
            domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()

        if not domain:
            return {
                "domain_id": None,
                "domain_name": "No Active Domain",
                "total_topics": 0,
                "total_skills": 0,
                "progress_percentage": 0.0,
                "topics": [],
            }

        topics = list(domain.get_all_topics()) if hasattr(domain, "get_all_topics") else list(domain.topics.all())
        topics_data = []
        total_skills_all = 0
        completed_skills_all = 0
        weighted_progress_sum = 0.0

        for t in topics:
            tp = cls.get_topic_progress(t.id)
            topics_data.append(tp)
            total_skills_all += tp["total_skills"]
            completed_skills_all += tp["completed_skills"]
            weighted_progress_sum += (tp["progress_percentage"] * tp["total_skills"])

        overall_pct = (
            round(weighted_progress_sum / total_skills_all, 2)
            if total_skills_all > 0
            else 0.0
        )

        return {
            "domain_id": str(domain.id),
            "domain_name": domain.name,
            "total_topics": len(topics),
            "total_skills": total_skills_all,
            "completed_skills": completed_skills_all,
            "progress_percentage": overall_pct,
            "topics": topics_data,
        }

    @classmethod
    def get_roadmap_level_progress(cls, domain_id: Optional[Union[str, uuid.UUID]] = None) -> Dict[str, Any]:
        """
        Calculate progression broken down by Roadmap difficulty level:
        Beginner, Intermediate, Advanced.
        """
        skills_qs = Skill.objects.select_related("topic", "roadmap_node").all()
        if domain_id:
            from django.db.models import Q
            skills_qs = skills_qs.filter(
                Q(topic__domain_id=domain_id) | Q(topic__additional_domains__id=domain_id)
            ).distinct()

        levels = {
            "beginner": {"total": 0, "completed": 0, "in_progress": 0, "points": 0.0},
            "intermediate": {"total": 0, "completed": 0, "in_progress": 0, "points": 0.0},
            "advanced": {"total": 0, "completed": 0, "in_progress": 0, "points": 0.0},
        }

        for skill in skills_qs:
            lvl = skill.difficulty_level.lower()
            if lvl not in levels:
                levels[lvl] = {"total": 0, "completed": 0, "in_progress": 0, "points": 0.0}

            levels[lvl]["total"] += 1
            node = getattr(skill, "roadmap_node", None)
            st = node.progress.status if (node and hasattr(node, "progress")) else RoadmapProgress.ProgressStatus.NOT_STARTED

            if st in (RoadmapProgress.ProgressStatus.COMPLETED, RoadmapProgress.ProgressStatus.MASTERED):
                levels[lvl]["completed"] += 1
                levels[lvl]["points"] += 100.0
            elif st == RoadmapProgress.ProgressStatus.IN_PROGRESS:
                levels[lvl]["in_progress"] += 1
                levels[lvl]["points"] += 50.0

        breakdown = {}
        for lvl, data in levels.items():
            tot = data["total"]
            pct = round(data["points"] / tot, 2) if tot > 0 else 0.0
            breakdown[lvl] = {
                "total_skills": tot,
                "completed_skills": data["completed"],
                "in_progress_skills": data["in_progress"],
                "progress_percentage": pct,
            }

        return breakdown
