import json
import logging
import time
from typing import Any, Dict, List, Optional, Tuple
from django.core.cache import cache
from django.db import transaction

from apps.assessments.models import Assessment, Question
from apps.roadmap.models import Skill, Topic
from apps.rag.llm.base import BaseLLMProvider
from .provider_resolver import (
    AssessmentProviderResolver,
    AssessmentProviderError,
    ProviderNotConfiguredError,
    ProviderUnavailableError,
)
from .question_validator import QuestionValidator, QuestionValidationError
from .scoring import AssessmentScoringRules

logger = logging.getLogger("brofessor")

MCQ_GENERATION_SYSTEM_PROMPT = """You are Brofessor's expert educational assessment engine.
Generate exactly ONE high-quality multiple-choice question (MCQ) aligned with the specified skill, topic, and difficulty level.

Requirements:
1. Generate exactly 4 options labelled "A", "B", "C", and "D".
2. Exactly one option must be the correct answer.
3. Provide a clear, detailed explanation of why the correct answer is right.
4. Provide distractor explanations detailing why each of the other three options is incorrect.
5. Assign a specific concept/tag tested (e.g., 'Arithmetic Operators', 'Type Casting', 'Variable Scope').
6. Stay STRICTLY within the scope of the target skill.

CRITICAL CODE SNIPPET RULE:
- If your question asks about code execution, syntax, or output (e.g., "What will be the output...?", "What is the result of...?"):
  YOU MUST INCLUDE THE FULL PYTHON CODE DIRECTLY INSIDE THE "prompt" FIELD USING MARKDOWN CODE BLOCKS (```python ... ```) OR INLINE CODE (`...`).
- NEVER write "the following code", "the following snippet", or "the following expression" without providing the actual code inside the "prompt" string!
- If the question is conceptual, state the question directly without mentioning "following code".

Example of a valid question with code snippet:
{
  "prompt": "What will be the output of the following Python code snippet?\\n\\n```python\\nx = 10 + 2\\nprint(x)\\n```",
  "options": [
    {"key": "A", "text": "12"},
    {"key": "B", "text": "10"},
    {"key": "C", "text": "102"},
    {"key": "D", "text": "TypeError"}
  ],
  "correct_answer": "A",
  "explanation": "In Python, 10 + 2 performs integer addition resulting in 12.",
  "distractor_explanations": {
    "B": "10 ignores the addition operand.",
    "C": "102 would only occur if strings '10' and '2' were concatenated.",
    "D": "Integer addition is valid and does not raise TypeError."
  },
  "concept": "Arithmetic Operators"
}

Difficulty Guidelines:
- EASY: Test foundational understanding, standard definitions, syntax, and basic usage.
- MEDIUM: Test practical application, code execution reasoning, comparing behavior, and standard trade-offs.
- HARD: Test edge cases, multi-step logic, subtle language rules, operator precedence/coercion, and nuanced behavior without introducing out-of-scope concepts.

Output MUST be valid JSON adhering strictly to this schema. Output ONLY the JSON object. Do not include markdown code block syntax or explanations outside the JSON."""

