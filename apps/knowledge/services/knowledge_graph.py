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
