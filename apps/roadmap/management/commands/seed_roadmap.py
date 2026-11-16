from django.core.management.base import BaseCommand
from django.core.management import call_command
from apps.roadmap.models import Domain, Skill
from apps.assessments.models import Assessment, Question


class Command(BaseCommand):
    help = "Seeds canonical Artificial Intelligence & Machine Learning domain roadmap and diagnostic assessments."

    def handle(self, *args, **options):
        self.stdout.write("Seeding canonical AI/ML domain roadmap...")

        # 1. Purge or deactivate non-AI/ML domains so ONLY Artificial Intelligence & Machine Learning is active
        canonical_slugs = ["artificial-intelligence-machine-learning"]
        non_aiml = Domain.objects.exclude(slug__in=canonical_slugs)
        if non_aiml.exists():
            non_aiml.update(is_active=False, is_selected=False)
            self.stdout.write("Deactivated non-AI/ML domains. Only Artificial Intelligence & Machine Learning is active.")

        # 2. Invoke idempotent canonical curriculum seeder
        call_command("seed_domain_roadmaps")

        # 3. Ensure AI/ML domain is active and selected
        aiml = Domain.objects.filter(slug="artificial-intelligence-machine-learning").first()
        if aiml:
            aiml.is_active = True
            aiml.is_selected = True
            aiml.save(update_fields=["is_active", "is_selected"])

        self.stdout.write(self.style.SUCCESS("Roadmap seeding complete! Only Artificial Intelligence & Machine Learning roadmap is active."))
