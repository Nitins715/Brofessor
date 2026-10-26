from dataclasses import dataclass
from decimal import Decimal
import json
import logging
import re
from typing import Any, Dict, Optional

from apps.assessments.models import Question
from apps.rag.llm import BaseLLMProvider, get_llm_provider
from .scoring import AssessmentScoringRules

logger = logging.getLogger("brofessor")

EVALUATION_SYSTEM_PROMPT = """You are Brofessor's expert academic answer evaluator.
Evaluate the user's response against the question prompt, reference answer, and evaluation rubric.

Assess:
1. Conceptual Correctness: Did the user accurately state the concepts and principles?
2. Completeness: Did the user cover the essential points and criteria?
3. Explanation Quality: Is the reasoning logical, precise, and well-articulated?

Award a normalized accuracy score between 0.00 and 1.00:
- 1.00: Completely correct and thorough explanation.
- 0.70 - 0.90: Good answer, minor gaps or slight imprecision.
- 0.40 - 0.60: Partial credit, core concept mentioned but significant gaps or inaccuracies.
- 0.10 - 0.30: Mostly incorrect, tangential or vague response.
- 0.00: Completely incorrect, irrelevant, or missing.

Respond ONLY with valid JSON in this exact structure:
{
  "accuracy": 0.85,
  "is_correct": true,
  "feedback": "Clear explanation of X. Missed the edge case regarding Y."
}

Do not include any text outside the JSON."""


@dataclass
class EvaluationResult:
    """Outcome of grading an individual answer."""
    accuracy: float
    score_awarded: Decimal
    is_correct: bool
    feedback: str


class AnswerEvaluationService:
    """
    Evaluates assessment answers.
    Evaluates MCQs deterministically and uses LLM for textual and explanation questions.
    Keeps evaluation logic strictly independent of question generation.
    """

    @classmethod
    def evaluate(
        cls,
        question: Question,
        user_response: str,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> EvaluationResult:
        """Route to appropriate evaluation strategy based on question type."""
        clean_response = (user_response or "").strip()

        if question.question_type == Question.QuestionType.MCQ:
            return cls._evaluate_mcq(question, clean_response)
        else:
            return cls._evaluate_textual(question, clean_response, llm_provider)

    @classmethod
    def _evaluate_mcq(cls, question: Question, user_response: str) -> EvaluationResult:
        """Deterministic evaluation for multiple choice questions."""
        if not user_response:
            return EvaluationResult(
                accuracy=0.0,
                score_awarded=Decimal("0.00"),
                is_correct=False,
                feedback="No answer selected.",
            )

        correct = (question.correct_answer or "").strip()
        user_norm = user_response.strip().upper()
        correct_norm = correct.upper()

        is_match = False

        # Direct key match (e.g. 'A' == 'A')
        if user_norm == correct_norm:
            is_match = True
        else:
            # Check if user passed full option text matching correct option
            for opt in question.options:
                opt_key = str(opt.get("key", "")).strip().upper()
                opt_text = str(opt.get("text", "")).strip().lower()
                if opt_key == correct_norm and (
                    user_response.lower() == opt_text or user_norm == opt_key
                ):
                    is_match = True
                    break

        accuracy = 1.0 if is_match else 0.0
        awarded = AssessmentScoringRules.calculate_awarded_points(question.points, accuracy)

        explanation = (question.rubric or {}).get("explanation", "")
        distractors = question.distractor_explanations or {}
        user_distractor = distractors.get(user_norm, "")

        if is_match:
            feedback = f"Correct! {explanation}".strip()
        else:
            if user_distractor:
                feedback = f"Incorrect. Option {user_norm} is incorrect: {user_distractor} Correct answer is {correct}: {explanation}".strip()
            else:
                feedback = f"Incorrect. The correct answer is {correct}. {explanation}".strip()

        return EvaluationResult(
            accuracy=accuracy,
            score_awarded=awarded,
            is_correct=is_match,
            feedback=feedback,
        )

    @classmethod
    def _evaluate_textual(
        cls,
        question: Question,
        user_response: str,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> EvaluationResult:
        """LLM-based evaluation for conceptual, textual, and project explanation answers."""
        if not user_response:
            return EvaluationResult(
                accuracy=0.0,
                score_awarded=Decimal("0.00"),
                is_correct=False,
                feedback="No answer provided.",
            )

        rubric_str = json.dumps(question.rubric) if question.rubric else "None"
        prompt = (
            f"Question Prompt:\n{question.prompt}\n\n"
            f"Reference Solution / Key Points:\n{question.correct_answer}\n\n"
            f"Evaluation Rubric:\n{rubric_str}\n\n"
            f"User's Submitted Answer:\n{user_response}\n\n"
            f"JSON Evaluation:"
        )

        active_llm = llm_provider or get_llm_provider()
        try:
            response = active_llm.generate(
                prompt=prompt,
                system_prompt=EVALUATION_SYSTEM_PROMPT,
                temperature=0.1,
            )
            raw_text = response.text
        except Exception as e:
            logger.error(f"LLM answer evaluation failed: {e}")
            # Fallback evaluation on error
            return EvaluationResult(
                accuracy=0.5,
                score_awarded=AssessmentScoringRules.calculate_awarded_points(question.points, 0.5),
                is_correct=False,
                feedback="Answer recorded. Automated evaluation temporarily encountered an issue.",
            )

        parsed = cls._parse_json(raw_text)
        accuracy_val = parsed.get("accuracy", 0.0)
        try:
            accuracy = max(0.0, min(1.0, float(accuracy_val)))
        except (ValueError, TypeError):
            accuracy = 0.0

        is_correct = parsed.get("is_correct", accuracy >= 0.70)
        feedback = parsed.get("feedback", "Evaluation complete.")

        awarded = AssessmentScoringRules.calculate_awarded_points(question.points, accuracy)

        logger.info(
            f"Evaluated textual answer for Q{question.order}: accuracy={accuracy}, "
            f"awarded={awarded}/{question.points}pts"
        )

        return EvaluationResult(
            accuracy=accuracy,
            score_awarded=awarded,
            is_correct=is_correct,
            feedback=feedback,
        )

    @classmethod
    def _parse_json(cls, text: str) -> Dict[str, Any]:
        """Safely extract JSON from evaluator output."""
        if not text:
            return {}
        clean = text.strip()
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if m:
            clean = m.group(1).strip()
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start : end + 1]
        try:
            return json.loads(clean)
        except json.JSONDecodeError:
            return {}
