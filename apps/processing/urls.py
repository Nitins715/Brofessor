from django.urls import path
from .views import (
    ProcessingOverviewView,
    JobStatusView,
    SourceProcessingStatusListView,
    SourceProcessingDetailView,
    RetrySourceProcessingView,
    EmbeddingProcessingStatusView,
    ExtractionProcessingStatusView,
    ProcessingFailuresView,
)

urlpatterns = [
    path("", ProcessingOverviewView.as_view(), name="processing-overview"),
    path("jobs/<str:task_id>/", JobStatusView.as_view(), name="processing-job-status"),
    path("sources/", SourceProcessingStatusListView.as_view(), name="processing-sources-list"),
    path("sources/<uuid:pk>/", SourceProcessingDetailView.as_view(), name="processing-source-detail"),
    path("sources/<uuid:pk>/retry/", RetrySourceProcessingView.as_view(), name="processing-source-retry"),
    path("embeddings/", EmbeddingProcessingStatusView.as_view(), name="processing-embeddings-status"),
    path("extractions/", ExtractionProcessingStatusView.as_view(), name="processing-extractions-status"),
    path("failures/", ProcessingFailuresView.as_view(), name="processing-failures"),
]
