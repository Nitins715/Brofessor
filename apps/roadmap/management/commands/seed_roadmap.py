from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.roadmap.models import Domain, Skill
from apps.assessments.models import Assessment, Question


class Command(BaseCommand):
    help = "Seeds canonical AI/ML and Data Science domains, roadmaps, and baseline diagnostic assessments."

    def handle(self, *args, **options):
        self.stdout.write("Seeding canonical AI/ML and Data Science domain roadmaps...")

        # 1. Purge any legacy domains that are not our canonical 2 domains
        canonical_slugs = ["artificial-intelligence-machine-learning", "data-science"]
        legacy_domains = Domain.objects.exclude(slug__in=canonical_slugs)
        if legacy_domains.exists():
            legacy_names = list(legacy_domains.values_list("name", flat=True))
            legacy_domains.delete()
            self.stdout.write(f"Removed legacy non-canonical domains: {legacy_names}")

        # 2. Invoke idempotent canonical curriculum seeder
        call_command("seed_domain_roadmaps")

        # 3. Ensure a canonical domain is selected if none currently selected
        if not Domain.objects.filter(is_selected=True).exists():
            first_domain = Domain.objects.filter(slug="artificial-intelligence-machine-learning").first() or Domain.objects.first()
            if first_domain:
                first_domain.is_selected = True
                first_domain.save(update_fields=["is_selected"])

        self.stdout.write(self.style.SUCCESS("Canonical roadmap seeding complete! Only AI/ML and Data Science domains are active."))
