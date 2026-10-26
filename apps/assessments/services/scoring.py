from decimal import Decimal
from typing import Tuple


class AssessmentScoringRules:
    """
    Standard scoring rules for Brofessor assessments:
    - Basic MCQ -> 1 point
    - Medium MCQ (Intermediate/Advanced/Expert) -> 2 points
    - Medium textual / conceptual question -> 3 points
    - Project / concept explanation question -> 5 points
    """

    @classmethod
    def get_points_for_question(cls, question_type: str, difficulty_level: str = "basic") -> int:
        q_type = (question_type or "mcq").lower().strip()
        diff = (difficulty_level or "basic").lower().strip()

        if q_type == "mcq":
            if diff in ("basic", "beginner", "easy"):
                return 1
            else:
                return 2  # Medium / Advanced / Expert MCQ
        elif q_type in ("textual", "code", "conceptual"):
            if diff in ("basic", "beginner"):
                return 2
            else:
                return 3  # Medium textual question
        elif q_type in ("explanation", "project"):
            return 5  # Project / concept explanation
        else:
            return 2

    @classmethod
    def calculate_awarded_points(cls, max_points: int, accuracy: float) -> Decimal:
        """
        Calculate awarded points from max points and normalized accuracy (0.0 to 1.0).
        awarded_points = maximum_points * accuracy
        """
        norm_accuracy = max(0.0, min(1.0, float(accuracy)))
        raw_awarded = float(max_points) * norm_accuracy
        return Decimal(str(round(raw_awarded, 2)))
