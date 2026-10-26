"""Middleware for Brofessor Local-First Single Workspace.

Ensures every incoming request is automatically authenticated as the single
local workspace user, eliminating unnecessary sign-in prompts and session expiration.
"""

import logging
from apps.accounts.models import User

logger = logging.getLogger("brofessor")


def get_or_create_local_user():
    """Ensure a default local workspace user exists for single-user local app."""
    user = User.objects.filter(is_superuser=True).first()
    if not user:
        user = User.objects.filter(username="brofessor").first()
    if not user:
        user = User.objects.first()
    if not user:
        user = User.objects.create_user(
            username="brofessor",
            email="local@brofessor.ai",
            password="brofessor-local-workspace-password",
        )
    return user


class LocalWorkspaceUserMiddleware:
    """
    Auto-authenticates every HTTP request to app and API routes as the single local workspace user.
    Removes login friction and ensures local-first zero-configuration access.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_paths = ["/", "/logout/"]
        if request.path not in exempt_paths:
            if not hasattr(request, "user") or not request.user.is_authenticated:
                try:
                    local_user = get_or_create_local_user()
                    request.user = local_user
                    if hasattr(request, "session") and not request.session.get("_auth_user_id"):
                        request.session["_auth_user_id"] = str(local_user.id)
                        request.session["_auth_user_backend"] = "django.contrib.auth.backends.ModelBackend"
                except Exception as e:
                    logger.warning(f"Failed to auto-authenticate local workspace user: {e}")

        response = self.get_response(request)
        return response

