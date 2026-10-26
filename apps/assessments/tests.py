import json
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from apps.roadmap.models import Domain, Topic, Skill, LearningResource, SkillResourceMapping
from apps.assessments.models import Assessment, Question, Attempt, Answer
from apps.assessments.services.provider_resolver import (
    AssessmentProviderResolver,
    ProviderNotConfiguredError,
    ProviderUnavailableError,
)
from apps.assessments.services.question_validator import (
    QuestionValidator,
    QuestionValidationError,
)
from apps.assessments.services.sequential_generator import (
    SequentialQuestionGenerationService,
)
from apps.assessments.services.assessment_engine import (
    AssessmentEngineService,
)
from apps.rag.llm.base import BaseLLMProvider, LLMResponse


class MockTestLLMProvider(BaseLLMProvider):
    """Custom controllable LLM Provider for unit tests."""
    _provider_name = "mock_test"
    _model_name = "test-model-1"

    def __init__(self, response_text: str = ""):
        self.response_text = response_text
        self.call_count = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            text=self.response_text,
            model=self._model_name,
            tokens_used=100,
        )


class AssessmentProviderResolverTestCase(TestCase):
    """Tests that difficulty tiers strictly resolve to their mandated providers."""

    def test_easy_tier_resolves_ollama(self):
        with patch("apps.assessments.services.provider_resolver.get_system_ai_config") as mock_cfg:
            mock_cfg.return_value = {
                "llm_provider": "ollama",
                "ollama_base_url": "http://127.0.0.1:11434",
                "ollama_model": "llama3.2",
            }
            provider = AssessmentProviderResolver.get_provider_for_difficulty("easy")
            self.assertEqual(provider.provider_name, "ollama")
            self.assertEqual(provider.model_name, "llama3.2")

    def test_easy_tier_missing_ollama_raises_error(self):
        with patch("apps.assessments.services.provider_resolver.get_system_ai_config") as mock_cfg:
            mock_cfg.return_value = {
                "llm_provider": "gemini",
                "ollama_base_url": "",
                "ollama_model": "",
            }
            with self.assertRaises(ProviderNotConfiguredError) as ctx:
                AssessmentProviderResolver.get_provider_for_difficulty("easy")
            self.assertEqual(ctx.exception.provider, "ollama")
            self.assertEqual(ctx.exception.difficulty, "easy")

    def test_medium_tier_resolves_cloud(self):
        with patch("apps.assessments.services.provider_resolver.get_system_ai_config") as mock_cfg:
            mock_cfg.return_value = {
                "llm_provider": "gemini",
                "gemini_api_key": "dummy-gemini-key",
                "gemini_model": "gemini-2.5-flash",
            }
            provider = AssessmentProviderResolver.get_provider_for_difficulty("medium")
            self.assertEqual(provider.provider_name, "gemini")

    def test_hard_tier_resolves_cloud(self):
        with patch("apps.assessments.services.provider_resolver.get_system_ai_config") as mock_cfg:
            mock_cfg.return_value = {
                "llm_provider": "openai",
                "openai_api_key": "sk-dummy-key",
                "openai_model": "gpt-4o-mini",
            }
            provider = AssessmentProviderResolver.get_provider_for_difficulty("hard")
            self.assertEqual(provider.provider_name, "openai")

    def test_cloud_missing_credentials_raises_error(self):
        with patch("apps.assessments.services.provider_resolver.get_system_ai_config") as mock_cfg:
            mock_cfg.return_value = {
                "llm_provider": "ollama",  # Cloud is unconfigured
                "gemini_api_key": "",
                "openai_api_key": "",
            }
            with self.assertRaises(ProviderNotConfiguredError) as ctx:
                AssessmentProviderResolver.get_provider_for_difficulty("medium")
            self.assertIn(ctx.exception.provider, ("gemini", "openai", "cloud"))


