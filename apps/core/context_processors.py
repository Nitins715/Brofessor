"""Global context processors for Brofessor templates."""
import sys
from apps.roadmap.models import Domain


def active_domain_context(request):
    """
    Globally supplies active_domain and available_domains to all templates.
    Enforces that only active domains are returned and default curriculum is populated automatically.
    """
    try:
        available_domains = list(Domain.objects.filter(is_active=True).order_by("name"))
        if not available_domains and "test" not in sys.argv:
            from django.core.management import call_command
            call_command("seed_roadmap")
            call_command("seed_domain_roadmaps")
            available_domains = list(Domain.objects.filter(is_active=True).order_by("name"))

        active_domain = Domain.objects.filter(is_selected=True, is_active=True).first()
        if not active_domain and available_domains:
            active_domain = available_domains[0]
            Domain.objects.filter(id=active_domain.id).update(is_selected=True)
            active_domain.is_selected = True

        return {
            "active_domain": active_domain,
            "available_domains": available_domains,
        }
    except Exception:
        return {
            "active_domain": None,
            "available_domains": [],
        }

