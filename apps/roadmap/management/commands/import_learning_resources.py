import json
import os
import sys
from datetime import datetime
from urllib.parse import urlparse

from django.core.management.base import BaseCommand, CommandError
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction

from apps.roadmap.models import Skill, LearningResource, SkillResourceMapping


class Command(BaseCommand):
    help = "Idempotently imports, validates, and maps curated external learning resources to roadmap skills."

    def add_arguments(self, parser):
        parser.add_argument(
            "--file",
            type=str,
            default=os.path.join("apps", "roadmap", "data", "aiml_learning_resources.json"),
            help="Path to JSON file containing learning resources seed data.",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Validate data and simulate execution without saving changes to the database.",
        )
        parser.add_argument(
            "--strict",
            action="store_true",
            help="Fail immediately on any validation warning or unknown skill reference.",
        )

    def validate_url(self, url: str) -> bool:
        """Validates that a URL is well-formed with valid scheme and network location."""
        if not url or not isinstance(url, str):
            return False
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.netloc:
            return False
        validator = URLValidator(schemes=["http", "https"])
        try:
            validator(url)
            return True
        except DjangoValidationError:
            return False

    def validate_date(self, date_str: str):
        """Validates and parses YYYY-MM-DD date format."""
        if not date_str:
            return None
        try:
            return datetime.strptime(str(date_str).strip(), "%Y-%m-%d").date()
        except ValueError:
            return None

    def handle(self, *args, **options):
        file_path = options["file"]
        dry_run = options.get("dry_run", False)
        strict = options.get("strict", False)

        if not os.path.isabs(file_path):
            file_path = os.path.abspath(file_path)

        if not os.path.exists(file_path):
            raise CommandError(f"Resource seed file not found: {file_path}")

        self.stdout.write(f"Reading seed file: {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise CommandError(f"Failed to parse JSON file: {e}")

        if not isinstance(data, list):
            raise CommandError("Expected top-level JSON array of resource entries.")

        if dry_run:
            self.stdout.write(self.style.WARNING("Running in DRY-RUN mode. No database records will be saved."))

        # Cache existing skills by slug for fast and accurate validation
        skills_by_slug = {s.slug: s for s in Skill.objects.select_related("topic", "topic__domain").all()}

        valid_resource_types = {c[0] for c in LearningResource.ResourceType.choices}
        valid_statuses = {c[0] for c in LearningResource.VerificationStatus.choices}

        errors = []
        warnings = []
        validated_entries = []
        seen_mappings = set()

        # Step 1: In-depth Schema & Integrity Validation
        for idx, entry in enumerate(data):
            entry_id = f"Entry #{idx + 1}"

            # Extract resource info
            if "resource" in entry and isinstance(entry["resource"], dict):
                r_info = entry["resource"]
                skill_slug = entry.get("skill_slug") or entry.get("skill")
                is_primary = entry.get("is_primary", False)
                order = entry.get("order", 0)
                notes = entry.get("notes", "")
            else:
                r_info = entry
                skill_slug = entry.get("skill_slug") or entry.get("skill")
                is_primary = entry.get("is_primary", False)
                order = entry.get("order", 0)
                notes = entry.get("notes", "")

            if not skill_slug:
                errors.append(f"{entry_id}: Missing 'skill_slug'.")
                continue

            if skill_slug not in skills_by_slug:
                msg = f"{entry_id}: Skill with slug '{skill_slug}' does not exist in the database."
                if strict:
                    errors.append(msg)
                else:
                    warnings.append(msg)
                continue

            url = (r_info.get("url") or "").strip()
            if not self.validate_url(url):
                errors.append(f"{entry_id} (skill '{skill_slug}'): Invalid or malformed URL '{url}'.")
                continue

            title = (r_info.get("title") or "").strip()
            if not title:
                errors.append(f"{entry_id}: Title is empty.")
                continue

            source = (r_info.get("source") or "External").strip()
            description = (r_info.get("description") or "").strip()

            resource_type = r_info.get("resource_type", LearningResource.ResourceType.PRIMARY).lower().strip()
            if resource_type not in valid_resource_types:
                errors.append(f"{entry_id}: Invalid resource_type '{resource_type}'. Valid choices: {sorted(valid_resource_types)}")
                continue

            verification_status = r_info.get("verification_status", LearningResource.VerificationStatus.VERIFIED).lower().strip()
            if verification_status not in valid_statuses:
                errors.append(f"{entry_id}: Invalid verification_status '{verification_status}'. Valid choices: {sorted(valid_statuses)}")
                continue

            raw_date = r_info.get("last_verified_date")
            parsed_date = self.validate_date(raw_date) if raw_date else None
            if raw_date and not parsed_date:
                warnings.append(f"{entry_id}: Malformed last_verified_date '{raw_date}' (expected YYYY-MM-DD).")

            # Duplicate mapping check within seed data
            mapping_key = (skill_slug, url)
            if mapping_key in seen_mappings:
                warnings.append(f"{entry_id}: Duplicate mapping detected for skill '{skill_slug}' and URL '{url}'. Will merge idempotently.")
            else:
                seen_mappings.add(mapping_key)

            validated_entries.append({
                "skill": skills_by_slug[skill_slug],
                "skill_slug": skill_slug,
                "url": url,
                "title": title,
                "description": description,
                "resource_type": resource_type,
                "source": source,
                "verification_status": verification_status,
                "last_verified_date": parsed_date,
                "is_primary": bool(is_primary),
                "order": int(order) if str(order).isdigit() else 0,
                "notes": notes,
            })

        # Report validation findings
        if warnings:
            self.stdout.write(self.style.WARNING(f"\nValidation Warnings ({len(warnings)}):"))
            for w in warnings[:15]:
                self.stdout.write(self.style.WARNING(f"  [WARN] {w}"))
            if len(warnings) > 15:
                self.stdout.write(self.style.WARNING(f"  ... and {len(warnings) - 15} more warnings."))

        if errors:
            self.stderr.write(self.style.ERROR(f"\nValidation Errors Encountered ({len(errors)}):"))
            for err in errors[:20]:
                self.stderr.write(self.style.ERROR(f"  [ERR] {err}"))
            if len(errors) > 20:
                self.stderr.write(self.style.ERROR(f"  ... and {len(errors) - 20} more errors."))
            raise CommandError(f"Import aborted due to {len(errors)} validation error(s).")

        self.stdout.write(self.style.SUCCESS(
            f"Validation passed: {len(validated_entries)} valid mappings found for {len(seen_mappings)} distinct pairs."
        ))

        # Step 2: Idempotent Database Execution
        stats = {
            "resources_created": 0,
            "resources_updated": 0,
            "resources_unchanged": 0,
            "mappings_created": 0,
            "mappings_updated": 0,
            "mappings_unchanged": 0,
        }

        try:
            with transaction.atomic():
                for item in validated_entries:
                    # 1. Upsert LearningResource by unique URL
                    existing_resource = LearningResource.objects.filter(url=item["url"]).first()
                    if not existing_resource:
                        if not dry_run:
                            resource = LearningResource.objects.create(
                                url=item["url"],
                                title=item["title"],
                                description=item["description"],
                                resource_type=item["resource_type"],
                                source=item["source"],
                                verification_status=item["verification_status"],
                                last_verified_date=item["last_verified_date"],
                            )
                        stats["resources_created"] += 1
                    else:
                        resource = existing_resource
                        needs_update = False
                        fields_to_check = {
                            "title": item["title"],
                            "description": item["description"],
                            "resource_type": item["resource_type"],
                            "source": item["source"],
                            "verification_status": item["verification_status"],
                        }
                        for field, val in fields_to_check.items():
                            if getattr(resource, field) != val:
                                setattr(resource, field, val)
                                needs_update = True
                        if item["last_verified_date"] and resource.last_verified_date != item["last_verified_date"]:
                            resource.last_verified_date = item["last_verified_date"]
                            needs_update = True

                        if needs_update:
                            if not dry_run:
                                resource.save()
                            stats["resources_updated"] += 1
                        else:
                            stats["resources_unchanged"] += 1

                    # 2. Upsert SkillResourceMapping
                    if dry_run:
                        stats["mappings_created"] += 1
                        continue

                    mapping = SkillResourceMapping.objects.filter(skill=item["skill"], resource=resource).first()
                    if not mapping:
                        SkillResourceMapping.objects.create(
                            skill=item["skill"],
                            resource=resource,
                            is_primary=item["is_primary"],
                            order=item["order"],
                            notes=item["notes"],
                        )
                        stats["mappings_created"] += 1
                    else:
                        m_needs_update = False
                        if mapping.is_primary != item["is_primary"]:
                            mapping.is_primary = item["is_primary"]
                            m_needs_update = True
                        if mapping.order != item["order"]:
                            mapping.order = item["order"]
                            m_needs_update = True
                        if item["notes"] and mapping.notes != item["notes"]:
                            mapping.notes = item["notes"]
                            m_needs_update = True

                        if m_needs_update:
                            mapping.save()
                            stats["mappings_updated"] += 1
                        else:
                            stats["mappings_unchanged"] += 1

                if dry_run:
                    # Rollback in dry-run
                    transaction.set_rollback(True)

        except Exception as e:
            raise CommandError(f"Database import failed: {e}")

        # Summary output
        self.stdout.write("\n" + "=" * 55)
        self.stdout.write(self.style.SUCCESS("  IMPORT EXECUTION SUMMARY"))
        self.stdout.write("=" * 55)
        self.stdout.write(f"  Mode:                {'DRY-RUN (Simulated)' if dry_run else 'COMMITTED TO DATABASE'}")
        self.stdout.write(f"  Resources Created:   {stats['resources_created']}")
        self.stdout.write(f"  Resources Updated:   {stats['resources_updated']}")
        self.stdout.write(f"  Resources Unchanged: {stats['resources_unchanged']}")
        self.stdout.write(f"  Mappings Created:    {stats['mappings_created']}")
        self.stdout.write(f"  Mappings Updated:    {stats['mappings_updated']}")
        self.stdout.write(f"  Mappings Unchanged:  {stats['mappings_unchanged']}")
        self.stdout.write("=" * 55)
