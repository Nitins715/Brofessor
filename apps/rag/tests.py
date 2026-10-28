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
from apps.processing.chunking.text_chunker import TextChunker


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
