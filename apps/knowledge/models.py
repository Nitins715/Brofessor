from django.db import models
from django.utils import timezone
from apps.core.models import BaseModel


class Concept(BaseModel):
    """Core knowledge entity or atomic concept in a subject area."""
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    domain = models.ForeignKey(
        "roadmap.Domain",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="concepts",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="concepts",
    )
    skills = models.ManyToManyField(
        "roadmap.Skill",
        blank=True,
        related_name="concepts",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Concept"
        verbose_name_plural = "Concepts"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Evidence(BaseModel):
    """
    Immutable raw learning or practical evidence record.
    Keeps raw inputs strictly separated from calculated mastery values.
    """
    class EvidenceType(models.TextChoices):
        DECLARED = "declared", "User-Declared Knowledge"
        PRACTICAL = "practical", "Practical/Project Evidence"
        LEARNING = "learning", "Learning Evidence"
        ASSESSMENT = "assessment", "Assessment Result"

    evidence_type = models.CharField(max_length=32, choices=EvidenceType.choices, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
    )
    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="evidence_items",
    )
    raw_data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Raw payload (e.g. self-ratings, git commit SHAs, quiz scores, note references).",
    )
    confidence_weight = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00,
        help_text="Evaluation weighting factor (0.00 to 1.00).",
    )
    recorded_at = models.DateTimeField(default=timezone.now, db_index=True)

    class Meta:
        verbose_name = "Evidence"
        verbose_name_plural = "Evidence Items"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["evidence_type", "recorded_at"]),
            models.Index(fields=["skill", "evidence_type"]),
        ]

    def __str__(self):
        return f"[{self.get_evidence_type_display()}] {self.title}"


class MasteryLevel(models.TextChoices):
    BEGINNER = "beginner", "Beginner"
    INTERMEDIATE = "intermediate", "Intermediate"
    ADVANCED = "advanced", "Advanced"
    EXPERT = "expert", "Expert"


class CalculatedMastery(BaseModel):
    """
    Aggregated and calculated mastery derived periodically or on-demand from Evidence.
    Separated from raw evidence to enable recalculations and formula revisions.
    """
    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calculated_masteries",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calculated_masteries",
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="calculated_masteries",
    )
    mastery_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Calculated mastery level percentage (0.00 to 100.00).",
    )
    mastery_level = models.CharField(
        max_length=32,
        choices=MasteryLevel.choices,
        default=MasteryLevel.BEGINNER,
        db_index=True,
    )
    knowledge_coverage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Calculated knowledge coverage percentage (0.00 to 100.00).",
    )
    confidence_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0.00,
        help_text="Confidence metric based on evidence freshness and diversity.",
    )
    evidence_count = models.PositiveIntegerField(default=0)
    last_calculated_at = models.DateTimeField(auto_now=True)
    calculation_metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Stores algorithm version, breakdown by evidence type, and intermediate weights.",
    )

    class Meta:
        verbose_name = "Calculated Mastery"
        verbose_name_plural = "Calculated Masteries"
        ordering = ["-last_calculated_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(skill__isnull=False) | models.Q(concept__isnull=False) | models.Q(topic__isnull=False),
                name="mastery_target_required",
            ),
        ]
        indexes = [
            models.Index(fields=["skill", "mastery_score"]),
            models.Index(fields=["topic", "mastery_score"]),
            models.Index(fields=["concept", "mastery_score"]),
            models.Index(fields=["mastery_level"]),
        ]

    def __str__(self):
        target = self.skill.name if self.skill else (self.topic.name if self.topic else (self.concept.name if self.concept else "Unknown"))
        return f"{target}: {self.mastery_score}% [{self.mastery_level}] (Confidence: {self.confidence_score})"


class KnowledgeGap(BaseModel):
    """
    Identified deficiency or weakness between required roadmap expectations and demonstrated knowledge.
    """
    class GapType(models.TextChoices):
        NO_EVIDENCE = "no_evidence", "Little or No Evidence"
        WEAK_COVERAGE = "weak_coverage", "Weak Knowledge Coverage"
        WEAK_ASSESSMENT = "weak_assessment", "Weak Assessment Performance"
        BELOW_ROADMAP_LEVEL = "below_level", "Mastery Below Expected Roadmap Level"

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"

    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="knowledge_gaps",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="knowledge_gaps",
    )
    gap_type = models.CharField(max_length=32, choices=GapType.choices, db_index=True)
    severity = models.CharField(max_length=32, choices=Severity.choices, default=Severity.MEDIUM, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    expected_level = models.CharField(max_length=32, blank=True)
    current_level = models.CharField(max_length=32, blank=True)
    current_score = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)
    target_score = models.DecimalField(max_digits=5, decimal_places=2, default=70.00)
    identified_at = models.DateTimeField(default=timezone.now, db_index=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Knowledge Gap"
        verbose_name_plural = "Knowledge Gaps"
        ordering = ["-identified_at"]
        indexes = [
            models.Index(fields=["status", "severity"]),
            models.Index(fields=["skill", "status"]),
        ]

    def __str__(self):
        target = self.skill.name if self.skill else (self.topic.name if self.topic else "General")
        return f"[{self.severity.upper()}] {self.title} ({target}) - {self.status}"


class Recommendation(BaseModel):
    """
    Actionable next-step recommendation generated to address an identified knowledge gap.
    """
    class ActionType(models.TextChoices):
        REVISE_TOPIC = "revise_topic", "Revise a Topic"
        STUDY_CONCEPT = "study_concept", "Study a Missing Concept"
        READ_SOURCE = "read_source", "Read/Revisit a Source"
        PRACTICE_QUESTIONS = "practice_questions", "Practice Questions"
        BUILD_PROJECT = "build_project", "Build/Practice a Project"
        REASSESS_SKILL = "reassess_skill", "Reassess a Weak Skill"

    class Priority(models.TextChoices):
        URGENT = "urgent", "Urgent"
        HIGH = "high", "High"
        MEDIUM = "medium", "Medium"
        LOW = "low", "Low"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        COMPLETED = "completed", "Completed"
        DISMISSED = "dismissed", "Dismissed"

    gap = models.ForeignKey(
        KnowledgeGap,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    skill = models.ForeignKey(
        "roadmap.Skill",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    topic = models.ForeignKey(
        "roadmap.Topic",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    action_type = models.CharField(max_length=32, choices=ActionType.choices, db_index=True)
    priority = models.CharField(max_length=32, choices=Priority.choices, default=Priority.MEDIUM, db_index=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.PENDING, db_index=True)
    title = models.CharField(max_length=255)
    description = models.TextField()
    suggested_action = models.TextField(blank=True)
    source = models.ForeignKey(
        "sources.Source",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    concept = models.ForeignKey(
        Concept,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    assessment = models.ForeignKey(
        "assessments.Assessment",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="recommendations",
    )
    metadata = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "Recommendation"
        verbose_name_plural = "Recommendations"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status", "priority"]),
            models.Index(fields=["skill", "status"]),
        ]

    def __str__(self):
        target = self.skill.name if self.skill else (self.topic.name if self.topic else "General")
        return f"[{self.priority.upper()}] {self.title} ({target}) - {self.action_type}"

