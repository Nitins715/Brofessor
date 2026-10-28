import logging
import time
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from apps.rag.query_processing import BaseQueryProcessor, DefaultQueryProcessor
from apps.rag.query_processing.adaptive_router import (
    AdaptiveRouter,
    QueryTransformer,
    QueryComplexityClassifier,
)
from apps.rag.services.hybrid_retrieval import HybridRetrievalService
from apps.rag.services.retrieval import SearchResult
from apps.rag.services.web_search import WebSearchService, WebSearchResult
from apps.rag.reranking import BaseReranker, RerankResult, get_reranker
from apps.rag.context import ContextBuilder, Citation
from apps.rag.llm import BaseLLMProvider, get_llm_provider
from apps.rag.workflow.grader import DocumentGrader, HallucinationChecker

logger = logging.getLogger("brofessor")

GROUNDED_SYSTEM_PROMPT = """You are Brofessor, an intelligent, local-first personal knowledge assistant.
Answer the user's question accurately and thoroughly using the provided context from the user's knowledge base and internal documents.

Guidelines:
1. Base your answer primarily on the provided context sources. Use the knowledge base to directly explain concepts, provide definitions, and show code examples.
2. Refer to the sources by their citation bracket (e.g., [Source 1], [Source 2]).
3. Be concise, clear, and structured in your explanations."""

SYSTEM_PROMPT = GROUNDED_SYSTEM_PROMPT

PARAMETRIC_SYSTEM_PROMPT = """You are Brofessor, an expert coding and AI mentor.
Provide a clear, accurate, and direct response to the user's question based on your core knowledge.
Keep explanations concise, well-structured, and helpful."""

WEB_GROUNDED_SYSTEM_PROMPT = """You are Brofessor, an intelligent knowledge assistant.
Answer the user's question using the provided external web search results.
Synthesize the information clearly, highlight key facts, and refer to sources using their web domain or title."""


class RAGState(TypedDict, total=False):
    """Advanced LangGraph State representation for the Adaptive Self-RAG & CRAG pipeline."""
    query: str
    processed_query: str
    transformed_query: str
    conversation_id: Optional[str]
    route_decision: str  # "PARAMETRIC", "RETRIEVAL", "WEB_SEARCH"
    allow_web_search: bool  # True when user has confirmed web search
    filters: Dict[str, Any]
    retrieval_top_k: int
    rerank_top_k: int
    retrieved_chunks: List[SearchResult]
    reranked_chunks: List[RerankResult]
    graded_chunks: List[SearchResult]
    grading_status: str  # "RELEVANT", "INSUFFICIENT"
    web_results: List[WebSearchResult]
    can_search_web: bool
    context_text: str
    citations: List[Dict[str, Any]]
    response_source: str  # "parametric", "documents", "web", "web_prompt"
    response_text: str
    tokens_used: Optional[int]
    error: Optional[str]
    metadata: Dict[str, Any]


