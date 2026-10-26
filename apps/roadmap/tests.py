import json
import os
import tempfile
from datetime import date

from django.test import TestCase, Client
from django.urls import reverse
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.accounts.models import User
from apps.roadmap.models import Domain, Topic, Skill, LearningResource, SkillResourceMapping
from apps.roadmap.management.commands.import_learning_resources import Command as ImportCommand


class LearningResourceModelTestCase(TestCase):
    """Tests for LearningResource and SkillResourceMapping models."""

    def setUp(self):
        self.domain = Domain.objects.create(name="AI/ML Domain", slug="aiml-test-domain")
        self.topic = Topic.objects.create(domain=self.domain, name="Foundations", slug="foundations", order=1)
        self.skill = Skill.objects.create(topic=self.topic, name="PyTorch Basics", slug="pytorch-basics", order=1)

    def test_create_learning_resource(self):
        resource = LearningResource.objects.create(
            title="PyTorch Official Documentation",
            url="https://pytorch.org/docs/stable/index.html",
            resource_type=LearningResource.ResourceType.OFFICIAL_DOCS,
            source="PyTorch Docs",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
            last_verified_date=date(2026, 10, 14),
            description="Official deep learning framework docs.",
        )
        self.assertEqual(resource.title, "PyTorch Official Documentation")
        self.assertEqual(resource.resource_type, "official_docs")
        self.assertTrue(resource.is_verified)
        self.assertIn("Official Docs", str(resource))

    def test_unverified_status(self):
        resource = LearningResource.objects.create(
            title="Draft Blog Post",
            url="https://example.com/draft",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="Personal Blog",
            verification_status=LearningResource.VerificationStatus.UNVERIFIED,
        )
        self.assertFalse(resource.is_verified)

    def test_skill_resource_mapping(self):
        res1 = LearningResource.objects.create(
            title="PyTorch Blitz",
            url="https://pytorch.org/tutorials/blitz",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="PyTorch Docs",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
        )
        res2 = LearningResource.objects.create(
            title="PyTorch Video",
            url="https://youtube.com/watch?v=pytorch",
            resource_type=LearningResource.ResourceType.VIDEO,
            source="YouTube",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
        )

        mapping1 = SkillResourceMapping.objects.create(
            skill=self.skill,
            resource=res1,
            is_primary=True,
            order=1,
            notes="Primary starting point",
        )
        mapping2 = SkillResourceMapping.objects.create(
            skill=self.skill,
            resource=res2,
            is_primary=False,
            order=2,
        )

        # Delegates
        self.assertEqual(mapping1.title, "PyTorch Blitz")
        self.assertEqual(mapping1.url, "https://pytorch.org/tutorials/blitz")
        self.assertEqual(mapping1.resource_type, "primary")
        self.assertEqual(mapping1.source, "PyTorch Docs")
        self.assertTrue(mapping1.is_verified)
        self.assertIn("[PRIMARY]", str(mapping1))

        # Skill helper methods
        verified_mappings = list(self.skill.get_verified_resource_mappings())
        self.assertEqual(len(verified_mappings), 2)
        # Primary should be first
        self.assertEqual(verified_mappings[0].id, mapping1.id)

        grouped = self.skill.get_grouped_resources()
        self.assertEqual(len(grouped[LearningResource.ResourceType.PRIMARY]), 1)
        self.assertEqual(len(grouped[LearningResource.ResourceType.VIDEO]), 1)
        self.assertEqual(len(grouped[LearningResource.ResourceType.OFFICIAL_DOCS]), 0)

    def test_unique_together_constraint(self):
        resource = LearningResource.objects.create(
            title="Single Resource",
            url="https://example.com/single",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="Example",
        )
        SkillResourceMapping.objects.create(skill=self.skill, resource=resource)
        with self.assertRaises(Exception):
            SkillResourceMapping.objects.create(skill=self.skill, resource=resource)


