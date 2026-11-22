import logging
from typing import Any, Dict, List, Optional
from django.db.models import Q

from apps.assessments.models import Answer, Question, Attempt, Assessment
from apps.roadmap.models import Skill, Topic, Domain

logger = logging.getLogger("brofessor")


class KnowledgeGraphService:
    """
    Personal Performance Knowledge Graph & Question Memory Service:
    Tracks question-level mastery history from diagnostic assessments:
    1. 'Need to Learn' Queue: Questions answered incorrectly and not yet corrected.
    2. 'Mastered' Graph Nodes: Questions answered correctly.
    3. Re-testing Hook: Feeds unmastered questions back into new assessments
       for that skill before calling LLM, eliminating redundant question generation.
    """

    @classmethod
    def get_latest_answers(cls, skill_id: Optional[str] = None) -> List[Answer]:
        """
        Retrieves the latest answer for each distinct question prompt/concept.
        """
        qs = Answer.objects.filter(attempt__completed_at__isnull=False).select_related(
            "question",
            "question__assessment",
            "question__assessment__skill",
            "question__assessment__skill__topic",
            "attempt",
        ).order_by("question__prompt", "-attempt__completed_at")

        if skill_id:
            qs = qs.filter(question__assessment__skill_id=skill_id)

        seen_prompts = set()
        latest_answers = []
        for ans in qs:
            prompt_key = (ans.question.prompt.strip().lower(), str(ans.question.assessment.skill_id or ""))
            if prompt_key not in seen_prompts:
                seen_prompts.add(prompt_key)
                latest_answers.append(ans)

        return latest_answers

    @classmethod
    def get_user_knowledge_stats(cls, domain: Optional[Domain] = None) -> Dict[str, Any]:
        """
        Calculates aggregate statistics for the Knowledge Graph.
        """
        all_latest = cls.get_latest_answers()
        if domain:
            domain_topics = domain.get_all_topics()
            all_latest = [
                a for a in all_latest
                if a.question.assessment.skill and a.question.assessment.skill.topic in domain_topics
            ]

        total_tested = len(all_latest)
        mastered = [a for a in all_latest if a.is_correct is True]
        need_to_learn = [a for a in all_latest if a.is_correct is False]

        mastery_rate = round((len(mastered) / total_tested * 100), 1) if total_tested > 0 else 0.0

        return {
            "total_tested": total_tested,
            "mastered_count": len(mastered),
            "need_to_learn_count": len(need_to_learn),
            "mastery_rate": mastery_rate,
        }

    @classmethod
    def get_need_to_learn_queue(
        cls,
        skill_id: Optional[str] = None,
        domain: Optional[Domain] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Returns all questions where the user's latest answer was incorrect.
        """
        latest_answers = cls.get_latest_answers(skill_id=skill_id)
        if domain:
            domain_topics = domain.get_all_topics()
            latest_answers = [
                a for a in latest_answers
                if a.question.assessment.skill and a.question.assessment.skill.topic in domain_topics
            ]

        incorrect_answers = [a for a in latest_answers if a.is_correct is False]

        items = []
        for ans in incorrect_answers[:limit]:
            q = ans.question
            skill = q.assessment.skill
            topic = skill.topic if skill else None

            explanation = ""
            if isinstance(q.distractor_explanations, dict) and ans.user_response in q.distractor_explanations:
                explanation = q.distractor_explanations[ans.user_response]
            elif isinstance(q.rubric, dict):
                explanation = q.rubric.get("explanation", "")

            attempt_count = Answer.objects.filter(
                question__prompt=q.prompt,
                attempt__completed_at__isnull=False,
            ).count()

            items.append({
                "question_id": str(q.id),
                "prompt": q.prompt,
                "concept": q.concept or (skill.name if skill else "General Concept"),
                "skill_id": str(skill.id) if skill else None,
                "skill_name": skill.name if skill else "General",
                "topic_name": topic.name if topic else "General",
                "difficulty_level": q.difficulty_level,
                "user_response": ans.user_response,
                "correct_answer": q.correct_answer,
                "options": q.options,
                "feedback": ans.feedback or explanation or "Review key concept and test again.",
                "attempt_count": attempt_count,
                "failed_at": ans.attempt.completed_at,
            })

        return items

    @classmethod
    def get_mastered_nodes(
        cls,
        skill_id: Optional[str] = None,
        domain: Optional[Domain] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """
        Returns all questions where the user's latest answer was correct.
        """
        latest_answers = cls.get_latest_answers(skill_id=skill_id)
        if domain:
            domain_topics = domain.get_all_topics()
            latest_answers = [
                a for a in latest_answers
                if a.question.assessment.skill and a.question.assessment.skill.topic in domain_topics
            ]

        correct_answers = [a for a in latest_answers if a.is_correct is True]

        items = []
        for ans in correct_answers[:limit]:
            q = ans.question
            skill = q.assessment.skill
            topic = skill.topic if skill else None

            items.append({
                "question_id": str(q.id),
                "prompt": q.prompt,
                "concept": q.concept or (skill.name if skill else "General Concept"),
                "skill_id": str(skill.id) if skill else None,
                "skill_name": skill.name if skill else "General",
                "topic_name": topic.name if topic else "General",
                "difficulty_level": q.difficulty_level,
                "user_response": ans.user_response,
                "correct_answer": q.correct_answer,
                "response_time_seconds": ans.response_time_seconds or 0.0,
                "mastered_at": ans.attempt.completed_at,
            })

        return items

    @classmethod
    def get_unmastered_questions_for_skill(cls, skill: Skill, limit: int = 5) -> List[Question]:
        """
        Returns Question objects that the user previously answered incorrectly on this skill
        and has not yet answered correctly. Used by the assessment generator to re-test
        weak areas before generating new questions.
        """
        if not skill:
            return []
        latest = cls.get_latest_answers(skill_id=str(skill.id))
        unmastered = [a.question for a in latest if a.is_correct is False]
        return unmastered[:limit]

    TRACK_PALETTES = {
        "swe_foundations": {
            "name": "Software Engineering Foundations",
            "bg": "#eff6ff",
            "border": "#3b82f6",
            "dark_bg": "#1e3a8a",
            "dark_border": "#60a5fa",
            "text": "#1e40af",
        },
        "ai_engineer": {
            "name": "AI Engineer",
            "bg": "#ecfdf5",
            "border": "#10b981",
            "dark_bg": "#064e3b",
            "dark_border": "#34d399",
            "text": "#065f46",
        },
        "agentic_ai": {
            "name": "Agentic AI Engineer",
            "bg": "#f5f3ff",
            "border": "#8b5cf6",
            "dark_bg": "#4c1d95",
            "dark_border": "#a78bfa",
            "text": "#5b21b6",
        },
        "mlops": {
            "name": "MLOps & LLMOps",
            "bg": "#fffbeb",
            "border": "#f59e0b",
            "dark_bg": "#78350f",
            "dark_border": "#fbbf24",
            "text": "#92400e",
        },
        "fde": {
            "name": "Forward Deployed AI",
            "bg": "#fff1f2",
            "border": "#f43f5e",
            "dark_bg": "#881337",
            "dark_border": "#fb7185",
            "text": "#9f1239",
        },
    }

    @classmethod
    def get_visual_graph_data(
        cls,
        domain: Optional[Domain] = None,
        track: Optional[str] = None,
        mode: str = "curriculum",
    ) -> Dict[str, Any]:
        """
        Builds graph payload (nodes and edges) formatted for Vis.js Network visualization.
        Modes:
        - 'curriculum': Prerequisite DAG across Skills and Topics color-coded by Track.
        - 'library': Knowledge Graph entities and semantic relationships extracted from sources.
        """
        if mode == "library":
            return cls._build_library_graph_data()
        return cls._build_curriculum_graph_data(domain=domain, track=track)

    @classmethod
    def _build_curriculum_graph_data(
        cls,
        domain: Optional[Domain] = None,
        track: Optional[str] = None,
    ) -> Dict[str, Any]:
        from apps.knowledge.models import CalculatedMastery

        skills_qs = Skill.objects.select_related("topic", "topic__domain").prefetch_related(
            "prerequisites",
            "prerequisites__topic",
            "downstream_skills",
            "downstream_skills__topic",
            "learning_resources",
            "assessments",
        )

        if domain:
            domain_topics = domain.get_all_topics()
            skills_qs = skills_qs.filter(topic__in=domain_topics)

        if track and track != "all":
            skills_qs = skills_qs.filter(topic__track=track)

        skills = list(skills_qs)
        included_ids = {str(s.id) for s in skills}

        masteries = {
            m.skill_id: m
            for m in CalculatedMastery.objects.filter(skill_id__in=[s.id for s in skills])
        }

        nodes = []
        edges = []
        mastered_count = 0

        for skill in skills:
            m = masteries.get(skill.id)
            score = float(m.mastery_score) if m else 0.0
            level = m.mastery_level if m else "unrated"
            if score >= 70.0 or level in ["expert", "advanced"]:
                mastered_count += 1

            track_code = skill.topic.track or "swe_foundations"
            palette = cls.TRACK_PALETTES.get(track_code, cls.TRACK_PALETTES["swe_foundations"])

            is_mastered = score >= 70.0 or level in ["expert", "advanced"]
            border_color = "#10b981" if is_mastered else palette["border"]
            border_width = 3 if is_mastered else (2 if level == "intermediate" else 1.5)

            prereq_items = [
                {"id": str(p.id), "name": p.name, "topic": p.topic.name}
                for p in skill.prerequisites.all()
            ]
            downstream_items = [
                {"id": str(d.id), "name": d.name, "topic": d.topic.name}
                for d in skill.downstream_skills.all()
            ]
            resource_items = [
                {
                    "title": r.title,
                    "url": r.url,
                    "resource_type": r.resource_type,
                    "source": getattr(r, "source", ""),
                }
                for r in skill.learning_resources.all()[:4]
            ]
            active_assessment = skill.assessments.filter(is_active=True).first()

            tooltip = (
                f"<b>{skill.name}</b><br/>"
                f"Topic: {skill.topic.name}<br/>"
                f"Track: {palette['name']}<br/>"
                f"Mastery: {score:.0f}% ({level.capitalize()})<br/>"
                f"Prerequisites: {len(prereq_items)} | Unlocks: {len(downstream_items)}"
            )

            nodes.append({
                "id": str(skill.id),
                "label": skill.name,
                "group": track_code,
                "track": track_code,
                "track_label": palette["name"],
                "topic": skill.topic.name,
                "difficulty": getattr(skill, "difficulty_level", "intermediate"),
                "mastery_score": score,
                "mastery_level": level,
                "shape": "box",
                "shapeProperties": {"borderRadius": 8},
                "margin": 10,
                "color": {
                    "background": palette["bg"],
                    "border": border_color,
                    "highlight": {
                        "background": "#ffffff",
                        "border": "#4f46e5",
                    },
                },
                "borderWidth": border_width,
                "font": {
                    "size": 12,
                    "color": "#0f172a",
                    "face": "Inter, system-ui, sans-serif",
                    "bold": is_mastered,
                },
                "title": tooltip,
                "details": {
                    "id": str(skill.id),
                    "name": skill.name,
                    "slug": skill.slug,
                    "topic": skill.topic.name,
                    "track": track_code,
                    "track_label": palette["name"],
                    "difficulty": getattr(skill, "difficulty_level", "intermediate"),
                    "description": skill.description or "",
                    "mastery_score": score,
                    "mastery_level": level,
                    "prerequisites": prereq_items,
                    "downstream": downstream_items,
                    "resources": resource_items,
                    "assessment_id": str(active_assessment.id) if active_assessment else None,
                },
            })

            for prereq in skill.prerequisites.all():
                if str(prereq.id) in included_ids:
                    edges.append({
                        "id": f"{prereq.id}->{skill.id}",
                        "from": str(prereq.id),
                        "to": str(skill.id),
                        "arrows": "to",
                        "color": {
                            "color": "#94a3b8",
                            "highlight": "#6366f1",
                            "hover": "#4f46e5",
                        },
                        "width": 1.5,
                        "smooth": {
                            "type": "cubicBezier",
                            "forceDirection": "horizontal",
                            "roundness": 0.35,
                        },
                    })

        return {
            "mode": "curriculum",
            "track": track or "all",
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "mastered_count": mastered_count,
                "tracks_count": len(cls.TRACK_PALETTES),
            },
            "tracks": [
                {"id": k, "label": v["name"], "color": v["border"]}
                for k, v in cls.TRACK_PALETTES.items()
            ],
            "nodes": nodes,
            "edges": edges,
        }

    @classmethod
    def _build_library_graph_data(cls) -> Dict[str, Any]:
        from apps.sources.models import Entity, Relationship

        ENTITY_COLORS = {
            "concept": {"bg": "#ecfdf5", "border": "#10b981", "label": "Concept"},
            "algorithm": {"bg": "#ecfeff", "border": "#06b6d4", "label": "Algorithm"},
            "technology": {"bg": "#eff6ff", "border": "#3b82f6", "label": "Technology"},
            "framework": {"bg": "#f5f3ff", "border": "#8b5cf6", "label": "Framework"},
            "architecture": {"bg": "#fffbeb", "border": "#f59e0b", "label": "Architecture"},
            "other": {"bg": "#f8fafc", "border": "#64748b", "label": "Other"},
        }

        entities = list(Entity.objects.prefetch_related("chunk_mappings")[:250])
        relationships = list(
            Relationship.objects.filter(
                source_entity__in=entities,
                target_entity__in=entities,
            ).select_related("source_entity", "target_entity")
        )

        nodes = []
        edges = []

        for e in entities:
            color_info = ENTITY_COLORS.get(e.entity_type, ENTITY_COLORS["other"])
            chunks_count = e.chunk_mappings.count()

            nodes.append({
                "id": str(e.id),
                "label": e.name,
                "group": e.entity_type,
                "entity_type": e.entity_type,
                "entity_type_label": color_info["label"],
                "shape": "ellipse",
                "color": {
                    "background": color_info["bg"],
                    "border": color_info["border"],
                    "highlight": {"background": "#ffffff", "border": "#6366f1"},
                },
                "borderWidth": 2,
                "font": {"size": 11, "color": "#0f172a"},
                "title": f"<b>{e.name}</b><br/>Type: {color_info['label']}<br/>References: {chunks_count} chunks",
                "details": {
                    "id": str(e.id),
                    "name": e.name,
                    "entity_type": e.entity_type,
                    "entity_type_label": color_info["label"],
                    "description": e.description or "Concept extracted from knowledge sources.",
                    "chunks_count": chunks_count,
                },
            })

        for r in relationships:
            edges.append({
                "id": str(r.id),
                "from": str(r.source_entity_id),
                "to": str(r.target_entity_id),
                "label": r.relation_type,
                "arrows": "to",
                "font": {"size": 9, "color": "#64748b", "align": "middle"},
                "color": {"color": "#cbd5e1", "highlight": "#6366f1"},
                "width": 1.5,
            })

        return {
            "mode": "library",
            "track": "all",
            "summary": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "mastered_count": 0,
                "tracks_count": len(ENTITY_COLORS),
            },
            "tracks": [
                {"id": k, "label": v["label"], "color": v["border"]}
                for k, v in ENTITY_COLORS.items()
            ],
            "nodes": nodes,
            "edges": edges,
        }
