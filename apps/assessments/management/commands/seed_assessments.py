"""Management command to seed baseline diagnostic assessment containers for foundational skills.

Creates clean, active assessment containers across topics in the active domain without
hardcoded questions. Questions are generated dynamically on-demand when the user takes the assessment.
"""

from django.core.management.base import BaseCommand
from apps.roadmap.models import Domain, Skill, Topic
from apps.assessments.models import Assessment
from apps.assessments.services.sequential_generator import SequentialQuestionGenerationService


class Command(BaseCommand):
    help = "Seed baseline diagnostic assessment containers for curriculum skills."

    def add_arguments(self, parser):
        parser.add_argument(
            "--all-skills",
            action="store_true",
            help="Create assessment containers for all skills rather than just foundational ones.",
        )

    def handle(self, *args, **options):
        self.stdout.write("Initializing baseline diagnostic assessments...")

        active_domain = Domain.objects.filter(is_selected=True).first() or Domain.objects.first()
        if not active_domain:
            self.stdout.write(self.style.WARNING("No domain found. Please seed roadmap first."))
            return

        topics = list(active_domain.get_all_topics())
        target_skills = []
        for topic in topics:
            skills = list(topic.skills.all().order_by("order"))
            target_skills.extend(skills if options.get("all_skills") else skills[:2])

        created_count = 0
        for skill in target_skills:
            existing = Assessment.objects.filter(skill=skill, difficulty_level="easy", is_active=True).first()
            if not existing:
                Assessment.objects.create(
                    skill=skill,
                    topic=skill.topic,
                    title=f"Diagnostic: {skill.name} (Easy)",
                    description=f"Foundational diagnostic evaluating baseline concepts in {skill.name}.",
                    difficulty_level="easy",
                    passing_score=70.00,
                    time_limit_minutes=15,
                    target_questions_count=10,
                    is_active=True,
                    status=Assessment.AssessmentStatus.ACTIVE,
                )
                created_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully initialized {created_count} diagnostic assessment containers for {active_domain.name}!"
            )
        )
