"""URL configuration for Brofessor project."""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)

# Modular API URLs
api_patterns = [
    path("", include("apps.core.urls")),
    path("accounts/", include("apps.accounts.urls")),
    path("sources/", include("apps.sources.urls")),
    path("knowledge/", include("apps.knowledge.urls")),
    path("roadmap/", include("apps.roadmap.urls")),
    path("assessments/", include("apps.assessments.urls")),
    path("mastery/", include("apps.knowledge.mastery_urls")),
    path("recommendations/", include("apps.knowledge.recommendation_urls")),
    path("rag/", include("apps.rag.urls")),
    path("conversations/", include("apps.rag.conversation_urls")),
    path("processing/", include("apps.processing.urls")),
    # OpenAPI Schema & Interactive Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui-alias"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_patterns)),
    path("api/v1/", include(api_patterns)),
    path("", include("apps.core.web_urls")),
]

from django.views.static import serve
from django.urls import re_path

# Serve media files (uploaded documents/PDFs) across local environments
urlpatterns += [
    re_path(r"^media/(?P<path>.*)$", serve, {"document_root": settings.MEDIA_ROOT}),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)


handler404 = "apps.core.views.custom_404_handler"
handler500 = "apps.core.views.custom_500_handler"
