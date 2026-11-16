import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from apps.rag.services.hybrid_retrieval import BM25Scorer, HybridRetrievalService
from apps.rag.services.web_search import WebSearchService, WebSearchResult
from apps.rag.services.retrieval import SearchResult
from apps.rag.query_processing.adaptive_router import AdaptiveRouter, QueryTransformer
from apps.rag.workflow.grader import DocumentGrader, HallucinationChecker
from apps.rag.services.rag import RAGService
from apps.rag.llm.base import BaseLLMProvider, LLMResponse
from apps.rag.models import Conversation, Message
from apps.rag.context.builder import ContextBuilder
from apps.sources.models import Source, Document, DocumentChunk, Entity, Relationship, EntityChunkMapping
from apps.rag.services.graph_service import KnowledgeGraphService, GraphTriple, SubgraphResult
from apps.processing.chunking.config import ChunkingConfig
from apps.processing.chunking.text_chunker import TextChunker
from apps.processing.pipeline import IngestionPipeline


class MockRAGLLMProvider(BaseLLMProvider):
    _provider_name = "mock_rag"
    _model_name = "mock-v1"

    def __init__(self, canned_response: str = "This is a verified test response."):
        self.canned_response = canned_response
        self.call_count = 0

    @property
    def model_name(self) -> str:
        return self._model_name

    def generate(self, prompt: str, system_prompt: str = None, **kwargs) -> LLMResponse:
        self.call_count += 1
        return LLMResponse(
            text=self.canned_response,
            model=self._model_name,
            tokens_used=50,
        )

    def generate_stream(self, prompt: str, system_prompt: str = None, **kwargs):
        self.call_count += 1
        words = self.canned_response.split(" ")
        for i, word in enumerate(words):
            yield word + (" " if i < len(words) - 1 else "")


class BM25ScorerTestCase(TestCase):
    """Tests for BM25 in-memory keyword retrieval."""

    def test_bm25_tokenization_and_scoring(self):
        scorer = BM25Scorer()
        tokens = scorer.tokenize("def calculate_fibonacci(n): return fibonacci(n-1) + fibonacci(n-2)")
        self.assertIn("calculate", tokens)
        self.assertIn("fibonacci", tokens)

        class DummyChunk:
            def __init__(self, cid, content):
                self.id = cid
                self.content = content

        c1 = DummyChunk("1", "Python lists are mutable ordered sequences.")
        c2 = DummyChunk("2", "Python dictionaries store key value pairs.")
        c3 = DummyChunk("3", "Calculus and derivatives in neural networks.")

        scored = scorer.score_corpus("mutable lists sequence", [c1, c2, c3])
        self.assertEqual(scored[0][1].id, "1")
        self.assertTrue(scored[0][0] > 0)


class AdaptiveRouterTestCase(TestCase):
    """Tests for routing intent: Parametric vs Retrieval vs Web Search."""

    def test_conversational_heuristic_routes_to_parametric(self):
        result = AdaptiveRouter.classify("Hello there!")
        self.assertEqual(result["category"], "PARAMETRIC")

    def test_arithmetic_heuristic_routes_to_parametric(self):
        result = AdaptiveRouter.classify("what is 15 * 4?")
        self.assertEqual(result["category"], "PARAMETRIC")

    def test_web_search_trigger_routes_to_web_search(self):
        result = AdaptiveRouter.classify("search web for latest PyTorch 2.5 release notes")
        self.assertEqual(result["category"], "WEB_SEARCH")

    def test_llm_classification_for_technical_question(self):
        mock_llm = MockRAGLLMProvider(
            canned_response=json.dumps({"category": "RETRIEVAL", "reason": "Requires documentation"})
        )
        result = AdaptiveRouter.classify(
            query="Explain how our custom chunking pipeline handles markdown headers",
            llm_provider=mock_llm,
        )
        self.assertEqual(result["category"], "RETRIEVAL")

    def test_programming_and_conceptual_queries_route_to_retrieval(self):
        queries = [
            "What is Python?",
            "What is REPL?",
            "Explain variables and data types",
            "What is an integer in python?",
            "How do single-line comments work in Python?",
        ]
        for q in queries:
            result = AdaptiveRouter.classify(q)
            self.assertEqual(
                result["category"],
                "RETRIEVAL",
                f"Query '{q}' should route to RETRIEVAL instead of PARAMETRIC",
            )