BATCH_MCQ_GENERATION_SYSTEM_PROMPT = """You are Brofessor's expert educational assessment engine.
Generate exactly 10 high-quality multiple-choice questions (MCQs) aligned with the specified skill, topic, and difficulty level.

STRICT FORMATTING REQUIREMENTS (MANDATORY):
1. Output MUST be RAW, VALID JSON ONLY.
2. The very first character of your response MUST be '{' and the very last character MUST be '}'.
3. Do NOT wrap the JSON in markdown code fences (do NOT use ``` or ```json).
4. Do NOT include any preamble, conversational introduction, or commentary.
5. All 10 questions must be contained in the "questions" array.
6. Ensure all JSON strings and quotes are properly escaped.

Requirements for each question:
1. Provide exactly 4 options labelled "A", "B", "C", and "D".
2. Exactly one option must be the correct answer ("A", "B", "C", or "D").
3. Provide a clear, detailed explanation of why the correct answer is right.
4. Provide distractor explanations detailing why each of the other three options is incorrect.
5. Assign a specific concept/tag tested (e.g. 'String Methods', 'Loop Constructs', 'List Comprehension', 'Operator Precedence').
6. Stay STRICTLY within the scope of the target skill.
7. Cover different subtopics and aspects of the skill to ensure variety and zero duplicate questions.

CRITICAL CODE SNIPPET RULE:
- If a question asks about code execution, syntax, or output (e.g., "What will be the output...?", "What is the result of...?"):
  YOU MUST INCLUDE THE FULL PYTHON CODE DIRECTLY INSIDE THE "prompt" FIELD USING MARKDOWN CODE BLOCKS (```python ... ```) OR INLINE CODE (`...`).
- NEVER write "the following code", "the following snippet", or "the following expression" without providing the actual code inside the "prompt" string!
- If the question is conceptual, state the question directly without mentioning "following code".

Required JSON output format:
{
  "questions": [
    {
      "prompt": "What is the result of the following Python expression?\\n\\n```python\\nprint(3 * 'ab')\\n```",
      "options": [
        {"key": "A", "text": "ababab"},
        {"key": "B", "text": "3ab"},
        {"key": "C", "text": "ab3"},
        {"key": "D", "text": "TypeError"}
      ],
      "correct_answer": "A",
      "explanation": "Multiplying a string by an integer in Python repeats the string that many times.",
      "distractor_explanations": {
        "B": "Python repeats the string rather than prefixing the number.",
        "C": "Suffixing is not valid multiplication behavior in Python.",
        "D": "String repetition with an integer is valid syntax."
      },
      "concept": "String Repetition"
    }
  ]
}

Difficulty Guidelines:
- EASY: Foundational understanding, definitions, syntax, standard operations.
- MEDIUM: Application, code execution, comparing behaviors, edge cases.
- HARD: Subtle language rules, operator precedence, scope subtleties, mutation vs re-binding.

Output raw JSON now, starting with '{' and ending with '}':"""


class ConcurrentGenerationError(Exception):
    """Raised when a concurrent generation request is already in progress."""
    pass


