from django.urls import path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from .views import HealthCheckView, ApiRootView

urlpatterns = [
    path("", ApiRootView.as_view(), name="api-root"),
    path("health/", HealthCheckView.as_view(), name="api-health"),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
