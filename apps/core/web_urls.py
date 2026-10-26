"""Web UI URL routing for Brofessor application."""

from django.urls import path
from .web_views import (
    LandingOrDashboardView,
    WebLoginView,
    WebDevLoginView,
    WebLogoutView,
    OnboardingView,
    CreateCustomDomainAjaxView,
    DashboardView,
    RoadmapView,
    RoadmapSkillStatusAjaxView,
    KnowledgeView,
    SkillDetailView,
    SourcesView,
    SourceDetailView,
    SourceRetryView,
    AssessmentsView,
    StartSkillAssessmentView,
    AssessmentTakeView,
    AssessmentResultView,
    ChatView,
    KnowledgeGapsView,
    SettingsView,
    ReseedRoadmapView,
    SelectActiveDomainView,
)

urlpatterns = [
    # Landing & Auth
    path("", LandingOrDashboardView.as_view(), name="web-landing"),
    path("login/", WebLoginView.as_view(), name="web-login"),
    path("dev-login/", WebDevLoginView.as_view(), name="web-dev-login"),
    path("logout/", WebLogoutView.as_view(), name="web-logout"),

    # Domain Selection
    path("domain/select/", SelectActiveDomainView.as_view(), name="web-select-domain"),
    path("domain/select/<uuid:pk>/", SelectActiveDomainView.as_view(), name="web-select-domain-pk"),

    # Onboarding
    path("onboarding/", OnboardingView.as_view(), name="web-onboarding"),
    path("onboarding/api/create-domain/", CreateCustomDomainAjaxView.as_view(), name="web-onboarding-create-domain"),

    # Main Application Shell & Views
    path("dashboard/", DashboardView.as_view(), name="web-dashboard"),
    path("roadmap/", RoadmapView.as_view(), name="web-roadmap"),
    path("roadmap/api/skills/<uuid:pk>/status/", RoadmapSkillStatusAjaxView.as_view(), name="web-roadmap-skill-status"),

    path("knowledge/", KnowledgeView.as_view(), name="web-knowledge"),
    path("knowledge/skills/<uuid:pk>/", SkillDetailView.as_view(), name="web-skill-detail"),

    path("sources/", SourcesView.as_view(), name="web-sources"),
    path("sources/<uuid:pk>/", SourceDetailView.as_view(), name="web-source-detail"),
    path("sources/<uuid:pk>/retry/", SourceRetryView.as_view(), name="web-source-retry"),

    # Assessments Flow & Results
    path("assessments/", AssessmentsView.as_view(), name="web-assessments"),
    path("assessments/start/", StartSkillAssessmentView.as_view(), name="web-assessment-start-post"),
    path("skills/<uuid:skill_id>/assessment/", StartSkillAssessmentView.as_view(), name="web-skill-assessment-start"),
    path("assessments/<uuid:pk>/take/", AssessmentTakeView.as_view(), name="web-assessment-take"),
    path("assessments/attempts/<uuid:attempt_id>/result/", AssessmentResultView.as_view(), name="web-assessment-result"),

    # AI Knowledge Assistant & Gaps
    path("chat/", ChatView.as_view(), name="web-chat"),
    path("gaps/", KnowledgeGapsView.as_view(), name="web-gaps"),
    path("settings/", SettingsView.as_view(), name="web-settings"),
    path("settings/reseed/", ReseedRoadmapView.as_view(), name="web-reseed"),
]