class SequentialQuestionGenerationService:
    """
    Orchestrates assessment question generation.
    Features:
    - Generates all 10 questions in a single query upfront to minimize LLM latency and costs
    - Lazy on-demand fallback for individual questions if needed
    - Enforces provider routing via AssessmentProviderResolver (Easy: Ollama, Medium/Hard: Cloud LLM)
    - Concurrency lock preventing duplicate requests
    - Persistent caching: Reopening an assessment never triggers unnecessary LLM calls
    - Bounded retries for malformed or invalid LLM responses
    - Strict server-side validation via QuestionValidator
    - Zero silent fallback to other providers
    """

    MAX_RETRIES = 2
    LOCK_TIMEOUT_SECONDS = 45

    @classmethod
    def get_or_create_skill_assessment(
        cls,
        skill: Skill,
        difficulty_level: str = "easy",
        target_questions_count: int = 10,
    ) -> Assessment:
        """
        Retrieves or creates an Assessment container for a Skill and difficulty level.
        Does not pre-generate questions upfront.
        """
        diff_norm = (difficulty_level or "easy").lower().strip()
        if diff_norm in ("basic", "beginner"):
            diff_norm = "easy"
        elif diff_norm in ("intermediate",):
            diff_norm = "medium"
        elif diff_norm in ("advanced", "expert"):
            diff_norm = "hard"

        assessment = Assessment.objects.filter(
            skill=skill,
            difficulty_level=diff_norm,
            is_active=True,
        ).order_by("-created_at").first()

        if not assessment:
            title = f"{skill.name} ({diff_norm.capitalize()}) Assessment"
            assessment = Assessment.objects.create(
                title=title,
                skill=skill,
                topic=skill.topic,
                difficulty_level=diff_norm,
                passing_score=70.00,
                target_questions_count=target_questions_count,
                status=Assessment.AssessmentStatus.ACTIVE,
                generation_status=Assessment.GenerationStatus.PENDING,
            )
            logger.info(f"Created assessment container for {skill.name} [{diff_norm}]")

        return assessment

    @classmethod
    def generate_assessment_questions_batch(
        cls,
        assessment: Assessment,
        target_count: int = 10,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[Question]:
        """
        Generates all questions for the assessment in a single LLM query.
        Caches and persists all questions to the database with orders 1..N.
        """
        existing_questions = list(assessment.questions.all().order_by("order"))
        if len(existing_questions) >= target_count:
            return existing_questions

        lock_key = f"assess_gen_batch_{assessment.id}"
        acquired = cache.add(lock_key, "generating_batch", timeout=cls.LOCK_TIMEOUT_SECONDS * 2)

        if not acquired:
            # Another request is currently generating this assessment batch
            for _ in range(12):
                time.sleep(1.0)
                curr = list(assessment.questions.all().order_by("order"))
                if len(curr) >= target_count:
                    return curr
            curr = list(assessment.questions.all().order_by("order"))
            if curr:
                return curr
            raise ConcurrentGenerationError(
                f"Assessment '{assessment.title}' is currently being generated. Please wait."
            )

        try:
            # Re-check under lock
            curr = list(assessment.questions.all().order_by("order"))
            if len(curr) >= target_count:
                return curr

            active_llm = AssessmentProviderResolver.get_provider_for_difficulty(
                difficulty=assessment.difficulty_level,
                override_provider=llm_provider,
            )

            assessment.generation_status = Assessment.GenerationStatus.GENERATING
            assessment.save(update_fields=["generation_status"])

            user_prompt = cls._build_batch_context_prompt(
                skill=assessment.skill,
                topic=assessment.topic,
                difficulty=assessment.difficulty_level,
                target_count=target_count,
            )

            skill_name = assessment.skill.name if assessment.skill else assessment.title
            last_error = None
            current_prompt = user_prompt

            for attempt_idx in range(1 + cls.MAX_RETRIES):
                start_time = time.perf_counter()
                try:
                    response = active_llm.generate(
                        prompt=current_prompt,
                        system_prompt=BATCH_MCQ_GENERATION_SYSTEM_PROMPT,
                        temperature=0.3,
                    )
                    raw_text = response.text
                    latency_ms = int((time.perf_counter() - start_time) * 1000)

                    raw_questions = QuestionValidator.parse_raw_batch_response(raw_text)

                    valid_questions: List[Dict[str, Any]] = []
                    seen_prompts: List[str] = [q.prompt for q in curr]

                    for item in raw_questions:
                        try:
                            sanitized = QuestionValidator.validate_and_sanitize_question(
                                raw_data=item,
                                skill_name=skill_name,
                                existing_prompts=seen_prompts,
                            )
                            valid_questions.append(sanitized)
                            seen_prompts.append(sanitized["prompt"])
                        except QuestionValidationError as ve:
                            logger.warning(f"Batch item failed validation: {ve}")

                    if not valid_questions:
                        raise QuestionValidationError("Batch generation returned 0 valid questions.")

                    points = AssessmentScoringRules.get_points_for_question("mcq", assessment.difficulty_level)

                    created_objs: List[Question] = []
                    existing_orders = set(assessment.questions.values_list("order", flat=True))
                    next_order = 1

                    with transaction.atomic():
                        for q_data in valid_questions:
                            while next_order in existing_orders:
                                next_order += 1
                            if next_order > target_count and len(created_objs) + len(curr) >= target_count:
                                break

                            q_obj = Question.objects.create(
                                assessment=assessment,
                                question_type=Question.QuestionType.MCQ,
                                difficulty_level=assessment.difficulty_level,
                                prompt=q_data["prompt"],
                                options=q_data["options"],
                                correct_answer=q_data["correct_answer"],
                                distractor_explanations=q_data.get("distractor_explanations", {}),
                                rubric={"explanation": q_data["explanation"]},
                                concept=q_data["concept"],
                                points=points,
                                order=next_order,
                                generation_metadata={
                                    "provider": getattr(active_llm, "provider_name", active_llm.__class__.__name__),
                                    "model": getattr(active_llm, "model_name", "unknown"),
                                    "latency_ms": latency_ms,
                                    "attempt": attempt_idx + 1,
                                    "batch": True,
                                },
                            )
                            existing_orders.add(next_order)
                            created_objs.append(q_obj)
                            next_order += 1

                    assessment.generation_status = Assessment.GenerationStatus.READY
                    assessment.provider_used = f"{getattr(active_llm, 'provider_name', active_llm.__class__.__name__)} ({getattr(active_llm, 'model_name', 'default')})"
                    assessment.generation_error = ""
                    assessment.save(update_fields=["generation_status", "provider_used", "generation_error"])

                    logger.info(
                        f"Successfully generated batch of {len(created_objs)} questions for '{assessment.title}' in {latency_ms}ms"
                    )
                    return list(assessment.questions.all().order_by("order"))

                except (QuestionValidationError, json.JSONDecodeError) as val_err:
                    last_error = val_err
                    logger.warning(f"Batch generation validation error on attempt {attempt_idx + 1}: {val_err}")
                    current_prompt = (
                        f"{user_prompt}\n\n"
                        f"NOTE: Your previous attempt failed with error: {val_err}. "
                        f"Please return ONLY a valid JSON object with key 'questions' containing 10 valid question objects."
                    )
                    continue

                except Exception as e:
                    last_error = e
                    logger.error(f"Batch LLM call failed on attempt {attempt_idx + 1}: {e}")
                    if isinstance(e, (ProviderNotConfiguredError, ProviderUnavailableError)):
                        raise
                    continue

            # If retries exhausted but we got at least some questions
            final_qs = list(assessment.questions.all().order_by("order"))
            if final_qs:
                assessment.generation_status = Assessment.GenerationStatus.READY
                assessment.save(update_fields=["generation_status"])
                return final_qs

            raise RuntimeError(
                f"Failed to generate assessment batch after {1 + cls.MAX_RETRIES} attempts. Last error: {last_error}"
            )

        except (ProviderNotConfiguredError, ProviderUnavailableError) as prov_err:
            assessment.generation_status = Assessment.GenerationStatus.FAILED
            assessment.generation_error = prov_err.message
            assessment.save(update_fields=["generation_status", "generation_error"])
            logger.error(f"Provider error for assessment {assessment.id}: {prov_err.message}")
            raise

        except Exception as e:
            assessment.generation_status = Assessment.GenerationStatus.FAILED
            assessment.generation_error = str(e)
            assessment.save(update_fields=["generation_status", "generation_error"])
            logger.error(f"Batch generation failure for assessment {assessment.id}: {e}")
            raise

        finally:
            cache.delete(lock_key)

    @classmethod
    def get_or_generate_question(
        cls,
        assessment: Assessment,
        requested_order: Optional[int] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> Question:
        """
        Returns an existing question at the requested order, or generates the assessment batch in a single query.
        If requested_order already exists in the database, returns it immediately without calling LLM.
        """
        existing_questions = list(assessment.questions.all().order_by("order"))
        current_count = len(existing_questions)

        # 1. If 0 questions exist, generate all 10 questions in a SINGLE batch LLM query upfront!
        if current_count == 0:
            logger.info(
                f"Zero questions exist for assessment '{assessment.title}'. Generating complete batch of {assessment.target_questions_count} questions."
            )
            cls.generate_assessment_questions_batch(
                assessment=assessment,
                target_count=assessment.target_questions_count,
                llm_provider=llm_provider,
            )
            existing_questions = list(assessment.questions.all().order_by("order"))
            current_count = len(existing_questions)

        target_order = requested_order if requested_order is not None else 1

        # 2. Caching check: Does this question already exist?
        for q in existing_questions:
            if q.order == target_order:
                logger.info(
                    f"Question order {target_order} for assessment {assessment.id} already cached. Returning without LLM call."
                )
                return q

        # Ensure we don't exceed target count
        if target_order > assessment.target_questions_count:
            # If all target questions exist, return the last one
            if existing_questions:
                return existing_questions[-1]
            target_order = assessment.target_questions_count

        # 2. Concurrency Lock: Prevent duplicate concurrent generation requests
        lock_key = f"assess_gen_lock_{assessment.id}_{target_order}"
        acquired = cache.add(lock_key, "generating", timeout=cls.LOCK_TIMEOUT_SECONDS)

        if not acquired:
            # Another request is currently generating this question.
            # Wait briefly to see if it finishes and persists the question.
            for _ in range(6):
                time.sleep(1.0)
                q_cached = assessment.questions.filter(order=target_order).first()
                if q_cached:
                    return q_cached

            raise ConcurrentGenerationError(
                f"Question {target_order} for assessment '{assessment.title}' is currently being generated. Please wait."
            )

        try:
            # Re-check under lock in case it was created right before lock acquisition
            q_cached = assessment.questions.filter(order=target_order).first()
            if q_cached:
                return q_cached

            # 3. Resolve Provider without silent fallback
            active_llm = AssessmentProviderResolver.get_provider_for_difficulty(
                difficulty=assessment.difficulty_level,
                override_provider=llm_provider,
            )

            # Mark assessment status as generating
            assessment.generation_status = Assessment.GenerationStatus.GENERATING
            assessment.save(update_fields=["generation_status"])

            # 4. Context-aware prompt generation
            existing_prompts = [q.prompt for q in existing_questions]
            user_prompt = cls._build_context_prompt(
                skill=assessment.skill,
                topic=assessment.topic,
                difficulty=assessment.difficulty_level,
                existing_prompts=existing_prompts,
                question_number=target_order,
                total_questions=assessment.target_questions_count,
            )

            # 5. LLM Call with Bounded Retries
            question = cls._generate_with_bounded_retries(
                assessment=assessment,
                active_llm=active_llm,
                user_prompt=user_prompt,
                existing_prompts=existing_prompts,
                target_order=target_order,
            )

            # 6. Check if assessment is now fully generated
            total_now = assessment.questions.count()
            if total_now >= assessment.target_questions_count:
                assessment.generation_status = Assessment.GenerationStatus.READY
            else:
                assessment.generation_status = Assessment.GenerationStatus.PENDING

            assessment.provider_used = f"{getattr(active_llm, 'provider_name', active_llm.__class__.__name__)} ({getattr(active_llm, 'model_name', 'default')})"
            assessment.generation_error = ""
            assessment.save(update_fields=["generation_status", "provider_used", "generation_error"])

            return question

        except (ProviderNotConfiguredError, ProviderUnavailableError) as prov_err:
            assessment.generation_status = Assessment.GenerationStatus.FAILED
            assessment.generation_error = prov_err.message
            assessment.save(update_fields=["generation_status", "generation_error"])
            logger.error(f"Provider error for assessment {assessment.id}: {prov_err.message}")
            raise

        except Exception as e:
            assessment.generation_status = Assessment.GenerationStatus.FAILED
            assessment.generation_error = str(e)
            assessment.save(update_fields=["generation_status", "generation_error"])
            logger.error(f"Generation failure for assessment {assessment.id}: {e}")
            raise

        finally:
            cache.delete(lock_key)

    @classmethod
    def _build_batch_context_prompt(
        cls,
        skill: Optional[Skill],
        topic: Optional[Topic],
        difficulty: str,
        target_count: int = 10,
    ) -> str:
        """Constructs rich contextual prompt to generate all questions in a single query."""
        topic_obj = topic or (skill.topic if skill else None)
        domain_obj = topic_obj.domain if topic_obj else None

        lines = [
            f"Generate a complete {target_count}-question assessment in a single JSON response.",
        ]
        if domain_obj:
            lines.append(f"Domain: {domain_obj.name}")
        if topic_obj:
            lines.append(f"Topic: {topic_obj.name}")
        if skill:
            lines.append(f"Skill: {skill.name}")
            if skill.description:
                lines.append(f"Skill Scope & Description: {skill.description}")
            if skill.key_concepts:
                concepts_str = ", ".join(str(c) for c in skill.key_concepts)
                lines.append(f"Key Concepts to Test: {concepts_str}")
            if skill.learning_objectives:
                objectives_str = ", ".join(str(o) for o in skill.learning_objectives)
                lines.append(f"Learning Objectives: {objectives_str}")
            prereqs = list(skill.prerequisites.values_list("name", flat=True))
            if prereqs:
                lines.append(f"Prerequisites: {', '.join(prereqs)}")

        lines.append(f"Target Difficulty: {difficulty.upper()}")
        lines.append(
            f"\nGenerate exactly {target_count} distinct questions in raw JSON starting with '{{' and ending with '}}'. "
            f"Do NOT include markdown backticks (```) around the JSON. Output raw JSON only."
        )
        return "\n".join(lines)

    @classmethod
    def _build_context_prompt(
        cls,
        skill: Optional[Skill],
        topic: Optional[Topic],
        difficulty: str,
        existing_prompts: List[str],
        question_number: int,
        total_questions: int,
    ) -> str:
        """Constructs rich contextual prompt passing only relevant skill data."""
        topic_obj = topic or (skill.topic if skill else None)
        domain_obj = topic_obj.domain if topic_obj else None

        lines = [
            f"Assessment: Question {question_number} of {total_questions}",
        ]
        if domain_obj:
            lines.append(f"Domain: {domain_obj.name}")
        if topic_obj:
            lines.append(f"Topic: {topic_obj.name}")
        if skill:
            lines.append(f"Skill: {skill.name}")
            if skill.description:
                lines.append(f"Skill Scope & Description: {skill.description}")
            if skill.key_concepts:
                concepts_str = ", ".join(str(c) for c in skill.key_concepts)
                lines.append(f"Key Concepts: {concepts_str}")
            if skill.learning_objectives:
                objectives_str = ", ".join(str(o) for o in skill.learning_objectives)
                lines.append(f"Learning Objectives: {objectives_str}")
            prereqs = list(skill.prerequisites.values_list("name", flat=True))
            if prereqs:
                lines.append(f"Prerequisites: {', '.join(prereqs)}")

        lines.append(f"Target Difficulty: {difficulty.upper()}")

        if existing_prompts:
            lines.append("\nPreviously generated questions in this assessment (DO NOT duplicate topics or phrasing):")
            for idx, p in enumerate(existing_prompts, start=1):
                clean_p = p.replace("\n", " ")[:140]
                lines.append(f"- Q{idx}: {clean_p}")

        lines.append("\nGenerate 1 new, distinct multiple-choice question in the required JSON format.")
        return "\n".join(lines)

    @classmethod
    def _generate_with_bounded_retries(
        cls,
        assessment: Assessment,
        active_llm: BaseLLMProvider,
        user_prompt: str,
        existing_prompts: List[str],
        target_order: int,
    ) -> Question:
        """Executes LLM generation with server-side validation and up to MAX_RETRIES retries."""
        last_error = None
        current_prompt = user_prompt
        skill_name = assessment.skill.name if assessment.skill else assessment.title

        for attempt_idx in range(1 + cls.MAX_RETRIES):
            start_time = time.perf_counter()
            try:
                response = active_llm.generate(
                    prompt=current_prompt,
                    system_prompt=MCQ_GENERATION_SYSTEM_PROMPT,
                    temperature=0.3,
                )
                raw_text = response.text
                latency_ms = int((time.perf_counter() - start_time) * 1000)

                # Parse JSON
                parsed_dict = QuestionValidator.parse_raw_response(raw_text)

                # Server-side validation
                sanitized = QuestionValidator.validate_and_sanitize_question(
                    raw_data=parsed_dict,
                    skill_name=skill_name,
                    existing_prompts=existing_prompts,
                )

                # Determine points based on difficulty
                points = AssessmentScoringRules.get_points_for_question("mcq", assessment.difficulty_level)

                # Save Question to Database
                with transaction.atomic():
                    question = Question.objects.create(
                        assessment=assessment,
                        question_type=Question.QuestionType.MCQ,
                        difficulty_level=assessment.difficulty_level,
                        prompt=sanitized["prompt"],
                        options=sanitized["options"],
                        correct_answer=sanitized["correct_answer"],
                        distractor_explanations=sanitized.get("distractor_explanations", {}),
                        rubric={"explanation": sanitized["explanation"]},
                        concept=sanitized["concept"],
                        points=points,
                        order=target_order,
                        generation_metadata={
                            "provider": getattr(active_llm, "provider_name", active_llm.__class__.__name__),
                            "model": getattr(active_llm, "model_name", "unknown"),
                            "latency_ms": latency_ms,
                            "attempt": attempt_idx + 1,
                        },
                    )
                logger.info(
                    f"Generated Q{target_order} for assessment '{assessment.title}' in {latency_ms}ms (attempt {attempt_idx + 1})"
                )
                return question

            except (QuestionValidationError, json.JSONDecodeError) as val_err:
                last_error = val_err
                logger.warning(
                    f"Validation error on attempt {attempt_idx + 1}/{1 + cls.MAX_RETRIES} for assessment {assessment.id}: {val_err}"
                )
                # Formulate corrective prompt for retry
                current_prompt = (
                    f"{user_prompt}\n\n"
                    f"NOTE: Your previous attempt failed validation with error: {val_err}. "
                    f"Please correct this and return ONLY valid JSON matching the exact schema."
                )
                continue

            except Exception as e:
                # If provider itself failed (e.g. ConnectionError, Timeout), don't retry locally if fatal
                last_error = e
                logger.error(f"LLM call failed on attempt {attempt_idx + 1}: {e}")
                if isinstance(e, (ProviderNotConfiguredError, ProviderUnavailableError)):
                    raise
                continue

        # If bounded retries exhausted
        raise RuntimeError(
            f"Failed to generate valid question after {1 + cls.MAX_RETRIES} attempts. Last error: {last_error}"
        )
