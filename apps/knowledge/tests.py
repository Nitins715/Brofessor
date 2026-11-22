from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.urls import reverse
from apps.roadmap.models import Domain, Topic, Skill
from apps.sources.models import Entity, Relationship
from apps.knowledge.services.knowledge_graph import KnowledgeGraphService
from apps.knowledge.models import CalculatedMastery, MasteryLevel

User = get_user_model()


class VisualConceptGraphTests(TestCase):
    """Tests for the interactive Vis.js Concept Graph engine and endpoints."""

    def setUp(self):
        self.user = User.objects.create_user(username="graphuser", password="password123")
        self.client = Client()
        self.client.force_login(self.user)

        # Create Domain, Topics across Tracks, and Skills
        self.domain = Domain.objects.create(name="AI & ML", slug="ai-ml", is_selected=True)
        self.topic_swe = Topic.objects.create(
            domain=self.domain,
            name="Python Fundamentals",
            slug="python-fundamentals",
            track="swe_foundations",
        )
        self.topic_ai = Topic.objects.create(
            domain=self.domain,
            name="Transformers & Attention",
            slug="transformers-attention",
            track="ai_engineer",
        )

        self.skill_python = Skill.objects.create(
            topic=self.topic_swe,
            name="Python Syntax",
            slug="python-syntax",
            difficulty_level="beginner",
        )
        self.skill_oop = Skill.objects.create(
            topic=self.topic_swe,
            name="OOP in Python",
            slug="oop-python",
            difficulty_level="intermediate",
        )
        self.skill_oop.prerequisites.add(self.skill_python)

        self.skill_transformers = Skill.objects.create(
            topic=self.topic_ai,
            name="Multi-Head Attention",
            slug="multi-head-attention",
            difficulty_level="advanced",
        )
        self.skill_transformers.prerequisites.add(self.skill_oop)

        # Set mastery on Python Syntax
        CalculatedMastery.objects.create(
            skill=self.skill_python,
            mastery_score=85.0,
            mastery_level=MasteryLevel.ADVANCED,
        )

    def test_curriculum_graph_nodes_and_edges(self):
        data = KnowledgeGraphService.get_visual_graph_data(domain=self.domain, mode="curriculum")

        self.assertEqual(data["mode"], "curriculum")
        self.assertEqual(len(data["nodes"]), 3)
        self.assertEqual(len(data["edges"]), 2)

        # Verify node fields
        node_ids = {n["id"] for n in data["nodes"]}
        self.assertIn(str(self.skill_python.id), node_ids)
        self.assertIn(str(self.skill_transformers.id), node_ids)

        python_node = next(n for n in data["nodes"] if n["id"] == str(self.skill_python.id))
        self.assertEqual(python_node["track"], "swe_foundations")
        self.assertEqual(python_node["mastery_score"], 85.0)
        self.assertEqual(python_node["mastery_level"], "advanced")
        self.assertIn("Python Syntax", python_node["title"])

        # Verify edge
        edge_from_to = [(e["from"], e["to"]) for e in data["edges"]]
        self.assertIn((str(self.skill_python.id), str(self.skill_oop.id)), edge_from_to)
        self.assertIn((str(self.skill_oop.id), str(self.skill_transformers.id)), edge_from_to)

    def test_track_filtering(self):
        # Filter for AI Engineer track only
        data_ai = KnowledgeGraphService.get_visual_graph_data(
            domain=self.domain,
            track="ai_engineer",
            mode="curriculum",
        )
        self.assertEqual(len(data_ai["nodes"]), 1)
        self.assertEqual(data_ai["nodes"][0]["track"], "ai_engineer")

    def test_library_graph_entities_and_relationships(self):
        entity_a = Entity.objects.create(
            name="Attention Mechanism",
            canonical_name="attention_mechanism",
            entity_type=Entity.EntityType.CONCEPT,
            description="Core transformer layer",
        )
        entity_b = Entity.objects.create(
            name="Transformers",
            canonical_name="transformers",
            entity_type=Entity.EntityType.ARCHITECTURE,
            description="Transformer architecture",
        )
        Relationship.objects.create(
            source_entity=entity_a,
            target_entity=entity_b,
            relation_type="part_of",
        )

        data = KnowledgeGraphService.get_visual_graph_data(mode="library")
        self.assertEqual(data["mode"], "library")
        self.assertGreaterEqual(len(data["nodes"]), 2)
        self.assertGreaterEqual(len(data["edges"]), 1)

    def test_visual_concept_graph_web_view(self):
        response = self.client.get(reverse("web-knowledge-graph"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "pages/knowledge_graph.html")
        self.assertIn("graph_data_json", response.context)
        self.assertIn("graph_summary", response.context)

    def test_visual_concept_graph_api_endpoint(self):
        response = self.client.get(reverse("api-knowledge-graph-data"), {"track": "swe_foundations"})
        self.assertEqual(response.status_code, 200)
        json_data = response.json()
        self.assertIn("nodes", json_data)
        self.assertIn("edges", json_data)
        self.assertIn("summary", json_data)
        self.assertEqual(json_data["track"], "swe_foundations")
