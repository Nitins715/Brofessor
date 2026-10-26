from django.urls import path
from .views import (
    MasteryListView,
    SkillMasteryView,
    TopicMasteryView,
    KnowledgeCoverageView,
    RecalculateKnowledgeView,
)

urlpatterns = [
    path("", MasteryListView.as_view(), name="mastery-list"),
    path("coverage/", KnowledgeCoverageView.as_view(), name="mastery-coverage"),
    path("recalculate/", RecalculateKnowledgeView.as_view(), name="mastery-recalculate"),
    path("skills/<uuid:pk>/", SkillMasteryView.as_view(), name="mastery-skill-detail"),
    path("skills/<uuid:pk>/recalculate/", SkillMasteryView.as_view(), name="mastery-skill-recalculate"),
    path("topics/<uuid:pk>/", TopicMasteryView.as_view(), name="mastery-topic-detail"),
    path("topics/<uuid:pk>/recalculate/", TopicMasteryView.as_view(), name="mastery-topic-recalculate"),
]
