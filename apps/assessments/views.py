import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter

from apps.roadmap.models import Skill, Topic
from apps.assessments.models import Assessment, Question, Attempt, Answer
from .serializers import (
    AssessmentSerializer,
    CreateAssessmentRequestSerializer,
    QuestionSerializer,
    QuestionReviewSerializer,
    SubmitAnswerRequestSerializer,
    AnswerResponseSerializer,
    AttemptSerializer,
    AttemptResultSerializer,
    SkillAssessmentHistorySerializer,
    SkillNextQuestionRequestSerializer,
)
from .services import (
    AssessmentEngineService,
    QuestionGenerationService,
    SequentialQuestionGenerationService,
    AssessmentProviderResolver,
    AssessmentProviderError,
    ProviderNotConfiguredError,
    ProviderUnavailableError,
    ConcurrentGenerationError,
)

logger = logging.getLogger("brofessor")


class AssessmentsIndexView(APIView):
    """Overview endpoint for Assessment & Scoring Engine module."""
    @extend_schema(summary="Assessments Module Overview")
    def get(self, request):
        return Response({
            "module": "assessments",
            "status": "ready",
            "endpoints": {
                "assessments": request.build_absolute_uri("assessments/"),
                "history": request.build_absolute_uri("history/"),
            },
        })


class AssessmentListCreateView(APIView):
    """List assessments or create a new assessment suite for a skill/topic."""

    @extend_schema(
        summary="List Assessments",
        responses={200: AssessmentSerializer(many=True)},
    )
    def get(self, request):
        qs = Assessment.objects.all().select_related("skill", "topic").order_by("-created_at")

        skill_id = request.query_params.get("skill_id")
        if skill_id:
            qs = qs.filter(skill_id=skill_id)

        topic_id = request.query_params.get("topic_id")
        if topic_id:
            qs = qs.filter(topic_id=topic_id)

        status_param = request.query_params.get("status")
        if status_param:
            qs = qs.filter(status=status_param.lower())

        serializer = AssessmentSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        summary="Create Assessment",
        request=CreateAssessmentRequestSerializer,
        responses={201: AssessmentSerializer},
    )
    def post(self, request):
        serializer = CreateAssessmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        assessment = AssessmentEngineService.create_assessment(
            title=data.get("title"),
            skill_id=data.get("skill_id"),
            topic_id=data.get("topic_id"),
            difficulty_level=data.get("difficulty_level", "easy"),
            auto_generate=data.get("auto_generate", False),
            passing_score=data.get("passing_score", 70.0),
            time_limit_minutes=data.get("time_limit_minutes"),
        )
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_201_CREATED)


class AssessmentDetailView(APIView):
    """View details of a specific Assessment."""

    @extend_schema(summary="Assessment Details", responses={200: AssessmentSerializer})
    def get(self, request, pk):
        assessment = Assessment.objects.filter(id=pk).select_related("skill", "topic").first()
        if not assessment:
            raise NotFound(detail=f"Assessment {pk} not found")
        return Response(AssessmentSerializer(assessment).data, status=status.HTTP_200_OK)


class AssessmentQuestionsView(APIView):
    """Retrieve questions for an assessment or trigger legacy batch generation."""

    @extend_schema(summary="Get Assessment Questions", responses={200: QuestionSerializer(many=True)})
    def get(self, request, pk):
        assessment = Assessment.objects.filter(id=pk).first()
        if not assessment:
            raise NotFound(detail=f"Assessment {pk} not found")

        questions = assessment.questions.all().order_by("order")
        include_answers = request.query_params.get("review") == "true"
        serializer_class = QuestionReviewSerializer if include_answers else QuestionSerializer
        return Response(serializer_class(questions, many=True).data, status=status.HTTP_200_OK)

    @extend_schema(summary="Generate Questions Batch", responses={200: QuestionSerializer(many=True)})
    def post(self, request, pk):
        assessment = Assessment.objects.filter(id=pk).first()
        if not assessment:
            raise NotFound(detail=f"Assessment {pk} not found")

        questions = QuestionGenerationService.generate_for_assessment(assessment)
        return Response(QuestionSerializer(questions, many=True).data, status=status.HTTP_200_OK)


