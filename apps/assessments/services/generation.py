import json
import logging
import re
from typing import Any, Dict, List, Optional
from django.db import transaction

from apps.assessments.models import Assessment, Question
from apps.roadmap.models import Skill, Topic
from apps.knowledge.models import Concept
from apps.rag.llm import BaseLLMProvider, get_llm_provider
from .scoring import AssessmentScoringRules

logger = logging.getLogger("brofessor")

GENERATION_SYSTEM_PROMPT = """You are Brofessor's expert educational assessment engine.
Generate a structured, rigorous assessment evaluating the user's comprehension of the specified skill or topic.

You MUST produce a JSON object with a "questions" array containing exactly 4 questions:
1. One Basic MCQ testing foundational definitions or core syntax (points: 1).
2. One Medium MCQ testing practical application or behavior (points: 2).
3. One Medium Textual / Conceptual Question requiring concise analysis (points: 3).
4. One Project / Concept Explanation Question asking the user to explain an architectural scenario, trade-off, or implementation (points: 5).

Respond ONLY with valid JSON in this exact structure:
{
  "questions": [
    {
      "question_type": "mcq",
      "difficulty_level": "basic",
      "prompt": "What is the primary function of...",
      "options": [
        {"key": "A", "text": "Option A text"},
        {"key": "B", "text": "Option B text"},
        {"key": "C", "text": "Option C text"},
        {"key": "D", "text": "Option D text"}
      ],
      "correct_answer": "A",
      "rubric": {
        "explanation": "Why option A is correct and others are incorrect."
      }
    },
    {
      "question_type": "mcq",
      "difficulty_level": "intermediate",
      "prompt": "In a scenario where...",
      "options": [
        {"key": "A", "text": "Option A"},
        {"key": "B", "text": "Option B"},
        {"key": "C", "text": "Option C"},
        {"key": "D", "text": "Option D"}
      ],
      "correct_answer": "B",
      "rubric": {"explanation": "Detailed explanation."}
    },
    {
      "question_type": "textual",
      "difficulty_level": "intermediate",
      "prompt": "Explain the difference between X and Y and when you would choose one over the other.",
      "options": [],
      "correct_answer": "Expected reference response covering key aspects of X vs Y.",
      "rubric": {
        "key_points": ["Definition of X", "Definition of Y", "Trade-off scenario"],
        "criteria": "Evaluates conceptual accuracy and clear comparison."
      }
    },
    {
      "question_type": "explanation",
      "difficulty_level": "advanced",
      "prompt": "Describe how you would design or implement...",
      "options": [],
      "correct_answer": "Comprehensive architectural solution covering design, components, and edge cases.",
      "rubric": {
        "key_points": ["System architecture", "Data flow", "Edge cases/resilience"],
        "criteria": "Evaluates practical depth and explanation quality."
      }
    }
  ]
}

Do not include any text or markdown formatting outside the valid JSON."""


class QuestionGenerationService:
    """
    Generates assessment questions targeted to a Skill or Topic using the LLM provider.
    Applies the finalized scoring rules to each question.
    """

    @classmethod
    def generate_for_assessment(
        cls,
        assessment: Assessment,
        llm_provider: Optional[BaseLLMProvider] = None,
    ) -> List[Question]:
        """
        Generate and persist questions for an Assessment instance.
        """
        skill = assessment.skill
        topic = assessment.topic or (skill.topic if skill else None)
        diff_level = assessment.difficulty_level or "intermediate"

        # Context gathering
        target_name = skill.name if skill else (topic.name if topic else assessment.title)
        target_desc = skill.description if skill else (topic.description if topic else "")

        # Incorporate known concepts linked to the skill if available
        related_concepts = []
        if skill:
            related_concepts = list(skill.concepts.values_list("name", flat=True)[:5])

        concepts_str = f"Related concepts: {', '.join(related_concepts)}." if related_concepts else ""

        prompt = (
            f"Generate an assessment for:\n"
            f"Target: {target_name}\n"
            f"Description: {target_desc}\n"
            f"Target Difficulty: {diff_level.upper()}\n"
            f"{concepts_str}\n\n"
            f"JSON Output:"
        )

        active_llm = llm_provider or get_llm_provider()
        logger.info(f"Generating questions for Assessment '{assessment.title}' via LLM [{active_llm.model_name}]")

        try:
            response = active_llm.generate(
                prompt=prompt,
                system_prompt=GENERATION_SYSTEM_PROMPT,
                temperature=0.2,
            )
            raw_text = response.text
        except Exception as e:
            logger.error(f"Failed to generate assessment questions: {e}")
            assessment.status = Assessment.AssessmentStatus.FAILED
            assessment.save(update_fields=["status"])
            raise RuntimeError(f"Question generation failed: {e}") from e

        parsed = cls._parse_json(raw_text)
        question_data_list = parsed.get("questions", [])

        if not question_data_list:
            logger.warning(f"No questions parsed from LLM response for {assessment.title}. Raw: {raw_text[:200]}")
            assessment.status = Assessment.AssessmentStatus.FAILED
            assessment.save(update_fields=["status"])
            return []

        created_questions: List[Question] = []

        with transaction.atomic():
            # Clear any existing draft questions
            assessment.questions.all().delete()

            for idx, q_dict in enumerate(question_data_list, start=1):
                q_type = q_dict.get("question_type", "mcq").lower()
                q_diff = q_dict.get("difficulty_level", diff_level).lower()

                # Calculate standard points
                points = AssessmentScoringRules.get_points_for_question(q_type, q_diff)

                q_obj = Question.objects.create(
                    assessment=assessment,
                    question_type=q_type,
                    difficulty_level=q_diff,
                    prompt=q_dict.get("prompt", f"Question {idx}").strip(),
                    options=q_dict.get("options", []),
                    correct_answer=q_dict.get("correct_answer", "").strip(),
                    rubric=q_dict.get("rubric", {}),
                    points=points,
                    order=idx,
                )
                created_questions.append(q_obj)

            assessment.status = Assessment.AssessmentStatus.ACTIVE
            assessment.save(update_fields=["status"])

        logger.info(f"Successfully generated {len(created_questions)} questions for Assessment '{assessment.title}'")
        return created_questions

    @classmethod
    def _parse_json(cls, text: str) -> Dict[str, Any]:
        """Extract and parse JSON safely from LLM output."""
        if not text:
            return {}

        clean = text.strip()
        # Handle code blocks ```json ... ```
        m = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean)
        if m:
            clean = m.group(1).strip()

        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start : end + 1]

        try:
            return json.loads(clean)
        except json.JSONDecodeError as err:
            logger.warning(f"Failed to parse questions JSON: {err}")
            return {}
