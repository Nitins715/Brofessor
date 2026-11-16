import sys
from django.apps import AppConfig
from django.db.models.signals import post_migrate


def auto_seed_default_roadmap(sender, **kwargs):
    """Ensure standard AI/ML curriculum roadmap is populated by default after migrations."""
    if sender.name != "apps.roadmap":
        return
    if "test" in sys.argv:
        return
    try:
        from apps.roadmap.models import Domain
        if not Domain.objects.filter(slug="artificial-intelligence-machine-learning").exists():
            from django.core.management import call_command
            call_command("seed_roadmap")
            call_command("seed_domain_roadmaps")
    except Exception:
        pass


class RoadmapConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.roadmap"
    label = "roadmap"

    def ready(self):
        post_migrate.connect(auto_seed_default_roadmap, sender=self)