class StartAttemptView(APIView):
    """Begin an attempt on an Assessment."""

    @extend_schema(summary="Start Assessment Attempt", responses={201: AttemptSerializer})
    def post(self, request, pk):
        assessment = Assessment.objects.filter(id=pk).first()
        if not assessment:
            raise NotFound(detail=f"Assessment {pk} not found")

        attempt = AssessmentEngineService.start_attempt(assessment_id=pk)
        return Response(AttemptSerializer(attempt).data, status=status.HTTP_201_CREATED)


class SubmitAnswerView(APIView):
    """Submit an answer to a question during an attempt and receive immediate evaluation."""

    @extend_schema(
        summary="Submit & Evaluate Answer",
        request=SubmitAnswerRequestSerializer,
        responses={200: AnswerResponseSerializer},
    )
    def post(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id).first()
        if not attempt:
            raise NotFound(detail=f"Attempt {attempt_id} not found")

        serializer = SubmitAnswerRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        answer = AssessmentEngineService.submit_and_evaluate_answer(
            attempt_id=attempt_id,
            question_id=data["question_id"],
            user_response=data["user_response"],
            response_time_seconds=data.get("response_time_seconds"),
        )

        resp_data = AnswerResponseSerializer(answer).data
        # Reveal correct answer and distractor explanation upon submission
        resp_data["correct_answer"] = answer.question.correct_answer
        resp_data["distractor_explanations"] = answer.question.distractor_explanations
        resp_data["explanation"] = (answer.question.rubric or {}).get("explanation", "")

        return Response(resp_data, status=status.HTTP_200_OK)


class CompleteAttemptView(APIView):
    """Finalize an attempt, calculate accuracy, identify weak concepts, and recommend learning resources."""

    @extend_schema(summary="Complete Attempt", responses={200: AttemptResultSerializer})
    def post(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id).first()
        if not attempt:
            raise NotFound(detail=f"Attempt {attempt_id} not found")

        summary = AssessmentEngineService.complete_attempt(attempt_id=attempt_id)
        return Response(
            {
                "attempt_id": summary.attempt_id,
                "assessment_id": summary.assessment_id,
                "title": summary.title,
                "skill_name": summary.skill_name,
                "topic_name": summary.topic_name,
                "score_percentage": summary.score_percentage,
                "score": summary.score_percentage,
                "passed": summary.passed,
                "total_points_possible": summary.total_points_possible,
                "total_points_awarded": summary.total_points_awarded,
                "total_questions": summary.total_questions,
                "correct_answers_count": summary.correct_answers_count,
                "answers": summary.answers,
                "completed_at": summary.completed_at,
                "evidence_id": summary.evidence_id,
                "concept_scores": summary.concept_scores,
                "weak_concepts": summary.weak_concepts,
                "recommended_resources": summary.recommended_resources,
                "next_difficulty": summary.next_difficulty,
                "next_skill_id": summary.next_skill_id,
                "next_skill_name": summary.next_skill_name,
            },
            status=status.HTTP_200_OK,
        )


