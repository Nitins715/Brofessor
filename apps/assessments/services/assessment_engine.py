from dataclasses import dataclass, field
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional, Union
import uuid
from django.utils import timezone
from django.db import transaction

from apps.assessments.models import Assessment, Question, Attempt, Answer
from apps.roadmap.models import Skill, Topic
from apps.knowledge.services import EvidenceService, PersonalKnowledgeModelService
from apps.rag.llm import BaseLLMProvider
from .generation import QuestionGenerationService
from .evaluation import AnswerEvaluationService, EvaluationResult

logger = logging.getLogger("brofessor")


@dataclass
class AttemptResultSummary:
    """Summary of a completed assessment attempt."""
    attempt_id: str
    assessment_id: str
    title: str
    skill_name: Optional[str]
    topic_name: Optional[str]
    score_percentage: float
    passed: bool
    total_points_possible: float
    total_points_awarded: float
    total_questions: int
    correct_answers_count: int
    answers: List[Dict[str, Any]]
    completed_at: str
    evidence_id: Optional[str] = None
    concept_scores: Dict[str, Any] = field(default_factory=dict)
    weak_concepts: List[str] = field(default_factory=list)
    recommended_resources: List[Dict[str, Any]] = field(default_factory=list)
    next_difficulty: Optional[str] = None
    next_skill_id: Optional[str] = None
    next_skill_name: Optional[str] = None



@dataclass
class SkillAssessmentHistory:
    """Historical assessment performance aggregated over the latest up to 3 attempts."""
    target_id: str
    target_name: str
    target_type: str  # "skill" or "topic"
    attempts_considered: int
    average_score: float
    latest_score: Optional[float]
    highest_score: Optional[float]
    passing_rate: float
    trend: str  # "improving", "declining", "consistent", "insufficient_data"
    attempts: List[Dict[str, Any]]


