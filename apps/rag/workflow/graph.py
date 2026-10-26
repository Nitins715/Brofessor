import logging
import time
from typing import Any, Dict, List, Optional, TypedDict
from langgraph.graph import StateGraph, START, END

from apps.rag.query_processing import BaseQueryProcessor, DefaultQueryProcessor
from apps.rag.services.retrieval import RetrievalService, SearchResult
from apps.rag.reranking import BaseReranker, RerankResult, get_reranker
from apps.rag.context import ContextBuilder, Citation
from apps.rag.llm import BaseLLMProvider, get_llm_provider

logger = logging.getLogger("brofessor")

SYSTEM_PROMPT = """You are Brofessor, an intelligent, local-first personal knowledge assistant.
Answer the user's question accurately and thoroughly using ONLY the provided context.

Follow these strict guidelines:
1. Base your answer strictly on the provided context sources. Do NOT invent, assume, or extrapolate facts not supported by the sources.
2. If the context does not contain enough information to answer the question, clearly state: "I don't have enough information in the provided knowledge base to answer this question."
3. Where appropriate, refer to the sources by their citation bracket (e.g., [Source 1], [Source 2]).
4. Be concise, clear, and structured in your explanations."""


class RAGState(TypedDict, total=False):
    """LangGraph State representation for the RAG pipeline."""
    query: str
    processed_query: str
    conversation_id: Optional[str]
    filters: Dict[str, Any]
    retrieval_top_k: int
    rerank_top_k: int
    retrieved_chunks: List[SearchResult]
    reranked_chunks: List[RerankResult]
    context_text: str
    citations: List[Dict[str, Any]]
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
    Build and compile a LangGraph StateGraph representing the sequential RAG workflow:
    Query Processing -> Retrieval -> Reranking -> Build Context -> Generation -> Return
    """
    qp = query_processor or DefaultQueryProcessor()
    ctx_builder = context_builder or ContextBuilder()

    def query_processing_node(state: RAGState) -> Dict[str, Any]:
        raw_query = state.get("query", "")
        processed = qp.process(raw_query)
        logger.info(f"Query processed: '{raw_query}' -> '{processed.retrieval_query}'")
        return {
            "processed_query": processed.retrieval_query,
        }

    def retrieval_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("processed_query") or state.get("query", "")
        top_k = state.get("retrieval_top_k", 10)
        filters = state.get("filters", {})

        results = RetrievalService.search(
            query=query,
            top_k=top_k,
            source_ids=filters.get("source_ids"),
            document_ids=filters.get("document_ids"),
            source_types=filters.get("source_types"),
            min_similarity=filters.get("min_similarity"),
        )
        logger.info(f"Retrieval returned {len(results)} chunks for query: '{query[:40]}...'")
        return {
            "retrieved_chunks": results,
        }

    def reranking_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("processed_query") or state.get("query", "")
        retrieved = state.get("retrieved_chunks", [])
        top_k = state.get("rerank_top_k", 4)

        active_reranker = reranker or get_reranker()
        reranked = active_reranker.rerank(query=query, results=retrieved, top_k=top_k)
        logger.info(f"Reranking reduced {len(retrieved)} candidate chunks to {len(reranked)} top chunks")
        return {
            "reranked_chunks": reranked,
        }

    def build_context_node(state: RAGState) -> Dict[str, Any]:
        reranked = state.get("reranked_chunks", [])
        built_ctx = ctx_builder.build(reranked)

        serialized_citations = [c.to_dict() for c in built_ctx.citations]
        return {
            "context_text": built_ctx.formatted_text,
            "citations": serialized_citations,
            "metadata": {
                **(state.get("metadata") or {}),
                "total_context_chars": built_ctx.total_chars,
                "context_truncated": built_ctx.truncated,
                "included_chunks": built_ctx.total_chunks,
            },
        }

    def generation_node(state: RAGState) -> Dict[str, Any]:
        query = state.get("query", "")
        context_text = state.get("context_text", "").strip()
        citations = state.get("citations", [])

        # Check if insufficient context retrieved
        if not context_text or not citations:
            fallback_msg = (
                "I don't have enough information in the provided knowledge base to answer this question. "
                "Please consider ingesting relevant documents or notes into Brofessor."
            )
            return {
                "response_text": fallback_msg,
                "tokens_used": 0,
            }

        prompt = (
            f"Context from knowledge base:\n"
            f"{context_text}\n\n"
            f"User Question: {query}\n\n"
            f"Answer:"
        )

        active_llm = llm_provider or get_llm_provider()
        start_time = time.time()
        try:
            llm_res = active_llm.generate(
                prompt=prompt,
                system_prompt=SYSTEM_PROMPT,
            )
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            logger.info(f"LLM generation finished in {elapsed_ms}ms using model {llm_res.model}")

            return {
                "response_text": llm_res.text,
                "tokens_used": llm_res.tokens_used,
                "metadata": {
                    **(state.get("metadata") or {}),
                    "llm_model": llm_res.model,
                    "generation_latency_ms": elapsed_ms,
                },
            }
        except Exception as e:
            logger.error(f"Error during LLM generation: {e}")
            return {
                "response_text": f"Error generating answer: {str(e)}",
                "error": str(e),
                "tokens_used": 0,
            }

    # Construct LangGraph workflow
    workflow = StateGraph(RAGState)
    workflow.add_node("query_processing", query_processing_node)
    workflow.add_node("retrieval", retrieval_node)
    workflow.add_node("reranking", reranking_node)
    workflow.add_node("build_context", build_context_node)
    workflow.add_node("generation", generation_node)

    # Wire edges: Query -> Retrieve -> Rerank -> Build Context -> Generate -> Return
    workflow.add_edge(START, "query_processing")
    workflow.add_edge("query_processing", "retrieval")
    workflow.add_edge("retrieval", "reranking")
    workflow.add_edge("reranking", "build_context")
    workflow.add_edge("build_context", "generation")
    workflow.add_edge("generation", END)

    return workflow.compile()