class AttemptResultView(APIView):
    """View results of an attempt with concept breakdown and recommended remediation."""

    @extend_schema(summary="Get Attempt Result", responses={200: AttemptResultSerializer})
    def get(self, request, attempt_id):
        attempt = Attempt.objects.filter(id=attempt_id).select_related("assessment", "assessment__skill", "assessment__topic").first()
        if not attempt:
            raise NotFound(detail=f"Attempt {attempt_id} not found")

        assessment = attempt.assessment
        skill = assessment.skill
        topic = assessment.topic

        answers = attempt.answers.select_related("question").order_by("question__order")
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

        # Recommended resources from skill
        recommended_resources = []
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

        # Progression
        curr_diff = (assessment.difficulty_level or "easy").lower().strip()
        next_difficulty = None
        if attempt.passed:
            if curr_diff in ("easy", "basic", "beginner"):
                next_difficulty = "medium"
            elif curr_diff in ("medium", "intermediate"):
                next_difficulty = "hard"

        next_skill = None
        next_skill_id = None
        next_skill_name = None
        if skill:
            next_skill = skill.get_next_skill(domain=topic.domain if topic else None)
            if next_skill:
                next_skill_id = str(next_skill.id)
                next_skill_name = next_skill.name

        return Response(
            {
                "attempt_id": str(attempt.id),
                "assessment_id": str(assessment.id),
                "title": assessment.title,
                "skill_name": skill.name if skill else None,
                "topic_name": topic.name if topic else None,
                "score_percentage": float(attempt.score) if attempt.score is not None else 0.0,
                "passed": attempt.passed,
                "total_points_possible": float(attempt.total_points_possible),
                "total_points_awarded": float(attempt.total_points_awarded),
                "total_questions": assessment.questions.count(),
                "correct_answers_count": sum(1 for a in answers if a.is_correct),
                "answers": answers_data,
                "completed_at": attempt.completed_at.isoformat() if attempt.completed_at else None,
                "concept_scores": attempt.concept_scores,
                "weak_concepts": attempt.weak_concepts,
                "recommended_resources": recommended_resources,
                "next_difficulty": next_difficulty,
                "next_skill_id": next_skill_id,
                "next_skill_name": next_skill_name,
            },
            status=status.HTTP_200_OK,
        )


class SkillAssessmentStatusView(APIView):
    """
    Checks configuration, cached questions, and active attempts for a skill and difficulty.
    Validates whether required provider (Ollama for Easy, Cloud for Medium/Hard) is configured.
    """

    @extend_schema(
        summary="Skill Assessment Status",
        parameters=[
            OpenApiParameter("difficulty", str, description="Difficulty level: easy, medium, hard"),
        ],
    )
    def get(self, request, skill_id):
        skill = Skill.objects.filter(id=skill_id).select_related("topic", "topic__domain").first()
        if not skill:
            raise NotFound(detail=f"Skill {skill_id} not found")

        difficulty = (request.query_params.get("difficulty") or "easy").lower().strip()
        if difficulty not in ("easy", "medium", "hard"):
            difficulty = "easy"

        # Check provider configuration
        provider_configured = False
        provider_name = ""
        provider_model = ""
        provider_error = ""

        try:
            prov = AssessmentProviderResolver.get_provider_for_difficulty(difficulty)
            provider_configured = True
            provider_name = getattr(prov, "provider_name", prov.__class__.__name__)
            provider_model = getattr(prov, "model_name", "")
        except AssessmentProviderError as prov_err:
            provider_configured = False
            provider_name = prov_err.provider
            provider_error = prov_err.message

        assessment = Assessment.objects.filter(
            skill=skill,
            difficulty_level=difficulty,
            is_active=True,
        ).order_by("-created_at").first()

        assessment_data = None
        active_attempt_data = None

        if assessment:
            questions_count = assessment.questions.count()
            active_attempt = assessment.attempts.filter(completed_at__isnull=True).order_by("-started_at").first()
            if active_attempt:
                answered_count = active_attempt.answers.count()
                active_attempt_data = {
                    "attempt_id": str(active_attempt.id),
                    "started_at": active_attempt.started_at.isoformat(),
                    "answered_count": answered_count,
                    "target_questions_count": assessment.target_questions_count,
                }

            assessment_data = {
                "assessment_id": str(assessment.id),
                "title": assessment.title,
                "difficulty_level": assessment.difficulty_level,
                "generation_status": assessment.generation_status,
                "generation_error": assessment.generation_error,
                "provider_used": assessment.provider_used,
                "questions_generated_count": questions_count,
                "target_questions_count": assessment.target_questions_count,
            }

        return Response({
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "topic_name": skill.topic.name if skill.topic else "",
            "difficulty": difficulty,
            "provider_configured": provider_configured,
            "provider_name": provider_name,
            "provider_model": provider_model,
            "provider_error": provider_error,
            "assessment": assessment_data,
            "active_attempt": active_attempt_data,
        }, status=status.HTTP_200_OK)


