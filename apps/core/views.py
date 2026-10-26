import time
import logging
from django.conf import settings
from django.db import connection
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
import redis

logger = logging.getLogger("brofessor")


class HealthCheckView(APIView):
    """
    Unified System Health Check.
    Checks status of Django, PostgreSQL/database (including pgvector), Redis, and Celery broker.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="System Health Check",
        description="Check status of Django core, database connection, Redis, and Celery broker configuration.",
        responses={200: inline_serializer("HealthResponse", fields={})},
    )
    def get(self, request, *args, **kwargs):

        health_data = {
            "status": "healthy",
            "service": "Brofessor Local-First Knowledge System",
            "timestamp": time.time(),
            "components": {},
        }

        all_ok = True

        # 1. Django check
        health_data["components"]["django"] = {
            "status": "up",
            "debug_mode": settings.DEBUG,
        }

        # 2. Database check
        db_status = {"status": "down", "engine": settings.DATABASES["default"]["ENGINE"]}
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1;")
                cursor.fetchone()
                db_status["status"] = "up"
                db_status["vendor"] = connection.vendor

                # Check pgvector extension if using PostgreSQL
                if connection.vendor == "postgresql":
                    cursor.execute(
                        "SELECT extname FROM pg_extension WHERE extname = 'vector';"
                    )
                    has_vector = cursor.fetchone() is not None
                    db_status["pgvector_installed"] = has_vector
        except Exception as e:
            logger.error(f"Database health check failed: {str(e)}")
            db_status["error"] = str(e)
            all_ok = False
        health_data["components"]["database"] = db_status

        # 3. Redis check
        redis_status = {"status": "down", "url": settings.REDIS_URL}
        try:
            r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
            if r.ping():
                redis_status["status"] = "up"
        except Exception as e:
            logger.warning(f"Redis health check failed: {str(e)}")
            redis_status["error"] = str(e)
            # In local-first offline dev, redis can be optional until docker starts
        health_data["components"]["redis"] = redis_status

        # 4. Celery broker configuration check
        health_data["components"]["celery"] = {
            "broker_configured": bool(settings.CELERY_BROKER_URL),
            "broker_url": settings.CELERY_BROKER_URL,
            "result_backend_configured": bool(settings.CELERY_RESULT_BACKEND),
        }

        # Overall status calculation
        if not all_ok:
            health_data["status"] = "degraded"
            return Response(health_data, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response(health_data, status=status.HTTP_200_OK)


class ApiRootView(APIView):
    """
    Root API view providing discovery for Brofessor endpoints.
    """
    permission_classes = [AllowAny]

    @extend_schema(
        summary="API Root",
        description="Lists all primary module endpoints of the Brofessor system.",
        responses={200: inline_serializer("ApiRootResponse", fields={})},
    )
    def get(self, request, *args, **kwargs):

        return Response({
            "name": "Brofessor API",
            "version": "1.0.0",
            "description": "Local-first Personal Knowledge System API",
            "endpoints": {
                "health": request.build_absolute_uri("health/"),
                "schema": request.build_absolute_uri("schema/"),
                "docs": request.build_absolute_uri("docs/"),
                "accounts": request.build_absolute_uri("accounts/"),
                "roadmap": request.build_absolute_uri("roadmap/"),
                "sources": request.build_absolute_uri("sources/"),
                "knowledge": request.build_absolute_uri("knowledge/"),
                "assessments": request.build_absolute_uri("assessments/"),
                "rag": request.build_absolute_uri("rag/"),
                "processing": request.build_absolute_uri("processing/"),
            },
        })


def custom_404_handler(request, exception=None):
    from django.http import JsonResponse
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "status_code": 404,
                    "type": "NotFound",
                    "message": "The requested API endpoint was not found.",
                    "details": None,
                },
            },
            status=404,
        )
    from django.views.defaults import page_not_found
    return page_not_found(request, exception)


def custom_500_handler(request):
    from django.http import JsonResponse
    if request.path.startswith("/api/"):
        return JsonResponse(
            {
                "success": False,
                "error": {
                    "status_code": 500,
                    "type": "InternalServerError",
                    "message": "An internal server error occurred.",
                    "details": None,
                },
            },
            status=500,
        )
    from django.views.defaults import server_error
    return server_error(request)