class QuestionValidatorTestCase(TestCase):
    """Tests server-side validation of MCQ structure, options, answers, and explanations."""

    def test_valid_mcq_passes_validation(self):
        raw = {
            "prompt": "Which Python operator tests whether two variables point to the exact same object in memory?",
            "options": [
                {"key": "A", "text": "=="},
                {"key": "B", "text": "is"},
                {"key": "C", "text": "in"},
                {"key": "D", "text": "="}
            ],
            "correct_answer": "B",
            "explanation": "The 'is' operator checks object identity rather than value equality.",
            "distractor_explanations": {
                "A": "== checks value equality, not memory identity.",
                "C": "in checks membership in a collection.",
                "D": "= is the variable assignment operator."
            },
            "concept": "Identity Operators"
        }
        sanitized = QuestionValidator.validate_and_sanitize_question(raw, skill_name="Python Operators")
        self.assertEqual(sanitized["correct_answer"], "B")
        self.assertEqual(len(sanitized["options"]), 4)
        self.assertEqual(sanitized["concept"], "Identity Operators")
        self.assertIn("A", sanitized["distractor_explanations"])

    def test_rejects_missing_options(self):
        raw = {
            "prompt": "What does len([1, 2, 3]) return?",
            "options": [
                {"key": "A", "text": "1"},
                {"key": "B", "text": "2"},
                {"key": "C", "text": "3"}
            ],
            "correct_answer": "C",
            "explanation": "len returns the length."
        }
        with self.assertRaises(QuestionValidationError):
            QuestionValidator.validate_and_sanitize_question(raw)

    def test_rejects_duplicate_options(self):
        raw = {
            "prompt": "What is 2 + 2 in Python?",
            "options": [
                {"key": "A", "text": "4"},
                {"key": "B", "text": "4"},
                {"key": "C", "text": "5"},
                {"key": "D", "text": "6"}
            ],
            "correct_answer": "A",
            "explanation": "2 + 2 is 4."
        }
        with self.assertRaises(QuestionValidationError):
            QuestionValidator.validate_and_sanitize_question(raw)

    def test_rejects_invalid_correct_answer_key(self):
        raw = {
            "prompt": "What is 2 * 3 in Python?",
            "options": [
                {"key": "A", "text": "6"},
                {"key": "B", "text": "5"},
                {"key": "C", "text": "7"},
                {"key": "D", "text": "8"}
            ],
            "correct_answer": "E",  # Invalid key
            "explanation": "2 * 3 is 6."
        }
        with self.assertRaises(QuestionValidationError):
            QuestionValidator.validate_and_sanitize_question(raw)

    def test_rejects_missing_explanation(self):
        raw = {
            "prompt": "What is 2 * 3 in Python?",
            "options": [
                {"key": "A", "text": "6"},
                {"key": "B", "text": "5"},
                {"key": "C", "text": "7"},
                {"key": "D", "text": "8"}
            ],
            "correct_answer": "A",
            "explanation": ""
        }
        with self.assertRaises(QuestionValidationError):
            QuestionValidator.validate_and_sanitize_question(raw)


