import sys
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.roadmap.models import Domain, Topic, Skill, RoadmapNode, RoadmapProgress
from apps.roadmap.curriculum_data import (
    DOMAINS_DATA,
    SHARED_FOUNDATION_TOPICS,
    AIML_SPECIALIZATION_TOPICS,
    DATA_SCIENCE_SPECIALIZATION_TOPICS,
)


class Command(BaseCommand):
    help = "Idempotently seeds AI/ML and Data Science domain roadmaps with shared CSE foundation."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Simulate execution without committing changes to the database.",
        )

    def handle(self, *args, **options):
        dry_run = options.get("dry_run", False)
        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No changes will be saved."))

        # 1. Pre-validation: Verify integrity of curriculum dataset
        self.stdout.write("Validating curriculum dataset integrity...")
        all_skills_data = {}
        for topic in SHARED_FOUNDATION_TOPICS + AIML_SPECIALIZATION_TOPICS + DATA_SCIENCE_SPECIALIZATION_TOPICS:
            for s in topic["skills"]:
                all_skills_data[s["slug"]] = s

        errors = []
        for slug, s in all_skills_data.items():
            for p in s.get("prerequisites", []):
                if p not in all_skills_data:
                    errors.append(f"Skill '{slug}' references unknown prerequisite '{p}'.")
                if p == slug:
                    errors.append(f"Skill '{slug}' has self-referential prerequisite.")

        # Cycle check
        visited = {}
        def check_cycle(slug, path):
            visited[slug] = 1
            for p in all_skills_data[slug].get("prerequisites", []):
                if p in path:
                    return path + [p]
                if p in all_skills_data and p not in visited:
                    cycle = check_cycle(p, path + [p])
                    if cycle:
                        return cycle
            visited[slug] = 2
            return None

        cycles = []
        for slug in all_skills_data:
            if slug not in visited:
                c = check_cycle(slug, [slug])
                if c:
                    cycles.append(c)

        if errors or cycles:
            for err in errors:
                self.stderr.write(self.style.ERROR(f"Integrity Error: {err}"))
            for cyc in cycles:
                self.stderr.write(self.style.ERROR(f"Prerequisite Cycle Detected: {' -> '.join(cyc)}"))
            sys.exit(1)

        self.stdout.write(self.style.SUCCESS(f"Validation passed: {len(all_skills_data)} skills, 0 errors, 0 cycles."))

        # Tracking stats
        stats = {
            "domains_created": 0,
            "domains_updated": 0,
            "domains_unchanged": 0,
            "topics_created": 0,
            "topics_updated": 0,
            "topics_unchanged": 0,
            "skills_created": 0,
            "skills_updated": 0,
            "skills_unchanged": 0,
            "nodes_created": 0,
            "nodes_updated": 0,
            "nodes_unchanged": 0,
            "prerequisites_linked": 0,
        }

        try:
            with transaction.atomic():
                # 2. Seed Domains
                domains_by_slug = {}
                for d_data in DOMAINS_DATA:
                    domain, created = Domain.objects.get_or_create(
                        slug=d_data["slug"],
                        defaults={
                            "name": d_data["name"],
                            "description": d_data["description"],
                            "is_active": d_data.get("is_active", True),
                            "is_selected": d_data.get("is_selected", False),
                        },
                    )
                    if created:
                        stats["domains_created"] += 1
                        self.stdout.write(f"  + Created Domain: {domain.name} ({domain.slug})")
                    else:
                        updated = False
                        if domain.name != d_data["name"]:
                            domain.name = d_data["name"]
                            updated = True
                        if domain.description != d_data["description"]:
                            domain.description = d_data["description"]
                            updated = True
                        if updated:
                            domain.save()
                            stats["domains_updated"] += 1
                            self.stdout.write(f"  ~ Updated Domain: {domain.name}")
                        else:
                            stats["domains_unchanged"] += 1
                    domains_by_slug[d_data["slug"]] = domain

                aiml_domain = domains_by_slug["artificial-intelligence-machine-learning"]
                ds_domain = domains_by_slug["data-science"]

                # 3. Seed Shared Foundation Topics (linked to both AI/ML and Data Science)
                self.stdout.write("\nSeeding Shared CSE Foundation (linked to both domains)...")
                shared_topics = []
                for t_data in SHARED_FOUNDATION_TOPICS:
                    topic, created = Topic.objects.get_or_create(
                        domain=aiml_domain,
                        slug=t_data["slug"],
                        defaults={
                            "name": t_data["name"],
                            "description": t_data["description"],
                            "priority": t_data.get("priority", "P0"),
                            "learning_objectives": t_data.get("learning_objectives", []),
                            "estimated_effort_hours": t_data.get("estimated_effort_hours", 0),
                            "order": t_data.get("order", 0),
                        },
                    )
                    if created:
                        stats["topics_created"] += 1
                    else:
                        updated = False
                        if topic.name != t_data["name"]:
                            topic.name = t_data["name"]
                            updated = True
                        if topic.description != t_data["description"]:
                            topic.description = t_data["description"]
                            updated = True
                        if topic.priority != t_data.get("priority", "P0"):
                            topic.priority = t_data.get("priority", "P0")
                            updated = True
                        if topic.learning_objectives != t_data.get("learning_objectives", []):
                            topic.learning_objectives = t_data.get("learning_objectives", [])
                            updated = True
                        if topic.estimated_effort_hours != t_data.get("estimated_effort_hours", 0):
                            topic.estimated_effort_hours = t_data.get("estimated_effort_hours", 0)
                            updated = True
                        if topic.order != t_data.get("order", 0):
                            topic.order = t_data.get("order", 0)
                            updated = True
                        if updated:
                            topic.save()
                            stats["topics_updated"] += 1
                        else:
                            stats["topics_unchanged"] += 1

                    # Ensure additional_domains includes Data Science
                    if not topic.additional_domains.filter(id=ds_domain.id).exists():
                        topic.additional_domains.add(ds_domain)

                    shared_topics.append((topic, t_data))

                # 4. Seed AI/ML Specialization Topics
                self.stdout.write("Seeding AI/ML Specialization Topics...")
                aiml_topics = []
                for t_data in AIML_SPECIALIZATION_TOPICS:
                    topic, created = Topic.objects.get_or_create(
                        domain=aiml_domain,
                        slug=t_data["slug"],
                        defaults={
                            "name": t_data["name"],
                            "description": t_data["description"],
                            "priority": t_data.get("priority", "P0"),
                            "learning_objectives": t_data.get("learning_objectives", []),
                            "estimated_effort_hours": t_data.get("estimated_effort_hours", 0),
                            "order": t_data.get("order", 0),
                        },
                    )
                    if created:
                        stats["topics_created"] += 1
                    else:
                        updated = False
                        if topic.name != t_data["name"]:
                            topic.name = t_data["name"]
                            updated = True
                        if topic.description != t_data["description"]:
                            topic.description = t_data["description"]
                            updated = True
                        if topic.priority != t_data.get("priority", "P0"):
                            topic.priority = t_data.get("priority", "P0")
                            updated = True
                        if topic.learning_objectives != t_data.get("learning_objectives", []):
                            topic.learning_objectives = t_data.get("learning_objectives", [])
                            updated = True
                        if topic.estimated_effort_hours != t_data.get("estimated_effort_hours", 0):
                            topic.estimated_effort_hours = t_data.get("estimated_effort_hours", 0)
                            updated = True
                        if topic.order != t_data.get("order", 0):
                            topic.order = t_data.get("order", 0)
                            updated = True
                        if updated:
                            topic.save()
                            stats["topics_updated"] += 1
                        else:
                            stats["topics_unchanged"] += 1
                    aiml_topics.append((topic, t_data))

                # 5. Seed Data Science Specialization Topics
                self.stdout.write("Seeding Data Science Specialization Topics...")
                ds_topics = []
                for t_data in DATA_SCIENCE_SPECIALIZATION_TOPICS:
                    topic, created = Topic.objects.get_or_create(
                        domain=ds_domain,
                        slug=t_data["slug"],
                        defaults={
                            "name": t_data["name"],
                            "description": t_data["description"],
                            "priority": t_data.get("priority", "P0"),
                            "learning_objectives": t_data.get("learning_objectives", []),
                            "estimated_effort_hours": t_data.get("estimated_effort_hours", 0),
                            "order": t_data.get("order", 0),
                        },
                    )
                    if created:
                        stats["topics_created"] += 1
                    else:
                        updated = False
                        if topic.name != t_data["name"]:
                            topic.name = t_data["name"]
                            updated = True
                        if topic.description != t_data["description"]:
                            topic.description = t_data["description"]
                            updated = True
                        if topic.priority != t_data.get("priority", "P0"):
                            topic.priority = t_data.get("priority", "P0")
                            updated = True
                        if topic.learning_objectives != t_data.get("learning_objectives", []):
                            topic.learning_objectives = t_data.get("learning_objectives", [])
                            updated = True
                        if topic.estimated_effort_hours != t_data.get("estimated_effort_hours", 0):
                            topic.estimated_effort_hours = t_data.get("estimated_effort_hours", 0)
                            updated = True
                        if topic.order != t_data.get("order", 0):
                            topic.order = t_data.get("order", 0)
                            updated = True
                        if updated:
                            topic.save()
                            stats["topics_updated"] += 1
                        else:
                            stats["topics_unchanged"] += 1
                    ds_topics.append((topic, t_data))

                # 6. Seed Skills & RoadmapNodes across all topics
                self.stdout.write("\nSeeding individual skills and roadmap nodes...")
                skills_by_slug = {}
                nodes_by_skill = {}

                all_topic_tuples = shared_topics + aiml_topics + ds_topics
                for topic, t_data in all_topic_tuples:
                    for s_order, s_data in enumerate(t_data["skills"], start=1):
                        skill, created = Skill.objects.get_or_create(
                            topic=topic,
                            slug=s_data["slug"],
                            defaults={
                                "name": s_data["name"],
                                "description": s_data["description"],
                                "difficulty_level": s_data["difficulty_level"],
                                "priority": s_data.get("priority", "P0"),
                                "learning_objectives": s_data.get("learning_objectives", []),
                                "key_concepts": s_data.get("key_concepts", []),
                                "interview_relevance": s_data.get("interview_relevance", ""),
                                "evaluation_criteria": s_data.get("evaluation_criteria", ""),
                                "estimated_effort_hours": s_data.get("estimated_effort_hours", 0),
                                "order": s_order,
                            },
                        )
                        if created:
                            stats["skills_created"] += 1
                        else:
                            updated = False
                            if skill.name != s_data["name"]:
                                skill.name = s_data["name"]
                                updated = True
                            if skill.description != s_data["description"]:
                                skill.description = s_data["description"]
                                updated = True
                            if skill.difficulty_level != s_data["difficulty_level"]:
                                skill.difficulty_level = s_data["difficulty_level"]
                                updated = True
                            if skill.priority != s_data.get("priority", "P0"):
                                skill.priority = s_data.get("priority", "P0")
                                updated = True
                            if skill.learning_objectives != s_data.get("learning_objectives", []):
                                skill.learning_objectives = s_data.get("learning_objectives", [])
                                updated = True
                            if skill.key_concepts != s_data.get("key_concepts", []):
                                skill.key_concepts = s_data.get("key_concepts", [])
                                updated = True
                            if skill.interview_relevance != s_data.get("interview_relevance", ""):
                                skill.interview_relevance = s_data.get("interview_relevance", "")
                                updated = True
                            if skill.evaluation_criteria != s_data.get("evaluation_criteria", ""):
                                skill.evaluation_criteria = s_data.get("evaluation_criteria", "")
                                updated = True
                            if skill.estimated_effort_hours != s_data.get("estimated_effort_hours", 0):
                                skill.estimated_effort_hours = s_data.get("estimated_effort_hours", 0)
                                updated = True
                            if skill.order != s_order:
                                skill.order = s_order
                                updated = True
                            if updated:
                                skill.save()
                                stats["skills_updated"] += 1
                            else:
                                stats["skills_unchanged"] += 1

                        skills_by_slug[skill.slug] = skill

                        # RoadmapNode & RoadmapProgress (Preserving user progress if already present)
                        node, node_created = RoadmapNode.objects.get_or_create(
                            skill=skill,
                            defaults={
                                "domain": topic.domain,
                                "topic": topic,
                                "order": s_order,
                            },
                        )
                        if node_created:
                            stats["nodes_created"] += 1
                            RoadmapProgress.objects.get_or_create(
                                node=node,
                                defaults={
                                    "status": RoadmapProgress.ProgressStatus.NOT_STARTED,
                                    "is_current": False,
                                },
                            )
                        else:
                            # Node already exists; update fields if needed but never overwrite progress
                            node_updated = False
                            if node.topic_id != topic.id:
                                node.topic = topic
                                node_updated = True
                            if node.order != s_order:
                                node.order = s_order
                                node_updated = True
                            if node_updated:
                                node.save()
                                stats["nodes_updated"] += 1
                            else:
                                stats["nodes_unchanged"] += 1

                        nodes_by_skill[skill.slug] = node

                # 7. Wire up Prerequisites (Acyclic dependencies)
                self.stdout.write("\nWiring up prerequisite dependencies on Skills and RoadmapNodes...")
                for topic, t_data in all_topic_tuples:
                    for s_data in t_data["skills"]:
                        skill = skills_by_slug.get(s_data["slug"])
                        node = nodes_by_skill.get(s_data["slug"])
                        if not skill or not node:
                            continue

                        prereq_slugs = s_data.get("prerequisites", [])
                        prereq_skills = []
                        prereq_nodes = []

                        for p_slug in prereq_slugs:
                            p_skill = skills_by_slug.get(p_slug)
                            p_node = nodes_by_skill.get(p_slug)
                            if p_skill and p_node:
                                prereq_skills.append(p_skill)
                                prereq_nodes.append(p_node)

                        # Set prerequisites on Skill
                        skill.prerequisites.set(prereq_skills)
                        # Set prerequisites on RoadmapNode
                        node.prerequisites.set(prereq_nodes)
                        stats["prerequisites_linked"] += len(prereq_skills)

                if dry_run:
                    self.stdout.write(self.style.WARNING("\nDry-run completed. Rolling back all database changes."))
                    transaction.set_rollback(True)

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Seeding failed: {str(e)}"))
            raise e

        # Final Report
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS("ROADMAP SEEDING COMPLETE"))
        self.stdout.write("=" * 60)
        self.stdout.write(f"Domains : {stats['domains_created']} created, {stats['domains_updated']} updated, {stats['domains_unchanged']} unchanged")
        self.stdout.write(f"Topics  : {stats['topics_created']} created, {stats['topics_updated']} updated, {stats['topics_unchanged']} unchanged")
        self.stdout.write(f"Skills  : {stats['skills_created']} created, {stats['skills_updated']} updated, {stats['skills_unchanged']} unchanged")
        self.stdout.write(f"Nodes   : {stats['nodes_created']} created, {stats['nodes_updated']} updated, {stats['nodes_unchanged']} unchanged")
        self.stdout.write(f"Prereqs : {stats['prerequisites_linked']} prerequisite links established")
        self.stdout.write("=" * 60)