class DocumentGraderTestCase(TestCase):
    """Tests for Self-RAG relevance grading and hallucination verification."""

    def test_high_similarity_passes_grader_immediately(self):
        chunk = SearchResult(
            chunk_id="1",
            chunk_index=0,
            content="Vector search computes cosine distances.",
            similarity_score=0.85,
            distance=0.15,
            document_id="d1",
            document_title="Doc 1",
            source_id="s1",
            source_name="Source 1",
            source_type="pdf",
            source_uri="file.pdf",
        )
        passed = DocumentGrader.grade_chunk("How does vector search work?", chunk)
        self.assertTrue(passed)

    def test_low_similarity_evaluates_via_llm(self):
        chunk = SearchResult(
            chunk_id="2",
            chunk_index=0,
            content="Irrelevant cooking recipe for apple pie.",
            similarity_score=0.2,
            distance=0.8,
            document_id="d2",
            document_title="Doc 2",
            source_id="s2",
            source_name="Source 2",
            source_type="article",
            source_uri="recipe.html",
        )
        mock_llm = MockRAGLLMProvider(canned_response=json.dumps({"relevant": "no"}))
        passed = DocumentGrader.grade_chunk("Explain gradient descent", chunk, llm_provider=mock_llm)
        self.assertFalse(passed)


class AdvancedRAGWorkflowIntegrationTestCase(TestCase):
    """Tests end-to-end LangGraph execution across parametric and CRAG branches."""

    def test_parametric_pipeline_execution(self):
        mock_llm = MockRAGLLMProvider(canned_response="Hello! I am Brofessor, your AI assistant.")
        result = RAGService.ask(
            query="hello",
            llm_provider=mock_llm,
        )
        self.assertEqual(result.response_source, "parametric")
        self.assertIn("Brofessor", result.answer)
        self.assertEqual(len(result.citations), 0)

    def test_crag_insufficient_docs_prompts_web_search(self):
        mock_llm = MockRAGLLMProvider(canned_response="Generic answer.")
        with patch.object(HybridRetrievalService, "search", return_value=[]):
            result = RAGService.ask(
                query="What was the exact stock closing price of NVIDIA on October 24 2026?",
                llm_provider=mock_llm,
            )
            self.assertEqual(result.response_source, "web_prompt")
            self.assertTrue(result.can_search_web)
            self.assertIn("search the web", result.answer.lower())

    def test_confirmed_web_search_executes_and_cites(self):
        mock_llm = MockRAGLLMProvider(canned_response="According to web results, the stock closed at $145.")
        mock_web_results = [
            WebSearchResult(
                title="NVIDIA Financial Report",
                snippet="NVIDIA closed at $145 on October 24 2026.",
                url="https://finance.example.com/nvda",
            )
        ]

        with patch.object(WebSearchService, "search", return_value=mock_web_results):
            result = RAGService.ask(
                query="What was the exact stock closing price of NVIDIA on October 24 2026?",
                allow_web_search=True,
                llm_provider=mock_llm,
            )
            self.assertEqual(result.response_source, "web")
            self.assertEqual(len(result.citations), 1)
            self.assertEqual(result.citations[0]["source_uri"], "https://finance.example.com/nvda")
            self.assertIn("$145", result.answer)

    def test_grounded_document_pipeline_with_citations_and_content(self):
        mock_llm = MockRAGLLMProvider(canned_response="Docker image creation involves build, tag, and push.")
        mock_search_results = [
            SearchResult(
                chunk_id="chunk-123",
                document_id="doc-123",
                source_id="src-123",
                content="The docker image lifecycle includes build, tag, push, run, and rm.",
                chunk_index=0,
                similarity_score=0.88,
                distance=0.12,
                source_name="Docker Architecture Guide",
                document_title="Docker Lifecycle",
                source_type="article",
                source_uri="https://example.com/docker",
            )
        ]


        with patch.object(HybridRetrievalService, "search", return_value=mock_search_results):
            result = RAGService.ask(
                query="what are parts of docker image lifecycle creation",
                llm_provider=mock_llm,
            )
            self.assertEqual(result.response_source, "documents")
            self.assertTrue(len(result.citations) >= 1)
            first_citation = result.citations[0]
            self.assertEqual(first_citation["chunk_id"], "chunk-123")
            self.assertIn("build, tag, push", first_citation["content"])
            self.assertIn("Docker", result.answer)