class SkillNextQuestionView(APIView):
    """
    Lazy sequential question generator and delivery endpoint.
    Retrieves or generates exactly ONE question at a time.
    Enforces local Ollama for Easy, Cloud API for Medium/Hard.
    Never exposes correct answer before user submission.
    """

    @extend_schema(
        summary="Get or Generate Next Question",
        request=SkillNextQuestionRequestSerializer,
    )
    def post(self, request, skill_id):
        skill = Skill.objects.filter(id=skill_id).select_related("topic", "topic__domain").first()
        if not skill:
            raise NotFound(detail=f"Skill {skill_id} not found")

        serializer = SkillNextQuestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        difficulty = serializer.validated_data.get("difficulty", "easy")
        requested_order = serializer.validated_data.get("order")
        attempt_id = serializer.validated_data.get("attempt_id")

        # 1. Get or create Assessment container for this skill & difficulty
        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=skill,
            difficulty_level=difficulty,
        )

        # 2. Get or create active attempt
        attempt = None
        if attempt_id:
            attempt = Attempt.objects.filter(id=attempt_id, assessment=assessment, completed_at__isnull=True).first()

        if not attempt:
            # Check for existing open attempt or create new one
            attempt = assessment.attempts.filter(completed_at__isnull=True).order_by("-started_at").first()
            if not attempt:
                attempt = AssessmentEngineService.start_attempt(assessment_id=assessment.id)

        # 3. Determine order if not explicitly specified
        if requested_order is None:
            # Find the lowest order question not yet answered in this attempt
            answered_orders = set(
                attempt.answers.values_list("question__order", flat=True)
            )
            existing_orders = list(assessment.questions.values_list("order", flat=True))

            next_unanswered = None
            for ord_num in sorted(existing_orders):
                if ord_num not in answered_orders:
                    next_unanswered = ord_num
                    break

            if next_unanswered:
                requested_order = next_unanswered
            else:
                requested_order = len(existing_orders) + 1

        # 4. Generate or fetch from cache
        try:
            question = SequentialQuestionGenerationService.get_or_generate_question(
                assessment=assessment,
                requested_order=requested_order,
            )
        except ProviderNotConfiguredError as pnc_err:
            return Response(
                {
                    "error": "provider_not_configured",
                    "provider": pnc_err.provider,
                    "difficulty": pnc_err.difficulty,
                    "message": pnc_err.message,
                    "can_retry": pnc_err.can_retry,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ProviderUnavailableError as pua_err:
            return Response(
                {
                    "error": "provider_unavailable",
                    "provider": pua_err.provider,
                    "difficulty": pua_err.difficulty,
                    "message": pua_err.message,
                    "can_retry": pua_err.can_retry,
                },
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        except ConcurrentGenerationError as cge_err:
            return Response(
                {
                    "error": "concurrent_generation",
                    "message": str(cge_err),
                    "can_retry": True,
                },
                status=status.HTTP_409_CONFLICT,
            )
        except Exception as gen_err:
            logger.error(f"Failed to generate question: {gen_err}")
            return Response(
                {
                    "error": "generation_failed",
                    "message": f"Assessment question generation failed: {gen_err}",
                    "can_retry": True,
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # 5. Check if already answered in this attempt
        existing_answer = attempt.answers.filter(question=question).first()
        is_answered = existing_answer is not None

        # Student facing serialized question (hides correct_answer unless answered)
        q_data = QuestionSerializer(question).data

        # Also serialize all generated questions for client caching so navigation is 0-latency
        all_questions_data = QuestionSerializer(
            assessment.questions.all().order_by("order"),
            many=True,
        ).data

        payload = {
            "assessment_id": str(assessment.id),
            "attempt_id": str(attempt.id),
            "skill_id": str(skill.id),
            "skill_name": skill.name,
            "topic_name": skill.topic.name if skill.topic else "",
            "difficulty": assessment.difficulty_level,
            "provider_used": assessment.provider_used,
            "order": question.order,
            "target_questions_count": assessment.target_questions_count,
            "total_generated": assessment.questions.count(),
            "question": q_data,
            "all_questions": all_questions_data,
            "is_answered": is_answered,
            "is_last_question": question.order >= assessment.target_questions_count,
        }

        if is_answered:
            payload["user_response"] = existing_answer.user_response
            payload["is_correct"] = existing_answer.is_correct
            payload["accuracy"] = existing_answer.accuracy
            payload["feedback"] = existing_answer.feedback
            payload["correct_answer"] = question.correct_answer
            payload["distractor_explanations"] = question.distractor_explanations
            payload["explanation"] = (question.rubric or {}).get("explanation", "")

        return Response(payload, status=status.HTTP_200_OK)


class SkillNextSkillView(APIView):
    """Returns the next skill in the roadmap progression."""

    @extend_schema(summary="Next Skill in Curriculum")
    def get(self, request, skill_id):
        skill = Skill.objects.filter(id=skill_id).select_related("topic", "topic__domain").first()
        if not skill:
            raise NotFound(detail=f"Skill {skill_id} not found")

        domain = skill.topic.domain if skill.topic else None
        next_skill = skill.get_next_skill(domain=domain)

        if not next_skill:
            return Response({
                "current_skill_id": str(skill.id),
                "current_skill_name": skill.name,
                "has_next_skill": False,
                "message": "Congratulations! You have completed all skills in this roadmap.",
            }, status=status.HTTP_200_OK)

        return Response({
            "current_skill_id": str(skill.id),
            "current_skill_name": skill.name,
            "has_next_skill": True,
            "next_skill_id": str(next_skill.id),
            "next_skill_name": next_skill.name,
            "next_topic_name": next_skill.topic.name if next_skill.topic else "",
            "order": next_skill.order,
        }, status=status.HTTP_200_OK)


class SkillAssessmentHistoryView(APIView):
    """View ongoing assessment history using up to the latest 3 assessments for a skill."""

    @extend_schema(summary="Skill Assessment History (Latest 3)", responses={200: SkillAssessmentHistorySerializer})
    def get(self, request, skill_id):
        history = AssessmentEngineService.get_skill_assessment_history(skill_id=skill_id)
        return Response(
            {
                "target_id": history.target_id,
                "target_name": history.target_name,
                "target_type": history.target_type,
                "attempts_considered": history.attempts_considered,
                "average_score": history.average_score,
                "latest_score": history.latest_score,
                "highest_score": history.highest_score,
                "passing_rate": history.passing_rate,
                "trend": history.trend,
                "attempts": history.attempts,
            },
            status=status.HTTP_200_OK,
        )


class TopicAssessmentHistoryView(APIView):
    """View ongoing assessment history using up to the latest 3 assessments for a topic."""

    @extend_schema(summary="Topic Assessment History (Latest 3)", responses={200: SkillAssessmentHistorySerializer})
    def get(self, request, topic_id):
        history = AssessmentEngineService.get_skill_assessment_history(topic_id=topic_id)
        return Response(
            {
                "target_id": history.target_id,
                "target_name": history.target_name,
                "target_type": history.target_type,
                "attempts_considered": history.attempts_considered,
                "average_score": history.average_score,
                "latest_score": history.latest_score,
                "highest_score": history.highest_score,
                "passing_rate": history.passing_rate,
                "trend": history.trend,
                "attempts": history.attempts,
            },
            status=status.HTTP_200_OK,
        )