class AssessmentEngineService:
    """
    Central orchestration service for creating assessments, managing attempts,
    evaluating answers, and publishing structured assessment evidence.
    """

    @classmethod
    def create_assessment(
        cls,
        title: Optional[str] = None,
        skill_id: Optional[Union[str, uuid.UUID]] = None,
        topic_id: Optional[Union[str, uuid.UUID]] = None,
        difficulty_level: str = "intermediate",
        auto_generate: bool = True,
        passing_score: float = 70.0,
        time_limit_minutes: Optional[int] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> Assessment:
        """Create a new Assessment suite, optionally auto-generating 4 questions."""
        skill = Skill.objects.filter(id=skill_id).first() if skill_id else None
        topic = Topic.objects.filter(id=topic_id).first() if topic_id else (skill.topic if skill else None)

        if not title:
            target_str = skill.name if skill else (topic.name if topic else "General")
            title = f"{target_str} ({difficulty_level.capitalize()}) Assessment"

        assessment = Assessment.objects.create(
            title=title,
            skill=skill,
            topic=topic,
            difficulty_level=difficulty_level,
            passing_score=Decimal(str(round(passing_score, 2))),
            time_limit_minutes=time_limit_minutes,
            status=Assessment.AssessmentStatus.DRAFT,
        )

        if auto_generate:
            QuestionGenerationService.generate_for_assessment(
                assessment=assessment,
                llm_provider=llm_provider,
            )

        return assessment

    @classmethod
    def start_attempt(cls, assessment_id: Union[str, uuid.UUID]) -> Attempt:
        """Begin a new attempt on an active Assessment."""
        assessment = Assessment.objects.get(id=assessment_id)
        if assessment.status != Assessment.AssessmentStatus.ACTIVE:
            assessment.status = Assessment.AssessmentStatus.ACTIVE
            assessment.save(update_fields=["status"])

        attempt = Attempt.objects.create(
            assessment=assessment,
            started_at=timezone.now(),
        )
        logger.info(f"Started attempt {attempt.id} on assessment '{assessment.title}'")
        return attempt

    @classmethod
    def submit_and_evaluate_answer(
        cls,
        attempt_id: Union[str, uuid.UUID],
        question_id: Union[str, uuid.UUID],
        user_response: str,
        response_time_seconds: Optional[float] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> Answer:
        """Submit a single answer and evaluate it immediately."""
        attempt = Attempt.objects.get(id=attempt_id)
        question = Question.objects.get(id=question_id)

        # Grade the answer
        eval_res: EvaluationResult = AnswerEvaluationService.evaluate(
            question=question,
            user_response=user_response,
            llm_provider=llm_provider,
        )

        answer, _ = Answer.objects.update_or_create(
            attempt=attempt,
            question=question,
            defaults={
                "user_response": user_response,
                "response_time_seconds": response_time_seconds,
                "accuracy": eval_res.accuracy,
                "score_awarded": eval_res.score_awarded,
                "is_correct": eval_res.is_correct,
                "feedback": eval_res.feedback,
            },
        )
        return answer

    @classmethod
    def complete_attempt(
        cls,
        attempt_id: Union[str, uuid.UUID],
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> AttemptResultSummary:
        """
        Finalize an attempt:
        1. Ensures all questions in assessment have answers (or 0-score defaults).
        2. Tally total points possible and awarded.
        3. Computes score percentage and pass/fail state.
        4. Calculates concept-level scores and identifies weak concepts.
        5. Recommends curated learning resources for targeted remediation.
        6. Computes next difficulty and next skill in progression.
        7. Emits Assessment Evidence into Personal Knowledge Model.
        """
        with transaction.atomic():
            attempt = Attempt.objects.select_related("assessment", "assessment__skill", "assessment__topic").get(
                id=attempt_id
            )
            assessment = attempt.assessment
            skill = assessment.skill
            topic = assessment.topic or (skill.topic if skill else None)
            questions = list(assessment.questions.all().order_by("order"))

            # Check if any questions were unsubmitted, grade them with empty response
            existing_answers = {a.question_id: a for a in attempt.answers.all()}
            for q in questions:
                if q.id not in existing_answers:
                    cls.submit_and_evaluate_answer(
                        attempt_id=attempt.id,
                        question_id=q.id,
                        user_response="",
                        llm_provider=llm_provider,
                    )

            # Reload answers
            answers = list(attempt.answers.select_related("question").order_by("question__order"))

            total_possible = sum(Decimal(str(q.points)) for q in questions)
            total_awarded = sum(a.score_awarded for a in answers)

            percentage = (
                Decimal(str(round((float(total_awarded) / float(total_possible)) * 100, 2)))
                if total_possible > 0
                else Decimal("0.00")
            )
            passed = percentage >= assessment.passing_score

            # Concept-level breakdown & Weak Concept Detection
            concept_map: Dict[str, Dict[str, Any]] = {}
            for a in answers:
                c = (a.question.concept or "").strip() or (skill.name if skill else "General")
                if c not in concept_map:
                    concept_map[c] = {
                        "correct": 0,
                        "total": 0,
                        "points_awarded": 0.0,
                        "points_possible": 0.0,
                    }
                concept_map[c]["total"] += 1
                concept_map[c]["points_possible"] += float(a.question.points)
                concept_map[c]["points_awarded"] += float(a.score_awarded)
                if a.is_correct:
                    concept_map[c]["correct"] += 1

            weak_concepts_list = []
            for c, stats in concept_map.items():
                acc = round((stats["correct"] / stats["total"]) * 100, 1) if stats["total"] > 0 else 0.0
                stats["accuracy"] = acc
                if acc < 70.0:
                    weak_concepts_list.append(c)

            attempt.total_points_possible = total_possible
            attempt.total_points_awarded = total_awarded
            attempt.score = percentage
            attempt.passed = passed
            attempt.concept_scores = concept_map
            attempt.weak_concepts = weak_concepts_list
            attempt.completed_at = timezone.now()
            attempt.feedback = f"Scored {total_awarded}/{total_possible} ({percentage}%). Passed: {passed}"
            attempt.save()

            assessment.status = Assessment.AssessmentStatus.COMPLETED
            assessment.save(update_fields=["status"])

            # Recommended Curated Learning Resources
            recommended_resources: List[Dict[str, Any]] = []
            if skill:
                verified_mappings = list(skill.get_verified_resource_mappings())
                for m in verified_mappings:
                    recommended_resources.append({
                        "id": str(m.resource.id),
                        "title": m.resource.title,
                        "url": m.resource.url,
                        "resource_type": m.resource.resource_type,
                        "resource_type_display": m.resource.get_resource_type_display(),
                        "source": m.resource.source,
                        "is_primary": m.is_primary,
                        "description": m.resource.description or "",
                    })

            # Next Difficulty and Skill Progression
            curr_diff = (assessment.difficulty_level or "easy").lower().strip()
            next_difficulty = None
            if passed:
                if curr_diff in ("easy", "basic", "beginner"):
                    next_difficulty = "medium"
                elif curr_diff in ("medium", "intermediate"):
                    next_difficulty = "hard"
                elif curr_diff in ("hard", "advanced", "expert"):
                    next_difficulty = None

            next_skill = None
            next_skill_id = None
            next_skill_name = None
            if skill:
                domain_to_check = topic.domain if topic else None
                next_skill = skill.get_next_skill(domain=domain_to_check)
                if next_skill:
                    next_skill_id = str(next_skill.id)
                    next_skill_name = next_skill.name

            # Create Assessment Evidence for Personal Knowledge Model
            evidence = None
            if skill or topic:
                evidence = EvidenceService.record_assessment_evidence(
                    title=f"Assessment: {assessment.title}",
                    skill=skill,
                    topic=topic,
                    score=float(total_awarded),
                    max_score=float(total_possible),
                    assessment_id=str(assessment.id),
                    confidence_weight=1.00,
                    raw_data={
                        "attempt_id": str(attempt.id),
                        "score_percentage": float(percentage),
                        "passed": passed,
                        "questions_count": len(questions),
                        "correct_count": sum(1 for a in answers if a.is_correct),
                        "difficulty": curr_diff,
                        "weak_concepts": weak_concepts_list,
                    },
                )
                if skill:
                    PersonalKnowledgeModelService.recalculate_skill_mastery(skill.id)

        # Build detailed result summary
        answers_data = [
            {
                "question_id": str(a.question.id),
                "order": a.question.order,
                "question_type": a.question.question_type,
                "concept": a.question.concept,
                "prompt": a.question.prompt,
                "user_response": a.user_response,
                "response_time_seconds": a.response_time_seconds,
                "accuracy": a.accuracy,
                "points_possible": a.question.points,
                "score_awarded": float(a.score_awarded),
                "is_correct": a.is_correct,
                "feedback": a.feedback,
            }
            for a in answers
        ]

        logger.info(
            f"Attempt {attempt.id} completed: {total_awarded}/{total_possible} ({percentage}%). Passed: {passed}. Weak: {weak_concepts_list}"
        )

        return AttemptResultSummary(
            attempt_id=str(attempt.id),
            assessment_id=str(assessment.id),
            title=assessment.title,
            skill_name=skill.name if skill else None,
            topic_name=topic.name if topic else None,
            score_percentage=float(percentage),
            passed=passed,
            total_points_possible=float(total_possible),
            total_points_awarded=float(total_awarded),
            total_questions=len(questions),
            correct_answers_count=sum(1 for a in answers if a.is_correct),
            answers=answers_data,
            completed_at=attempt.completed_at.isoformat(),
            evidence_id=str(evidence.id) if evidence else None,
            concept_scores=concept_map,
            weak_concepts=weak_concepts_list,
            recommended_resources=recommended_resources,
            next_difficulty=next_difficulty,
            next_skill_id=next_skill_id,
            next_skill_name=next_skill_name,
        )

    @classmethod
    def get_skill_assessment_history(
        cls,
        skill_id: Optional[Union[str, uuid.UUID]] = None,
        topic_id: Optional[Union[str, uuid.UUID]] = None,
    ) -> SkillAssessmentHistory:
        """
        Maintain assessment history and evaluate ongoing performance using
        up to the latest 3 assessments for the relevant skill/topic.
        Uses fewer assessments when fewer exist.
        """
        attempts_qs = Attempt.objects.filter(completed_at__isnull=False)

        if skill_id:
            skill = Skill.objects.get(id=skill_id)
            target_id = str(skill.id)
            target_name = skill.name
            target_type = "skill"
            attempts_qs = attempts_qs.filter(assessment__skill=skill)
        elif topic_id:
            topic = Topic.objects.get(id=topic_id)
            target_id = str(topic.id)
            target_name = topic.name
            target_type = "topic"
            attempts_qs = attempts_qs.filter(assessment__topic=topic)
        else:
            raise ValueError("Either skill_id or topic_id must be provided.")

        # Order by newest first and take up to latest 3
        all_ordered = list(attempts_qs.order_by("-completed_at")[:3])
        count = len(all_ordered)

        if count == 0:
            return SkillAssessmentHistory(
                target_id=target_id,
                target_name=target_name,
                target_type=target_type,
                attempts_considered=0,
                average_score=0.0,
                latest_score=None,
                highest_score=None,
                passing_rate=0.0,
                trend="insufficient_data",
                attempts=[],
            )

        scores = [float(a.score) for a in all_ordered if a.score is not None]
        avg_score = round(sum(scores) / len(scores), 2) if scores else 0.0
        latest_score = scores[0] if scores else None
        highest_score = max(scores) if scores else None
        passed_count = sum(1 for a in all_ordered if a.passed)
        passing_rate = round((passed_count / count) * 100, 2)

        # Calculate trend if at least 2 attempts
        if len(scores) >= 2:
            delta = scores[0] - scores[1]
            if delta > 3.0:
                trend = "improving"
            elif delta < -3.0:
                trend = "declining"
            else:
                trend = "consistent"
        else:
            trend = "consistent"

        serialized_attempts = [
            {
                "attempt_id": str(a.id),
                "assessment_id": str(a.assessment.id),
                "assessment_title": a.assessment.title,
                "score": float(a.score) if a.score is not None else 0.0,
                "total_points_awarded": float(a.total_points_awarded),
                "total_points_possible": float(a.total_points_possible),
                "passed": a.passed,
                "completed_at": a.completed_at.isoformat(),
            }
            for a in all_ordered
        ]

        return SkillAssessmentHistory(
            target_id=target_id,
            target_name=target_name,
            target_type=target_type,
            attempts_considered=count,
            average_score=avg_score,
            latest_score=latest_score,
            highest_score=highest_score,
            passing_rate=passing_rate,
            trend=trend,
            attempts=serialized_attempts,
        )
