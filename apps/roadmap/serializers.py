from rest_framework import serializers
from apps.roadmap.models import (
    Domain,
    Topic,
    Skill,
    RoadmapNode,
    RoadmapProgress,
    LearningResource,
    SkillResourceMapping,
)


class LearningResourceSerializer(serializers.ModelSerializer):
    """Serializer for curated external learning resource."""
    is_verified = serializers.BooleanField(read_only=True)

    class Meta:
        model = LearningResource
        fields = [
            "id",
            "title",
            "url",
            "description",
            "resource_type",
            "source",
            "verification_status",
            "is_verified",
            "last_verified_date",
            "created_at",
            "updated_at",
        ]


class SkillResourceMappingSerializer(serializers.ModelSerializer):
    """Serializer for mapping between Skill and LearningResource."""
    resource = LearningResourceSerializer(read_only=True)
    resource_id = serializers.PrimaryKeyRelatedField(
        queryset=LearningResource.objects.all(),
        source="resource",
        write_only=True,
    )
    skill_id = serializers.PrimaryKeyRelatedField(
        queryset=Skill.objects.all(),
        source="skill",
        write_only=True,
        required=False,
    )
    title = serializers.CharField(read_only=True)
    url = serializers.CharField(read_only=True)
    resource_type = serializers.CharField(read_only=True)
    source = serializers.CharField(read_only=True)
    verification_status = serializers.CharField(read_only=True)
    is_verified = serializers.BooleanField(read_only=True)
    last_verified_date = serializers.DateField(read_only=True)

    class Meta:
        model = SkillResourceMapping
        fields = [
            "id",
            "skill_id",
            "resource_id",
            "resource",
            "title",
            "url",
            "resource_type",
            "source",
            "verification_status",
            "is_verified",
            "last_verified_date",
            "is_primary",
            "order",
            "notes",
            "created_at",
            "updated_at",
        ]


class SkillSerializer(serializers.ModelSerializer):
    """Serializer for roadmap Skill."""
    topic_name = serializers.CharField(source="topic.name", read_only=True)
    prerequisite_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        source="prerequisites",
        required=False,
    )
    resources = SkillResourceMappingSerializer(source="get_verified_resource_mappings", many=True, read_only=True)

    class Meta:
        model = Skill
        fields = [
            "id",
            "topic",
            "topic_name",
            "name",
            "slug",
            "description",
            "difficulty_level",
            "priority",
            "learning_objectives",
            "key_concepts",
            "interview_relevance",
            "evaluation_criteria",
            "estimated_effort_hours",
            "prerequisite_ids",
            "order",
            "resources",
            "created_at",
            "updated_at",
        ]


class TopicSerializer(serializers.ModelSerializer):
    """Serializer for roadmap Topic with skills count."""
    skills_count = serializers.SerializerMethodField()
    additional_domain_ids = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Domain.objects.all(),
        source="additional_domains",
        required=False,
    )

    class Meta:
        model = Topic
        fields = [
            "id",
            "domain",
            "additional_domain_ids",
            "name",
            "slug",
            "description",
            "priority",
            "learning_objectives",
            "estimated_effort_hours",
            "order",
            "skills_count",
            "created_at",
            "updated_at",
        ]

    def get_skills_count(self, obj):
        return obj.skills.count()


class DomainSerializer(serializers.ModelSerializer):
    """Serializer for knowledge Domain."""
    topic_count = serializers.SerializerMethodField()
    skill_count = serializers.SerializerMethodField()

    class Meta:
        model = Domain
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "is_active",
            "is_selected",
            "topic_count",
            "skill_count",
            "created_at",
            "updated_at",
        ]

    def get_topic_count(self, obj):
        return obj.get_all_topics().count() if hasattr(obj, "get_all_topics") else obj.topics.count()

    def get_skill_count(self, obj):
        if hasattr(obj, "get_all_topics"):
            return Skill.objects.filter(topic__in=obj.get_all_topics()).distinct().count()
        return Skill.objects.filter(topic__domain=obj).count()


class RoadmapProgressSerializer(serializers.ModelSerializer):
    """Serializer for RoadmapProgress records."""
    skill_id = serializers.CharField(source="node.skill.id", read_only=True)
    skill_name = serializers.CharField(source="node.skill.name", read_only=True)

    class Meta:
        model = RoadmapProgress
        fields = [
            "id",
            "skill_id",
            "skill_name",
            "status",
            "is_current",
            "completed_at",
            "notes",
            "created_at",
            "updated_at",
        ]


class UpdateSkillProgressSerializer(serializers.Serializer):
    """Payload to update a skill's progression state."""
    status = serializers.ChoiceField(choices=RoadmapProgress.ProgressStatus.choices, required=True)
    is_current = serializers.BooleanField(required=False, default=False)
    notes = serializers.CharField(required=False, allow_blank=True, default="")

