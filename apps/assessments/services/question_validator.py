import json
import logging
import re
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("brofessor")


class QuestionValidationError(Exception):
    """Raised when an LLM-generated question fails schema or semantic validation."""
    pass


class QuestionValidator:
    """
    Strict server-side validation and sanitization for LLM-generated multiple-choice questions.
    Ensures:
    - Well-formed JSON
    - Non-empty prompt
    - Exactly 4 unique options labelled A, B, C, D
    - Exactly one valid correct answer in {'A', 'B', 'C', 'D'}
    - Clear explanation of the correct solution
    - Explanations for distractor options
    - Concept tag
    """

    EXPECTED_KEYS = {"A", "B", "C", "D"}

    @classmethod
    def parse_raw_response(cls, text: str) -> Dict[str, Any]:
        """Extracts JSON object from raw LLM text output."""
        if not text or not isinstance(text, str):
            raise QuestionValidationError("LLM response is empty or non-textual.")

        clean = text.strip()

        # Strip outer markdown code block fences if present at boundary
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
            if clean.rstrip().endswith("```"):
                clean = clean.rstrip()[:-3]
            clean = clean.strip()

        # Find enclosing JSON brackets
        start = clean.find("{")
        end = clean.rfind("}")
        if start != -1 and end != -1 and end > start:
            clean = clean[start : end + 1]

        try:
            parsed = json.loads(clean, strict=False)
        except json.JSONDecodeError as err:
            raise QuestionValidationError(f"Invalid JSON format in LLM output: {err}") from err

        if not isinstance(parsed, dict):
            raise QuestionValidationError("Expected JSON object at top level.")

        return parsed

    @classmethod
    def parse_raw_batch_response(cls, text: str) -> List[Dict[str, Any]]:
        """
        Extracts a list of question JSON objects from raw batch LLM output.
        Accepts:
        - {"questions": [ ... ]}
        - [ { ... }, { ... } ]
        - Single question object: {"prompt": "...", "options": ...}
        - Object with any key containing a list of question dicts
        """
        if not text or not isinstance(text, str):
            raise QuestionValidationError("LLM response is empty or non-textual.")

        clean = text.strip()

        # Strip outer markdown code block fences if present at boundary
        if clean.startswith("```"):
            clean = clean.split("\n", 1)[-1]
            if clean.rstrip().endswith("```"):
                clean = clean.rstrip()[:-3]
            clean = clean.strip()

        # Locate outermost JSON structure directly by finding first and last brackets
        first_curly = clean.find("{")
        first_square = clean.find("[")

        target_json = clean
        if first_square != -1 and (first_curly == -1 or first_square < first_curly):
            last_square = clean.rfind("]")
            if last_square > first_square:
                target_json = clean[first_square : last_square + 1]
        elif first_curly != -1:
            last_curly = clean.rfind("}")
            if last_curly > first_curly:
                target_json = clean[first_curly : last_curly + 1]

        try:
            parsed = json.loads(target_json, strict=False)
        except json.JSONDecodeError as err:
            raise QuestionValidationError(f"Invalid JSON format in batch LLM output: {err}") from err

        raw_list = []
        if isinstance(parsed, list):
            raw_list = parsed
        elif isinstance(parsed, dict):
            if "questions" in parsed and isinstance(parsed["questions"], list):
                raw_list = parsed["questions"]
            elif "prompt" in parsed and "options" in parsed:
                # Single question object passed to batch parser
                raw_list = [parsed]
            else:
                for v in parsed.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict):
                        raw_list = v
                        break

        if not raw_list:
            raise QuestionValidationError("No valid list of questions found in LLM output.")

        return [item for item in raw_list if isinstance(item, dict)]

    @classmethod
    def validate_and_sanitize_question(
        cls,
        raw_data: Dict[str, Any],
        skill_name: Optional[str] = None,
        existing_prompts: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Validates structure and semantics of a single generated question payload.
        Returns cleaned dictionary ready for database persistence.
        """
        # 1. Prompt validation
        prompt = str(raw_data.get("prompt") or "").strip()
        if len(prompt) < 10:
            raise QuestionValidationError("Question prompt is missing or too short (minimum 10 characters).")

        # Validate that prompt referencing a code snippet actually includes code
        prompt_lower = prompt.lower()
        mentions_code = any(
            phrase in prompt_lower
            for phrase in [
                "following code",
                "following snippet",
                "following python",
                "following expression",
                "this code snippet",
                "this python code",
                "output of the",
                "result of the",
            ]
        )
        has_code_content = (
            "```" in prompt
            or "`" in prompt
            or "\n" in prompt
            or any(sym in prompt for sym in ["def ", "print(", "class ", " = ", "==", "for ", "while ", "+", "-", "*", "/", "%", ">", "<"])
        )
        if mentions_code and not has_code_content:
            explanation = str(raw_data.get("explanation") or "")
            code_in_expl = re.findall(r"`([^`]+)`", explanation)
            rescued_code = None
            if code_in_expl:
                rescued_code = code_in_expl[0].strip()
            else:
                expr_in_expl = re.findall(r"\(([a-zA-Z0-9_\s\+\-\*\/\%\=\<\>\.\,]+)\)", explanation)
                for cand in expr_in_expl:
                    if any(op in cand for op in ["+", "-", "*", "/", "%", "=", "<", ">", "print"]):
                        rescued_code = cand.strip()
                        break

            if rescued_code:
                prompt = f"{prompt}\n\n```python\n{rescued_code}\n```"
                logger.info(f"Auto-rescued missing code snippet into prompt: '{rescued_code}'")
            else:
                raise QuestionValidationError(
                    "Question prompt mentions a code snippet or expression, but omitted the code block. "
                    "Please embed the code snippet using ```python ... ```."
                )

        # Duplicate check against existing questions for this skill
        if existing_prompts:
            clean_existing = [p.lower().strip() for p in existing_prompts]
            if prompt.lower() in clean_existing:
                raise QuestionValidationError("Generated question is a duplicate of a previously generated question.")

        # 2. Options validation
        raw_options = raw_data.get("options")
        if not isinstance(raw_options, list):
            raise QuestionValidationError("Options must be a list of 4 items.")

        if len(raw_options) != 4:
            raise QuestionValidationError(f"Expected exactly 4 options, found {len(raw_options)}.")

        clean_options: List[Dict[str, str]] = []
        found_keys = set()
        seen_texts = set()

        for idx, opt in enumerate(raw_options):
            if isinstance(opt, dict):
                key = str(opt.get("key") or "").upper().strip()
                text = str(opt.get("text") or "").strip()
            elif isinstance(opt, str):
                # Fallback format: "A) Option text" or "A. Option text"
                m_opt = re.match(r"^([A-Da-d])[\)\.:]\s*(.+)$", opt.strip())
                if m_opt:
                    key = m_opt.group(1).upper()
                    text = m_opt.group(2).strip()
                else:
                    default_keys = ["A", "B", "C", "D"]
                    key = default_keys[idx] if idx < 4 else f"OPT_{idx}"
                    text = opt.strip()
            else:
                raise QuestionValidationError(f"Invalid option item at index {idx}.")

            if key not in cls.EXPECTED_KEYS:
                raise QuestionValidationError(f"Option key '{key}' is invalid; must be one of A, B, C, D.")

            if not text:
                raise QuestionValidationError(f"Option '{key}' text is empty.")

            if text.lower() in seen_texts:
                raise QuestionValidationError(f"Duplicate option text detected: '{text}'.")

            seen_texts.add(text.lower())
            found_keys.add(key)
            clean_options.append({"key": key, "text": text})

        if found_keys != cls.EXPECTED_KEYS:
            missing = cls.EXPECTED_KEYS - found_keys
            raise QuestionValidationError(f"Options are missing required keys: {sorted(missing)}.")

        # Sort options cleanly by key A, B, C, D
        clean_options.sort(key=lambda o: o["key"])

        # 3. Correct answer validation
        correct_answer = str(raw_data.get("correct_answer") or "").upper().strip()
        # If full text was passed, match key
        if correct_answer not in cls.EXPECTED_KEYS:
            matched_key = None
            for opt in clean_options:
                if correct_answer.lower() == opt["text"].lower():
                    matched_key = opt["key"]
                    break
            if matched_key:
                correct_answer = matched_key
            else:
                raise QuestionValidationError(
                    f"Correct answer '{correct_answer}' is invalid. Must be one of A, B, C, D."
                )

        # 4. Explanation & Rubric
        explanation = str(raw_data.get("explanation") or "").strip()
        if not explanation:
            rubric_obj = raw_data.get("rubric")
            if isinstance(rubric_obj, dict):
                explanation = str(rubric_obj.get("explanation") or "").strip()

        if not explanation:
            raise QuestionValidationError("Missing explanation for the correct answer.")

        # 5. Distractor explanations (for why wrong options are incorrect)
        distractor_explanations = raw_data.get("distractor_explanations") or {}
        if not isinstance(distractor_explanations, dict):
            distractor_explanations = {}

        # 6. Concept / Tag
        concept = str(raw_data.get("concept") or "").strip()
        if not concept:
            concept = skill_name or "Core Concept"

        return {
            "prompt": prompt,
            "options": clean_options,
            "correct_answer": correct_answer,
            "explanation": explanation,
            "distractor_explanations": distractor_explanations,
            "concept": concept,
        }