def create_rag_graph(
    query_processor: Optional[BaseQueryProcessor] = None,
    reranker: Optional[BaseReranker] = None,
    llm_provider: Optional[BaseLLMProvider] = None,
    context_builder: Optional[ContextBuilder] = None,
):
    """
    Builds the Advanced LangGraph Adaptive Self-RAG & Corrective RAG (CRAG) workflow.
    """
    qp = query_processor or DefaultQueryProcessor()
    ctx_builder = context_builder or ContextBuilder()
    active_llm = llm_provider or get_llm_provider()

    # =========================================================================
    # Node 1: Adaptive Query Router
    # =========================================================================
    def router_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        # If user explicitly flagged allow_web_search, honor it immediately
        if state.get("allow_web_search"):
            return {
                "route_decision": "WEB_SEARCH",
                "processed_query": query,
            }

        decision = AdaptiveRouter.classify(query=query, llm_provider=active_llm)
        category = decision.get("category", "RETRIEVAL")
        logger.info(f"AdaptiveRouter classified query '{query[:40]}...' as: {category} ({decision.get('reason')})")
        return {
            "route_decision": category,
            "processed_query": query,
            "metadata": {
                **(state.get("metadata") or {}),
                "router_decision": category,
                "router_reason": decision.get("reason", ""),
            },
        }

    # =========================================================================
    # Node 2: Parametric Generation Node (No documents needed)
    # =========================================================================
    def parametric_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        start_time = time.time()
        try:
            res = active_llm.generate(
                prompt=query,
                system_prompt=PARAMETRIC_SYSTEM_PROMPT,
            )
            elapsed = round((time.time() - start_time) * 1000, 2)
            return {
                "response_text": res.text,
                "response_source": "parametric",
                "citations": [],
                "tokens_used": res.tokens_used,
                "metadata": {
                    **(state.get("metadata") or {}),
                    "generation_type": "parametric",
                    "latency_ms": elapsed,
                },
            }
        except Exception as e:
            err_str = str(e)
            if any(term in err_str.lower() for term in ("downtime", "high demand", "timed out", "down", "503", "429")):
                friendly = "⚠️ The AI Cloud API is currently experiencing downtime or high demand. Please try again in a few moments or switch to local Ollama in Settings."
            else:
                friendly = f"Generation error: {e}"
            return {
                "response_text": friendly,
                "response_source": "parametric",
                "error": str(e),
            }

    # =========================================================================
    # Node 3: Query Transformation Node
    # =========================================================================
    def query_transform_node(state: RAGState) -> Dict[str, Any]:
        raw_query = state.get("query", "")
        transformed = QueryTransformer.transform(query=raw_query, llm_provider=active_llm)
        logger.info(f"QueryTransformer: '{raw_query[:35]}...' -> '{transformed[:35]}...'")
        return {
            "transformed_query": transformed,
        }

    # =========================================================================
    # Node 4: Hybrid Retrieval Node (Dense Vector + BM25 Lexical + RRF)
    # =========================================================================
    def hybrid_retrieval_node(state: RAGState) -> Dict[str, Any]:
        search_query = state.get("transformed_query") or state.get("query", "")
        top_k = state.get("retrieval_top_k", 10)
        filters = state.get("filters", {})

        results = HybridRetrievalService.search(
            query=search_query,
            top_k=top_k,
            source_ids=filters.get("source_ids"),
            document_ids=filters.get("document_ids"),
            source_types=filters.get("source_types"),
            min_similarity=filters.get("min_similarity"),
        )
        logger.info(f"Hybrid retrieval returned {len(results)} chunks for query: '{search_query[:40]}...'")
        return {
            "retrieved_chunks": results,
        }

    # =========================================================================
    # Node 5: Reranking Node
    # =========================================================================
    def reranking_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("transformed_query") or state.get("query", "")
        retrieved = state.get("retrieved_chunks", [])
        top_k = state.get("rerank_top_k", 4)

        active_reranker = reranker or get_reranker()
        reranked = active_reranker.rerank(query=query, results=retrieved, top_k=top_k)
        logger.info(f"Reranking retained {len(reranked)} top chunks")
        return {
            "reranked_chunks": reranked,
        }

    # =========================================================================
    # Node 6: Self-RAG Document Grader Node
    # =========================================================================
    def document_grading_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        reranked = state.get("reranked_chunks", [])
        if not reranked:
            return {
                "graded_chunks": [],
                "grading_status": "INSUFFICIENT",
            }

        candidate_search_results = [r.search_result for r in reranked]

        # For simple/direct queries, fast-track top reranked chunks without multi-LLM latency
        is_hard = QueryComplexityClassifier.is_hard(query)
        if not is_hard:
            logger.info(f"Query is straightforward, fast-tracking {len(reranked)} reranked chunks.")
            return {
                "graded_chunks": reranked,
                "grading_status": "RELEVANT",
            }

        relevant_search_results, status = DocumentGrader.filter_and_evaluate(
            query=query,
            chunks=candidate_search_results,
            llm_provider=active_llm,
        )
        logger.info(f"DocumentGrader evaluated chunks: {len(relevant_search_results)}/{len(candidate_search_results)} relevant. Status: {status}")

        if status == "RELEVANT" and relevant_search_results:
            relevant_ids = {r.chunk_id for r in relevant_search_results}
            kept_reranked = [r for r in reranked if r.search_result.chunk_id in relevant_ids]
            return {
                "graded_chunks": kept_reranked or reranked,
                "grading_status": "RELEVANT",
            }

        # If strict LLM grader returned insufficient, verify if top reranked chunks have solid vector similarity
        solid_chunks = [r for r in reranked if r.search_result.similarity_score >= 0.35]
        if solid_chunks:
            logger.info(f"Retaining {len(solid_chunks)} chunks with solid vector similarity (>= 0.35) despite strict grading.")
            return {
                "graded_chunks": solid_chunks,
                "grading_status": "RELEVANT",
            }

        return {
            "graded_chunks": [],
            "grading_status": "INSUFFICIENT",
        }

    # =========================================================================
    # Node 7: Corrective RAG (CRAG) Fallback / Permission Prompt Node
    # =========================================================================
    def crag_fallback_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")

        # If user pre-authorized web search, proceed to web retrieval immediately
        if state.get("allow_web_search"):
            return {
                "route_decision": "WEB_SEARCH",
            }

        # Otherwise, ask permission and offer parametric preview
        notice = (
            f"I couldn't find sufficient information in your stored documents to answer this question accurately.\n\n"
            f"Would you like me to search the web for **\"{query}\"**?"
        )
        return {
            "response_text": notice,
            "response_source": "web_prompt",
            "can_search_web": True,
            "citations": [],
            "tokens_used": 0,
            "metadata": {
                **(state.get("metadata") or {}),
                "crag_fallback": True,
                "suggested_web_query": query,
            },
        }

    # =========================================================================
    # Node 8: Web Search Execution & Grounded Generation Node
    # =========================================================================
    def web_search_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        web_results = WebSearchService.search(query=query, max_results=4)
        logger.info(f"WebSearchService retrieved {len(web_results)} results for query: '{query[:40]}...'")

        if not web_results:
            fallback = (
                f"I searched the web for \"{query}\", but did not find accessible results. "
                "Please verify your query or internet connection."
            )
            return {
                "response_text": fallback,
                "response_source": "web",
                "citations": [],
                "tokens_used": 0,
            }

        # Build web context
        web_context_parts = []
        web_citations = []
        for idx, item in enumerate(web_results, 1):
            web_context_parts.append(f"[Web {idx}] {item.title}\n{item.snippet}\nSource URL: {item.url}")
            web_citations.append({
                "citation_number": idx,
                "document_title": item.title,
                "source_name": "Web Search (DuckDuckGo)",
                "source_uri": item.url,
                "source_type": "web",
                "content_snippet": item.snippet[:200],
            })

        web_context_text = "\n\n".join(web_context_parts)
        prompt = (
            f"External Web Context:\n{web_context_text}\n\n"
            f"User Question: {query}\n\n"
            f"Answer based on the web context:"
        )

        try:
            res = active_llm.generate(
                prompt=prompt,
                system_prompt=WEB_GROUNDED_SYSTEM_PROMPT,
            )
            return {
                "response_text": res.text,
                "response_source": "web",
                "citations": web_citations,
                "tokens_used": res.tokens_used,
                "metadata": {
                    **(state.get("metadata") or {}),
                    "web_results_count": len(web_results),
                },
            }
        except Exception as e:
            return {
                "response_text": f"Error generating web answer: {e}",
                "response_source": "web",
                "citations": web_citations,
                "error": str(e),
            }

    # =========================================================================
    # Node 9: Build Context & Citations Node (From Stored Docs)
    # =========================================================================
    def build_context_node(state: RAGState) -> Dict[str, Any]:
        graded_chunks = state.get("graded_chunks", [])
        rerank_items = []
        for idx, c in enumerate(graded_chunks):
            if isinstance(c, RerankResult):
                rerank_items.append(c)
            else:
                rerank_items.append(
                    RerankResult(
                        search_result=c,
                        rerank_score=getattr(c, "similarity_score", 1.0),
                        original_rank=idx + 1,
                        new_rank=idx + 1,
                    )
                )


        built_ctx = ctx_builder.build(rerank_items)
        serialized_citations = [c.to_dict() for c in built_ctx.citations]
        return {
            "context_text": built_ctx.formatted_text,
            "citations": serialized_citations,
            "metadata": {
                **(state.get("metadata") or {}),
                "total_context_chars": built_ctx.total_chars,
                "included_chunks": built_ctx.total_chunks,
            },
        }

    # =========================================================================
    # Node 10: Grounded Generation Node (Document-Grounded + Hallucination Check)
    # =========================================================================
    def grounded_generation_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        context_text = state.get("context_text", "").strip()
        citations = state.get("citations", [])

        prompt = (
            f"Context from knowledge base:\n"
            f"{context_text}\n\n"
            f"User Question: {query}\n\n"
            f"Answer:"
        )

        start_time = time.time()
        try:
            res = active_llm.generate(
                prompt=prompt,
                system_prompt=GROUNDED_SYSTEM_PROMPT,
            )
            elapsed_ms = round((time.time() - start_time) * 1000, 2)

            # Self-RAG Hallucination check
            is_grounded = HallucinationChecker.is_grounded(
                answer=res.text,
                context=context_text,
                llm_provider=active_llm,
            )

            return {
                "response_text": res.text,
                "response_source": "documents",
                "citations": citations,
                "tokens_used": res.tokens_used,
                "metadata": {
                    **(state.get("metadata") or {}),
                    "is_grounded": is_grounded,
                    "generation_latency_ms": elapsed_ms,
                    "llm_model": res.model,
                },
            }
        except Exception as e:
            logger.error(f"Error during grounded generation: {e}")
            err_str = str(e)
            if any(term in err_str.lower() for term in ("downtime", "high demand", "timed out", "down", "503", "429")):
                friendly = "⚠️ The AI Cloud API is currently experiencing downtime or high demand. Please try again in a few moments or switch to local Ollama in Settings."
            else:
                friendly = f"Error generating answer: {str(e)}"
            return {
                "response_text": friendly,
                "response_source": "documents",
                "error": str(e),
                "tokens_used": 0,
            }

    # =========================================================================
    # Router Conditional Edges
    # =========================================================================
    def route_decision_edge(state: RAGState) -> str:
        decision = state.get("route_decision", "RETRIEVAL")
        if decision == "PARAMETRIC":
            return "parametric"
        elif decision == "WEB_SEARCH":
            return "web_search"
        else:
            return "query_transform"

    def grading_decision_edge(state: RAGState) -> str:
        status = state.get("grading_status", "INSUFFICIENT")
        if status == "RELEVANT":
            return "build_context"
        else:
            return "crag_fallback"

    def crag_decision_edge(state: RAGState) -> str:
        if state.get("allow_web_search"):
            return "web_search"
        return "end"

    # =========================================================================
    # Assemble LangGraph Workflow
    # =========================================================================
    workflow = StateGraph(RAGState)

    workflow.add_node("router", router_node)
    workflow.add_node("parametric", parametric_node)
    workflow.add_node("query_transform", query_transform_node)
    workflow.add_node("hybrid_retrieval", hybrid_retrieval_node)
    workflow.add_node("reranking", reranking_node)
    workflow.add_node("document_grading", document_grading_node)
    workflow.add_node("crag_fallback", crag_fallback_node)
    workflow.add_node("web_search", web_search_node)
    workflow.add_node("build_context", build_context_node)
    workflow.add_node("grounded_generation", grounded_generation_node)

    # Wire Edges
    workflow.add_edge(START, "router")

    # Conditional Branch from Router
    workflow.add_conditional_edges(
        "router",
        route_decision_edge,
        {
            "parametric": "parametric",
            "web_search": "web_search",
            "query_transform": "query_transform",
        },
    )

    # Retrieval Pipeline
    workflow.add_edge("query_transform", "hybrid_retrieval")
    workflow.add_edge("hybrid_retrieval", "reranking")
    workflow.add_edge("reranking", "document_grading")

    # Conditional Branch from Document Grading (Self-RAG)
    workflow.add_conditional_edges(
        "document_grading",
        grading_decision_edge,
        {
            "build_context": "build_context",
            "crag_fallback": "crag_fallback",
        },
    )

    # CRAG Fallback branch: if user allowed web search -> web_search, else END
    workflow.add_conditional_edges(
        "crag_fallback",
        crag_decision_edge,
        {
            "web_search": "web_search",
            "end": END,
        },
    )

    # Context -> Generation -> END
    workflow.add_edge("build_context", "grounded_generation")
    workflow.add_edge("grounded_generation", END)
    workflow.add_edge("parametric", END)
    workflow.add_edge("web_search", END)

    return workflow.compile()
