from rest_framework import serializers
from apps.assessments.models import Assessment, Question, Attempt, Answer


class QuestionOptionSerializer(serializers.Serializer):
    key = serializers.CharField()
    text = serializers.CharField()


class QuestionSerializer(serializers.ModelSerializer):
    """Student-facing question serializer (excludes correct answer and explanations during active attempts)."""
    options = serializers.ListField(child=serializers.DictField())

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "difficulty_level",
            "concept",
            "prompt",
            "options",
            "points",
            "order",
        ]


class QuestionReviewSerializer(serializers.ModelSerializer):
    """Full question serializer including rubric, correct answer, and distractor explanations for review."""
    options = serializers.ListField(child=serializers.DictField())

    class Meta:
        model = Question
        fields = [
            "id",
            "question_type",
            "difficulty_level",
            "concept",
            "prompt",
            "options",
            "correct_answer",
            "distractor_explanations",
            "rubric",
            "points",
            "order",
            "generation_metadata",
        ]


class AssessmentSerializer(serializers.ModelSerializer):
    questions_count = serializers.SerializerMethodField()
    skill_name = serializers.CharField(source="skill.name", read_only=True)
    topic_name = serializers.CharField(source="topic.name", read_only=True)

    class Meta:
        model = Assessment
        fields = [
            "id",
            "title",
            "description",
            "skill",
            "skill_name",
            "topic",
            "topic_name",
            "status",
            "difficulty_level",
            "generation_status",
            "generation_error",
            "target_questions_count",
            "provider_used",
            "passing_score",
            "time_limit_minutes",
            "questions_count",
            "is_active",
            "created_at",
            "updated_at",
        ]

    def get_questions_count(self, obj):
        return obj.questions.count()


class CreateAssessmentRequestSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    skill_id = serializers.UUIDField(required=False, allow_null=True)
    topic_id = serializers.UUIDField(required=False, allow_null=True)
    difficulty_level = serializers.ChoiceField(
        choices=Assessment.DifficultyLevel.choices,
        default=Assessment.DifficultyLevel.EASY,
    )
    auto_generate = serializers.BooleanField(default=True)
    passing_score = serializers.FloatField(default=70.0, min_value=0.0, max_value=100.0)
    time_limit_minutes = serializers.IntegerField(required=False, allow_null=True)


class SubmitAnswerRequestSerializer(serializers.Serializer):
    question_id = serializers.UUIDField(required=True)
    user_response = serializers.CharField(required=True, allow_blank=True)
    response_time_seconds = serializers.FloatField(required=False, allow_null=True, min_value=0.0)


class AnswerResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = [
            "id",
            "question_id",
            "user_response",
            "response_time_seconds",
            "accuracy",
            "score_awarded",
            "is_correct",
            "feedback",
        ]


class AttemptSerializer(serializers.ModelSerializer):
    assessment_title = serializers.CharField(source="assessment.title", read_only=True)

    class Meta:
        model = Attempt
        fields = [
            "id",
            "assessment",
            "assessment_title",
            "started_at",
            "completed_at",
            "total_points_possible",
            "total_points_awarded",
            "score",
            "passed",
            "concept_scores",
            "weak_concepts",
            "feedback",
        ]


class AttemptResultSerializer(serializers.Serializer):
    attempt_id = serializers.CharField()
    assessment_id = serializers.CharField()
    title = serializers.CharField()
    skill_name = serializers.CharField(allow_null=True)
    topic_name = serializers.CharField(allow_null=True)
    score_percentage = serializers.FloatField()
    passed = serializers.BooleanField()
    total_points_possible = serializers.FloatField()
    total_points_awarded = serializers.FloatField()
    total_questions = serializers.IntegerField()
    correct_answers_count = serializers.IntegerField()
    answers = serializers.ListField()
    completed_at = serializers.CharField()
    evidence_id = serializers.CharField(allow_null=True)
    concept_scores = serializers.DictField(default=dict)
    weak_concepts = serializers.ListField(default=list)
    recommended_resources = serializers.ListField(default=list)
    next_difficulty = serializers.CharField(allow_null=True, required=False)
    next_skill_id = serializers.CharField(allow_null=True, required=False)
    next_skill_name = serializers.CharField(allow_null=True, required=False)


class SkillAssessmentHistorySerializer(serializers.Serializer):
    target_id = serializers.CharField()
    target_name = serializers.CharField()
    target_type = serializers.CharField()
    attempts_considered = serializers.IntegerField()
    average_score = serializers.FloatField()
    latest_score = serializers.FloatField(allow_null=True)
    highest_score = serializers.FloatField(allow_null=True)
    passing_rate = serializers.FloatField()
    trend = serializers.CharField()
    attempts = serializers.ListField()


class SkillNextQuestionRequestSerializer(serializers.Serializer):
    difficulty = serializers.ChoiceField(
        choices=["easy", "medium", "hard"],
        default="easy",
        required=False,
    )
    order = serializers.IntegerField(required=False, min_value=1)
    attempt_id = serializers.UUIDField(required=False, allow_null=True)