class SequentialGenerationAndAssessmentTestCase(TestCase):
    """End-to-end tests for sequential generation, caching, retries, evaluation, and progression."""

    def setUp(self):
        self.domain = Domain.objects.create(name="AI / ML Engineering", slug="aiml-test")
        self.topic1 = Topic.objects.create(domain=self.domain, name="Python Foundations", slug="python-foundations", order=1)
        self.topic2 = Topic.objects.create(domain=self.domain, name="Data Structures", slug="data-structures", order=2)

        self.skill1 = Skill.objects.create(
            topic=self.topic1,
            name="Python Operators",
            slug="python-operators",
            description="Arithmetic, comparison, logical, identity, membership, and bitwise operators in Python.",
            learning_objectives=["Understand precedence", "Use identity vs equality"],
            key_concepts=["Arithmetic", "Identity Operators", "Bitwise Operators"],
            order=1,
        )

        self.skill2 = Skill.objects.create(
            topic=self.topic1,
            name="Control Flow",
            slug="control-flow",
            description="if/else branches, loops, and comprehensions.",
            order=2,
        )

        # Seed curated learning resources
        self.res1 = LearningResource.objects.create(
            title="Python Operators - GeeksforGeeks",
            url="https://www.geeksforgeeks.org/python-operators/",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="GeeksforGeeks",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
        )
        SkillResourceMapping.objects.create(skill=self.skill1, resource=self.res1, is_primary=True, order=1)

        self.res2 = LearningResource.objects.create(
            title="Official Python Built-in Operators",
            url="https://docs.python.org/3/library/stdtypes.html",
            resource_type=LearningResource.ResourceType.OFFICIAL_DOCS,
            source="Python Docs",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
        )
        SkillResourceMapping.objects.create(skill=self.skill1, resource=self.res2, is_primary=False, order=2)

        self.valid_mcq_payload = json.dumps({
            "prompt": "What is the output of 5 // 2 in Python 3?",
            "options": [
                {"key": "A", "text": "2.5"},
                {"key": "B", "text": "2"},
                {"key": "C", "text": "3"},
                {"key": "D", "text": "2.0"}
            ],
            "correct_answer": "B",
            "explanation": "Floor division // truncates fractional results and yields integer 2.",
            "distractor_explanations": {
                "A": "2.5 is the float result of standard division (5 / 2).",
                "C": "3 is rounded up, whereas floor division truncates towards negative infinity.",
                "D": "2.0 would be returned if one operand was a float (e.g. 5.0 // 2)."
            },
            "concept": "Arithmetic Operators"
        })

    def test_sequential_generation_and_caching(self):
        """Verify questions generate lazily one at a time and are cached without repeat LLM calls."""
        mock_provider = MockTestLLMProvider(response_text=self.valid_mcq_payload)

        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=self.skill1,
            difficulty_level="easy",
            target_questions_count=5,
        )
        self.assertEqual(assessment.questions.count(), 0)

        # 1. Generate Question 1
        q1 = SequentialQuestionGenerationService.get_or_generate_question(
            assessment=assessment,
            requested_order=1,
            llm_provider=mock_provider,
        )
        self.assertEqual(q1.order, 1)
        self.assertEqual(q1.concept, "Arithmetic Operators")
        self.assertEqual(mock_provider.call_count, 1)
        self.assertEqual(assessment.questions.count(), 1)

        # 2. Requesting Question 1 again MUST return from cache without calling LLM
        q1_cached = SequentialQuestionGenerationService.get_or_generate_question(
            assessment=assessment,
            requested_order=1,
            llm_provider=mock_provider,
        )
        self.assertEqual(q1_cached.id, q1.id)
        self.assertEqual(mock_provider.call_count, 1)  # LLM call count remains 1

    def test_bounded_retries_on_malformed_json(self):
        """Verify generator retries up to MAX_RETRIES on malformed JSON and succeeds."""
        bad_response = "Not valid json at all!"
        good_response = self.valid_mcq_payload

        call_records = []

        class FlakyLLMProvider(BaseLLMProvider):
            _provider_name = "flaky"
            _model_name = "flaky-v1"

            @property
            def model_name(self) -> str:
                return self._model_name

            def generate(self, prompt, **kwargs):
                call_records.append(1)
                if len(call_records) == 1:
                    return LLMResponse(text=bad_response, model=self._model_name)
                return LLMResponse(text=good_response, model=self._model_name)

        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=self.skill1,
            difficulty_level="easy",
        )

        q = SequentialQuestionGenerationService.get_or_generate_question(
            assessment=assessment,
            requested_order=1,
            llm_provider=FlakyLLMProvider(),
        )
        self.assertEqual(len(call_records), 2)  # 1 failure + 1 retry success
        self.assertEqual(q.order, 1)
        self.assertEqual(q.correct_answer, "B")

    def test_batch_question_generation_10_questions_in_single_query(self):
        """Verify generating 10 questions in a single query creates all questions at once."""
        questions_list = []
        for i in range(1, 11):
            questions_list.append({
                "prompt": f"Test question number {i}: What is the value of {i} * 2?",
                "options": [
                    {"key": "A", "text": str(i * 2)},
                    {"key": "B", "text": str(i * 2 + 1)},
                    {"key": "C", "text": str(i * 2 - 1)},
                    {"key": "D", "text": str(i * 2 + 2)},
                ],
                "correct_answer": "A",
                "explanation": f"Multiplying {i} by 2 yields {i * 2}.",
                "distractor_explanations": {
                    "B": "Incorrect by +1",
                    "C": "Incorrect by -1",
                    "D": "Incorrect by +2"
                },
                "concept": f"Multiplication-{i}"
            })

        batch_payload = json.dumps({"questions": questions_list})
        mock_provider = MockTestLLMProvider(response_text=batch_payload)

        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=self.skill1,
            difficulty_level="easy",
            target_questions_count=10,
        )
        self.assertEqual(assessment.questions.count(), 0)

        # Generating question 1 triggers batch generation for all 10 questions!
        q1 = SequentialQuestionGenerationService.get_or_generate_question(
            assessment=assessment,
            requested_order=1,
            llm_provider=mock_provider,
        )

        self.assertEqual(q1.order, 1)
        self.assertEqual(mock_provider.call_count, 1)  # Only 1 query made!
        self.assertEqual(assessment.questions.count(), 10)  # All 10 created!
        self.assertEqual(assessment.generation_status, Assessment.GenerationStatus.READY)

        # Checking questions 2 to 10 requires 0 extra LLM calls
        for order in range(2, 11):
            q_cached = SequentialQuestionGenerationService.get_or_generate_question(
                assessment=assessment,
                requested_order=order,
                llm_provider=mock_provider,
            )
            self.assertEqual(q_cached.order, order)
        self.assertEqual(mock_provider.call_count, 1)  # Still exactly 1 call!

    def test_assessment_execution_evaluation_and_weak_concept_detection(self):
        """Verify answering, response times, concept breakdown, weakness detection, and recommendations."""
        assessment = SequentialQuestionGenerationService.get_or_create_skill_assessment(
            skill=self.skill1,
            difficulty_level="easy",
            target_questions_count=2,
        )

        # Manually create 2 questions with different concepts
        q1 = Question.objects.create(
            assessment=assessment,
            question_type=Question.QuestionType.MCQ,
            order=1,
            concept="Arithmetic Operators",
            prompt="What is 10 // 3?",
            options=[{"key": "A", "text": "3"}, {"key": "B", "text": "3.33"}, {"key": "C", "text": "4"}, {"key": "D", "text": "1"}],
            correct_answer="A",
            points=1,
            rubric={"explanation": "Floor division returns 3."},
            distractor_explanations={"B": "B is float division result."}
        )

        q2 = Question.objects.create(
            assessment=assessment,
            question_type=Question.QuestionType.MCQ,
            order=2,
            concept="Identity Operators",
            prompt="What does 'a is b' test?",
            options=[{"key": "A", "text": "Value equality"}, {"key": "B", "text": "Object identity"}, {"key": "C", "text": "Type equality"}, {"key": "D", "text": "Scope"}],
            correct_answer="B",
            points=1,
            rubric={"explanation": "'is' tests object identity in memory."},
            distractor_explanations={"A": "Value equality is tested by ==."}
        )

        # Start attempt
        attempt = AssessmentEngineService.start_attempt(assessment.id)

        # Submit Q1: Correct with 4.5 seconds response time
        ans1 = AssessmentEngineService.submit_and_evaluate_answer(
            attempt_id=attempt.id,
            question_id=q1.id,
            user_response="A",
            response_time_seconds=4.5,
        )
        self.assertTrue(ans1.is_correct)
        self.assertEqual(ans1.response_time_seconds, 4.5)
        self.assertIn("Correct!", ans1.feedback)

        # Submit Q2: Incorrect (picked A) with 8.0 seconds response time
        ans2 = AssessmentEngineService.submit_and_evaluate_answer(
            attempt_id=attempt.id,
            question_id=q2.id,
            user_response="A",
            response_time_seconds=8.0,
        )
        self.assertFalse(ans2.is_correct)
        self.assertEqual(ans2.response_time_seconds, 8.0)
        # Verify distractor explanation is surfaced!
        self.assertIn("Option A is incorrect", ans2.feedback)
        self.assertIn("Value equality is tested by ==", ans2.feedback)

        # Finalize attempt
        summary = AssessmentEngineService.complete_attempt(attempt_id=attempt.id)
        self.assertEqual(summary.score_percentage, 50.0)
        self.assertFalse(summary.passed)

        # Verify Concept-Level Scoring & Weak Concepts
        concept_scores = summary.concept_scores
        self.assertIn("Arithmetic Operators", concept_scores)
        self.assertEqual(concept_scores["Arithmetic Operators"]["accuracy"], 100.0)
        self.assertIn("Identity Operators", concept_scores)
        self.assertEqual(concept_scores["Identity Operators"]["accuracy"], 0.0)

        # Weak concepts (< 70% accuracy)
        self.assertIn("Identity Operators", summary.weak_concepts)
        self.assertNotIn("Arithmetic Operators", summary.weak_concepts)

        # Curated Learning Resources Recommended
        self.assertTrue(len(summary.recommended_resources) >= 2)
        res_titles = [r["title"] for r in summary.recommended_resources]
        self.assertIn("Python Operators - GeeksforGeeks", res_titles)

        # Check Next Skill navigation
        self.assertEqual(summary.next_skill_name, "Control Flow")

    def test_drf_endpoints_workflow(self):
        """Test DRF endpoints: next-question, submit-answer, complete, next-skill."""
        client = APIClient()
        mock_provider = MockTestLLMProvider(response_text=self.valid_mcq_payload)

        # 1. Next question endpoint
        with patch("apps.assessments.services.sequential_generator.AssessmentProviderResolver.get_provider_for_difficulty", return_value=mock_provider):
            res = client.post(
                f"/api/v1/assessments/skills/{self.skill1.id}/next-question/",
                data={"difficulty": "easy", "order": 1},
                format="json",
            )
            self.assertEqual(res.status_code, status.HTTP_200_OK)
            data = res.json()
            self.assertEqual(data["order"], 1)
            self.assertEqual(data["difficulty"], "easy")
            self.assertFalse(data["is_answered"])
            # Ensure correct answer is NOT exposed to student before submission!
            self.assertNotIn("correct_answer", data["question"])

            attempt_id = data["attempt_id"]
            question_id = data["question"]["id"]

        # 2. Submit answer endpoint
        submit_res = client.post(
            f"/api/v1/assessments/attempts/{attempt_id}/submit-answer/",
            data={
                "question_id": question_id,
                "user_response": "B",
                "response_time_seconds": 3.2,
            },
            format="json",
        )
        self.assertEqual(submit_res.status_code, status.HTTP_200_OK)
        sub_data = submit_res.json()
        self.assertTrue(sub_data["is_correct"])
        # Now revealed
        self.assertEqual(sub_data["correct_answer"], "B")
        self.assertEqual(sub_data["response_time_seconds"], 3.2)

        # 3. Next skill endpoint
        next_skill_res = client.get(f"/api/v1/assessments/skills/{self.skill1.id}/next-skill/")
        self.assertEqual(next_skill_res.status_code, status.HTTP_200_OK)
        self.assertTrue(next_skill_res.json()["has_next_skill"])
        self.assertEqual(next_skill_res.json()["next_skill_name"], "Control Flow")