class ParagraphChunkerTestCase(TestCase):
    """Tests semantic and paragraph-aware document chunking."""

    def test_preserves_code_blocks_intact(self):
        chunker = TextChunker()
        doc = (
            "# Introduction\n\n"
            "Here is a code example:\n\n"
            "```python\n"
            "def add(a, b):\n"
            "    return a + b\n"
            "```\n\n"
            "This concludes the function explanation."
        )
        chunks = chunker.chunk(doc)
        self.assertTrue(len(chunks) >= 1)
        found_code = any("def add(a, b):" in c.content for c in chunks)
        self.assertTrue(found_code)


class QueryTransformerTestCase(TestCase):
    """Tests for multi-turn conversational follow-up detection and query condensation."""

    def test_is_follow_up_detection(self):
        follow_ups = [
            "what about its advantages?",
            "can you explain more about that?",
            "how does this work?",
            "why?",
            "and what else?",
            "give me an example of it",
        ]
        for q in follow_ups:
            self.assertTrue(
                QueryTransformer.is_follow_up(q),
                f"Query '{q}' should be identified as a follow-up query",
            )

        standalone_queries = [
            "What is Docker containerization?",
            "Explain Transformer architecture in detail",
            "How to write unit tests in Django?",
        ]
        for q in standalone_queries:
            self.assertFalse(
                QueryTransformer.is_follow_up(q),
                f"Query '{q}' should not be identified as a follow-up query",
            )

    def test_condense_query_with_chat_history(self):
        mock_llm = MockRAGLLMProvider(canned_response="What are the key advantages of Python?")
        chat_history = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a high-level interpreted programming language."},
        ]
        condensed = QueryTransformer.condense_query(
            query="What are its advantages?",
            chat_history=chat_history,
            llm_provider=mock_llm,
        )
        self.assertEqual(condensed, "What are the key advantages of Python?")

    def test_condense_query_without_chat_history_returns_original(self):
        query = "What are its advantages?"
        condensed = QueryTransformer.condense_query(query=query, chat_history=[])
        self.assertEqual(condensed, query)


class StreamingRAGTestCase(TestCase):
    """Tests for SSE streaming generator and API endpoint."""

    def test_llm_generate_stream(self):
        mock_llm = MockRAGLLMProvider(canned_response="Alpha Beta Gamma")
        tokens = list(mock_llm.generate_stream("Test prompt"))
        self.assertTrue(len(tokens) > 0)
        self.assertEqual("".join(tokens).strip(), "Alpha Beta Gamma")

    def test_ask_stream_yields_expected_sse_events(self):
        mock_llm = MockRAGLLMProvider(canned_response="Hello world streaming test.")
        events = list(
            RAGService.ask_stream(
                query="Hello",
                llm_provider=mock_llm,
            )
        )
        self.assertTrue(len(events) > 0)
        joined_events = "".join(events)
        self.assertIn("event: conversation", joined_events)
        self.assertIn("event: stage", joined_events)
        self.assertIn("event: token", joined_events)
        self.assertIn("event: done", joined_events)

    def test_rag_chat_stream_api_endpoint(self):
        client = APIClient()
        mock_llm = MockRAGLLMProvider(canned_response="Streaming API response.")

        with patch("apps.rag.workflow.graph.get_llm_provider", return_value=mock_llm):
            response = client.post(
                "/api/v1/rag/chat/stream/",
                data={"query": "Hello API streaming"},
                format="json",
            )
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertEqual(response["Content-Type"], "text/event-stream")
            content = b"".join(response.streaming_content).decode("utf-8")
            self.assertIn("event: conversation", content)
            self.assertIn("event: stage", content)
            self.assertIn("event: done", content)


