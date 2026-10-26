from rest_framework import serializers
from apps.knowledge.models import Concept, Evidence, CalculatedMastery, KnowledgeGap, Recommendation


class ConceptSerializer(serializers.ModelSerializer):
    """Serializer for Concept instances with mapped skills information."""
    skills = serializers.SerializerMethodField()
    evidence_count = serializers.SerializerMethodField()

    class Meta:
        model = Concept
        fields = [
            "id",
            "name",
            "slug",
            "description",
            "domain",
            "topic",
            "skills",
            "evidence_count",
            "metadata",
            "created_at",
            "updated_at",
        ]

    def get_skills(self, obj):
        return [{"id": str(s.id), "name": s.name} for s in obj.skills.all()]

    def get_evidence_count(self, obj):
        return obj.evidence_items.count()


class EvidenceSerializer(serializers.ModelSerializer):
    """Serializer for Evidence records."""
    source_name = serializers.CharField(source="source.name", read_only=True)
    concept_name = serializers.CharField(source="concept.name", read_only=True)
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = Evidence
        fields = [
            "id",
            "evidence_type",
            "title",
            "description",
            "source",
            "source_name",
            "concept",
            "concept_name",
            "topic",
            "topic_name",
            "skill",
            "skill_name",
            "raw_data",
            "confidence_weight",
            "recorded_at",
        ]


class RecordEvidenceRequestSerializer(serializers.Serializer):
    """Payload to record new user-declared or practical knowledge evidence."""
    evidence_type = serializers.ChoiceField(choices=Evidence.EvidenceType.choices, required=True)
    title = serializers.CharField(max_length=255, required=True)
    description = serializers.CharField(required=False, allow_blank=True, default="")
    skill_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    topic_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    concept_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    confidence_weight = serializers.FloatField(required=False, default=1.0, min_value=0.0, max_value=1.0)
    raw_data = serializers.DictField(required=False, default=dict)


class SkillKnowledgeResponseSerializer(serializers.Serializer):
    """Consolidated knowledge view for a skill."""
    skill_id = serializers.CharField()
    skill_name = serializers.CharField()
    topic_id = serializers.CharField()
    topic_name = serializers.CharField()
    difficulty_level = serializers.CharField()
    total_evidence_count = serializers.IntegerField()
    evidence_breakdown = serializers.DictField()
    covered_concepts = serializers.ListField()
    last_supported_at = serializers.CharField(allow_null=True)
    mastery_score = serializers.FloatField()
    confidence_score = serializers.FloatField()
    evidence_items = serializers.ListField()


class KnowledgeProfileResponseSerializer(serializers.Serializer):
    """High-level personal knowledge model profile across all roadmap skills."""
    total_encountered_skills = serializers.IntegerField()
    total_roadmap_skills = serializers.IntegerField()
    coverage_percentage = serializers.FloatField()
    total_concepts_extracted = serializers.IntegerField()
    total_evidence_items = serializers.IntegerField()
    evidence_by_type = serializers.DictField()
    encountered_skills = serializers.ListField()


class KnowledgeExtractionResponseSerializer(serializers.Serializer):
    """Result after triggering source knowledge extraction."""
    source_id = serializers.CharField()
    concepts_extracted = serializers.IntegerField()
    concepts_mapped = serializers.IntegerField()
    evidence_recorded = serializers.IntegerField()
    affected_skills = serializers.ListField()
    status = serializers.CharField()
    error = serializers.CharField(allow_null=True, required=False)
    metadata = serializers.DictField()


class CalculatedMasterySerializer(serializers.ModelSerializer):
    """Serializer for CalculatedMastery model."""
    skill_name = serializers.CharField(source="skill.name", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = CalculatedMastery
        fields = [
            "id",
            "skill",
            "skill_name",
            "topic",
            "topic_name",
            "mastery_score",
            "mastery_level",
            "knowledge_coverage",
            "confidence_score",
            "evidence_count",
            "last_calculated_at",
            "calculation_metadata",
        ]


class KnowledgeGapSerializer(serializers.ModelSerializer):
    """Serializer for KnowledgeGap model."""
    skill_name = serializers.CharField(source="skill.name", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)

    class Meta:
        model = KnowledgeGap
        fields = [
            "id",
            "skill",
            "skill_name",
            "topic",
            "topic_name",
            "gap_type",
            "severity",
            "status",
            "title",
            "description",
            "expected_level",
            "current_level",
            "current_score",
            "target_score",
            "identified_at",
            "resolved_at",
            "metadata",
        ]


class RecommendationSerializer(serializers.ModelSerializer):
    """Serializer for Recommendation model."""
    skill_name = serializers.CharField(source="skill.name", read_only=True, default=None)
    topic_name = serializers.CharField(source="topic.name", read_only=True, default=None)
    source_title = serializers.CharField(source="source.title", read_only=True, default=None)
    assessment_title = serializers.CharField(source="assessment.title", read_only=True, default=None)

    class Meta:
        model = Recommendation
        fields = [
            "id",
            "gap",
            "skill",
            "skill_name",
            "topic",
            "topic_name",
            "action_type",
            "priority",
            "status",
            "title",
            "description",
            "suggested_action",
            "source",
            "source_title",
            "concept",
            "assessment",
            "assessment_title",
            "created_at",
            "metadata",
        ]


class UpdateRecommendationSerializer(serializers.Serializer):
    """Payload to update recommendation status."""
    status = serializers.ChoiceField(choices=Recommendation.Status.choices, required=True)