class URLAndDateValidationTestCase(TestCase):
    """Tests URL validation and date parsing in import command."""

    def setUp(self):
        self.cmd = ImportCommand()

    def test_valid_urls(self):
        valid = [
            "https://www.geeksforgeeks.org/python-variables/",
            "http://pytorch.org/docs/stable/index.html",
            "https://github.com/huggingface/transformers",
            "https://sub.domain.co.uk/path?arg=1&param=two#fragment",
        ]
        for url in valid:
            self.assertTrue(self.cmd.validate_url(url), f"Failed for {url}")

    def test_invalid_urls(self):
        invalid = [
            "",
            None,
            "not-a-url",
            "ftp://ftp.example.com",
            "javascript:alert(1)",
            "http:///no-domain.com",
            "https://",
        ]
        for url in invalid:
            self.assertFalse(self.cmd.validate_url(url), f"Should fail for {url}")

    def test_valid_and_invalid_dates(self):
        self.assertEqual(self.cmd.validate_date("2026-10-14"), date(2026, 10, 14))
        self.assertIsNone(self.cmd.validate_date("invalid-date"))
        self.assertIsNone(self.cmd.validate_date(""))
        self.assertIsNone(self.cmd.validate_date(None))


class ImportCommandTestCase(TestCase):
    """Tests the import_learning_resources management command."""

    def setUp(self):
        self.domain = Domain.objects.create(name="Import Domain", slug="import-domain")
        self.topic = Topic.objects.create(domain=self.domain, name="Math", slug="math", order=1)
        self.skill = Skill.objects.create(topic=self.topic, name="Calculus", slug="math-calculus", order=1)

    def test_successful_import_and_idempotence(self):
        data = [
            {
                "skill_slug": "math-calculus",
                "is_primary": True,
                "order": 1,
                "notes": "Calculus primer",
                "resource": {
                    "title": "Essence of Calculus",
                    "url": "https://www.youtube.com/playlist?list=calculus",
                    "description": "Visual intuition of derivatives and integrals.",
                    "resource_type": "video",
                    "source": "YouTube",
                    "verification_status": "verified",
                    "last_verified_date": "2026-10-14",
                },
            },
            {
                "skill_slug": "math-calculus",
                "is_primary": False,
                "order": 2,
                "resource": {
                    "title": "Calculus Documentation",
                    "url": "https://docs.scipy.org/doc/scipy/reference/tutorial/integrate.html",
                    "description": "Numerical integration docs.",
                    "resource_type": "official_docs",
                    "source": "SciPy Docs",
                    "verification_status": "verified",
                    "last_verified_date": "2026-10-14",
                },
            },
        ]

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            # 1. First run: creates resources
            call_command("import_learning_resources", file=temp_path)
            self.assertEqual(LearningResource.objects.count(), 2)
            self.assertEqual(SkillResourceMapping.objects.count(), 2)

            # 2. Second run: 100% idempotent
            call_command("import_learning_resources", file=temp_path)
            self.assertEqual(LearningResource.objects.count(), 2)
            self.assertEqual(SkillResourceMapping.objects.count(), 2)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_dry_run_leaves_database_untouched(self):
        data = [
            {
                "skill_slug": "math-calculus",
                "is_primary": True,
                "resource": {
                    "title": "Dry Run Resource",
                    "url": "https://example.com/dry-run",
                    "resource_type": "primary",
                    "source": "Example",
                    "verification_status": "verified",
                },
            }
        ]

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            call_command("import_learning_resources", file=temp_path, dry_run=True)
            self.assertEqual(LearningResource.objects.filter(url="https://example.com/dry-run").count(), 0)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_invalid_url_raises_command_error(self):
        data = [
            {
                "skill_slug": "math-calculus",
                "resource": {
                    "title": "Bad Resource",
                    "url": "not_a_valid_url",
                    "resource_type": "primary",
                    "source": "Example",
                },
            }
        ]

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(CommandError):
                call_command("import_learning_resources", file=temp_path)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_missing_skill_strict_mode_raises(self):
        data = [
            {
                "skill_slug": "non-existent-skill-slug",
                "resource": {
                    "title": "Orphan Resource",
                    "url": "https://example.com/orphan",
                    "resource_type": "primary",
                    "source": "Example",
                },
            }
        ]

        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".json", encoding="utf-8") as f:
            json.dump(data, f)
            temp_path = f.name

        try:
            with self.assertRaises(CommandError):
                call_command("import_learning_resources", file=temp_path, strict=True)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