class MultiTurnConversationTestCase(TestCase):
    """Tests for multi-turn conversation persistence and retrieval."""

    def test_multi_turn_persists_messages_and_passes_history(self):
        mock_llm = MockRAGLLMProvider(canned_response="First turn answer.")

        # First turn
        res1 = RAGService.ask(
            query="Tell me about Docker",
            llm_provider=mock_llm,
        )
        self.assertIsNotNone(res1.conversation_id)
        conv = Conversation.objects.get(id=res1.conversation_id)
        self.assertEqual(conv.messages.count(), 2)

        # Second turn with follow-up
        mock_llm.canned_response = "Docker compares favorably to VMs because of shared kernels."
        res2 = RAGService.ask(
            query="How does it compare to VMs?",
            conversation_id=str(conv.id),
            llm_provider=mock_llm,
        )
        self.assertEqual(str(res2.conversation_id), str(conv.id))
        self.assertEqual(conv.messages.count(), 4)

        messages = list(conv.messages.order_by("created_at"))
        self.assertEqual(messages[0].role, "user")
        self.assertEqual(messages[0].content, "Tell me about Docker")
        self.assertEqual(messages[1].role, "assistant")
        self.assertEqual(messages[2].role, "user")
        self.assertEqual(messages[2].content, "How does it compare to VMs?")
        self.assertEqual(messages[3].role, "assistant")


class HierarchicalChunkingTestCase(TestCase):
    """Tests for Hierarchical Parent-Child ('Small-to-Big') chunking."""

    def test_chunk_hierarchical_generates_parents_and_children(self):
        config = ChunkingConfig(
            parent_chunk_size=400,
            parent_chunk_overlap=50,
            child_chunk_size=120,
            child_chunk_overlap=20,
        )
        chunker = TextChunker(config=config)
        sample_doc = (
            "# Section 1: Introduction to Vector Search\n\n"
            "Vector search enables semantic retrieval using dense embeddings. "
            "It computes cosine similarity or Euclidean distance between query and documents.\n\n"
            "Traditional keyword matching like BM25 relies on exact term overlap. "
            "Combining both dense vectors and sparse keywords yields hybrid search.\n\n"
            "# Section 2: Reciprocal Rank Fusion\n\n"
            "Reciprocal rank fusion combines rankings from diverse retrieval mechanisms. "
            "It operates robustly without requiring calibrated similarity score distributions."
        )

        parents, children = chunker.chunk_hierarchical(sample_doc)
        self.assertTrue(len(parents) >= 1)
        self.assertTrue(len(children) >= len(parents))

        # Check parent metadata
        for p in parents:
            self.assertEqual(p.chunk_level, "parent")
            self.assertIsNone(p.parent_index)

        # Check child metadata & linking
        for c in children:
            self.assertEqual(c.chunk_level, "child")
            self.assertIsNotNone(c.parent_index)
            self.assertTrue(0 <= c.parent_index < len(parents))
            parent_text = parents[c.parent_index].content
            # Verify child words originate from parent section
            first_words = [w for w in c.content.split() if len(w) > 3][:3]
            for w in first_words:
                self.assertIn(w, parent_text)

    def test_ingestion_pipeline_persists_parent_child_hierarchy(self):
        test_content = (
            "Brofessor is an AI learning assistant.\n\n"
            "It implements advanced RAG features like Self-RAG and CRAG.\n\n"
            "Hierarchical chunking enables small-to-big retrieval for superior precision.\n\n"
            "Small chunks are indexed for vector search, while big parent sections are fed to the LLM."
        )
        source = Source.objects.create(
            name="Hierarchical RAG Test Note",
            source_type=Source.SourceType.NOTE,
            uri="note://rag-test",
            metadata={"content": test_content},
        )

        doc = IngestionPipeline.process_source(source.id)
        self.assertIsNotNone(doc)
        self.assertTrue(doc.chunks.count() > 0)

        # Check for parent and child chunks
        parents = doc.chunks.filter(chunk_level=DocumentChunk.ChunkLevel.PARENT)
        children = doc.chunks.filter(chunk_level=DocumentChunk.ChunkLevel.CHILD)
        self.assertTrue(parents.count() >= 1)
        self.assertTrue(children.count() >= 1)

        # Verify foreign key link from child to parent
        first_child = children.first()
        self.assertIsNotNone(first_child.parent_chunk)
        self.assertEqual(first_child.parent_chunk.chunk_level, DocumentChunk.ChunkLevel.PARENT)


