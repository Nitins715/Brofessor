from django.urls import path
from .views import (
    AssessmentsIndexView,
    AssessmentListCreateView,
    AssessmentDetailView,
    AssessmentQuestionsView,
    StartAttemptView,
    SubmitAnswerView,
    CompleteAttemptView,
    AttemptResultView,
    SkillAssessmentStatusView,
    SkillNextQuestionView,
    SkillNextSkillView,
    SkillAssessmentHistoryView,
    TopicAssessmentHistoryView,
)

urlpatterns = [
    # Top-level assessment suite routes
    path("", AssessmentListCreateView.as_view(), name="assessment-list-create"),
    path("<uuid:pk>/", AssessmentDetailView.as_view(), name="assessment-detail"),
    path("<uuid:pk>/questions/", AssessmentQuestionsView.as_view(), name="assessment-questions"),
    path("<uuid:pk>/attempt/", StartAttemptView.as_view(), name="assessment-start-attempt"),
    path("<uuid:pk>/start/", StartAttemptView.as_view(), name="assessment-start-attempt-alias"),

    # Nested namespace aliases for backward compatibility
    path("assessments/", AssessmentListCreateView.as_view(), name="assessment-list-create-nested"),
    path("assessments/<uuid:pk>/", AssessmentDetailView.as_view(), name="assessment-detail-nested"),
    path("assessments/<uuid:pk>/questions/", AssessmentQuestionsView.as_view(), name="assessment-questions-nested"),
    path("assessments/<uuid:pk>/attempt/", StartAttemptView.as_view(), name="assessment-start-attempt-nested"),
    path("assessments/<uuid:pk>/start/", StartAttemptView.as_view(), name="assessment-start-attempt-alias-nested"),

    # Sequential question generation & delivery routes
    path("skills/<uuid:skill_id>/status/", SkillAssessmentStatusView.as_view(), name="assessment-skill-status"),
    path("skills/<uuid:skill_id>/next-question/", SkillNextQuestionView.as_view(), name="assessment-skill-next-question"),
    path("skills/<uuid:skill_id>/question/", SkillNextQuestionView.as_view(), name="assessment-skill-question-alias"),
    path("skills/<uuid:skill_id>/next-skill/", SkillNextSkillView.as_view(), name="assessment-skill-next-skill"),

    # Attempt execution routes
    path("attempts/<uuid:attempt_id>/answers/", SubmitAnswerView.as_view(), name="assessment-submit-answer"),
    path("attempts/<uuid:attempt_id>/submit-answer/", SubmitAnswerView.as_view(), name="assessment-submit-answer-alias"),
    path("attempts/<uuid:attempt_id>/complete/", CompleteAttemptView.as_view(), name="assessment-complete-attempt"),
    path("attempts/<uuid:attempt_id>/result/", AttemptResultView.as_view(), name="assessment-attempt-result"),

    # Historical analytics
    path("skills/<uuid:skill_id>/history/", SkillAssessmentHistoryView.as_view(), name="assessment-history-skill-root"),
    path("topics/<uuid:topic_id>/history/", TopicAssessmentHistoryView.as_view(), name="assessment-history-topic-root"),
    path("history/skills/<uuid:skill_id>/", SkillAssessmentHistoryView.as_view(), name="assessment-history-skill"),
    path("history/topics/<uuid:topic_id>/", TopicAssessmentHistoryView.as_view(), name="assessment-history-topic"),
]
