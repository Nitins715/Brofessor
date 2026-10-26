from django.urls import path
from .views import (
    RecommendationListView,
    RecommendationDetailView,
    KnowledgeGapListView,
)

urlpatterns = [
    path("", RecommendationListView.as_view(), name="recommendation-list"),
    path("generate/", RecommendationListView.as_view(), name="recommendation-generate"),
    path("gaps/", KnowledgeGapListView.as_view(), name="recommendation-gaps"),
    path("gaps/evaluate/", KnowledgeGapListView.as_view(), name="recommendation-gaps-evaluate"),
    path("<uuid:pk>/", RecommendationDetailView.as_view(), name="recommendation-detail"),
]