class ResourceAPITestCase(TestCase):
    """Tests the REST API endpoints for Learning Resources."""

    def setUp(self):
        self.client = Client()
        self.domain = Domain.objects.create(name="API Domain", slug="api-domain")
        self.topic = Topic.objects.create(domain=self.domain, name="API Topic", slug="api-topic", order=1)
        self.skill = Skill.objects.create(topic=self.topic, name="API Skill", slug="api-skill", order=1)

        self.res1 = LearningResource.objects.create(
            title="GFG Python Guide",
            url="https://www.geeksforgeeks.org/python-api-test/",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="GeeksforGeeks",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
            last_verified_date=date(2026, 10, 14),
        )
        self.mapping1 = SkillResourceMapping.objects.create(
            skill=self.skill,
            resource=self.res1,
            is_primary=True,
            order=1,
        )

    def test_get_skill_resources_flat(self):
        url = reverse("roadmap-skill-resources", kwargs={"pk": self.skill.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "GFG Python Guide")
        self.assertTrue(data[0]["is_primary"])
        self.assertEqual(data[0]["source"], "GeeksforGeeks")

    def test_get_skill_resources_grouped(self):
        url = reverse("roadmap-skill-resources", kwargs={"pk": self.skill.id}) + "?grouped=true"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("primary", data)
        self.assertIn("official_docs", data)
        self.assertEqual(len(data["primary"]), 1)

    def test_list_and_search_resources(self):
        url = reverse("roadmap-resources-list") + "?search=GFG"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["title"], "GFG Python Guide")

    def test_create_and_detail_resource(self):
        url = reverse("roadmap-resources-list")
        payload = {
            "title": "New Official Guide",
            "url": "https://docs.python.org/3/new",
            "resource_type": "official_docs",
            "source": "Python Docs",
            "verification_status": "verified",
        }
        create_resp = self.client.post(url, data=json.dumps(payload), content_type="application/json")
        self.assertEqual(create_resp.status_code, 201)
        res_id = create_resp.json()["id"]

        detail_url = reverse("roadmap-resource-detail", kwargs={"pk": res_id})
        detail_resp = self.client.get(detail_url)
        self.assertEqual(detail_resp.status_code, 200)
        self.assertEqual(detail_resp.json()["title"], "New Official Guide")


class SkillDetailUIIntegrationTestCase(TestCase):
    """Tests the Skill Detail Web UI rendering external resources and empty states."""

    def setUp(self):
        self.user = User.objects.create_user(username="testdev", password="password123")
        self.client = Client()
        self.client.force_login(self.user)

        self.domain = Domain.objects.create(name="UI Test Domain", slug="ui-domain", is_selected=True)
        self.topic = Topic.objects.create(domain=self.domain, name="UI Topic", slug="ui-topic", order=1)
        self.skill_with_res = Skill.objects.create(topic=self.topic, name="Skill With Resources", slug="skill-with-res", order=1)
        self.skill_empty = Skill.objects.create(topic=self.topic, name="Skill Empty", slug="skill-empty", order=2)

        self.resource = LearningResource.objects.create(
            title="Verified GFG Machine Learning Primer",
            url="https://www.geeksforgeeks.org/ml-primer/",
            description="Clear overview of supervised and unsupervised paradigms.",
            resource_type=LearningResource.ResourceType.PRIMARY,
            source="GeeksforGeeks",
            verification_status=LearningResource.VerificationStatus.VERIFIED,
            last_verified_date=date(2026, 10, 14),
        )
        SkillResourceMapping.objects.create(
            skill=self.skill_with_res,
            resource=self.resource,
            is_primary=True,
            order=1,
        )

    def test_skill_with_verified_resources_renders_correctly(self):
        url = reverse("web-skill-detail", kwargs={"pk": self.skill_with_res.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Heading and Badges
        self.assertIn("Curated External Learning Resources", content)
        self.assertIn("Verified GFG Machine Learning Primer", content)
        self.assertIn("GeeksforGeeks", content)
        self.assertIn("https://www.geeksforgeeks.org/ml-primer/", content)
        self.assertIn('target="_blank"', content)
        self.assertIn("Open", content)

        # Decoupling Notice (Requirement 9)
        self.assertIn("Self-Study Resources:", content)
        self.assertIn("External completion does not alter Brofessor assessment scores", content)

    def test_skill_without_resources_renders_empty_state(self):
        url = reverse("web-skill-detail", kwargs={"pk": self.skill_empty.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        content = response.content.decode("utf-8")

        # Empty State (Requirement 8)
        self.assertIn("Curated External Learning Resources", content)
        self.assertIn("0 verified", content)
        self.assertIn("No verified resources available yet", content)
