from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class Assessment(BaseModel):
    """Assessment suite targeting a skill or topic evaluation."""
    class AssessmentStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        ACTIVE = "active", "Active"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    class DifficultyLevel(models.TextChoices):
        EASY = "easy", "Easy"
        MEDIUM = "medium", "Medium"
        HARD = "hard", "Hard"
        BASIC = "basic", "Basic"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"
        EXPERT = "expert", "Expert"

    class GenerationStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        GENERATING = "generating", "Generating"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessments",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assessments",
    )
    status = models.CharField(
        max_length=32,
        choices=AssessmentStatus.choices,
        default=AssessmentStatus.ACTIVE,
        db_index=True,
    )
    difficulty_level = models.CharField(
        max_length=32,
        choices=DifficultyLevel.choices,
        default=DifficultyLevel.EASY,
        db_index=True,
    )
    generation_status = models.CharField(
        max_length=32,
        choices=GenerationStatus.choices,
        default=GenerationStatus.PENDING,
        db_index=True,
    )
    generation_error = models.TextField(blank=True, help_text="Error message from last LLM generation attempt")
    target_questions_count = models.PositiveIntegerField(
        default=10,
        help_text="Target number of questions in this assessment",
    )
    provider_used = models.CharField(max_length=64, blank=True, help_text="LLM provider and model recorded for generation audit")
    passing_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=70.00,
        help_text="Passing threshold percentage (e.g. 70.00%).",
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Optional time limit in minutes.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Assessment"
        verbose_name_plural = "Assessments"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["skill", "difficulty_level", "is_active"]),
        ]

    def __str__(self):
        return f"{self.title} [{self.difficulty_level.upper()}] - {self.status}"


class Question(BaseModel):
    """Individual question within an Assessment supporting MCQ, textual, or code answers."""
    class QuestionType(models.TextChoices):
        MCQ = "mcq", "Multiple Choice"
        TEXTUAL = "textual", "Textual / Conceptual"
        EXPLANATION = "explanation", "Explanation / Project-based"
        CODE = "code", "Code / Practical"

    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="questions")
    question_type = models.CharField(
        max_length=32,
        choices=QuestionType.choices,
        default=QuestionType.MCQ,
    )
    difficulty_level = models.CharField(
        max_length=32,
        default="easy",
        help_text="easy, medium, hard, basic, intermediate, advanced",
    )
    concept = models.CharField(
        max_length=255,
        blank=True,
        db_index=True,
        help_text="Specific concept or tag tested by this question (e.g. 'Identity Operators')",
    )
    prompt = models.TextField(help_text="Question text or prompt.")
    options = models.JSONField(
        default=list,
        blank=True,
        help_text="For MCQ: list of options, e.g. [{'key': 'A', 'text': '...'}]",
    )
    correct_answer = models.TextField(
        blank=True,
        help_text="Correct option key for MCQ, or reference solution for textual evaluation.",
    )
    distractor_explanations = models.JSONField(
        default=dict,
        blank=True,
        help_text="Explanations for why incorrect options (distractors) are wrong: {'B': '...'}",
    )
    rubric = models.JSONField(
        default=dict,
        blank=True,
        help_text="Grading criteria, key points required, or solution explanation.",
    )
    generation_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Latency, provider, tokens used, and attempt details",
    )
    points = models.PositiveIntegerField(default=1)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        ordering = ["assessment", "order"]
        indexes = [
            models.Index(fields=["assessment", "order"]),
            models.Index(fields=["concept"]),
        ]

    def __str__(self):
        return f"Q{self.order} ({self.get_question_type_display()} - {self.points}pts): {self.prompt[:50]}"


class Attempt(BaseModel):
    """An instance of a user taking an Assessment."""
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE, related_name="attempts")
    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)
    total_points_possible = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    total_points_awarded = models.DecimalField(max_digits=6, decimal_places=2, default=0.00)
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Achieved score percentage (0.00 to 100.00).",
    )
    passed = models.BooleanField(null=True, blank=True)
    concept_scores = models.JSONField(
        default=dict,
        blank=True,
        help_text="Performance aggregated by concept/tag: {concept: {correct: int, total: int, accuracy: float}}",
    )
    weak_concepts = models.JSONField(
        default=list,
        blank=True,
        help_text="List of weak concepts requiring targeted remediation",
    )
    feedback = models.TextField(blank=True)

    class Meta:
        verbose_name = "Assessment Attempt"
        verbose_name_plural = "Assessment Attempts"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["assessment", "started_at"]),
        ]

    def __str__(self):
        status_str = "Passed" if self.passed else ("Failed" if self.passed is False else "In progress")
        return f"{self.assessment.title} Attempt - {status_str} ({self.score}%)"


class Answer(BaseModel):
    """User answer submission for an individual question during an attempt."""
    attempt = models.ForeignKey(Attempt, on_delete=models.CASCADE, related_name="answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    user_response = models.TextField()
    response_time_seconds = models.FloatField(
        null=True,
        blank=True,
        help_text="Time taken by user to respond in seconds",
    )
    accuracy = models.FloatField(
        default=0.0,
        help_text="Normalized accuracy value between 0.0 and 1.0.",
    )
    score_awarded = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    is_correct = models.BooleanField(null=True, blank=True)
    feedback = models.TextField(blank=True)

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        unique_together = [("attempt", "question")]
        indexes = [
            models.Index(fields=["attempt", "question"]),
        ]

    def __str__(self):
        return f"Ans: {self.attempt_id} - Q{self.question.order} (Accuracy: {self.accuracy})"
