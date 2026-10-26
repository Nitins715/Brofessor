from django.urls import path
from .views import (
    SourceListView,
    SourceDetailView,
    SourceStatusView,
    RetrySourceView,
    SourceDocumentView,
    SourceChunksView,
    AddTextSourceView,
    AddArticleSourceView,
    AddYouTubeSourceView,
    UploadPDFSourceView,
    EmbedSourceView,
    RetryEmbeddingsView,
)

urlpatterns = [
    path("", SourceListView.as_view(), name="source-list"),
    path("embed/retry/", RetryEmbeddingsView.as_view(), name="source-embed-retry"),
    path("<uuid:pk>/", SourceDetailView.as_view(), name="source-detail"),
    path("<uuid:pk>/status/", SourceStatusView.as_view(), name="source-status"),
    path("<uuid:pk>/retry/", RetrySourceView.as_view(), name="source-retry"),
    path("<uuid:pk>/documents/", SourceDocumentView.as_view(), name="source-document"),
    path("<uuid:pk>/chunks/", SourceChunksView.as_view(), name="source-chunks"),
    path("<uuid:pk>/embed/", EmbedSourceView.as_view(), name="source-embed"),
    path("text/", AddTextSourceView.as_view(), name="source-add-text"),
    path("article/", AddArticleSourceView.as_view(), name="source-add-article"),
    path("youtube/", AddYouTubeSourceView.as_view(), name="source-add-youtube"),
    path("pdf/", UploadPDFSourceView.as_view(), name="source-upload-pdf"),
]