class SmallToBigRetrievalTestCase(TestCase):
    """Tests for Small-to-Big Retrieval context assembly and deduplication."""

    def test_context_builder_expands_to_parent_content(self):
        parent_section_text = (
            "FULL SECTION: Transformer models rely on self-attention mechanisms. "
            "Self-attention allows tokens to attend to other tokens dynamically across the sequence. "
            "Scaled dot-product attention computes Q, K, V matrix multiplications."
        )

        child_1 = SearchResult(
            chunk_id="child-1",
            chunk_index=1,
            content="Self-attention allows tokens to attend to other tokens.",
            similarity_score=0.92,
            distance=0.08,
            document_id="doc-1",
            document_title="Attention Deep Dive",
            source_id="src-1",
            source_name="Transformers Paper",
            source_type="article",
            source_uri="https://arxiv.org/abs/1706.03762",
            chunk_level="child",
            parent_chunk_id="parent-1",
            parent_content=parent_section_text,
        )

        builder = ContextBuilder(enable_small_to_big=True)
        context = builder.build([child_1])

        self.assertEqual(context.total_chunks, 1)
        # Formatted text fed to the LLM must contain the FULL parent section text
        self.assertIn("FULL SECTION: Transformer models rely on self-attention", context.formatted_text)
        self.assertIn("Scaled dot-product attention computes Q, K, V", context.formatted_text)

        # Citations must record the child snippet and parent context
        citation = context.citations[0]
        self.assertEqual(citation.chunk_id, "child-1")
        self.assertEqual(citation.parent_chunk_id, "parent-1")
        self.assertIn("Self-attention allows", citation.snippet)
        self.assertIn("FULL SECTION", citation.content)

    def test_context_builder_deduplicates_multiple_children_from_same_parent(self):
        parent_section_text = (
            "PARENT BLOCK: Reciprocal Rank Fusion (RRF) is an unsupervised ranking algorithm. "
            "It combines multiple rank lists into a single consolidated scoring list. "
            "It is especially effective for hybrid dense-sparse search."
        )

        # Two child chunks matched from the SAME parent section
        child_1 = SearchResult(
            chunk_id="child-101",
            chunk_index=10,
            content="Reciprocal Rank Fusion is an unsupervised ranking algorithm.",
            similarity_score=0.95,
            distance=0.05,
            document_id="doc-2",
            document_title="Hybrid Search",
            source_id="src-2",
            source_name="Information Retrieval",
            source_type="article",
            source_uri="https://example.com/rrf",
            chunk_level="child",
            parent_chunk_id="parent-shared-1",
            parent_content=parent_section_text,
        )

        child_2 = SearchResult(
            chunk_id="child-102",
            chunk_index=11,
            content="It is especially effective for hybrid dense-sparse search.",
            similarity_score=0.88,
            distance=0.12,
            document_id="doc-2",
            document_title="Hybrid Search",
            source_id="src-2",
            source_name="Information Retrieval",
            source_type="article",
            source_uri="https://example.com/rrf",
            chunk_level="child",
            parent_chunk_id="parent-shared-1",
            parent_content=parent_section_text,
        )

        builder = ContextBuilder(enable_small_to_big=True)
        context = builder.build([child_1, child_2])

        # Both child citations are captured for provenance
        self.assertEqual(len(context.citations), 2)
        self.assertEqual(context.citations[0].chunk_id, "child-101")
        self.assertEqual(context.citations[1].chunk_id, "child-102")

        # But the parent text must ONLY appear ONCE in the prompt text
        count_occurrences = context.formatted_text.count("PARENT BLOCK: Reciprocal Rank Fusion")
        self.assertEqual(
            count_occurrences,
            1,
            "Parent section text should be deduplicated in LLM prompt rather than repeated",
        )


