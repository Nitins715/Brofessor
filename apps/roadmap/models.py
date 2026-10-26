from django.db import models
from apps.core.models import BaseModel


class Domain(BaseModel):
    """High-level knowledge or engineering domain (e.g. Full-Stack, AI Engineering)."""
    name = models.CharField(max_length=255, unique=True)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    is_selected = models.BooleanField(default=False, help_text="Currently active/selected domain for the user.")

    class Meta:
        verbose_name = "Domain"
        verbose_name_plural = "Domains"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def get_all_topics(self):
        """Returns primary topics plus shared topics linked to this domain."""
        return (Topic.objects.filter(domain=self) | Topic.objects.filter(additional_domains=self)).distinct().order_by("order", "name")


class Topic(BaseModel):
    """Key subject area under a Domain."""
    class Priority(models.TextChoices):
        P0 = "P0", "P0 - Core"
        P1 = "P1", "P1 - Important"
        P2 = "P2", "P2 - Elective"

    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="topics")
    additional_domains = models.ManyToManyField(Domain, blank=True, related_name="shared_topics")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    priority = models.CharField(
        max_length=4,
        choices=Priority.choices,
        default=Priority.P0,
    )
    learning_objectives = models.JSONField(default=list, blank=True)
    estimated_effort_hours = models.PositiveIntegerField(default=0, help_text="Estimated learning effort in hours")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Topic"
        verbose_name_plural = "Topics"
        ordering = ["domain", "order", "name"]
        unique_together = [("domain", "slug")]
        indexes = [
            models.Index(fields=["domain", "order"]),
        ]

    def __str__(self):
        return f"{self.domain.name} > {self.name}"

    def get_all_domains(self):
        return (Domain.objects.filter(id=self.domain_id) | self.additional_domains.all()).distinct()


class Skill(BaseModel):
    """Specific measurable capability under a Topic."""
    class Priority(models.TextChoices):
        P0 = "P0", "P0 - Core"
        P1 = "P1", "P1 - Important"
        P2 = "P2", "P2 - Elective"

    class Difficulty(models.TextChoices):
        BEGINNER = "beginner", "Beginner"
        INTERMEDIATE = "intermediate", "Intermediate"
        ADVANCED = "advanced", "Advanced"

    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="skills")
    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    difficulty_level = models.CharField(
        max_length=32,
        choices=Difficulty.choices,
        default=Difficulty.BEGINNER,
    )
    priority = models.CharField(
        max_length=4,
        choices=Priority.choices,
        default=Priority.P0,
    )
    learning_objectives = models.JSONField(default=list, blank=True)
    key_concepts = models.JSONField(default=list, blank=True)
    interview_relevance = models.TextField(blank=True)
    evaluation_criteria = models.TextField(blank=True)
    estimated_effort_hours = models.PositiveIntegerField(default=0, help_text="Estimated learning effort in hours")
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="downstream_skills",
    )
    order = models.PositiveIntegerField(default=0)
    learning_resources = models.ManyToManyField(
        "LearningResource",
        through="SkillResourceMapping",
        related_name="skills",
        blank=True,
    )

    class Meta:
        verbose_name = "Skill"
        verbose_name_plural = "Skills"
        ordering = ["topic", "order", "name"]
        unique_together = [("topic", "slug")]
        indexes = [
            models.Index(fields=["topic", "order"]),
        ]

    def __str__(self):
        return f"{self.topic.name} > {self.name}"

    def get_verified_resource_mappings(self):
        return self.resource_mappings.filter(
            resource__verification_status=LearningResource.VerificationStatus.VERIFIED
        ).select_related("resource").order_by("-is_primary", "order", "resource__title")

    def get_grouped_resources(self):
        """Returns verified resources grouped by resource_type with primary items first."""
        mappings = self.get_verified_resource_mappings()
        groups = {
            LearningResource.ResourceType.PRIMARY: [],
            LearningResource.ResourceType.OFFICIAL_DOCS: [],
            LearningResource.ResourceType.PRACTICE: [],
            LearningResource.ResourceType.VIDEO: [],
        }
        for m in mappings:
            r_type = m.resource.resource_type
            if r_type not in groups:
                groups[r_type] = []
            groups[r_type].append(m)
        return groups

    def get_next_skill(self, domain=None):
        """Returns the next sequential Skill in the curriculum roadmap."""
        # 1. Next skill in current topic
        next_in_topic = Skill.objects.filter(
            topic=self.topic,
            order__gt=self.order,
        ).order_by("order", "name").first()
        if next_in_topic:
            return next_in_topic

        # 2. First skill in next topic in the domain
        active_domain = domain or self.topic.domain
        all_topics = list(active_domain.get_all_topics()) if hasattr(active_domain, "get_all_topics") else list(active_domain.topics.all().order_by("order", "name"))
        try:
            current_topic_idx = [t.id for t in all_topics].index(self.topic_id)
            for next_topic in all_topics[current_topic_idx + 1:]:
                first_skill = next_topic.skills.all().order_by("order", "name").first()
                if first_skill:
                    return first_skill
        except ValueError:
            pass

        return None


