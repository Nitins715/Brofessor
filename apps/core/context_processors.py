"""Global context processors for Brofessor templates."""
from apps.roadmap.models import Domain


def active_domain_context(request):
    """
    Globally supplies active_domain and available_domains to all templates.
    Enforces that only active domains are returned.
    """
    try:
        available_domains = list(Domain.objects.filter(is_active=True).order_by("name"))
        active_domain = Domain.objects.filter(is_selected=True, is_active=True).first()
        if not active_domain and available_domains:
            active_domain = available_domains[0]
        return {
            "active_domain": active_domain,
            "available_domains": available_domains,
        }
    except Exception:
        return {
            "active_domain": None,
            "available_domains": [],
        }