class KnowledgeGraphRAGTestCase(TestCase):
    """Tests for Graph-RAG Entity-Relationship extraction, BFS traversal, and multi-hop retrieval."""

    def test_normalize_name(self):
        self.assertEqual(KnowledgeGraphService.normalize_name("  `Docker Container` "), "docker container")
        self.assertEqual(KnowledgeGraphService.normalize_name("Self-Attention [Layer]"), "self-attention layer")

    def test_extract_triples_via_llm_json(self):
        canned_json = json.dumps([
            {
                "source": "Transformer",
                "source_type": "architecture",
                "relation": "USES",
                "target": "Self-Attention",
                "target_type": "concept",
                "description": "Transformers utilize self-attention for sequence modeling.",
            },
            {
                "source": "Self-Attention",
                "source_type": "concept",
                "relation": "PREREQUISITE_OF",
                "target": "BERT",
                "target_type": "architecture",
                "description": "BERT is built on self-attention.",
            }
        ])
        mock_llm = MockRAGLLMProvider(canned_response=canned_json)

        triples = KnowledgeGraphService.extract_triples_from_text(
            text="The Transformer architecture relies on self-attention mechanisms, which are a prerequisite for BERT.",
            llm_provider=mock_llm,
        )
        self.assertEqual(len(triples), 2)
        self.assertEqual(triples[0].source_name, "Transformer")
        self.assertEqual(triples[0].target_name, "Self-Attention")
        self.assertEqual(triples[0].relation_type, "uses")
        self.assertEqual(triples[1].source_name, "Self-Attention")
        self.assertEqual(triples[1].relation_type, "prerequisite_of")

    def test_index_chunk_persists_entities_and_relations(self):
        source = Source.objects.create(
            name="Cloud Systems",
            source_type=Source.SourceType.ARTICLE,
            uri="https://example.com/cloud",
        )
        doc = Document.objects.create(
            source=source,
            title="Container Virtualization",
            content="Docker uses Linux cgroups and namespaces.",
        )
        chunk = DocumentChunk.objects.create(
            document=doc,
            chunk_index=0,
            content="Docker uses Linux cgroups for resource limitation and isolation.",
        )

        canned_json = json.dumps([
            {
                "source": "Docker",
                "source_type": "technology",
                "relation": "USES",
                "target": "Linux cgroups",
                "target_type": "concept",
                "description": "Docker uses Linux cgroups for resource control.",
            }
        ])
        mock_llm = MockRAGLLMProvider(canned_response=canned_json)

        relations = KnowledgeGraphService.index_chunk(chunk, llm_provider=mock_llm)
        self.assertEqual(len(relations), 1)

        # Check Entity records
        docker_ent = Entity.objects.filter(canonical_name="docker").first()
        cgroups_ent = Entity.objects.filter(canonical_name="linux cgroups").first()
        self.assertIsNotNone(docker_ent)
        self.assertIsNotNone(cgroups_ent)

        # Check Relationship record
        rel = Relationship.objects.filter(source_entity=docker_ent, target_entity=cgroups_ent).first()
        self.assertIsNotNone(rel)
        self.assertEqual(rel.relation_type, "uses")
        self.assertEqual(rel.source_chunk_id, chunk.id)

        # Check EntityChunkMapping
        mappings = EntityChunkMapping.objects.filter(chunk=chunk)
        self.assertEqual(mappings.count(), 2)

    def test_multi_hop_subgraph_traversal(self):
        # Create a 2-hop graph:
        # A (Docker) -> USES -> B (cgroups) -> PART_OF -> C (Linux Kernel)
        ent_a = Entity.objects.create(name="Docker", canonical_name="docker", entity_type="technology")
        ent_b = Entity.objects.create(name="cgroups", canonical_name="cgroups", entity_type="concept")
        ent_c = Entity.objects.create(name="Linux Kernel", canonical_name="linux kernel", entity_type="technology")

        Relationship.objects.create(
            source_entity=ent_a,
            target_entity=ent_b,
            relation_type="uses",
            description="Docker uses cgroups for resource isolation",
        )
        Relationship.objects.create(
            source_entity=ent_b,
            target_entity=ent_c,
            relation_type="part_of",
            description="cgroups is a Linux kernel feature",
        )

        # Query matching:
        found = KnowledgeGraphService.find_query_entities("Explain how Docker manages system resources")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].canonical_name, "docker")

        # 2-Hop BFS traversal
        subgraph = KnowledgeGraphService.traverse_subgraph(start_entities=found, max_depth=2)
        self.assertEqual(len(subgraph.entities), 3)
        self.assertEqual(len(subgraph.relationships), 2)

        formatted_text = subgraph.to_text()
        self.assertIn("[Docker] --USES--> [cgroups]", formatted_text)
        self.assertIn("[cgroups] --PART_OF--> [Linux Kernel]", formatted_text)

    def test_context_builder_incorporates_graph_context(self):
        graph_text = "• [Attention] --USES--> [Softmax] (Normalization across tokens)"
        builder = ContextBuilder()
        ctx = builder.build([], graph_context=graph_text)
        self.assertIn("Knowledge Graph Relational Connections", ctx.formatted_text)
        self.assertIn("[Attention] --USES--> [Softmax]", ctx.formatted_text)