class LearningResource(BaseModel):
    """Curated external learning material (article, official documentation, video, practice problem)."""

    class ResourceType(models.TextChoices):
        PRIMARY = "primary", "Primary"
        OFFICIAL_DOCS = "official_docs", "Official Docs"
        PRACTICE = "practice", "Practice"
        VIDEO = "video", "Video"

    class VerificationStatus(models.TextChoices):
        VERIFIED = "verified", "Verified"
        UNVERIFIED = "unverified", "Unverified"
        PENDING = "pending", "Pending Verification"
        BROKEN = "broken", "Broken / Inaccessible"

    title = models.CharField(max_length=255)
    url = models.URLField(max_length=1024, unique=True)
    description = models.TextField(blank=True)
    resource_type = models.CharField(
        max_length=32,
        choices=ResourceType.choices,
        default=ResourceType.PRIMARY,
        db_index=True,
    )
    source = models.CharField(
        max_length=128,
        help_text="Source platform or publisher (e.g. GeeksforGeeks, Python Docs, PyTorch Docs, YouTube, GitHub)",
        db_index=True,
    )
    verification_status = models.CharField(
        max_length=32,
        choices=VerificationStatus.choices,
        default=VerificationStatus.VERIFIED,
        db_index=True,
    )
    last_verified_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date the resource content and URL were last verified",
    )

    class Meta:
        verbose_name = "Learning Resource"
        verbose_name_plural = "Learning Resources"
        ordering = ["source", "title"]
        indexes = [
            models.Index(fields=["resource_type", "verification_status"]),
        ]

    def __str__(self):
        return f"[{self.get_resource_type_display()}] {self.title} ({self.source})"

    @property
    def is_verified(self):
        return self.verification_status == self.VerificationStatus.VERIFIED


class SkillResourceMapping(BaseModel):
    """Associates a Skill with a LearningResource, supporting ordering and primary designation."""
    skill = models.ForeignKey(
        Skill,
        on_delete=models.CASCADE,
        related_name="resource_mappings",
    )
    resource = models.ForeignKey(
        LearningResource,
        on_delete=models.CASCADE,
        related_name="skill_mappings",
    )
    is_primary = models.BooleanField(
        default=False,
        help_text="Designates this as a primary/recommended resource for this skill.",
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Display order within this skill and resource type group.",
    )
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Skill Resource Mapping"
        verbose_name_plural = "Skill Resource Mappings"
        unique_together = [("skill", "resource")]
        ordering = ["skill", "-is_primary", "order", "created_at"]
        indexes = [
            models.Index(fields=["skill", "is_primary", "order"]),
        ]

    def __str__(self):
        flag = " [PRIMARY]" if self.is_primary else ""
        return f"{self.skill.name} -> {self.resource.title}{flag}"

    @property
    def title(self):
        return self.resource.title

    @property
    def url(self):
        return self.resource.url

    @property
    def description(self):
        return self.resource.description

    @property
    def resource_type(self):
        return self.resource.resource_type

    @property
    def source(self):
        return self.resource.source

    @property
    def verification_status(self):
        return self.resource.verification_status

    @property
    def is_verified(self):
        return self.resource.is_verified

    @property
    def last_verified_date(self):
        return self.resource.last_verified_date


class RoadmapNode(BaseModel):
    """Node in the roadmap tree/DAG representing skill sequence and prerequisites."""
    domain = models.ForeignKey(Domain, on_delete=models.CASCADE, related_name="roadmap_nodes")
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name="roadmap_nodes")
    skill = models.OneToOneField(Skill, on_delete=models.CASCADE, related_name="roadmap_node")
    parent = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="children",
    )
    prerequisites = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="unlocks",
    )
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = "Roadmap Node"
        verbose_name_plural = "Roadmap Nodes"
        ordering = ["domain", "order"]
        indexes = [
            models.Index(fields=["domain", "order"]),
        ]

    def __str__(self):
        return f"Node: {self.skill.name} ({self.domain.name})"


class RoadmapProgress(BaseModel):
    """Tracks single-user learning progression through a roadmap node."""
    class ProgressStatus(models.TextChoices):
        NOT_STARTED = "not_started", "Not Started"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        MASTERED = "mastered", "Mastered"

    node = models.OneToOneField(RoadmapNode, on_delete=models.CASCADE, related_name="progress")
    status = models.CharField(
        max_length=32,
        choices=ProgressStatus.choices,
        default=ProgressStatus.NOT_STARTED,
        db_index=True,
    )
    is_current = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        verbose_name = "Roadmap Progress"
        verbose_name_plural = "Roadmap Progress Records"
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.node.skill.name}: {self.status}"

