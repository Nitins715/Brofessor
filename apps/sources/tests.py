import json
from unittest.mock import patch, MagicMock

from django.test import TestCase, Client
from django.urls import reverse

from apps.accounts.models import User
from apps.sources.models import Source, Document


class SourceClipViewTestCase(TestCase):
    """Tests for the 1-Click Bookmarklet Web Clipper View (GET & POST)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="clipper-tester",
            email="clipper@example.com",
            password="testpassword123",
        )
        self.client.force_login(self.user)
        self.clip_url = reverse("web-source-clip")

    def test_get_clip_popup_prefills_context(self):
        response = self.client.get(self.clip_url, {
            "url": "https://example.com/deep-dive-transformers",
            "title": "Deep Dive into Transformers",
            "selected": "Attention mechanisms allow models to focus on relevant tokens.",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/clip_popup.html")
        self.assertEqual(response.context["url"], "https://example.com/deep-dive-transformers")
        self.assertEqual(response.context["title"], "Deep Dive into Transformers")
        self.assertEqual(
            response.context["selected_text"],
            "Attention mechanisms allow models to focus on relevant tokens.",
        )
        self.assertFalse(response.context["success"])

    def test_get_clip_popup_defaults_when_empty(self):
        response = self.client.get(self.clip_url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["url"], "")
        self.assertEqual(response.context["title"], "Clipped Web Article")
        self.assertEqual(response.context["selected_text"], "")
        self.assertFalse(response.context["success"])

    @patch("apps.processing.pipeline.IngestionPipeline.process_source")
    def test_post_clip_creates_and_ingests_source(self, mock_process_source):
        mock_doc = MagicMock()
        mock_doc.chunks.count.return_value = 7
        mock_process_source.return_value = mock_doc

        target_url = "https://arxiv.org/abs/2401.00001"
        target_title = "Agentic Workflows in Distributed Systems"
        excerpt = "Multi-agent debate leads to higher factual accuracy."

        response = self.client.post(self.clip_url, {
            "url": target_url,
            "title": target_title,
            "selected_text": excerpt,
        })

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/clip_popup.html")
        self.assertTrue(response.context["success"])
        self.assertEqual(response.context["chunks_count"], 7)

        # Verify source saved in database
        source = Source.objects.get(uri=target_url)
        self.assertEqual(source.name, target_title)
        self.assertEqual(source.source_type, Source.SourceType.ARTICLE)
        self.assertEqual(source.metadata.get("clipped_via"), "browser_bookmarklet")
        self.assertEqual(source.metadata.get("selected_text"), excerpt)
        mock_process_source.assert_called_once_with(source.id)

    @patch("apps.processing.pipeline.IngestionPipeline.process_source")
    def test_post_clip_idempotent_for_existing_uri(self, mock_process_source):
        mock_doc = MagicMock()
        mock_doc.chunks.count.return_value = 3
        mock_process_source.return_value = mock_doc

        existing_url = "https://pytorch.org/tutorials/intro.html"
        existing_source = Source.objects.create(
            name="Original PyTorch Intro",
            source_type=Source.SourceType.ARTICLE,
            uri=existing_url,
        )

        response = self.client.post(self.clip_url, {
            "url": existing_url,
            "title": "Updated Title Attempt",
            "selected_text": "Updated selection",
        })

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["success"])
        # Does not create duplicate source
        self.assertEqual(Source.objects.filter(uri=existing_url).count(), 1)
        mock_process_source.assert_called_once_with(existing_source.id)

    def test_post_clip_missing_url_returns_error(self):
        response = self.client.post(self.clip_url, {
            "url": "",
            "title": "Article without URL",
            "selected_text": "Some text",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["success"])
        self.assertIn("A valid target URL is required", response.context["error_message"])

    @patch("apps.processing.pipeline.IngestionPipeline.process_source")
    def test_post_clip_handles_ingestion_failure(self, mock_process_source):
        mock_process_source.side_effect = RuntimeError("Extraction engine offline")

        response = self.client.post(self.clip_url, {
            "url": "https://example.com/failure-case",
            "title": "Will Fail Ingestion",
            "selected_text": "",
        })

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["success"])
        self.assertIn("Extraction engine offline", response.context["error_message"])


class SourceClipApiViewTestCase(TestCase):
    """Tests for the Bookmarklet REST API Endpoint (POST /api/sources/clip/)."""

    def setUp(self):
        self.user = User.objects.create_user(
            username="api-clipper-tester",
            email="apiclipper@example.com",
            password="testpassword123",
        )
        self.client.force_login(self.user)
        self.api_url = reverse("api-source-clip")

    @patch("apps.processing.pipeline.IngestionPipeline.process_source")
    def test_api_clip_json_success(self, mock_process_source):
        mock_doc = MagicMock()
        mock_doc.chunks.count.return_value = 12
        mock_process_source.return_value = mock_doc

        payload = {
            "url": "https://huggingface.co/blog/smolagents",
            "title": "Smolagents Introduction",
            "selected_text": "Building minimalist agents in Python.",
        }

        response = self.client.post(
            self.api_url,
            data=json.dumps(payload),
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["name"], "Smolagents Introduction")
        self.assertEqual(data["chunks_count"], 12)

        source = Source.objects.get(id=data["source_id"])
        self.assertEqual(source.uri, payload["url"])
        self.assertEqual(source.metadata.get("clipped_via"), "bookmarklet_api")

    def test_api_clip_missing_url_returns_400(self):
        payload = {
            "title": "No URL Here",
        }
        response = self.client.post(
            self.api_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertIn("Missing required 'url' parameter", data["error"])

    @patch("apps.processing.pipeline.IngestionPipeline.process_source")
    def test_api_clip_pipeline_error_returns_500(self, mock_process_source):
        mock_process_source.side_effect = Exception("HTML scraper blocked by robot.txt")

        payload = {
            "url": "https://example.com/blocked-page",
            "title": "Blocked Article",
        }
        response = self.client.post(
            self.api_url,
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 500)
        data = response.json()
        self.assertIn("HTML scraper blocked by robot.txt", data["error"])