class LangSmithAndIntegrationsTestCase(TestCase):
    """Tests for LangSmith Observability, ping verification, and API key management."""

    def setUp(self):
        self.client = APIClient()
        from apps.rag.llm.registry import save_system_ai_config
        save_system_ai_config({"langsmith_api_key": "", "langsmith_tracing": False, "gemini_api_key": ""})

    def tearDown(self):
        import os
        from apps.rag.llm.registry import sync_langsmith_env, save_system_ai_config
        save_system_ai_config({"langsmith_api_key": "", "langsmith_tracing": False, "gemini_api_key": ""})
        sync_langsmith_env({"langsmith_api_key": "", "langsmith_tracing": False})
        os.environ.pop("LANGSMITH_API_KEY", None)
        os.environ.pop("LANGCHAIN_API_KEY", None)
        os.environ["LANGSMITH_TRACING"] = "false"
        os.environ["LANGCHAIN_TRACING_V2"] = "false"

    @patch("requests.get")
    def test_verify_langsmith_key_success(self, mock_get):
        from apps.rag.services.integrations import verify_langsmith_key
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        result = verify_langsmith_key("lsv2_pt_validkey12345", project_name="test-rag-proj")
        self.assertTrue(result["connected"])
        self.assertEqual(result["status"], "connected")
        self.assertEqual(result["project"], "test-rag-proj")
        self.assertIn("Connected to LangSmith", result["message"])

    @patch("requests.get")
    def test_verify_langsmith_key_unauthorized(self, mock_get):
        from apps.rag.services.integrations import verify_langsmith_key
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_get.return_value = mock_resp

        result = verify_langsmith_key("lsv2_pt_invalidkey", project_name="test-rag-proj")
        self.assertFalse(result["connected"])
        self.assertEqual(result["status"], "unauthorized")
        self.assertIn("Authentication failed", result["message"])

    def test_verify_langsmith_key_empty(self):
        from apps.rag.services.integrations import verify_langsmith_key
        result = verify_langsmith_key("")
        self.assertFalse(result["connected"])
        self.assertFalse(result["configured"])
        self.assertEqual(result["status"], "not_configured")

    @patch("requests.get")
    def test_verify_gemini_key_success(self, mock_get):
        from apps.rag.services.integrations import verify_gemini_key
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        result = verify_gemini_key("AIzaSyValidGeminiKey", model_name="gemini-3.6-flash")
        self.assertTrue(result["connected"])
        self.assertEqual(result["status"], "connected")
        self.assertIn("Connected to Google Gemini", result["message"])

    def test_sync_langsmith_env(self):
        import os
        from apps.rag.llm.registry import sync_langsmith_env

        # 1. Test enable
        sync_langsmith_env({
            "langsmith_api_key": "lsv2_pt_mykey",
            "langsmith_project": "brofessor-eval",
            "langsmith_tracing": True,
        })
        self.assertEqual(os.environ.get("LANGSMITH_API_KEY"), "lsv2_pt_mykey")
        self.assertEqual(os.environ.get("LANGSMITH_PROJECT"), "brofessor-eval")
        self.assertEqual(os.environ.get("LANGSMITH_TRACING"), "true")

        # 2. Test disable
        sync_langsmith_env({
            "langsmith_api_key": "",
            "langsmith_tracing": False,
        })
        self.assertIsNone(os.environ.get("LANGSMITH_API_KEY"))
        self.assertEqual(os.environ.get("LANGSMITH_TRACING"), "false")

    @patch("requests.get")
    def test_integrations_status_api(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        response = self.client.get("/api/v1/rag/integrations/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("langsmith", response.data)
        self.assertIn("gemini", response.data)
        self.assertIn("active_llm", response.data)

    @patch("requests.get")
    def test_integrations_verify_api_and_save(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_get.return_value = mock_resp

        payload = {
            "langsmith_api_key": "lsv2_pt_testkey12345",
            "langsmith_project": "golden-dataset-v1",
            "gemini_api_key": "AIzaSyTestKey9876",
            "gemini_model": "gemini-3.6-flash",
            "save": True,
        }
        response = self.client.post(
            "/api/v1/rag/integrations/verify/",
            data=json.dumps(payload),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertTrue(response.data["saved"])
        self.assertTrue(response.data["langsmith"]["connected"])
        self.assertEqual(response.data["langsmith"]["project"], "golden-dataset-v1")
        self.assertTrue(response.data["gemini"]["connected"])

    @patch("apps.rag.llm.registry.sync_langsmith_env")
    @patch("apps.rag.workflow.graph.create_rag_graph")
    def test_rag_service_attaches_langsmith_tracing_metadata(self, mock_graph, mock_sync):
        from apps.rag.llm.registry import save_system_ai_config

        save_system_ai_config({
            "langsmith_api_key": "lsv2_pt_activekey",
            "langsmith_project": "test-rag-traces",
            "langsmith_tracing": True,
        })

        mock_app = MagicMock()
        mock_app.invoke.return_value = {
            "response_text": "Traced response with LangSmith metadata.",
            "citations": [],
            "tokens_used": 25,
            "error": None,
            "response_source": "documents",
            "metadata": {},
        }
        mock_graph.return_value = mock_app

        res = RAGService.ask(
            query="What is LangSmith tracing?",
            llm_provider=MockRAGLLMProvider(),
        )
        self.assertIn("Traced response", res.answer)

        # Verify app.invoke was called with config containing run_name and metadata
        self.assertTrue(mock_app.invoke.called)
        call_args, call_kwargs = mock_app.invoke.call_args
        config = call_kwargs.get("config")
        self.assertIsNotNone(config)
        self.assertIn("brofessor", config.get("tags", []))
        self.assertIn("conversation_id", config.get("metadata", {}))




