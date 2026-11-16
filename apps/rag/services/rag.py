from dataclasses import dataclass, field
import json
import logging
import queue
import threading
import time
from typing import Any, Dict, Iterator, List, Optional, Union
import uuid

from django.conf import settings
from apps.rag.models import Conversation, Message, RetrievedChunk
from apps.rag.query_processing import BaseQueryProcessor
from apps.rag.reranking import BaseReranker
from apps.rag.llm import BaseLLMProvider
from apps.rag.context import ContextBuilder

logger = logging.getLogger("brofessor")


def format_sse(event: str, data: Any) -> str:
    """Format payload according to W3C Server-Sent Events (SSE) specification."""
    payload = json.dumps(data) if not isinstance(data, str) else data
    return f"event: {event}\ndata: {payload}\n\n"


@dataclass
class RAGResult:
    """Consolidated result returned by the RAG service."""
    conversation_id: str
    message_id: str
    query: str
    answer: str
    citations: List[Dict[str, Any]]
    retrieved_count: int
    reranked_count: int
    response_source: str = "documents"  # "parametric", "documents", "web", "web_prompt"
    can_search_web: bool = False
    tokens_used: Optional[int] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conversation_id": self.conversation_id,
            "message_id": self.message_id,
            "query": self.query,
            "answer": self.answer,
            "citations": self.citations,
            "retrieved_count": self.retrieved_count,
            "reranked_count": self.reranked_count,
            "response_source": self.response_source,
            "can_search_web": self.can_search_web,
            "tokens_used": self.tokens_used,
            "error": self.error,
            "metadata": self.metadata,
        }


class RAGService:
    """
    High-level RAG Orchestration Service.
    Executes the LangGraph pipeline with multi-turn conversational memory,
    pipeline stage telemetry, progressive token streaming, and citation persistence.
    """

    @classmethod
    def ask(
        cls,
        query: str,
        conversation_id: Optional[Union[str, uuid.UUID]] = None,
        domain_id: Optional[Union[str, uuid.UUID]] = None,
        allow_web_search: bool = False,
        retrieval_top_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        query_processor: Optional[BaseQueryProcessor] = None,
        reranker: Optional[BaseReranker] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
    ) -> RAGResult:
        start_time = time.time()
        retrieval_k = retrieval_top_k or getattr(settings, "RAG_RETRIEVAL_TOP_K", 10)
        rerank_k = rerank_top_k or getattr(settings, "RAG_RERANK_TOP_K", 4)
        active_filters = filters or {}

        # 1. Resolve or create Conversation and load preceding multi-turn chat history
        conversation = None
        chat_history: List[Dict[str, str]] = []
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id).first()
            if conversation:
                past_messages = list(conversation.messages.order_by("-created_at")[:6])
                for m in reversed(past_messages):
                    chat_history.append({"role": m.role, "content": m.content})

        if not conversation:
            title = (query.strip()[:47] + "...") if len(query.strip()) > 50 else query.strip()
            conversation = Conversation.objects.create(
                title=title or "New Conversation",
                domain_id=domain_id,
            )

        # 2. Record User Message
        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.SenderRole.USER,
            content=query,
        )

        # 3. Build & execute LangGraph workflow
        from apps.rag.workflow.graph import create_rag_graph, RAGState
        from apps.rag.llm.registry import get_system_ai_config, sync_langsmith_env

        ai_cfg = get_system_ai_config()
        run_config = None
        if ai_cfg.get("langsmith_api_key"):
            sync_langsmith_env(ai_cfg)
            run_config = {
                "tags": ["brofessor", "chat", "rag"],
                "metadata": {
                    "conversation_id": str(conversation.id),
                    "user_message_id": str(user_message.id),
                    "query": query[:100],
                },
                "run_name": f"Brofessor RAG: {query[:35]}",
            }

        app = create_rag_graph(
            query_processor=query_processor,
            reranker=reranker,
            llm_provider=llm_provider,
            context_builder=context_builder,
        )

        initial_state: RAGState = {
            "query": query,
            "conversation_id": str(conversation.id),
            "chat_history": chat_history,
            "allow_web_search": allow_web_search,
            "filters": active_filters,
            "retrieval_top_k": retrieval_k,
            "rerank_top_k": rerank_k,
            "metadata": {
                "user_message_id": str(user_message.id),
                "has_chat_history": len(chat_history) > 0,
            },
        }

        logger.info(f"Invoking LangGraph RAG workflow for query: '{query[:50]}' (history turns: {len(chat_history)})...")
        final_state: RAGState = app.invoke(initial_state, config=run_config) if run_config else app.invoke(initial_state)

        answer = final_state.get("response_text", "")
        citations = final_state.get("citations", [])
        tokens_used = final_state.get("tokens_used")
        error_msg = final_state.get("error")
        response_source = final_state.get("response_source", "documents")
        can_search_web = bool(final_state.get("can_search_web", False))

        meta = final_state.get("metadata", {})
        meta["total_pipeline_ms"] = round((time.time() - start_time) * 1000, 2)
        meta["response_source"] = response_source
        meta["can_search_web"] = can_search_web

        # 4. Record Assistant Message
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.SenderRole.ASSISTANT,
            content=answer,
            tokens_used=tokens_used,
            metadata={
                **meta,
                "retrieved_count": len(final_state.get("retrieved_chunks", [])),
                "reranked_count": len(final_state.get("reranked_chunks", [])),
            },
        )

        # 5. Persist grounding RetrievedChunk references safely
        retrieved_chunk_objects = []
        for citation in citations:
            chunk_id = citation.get("chunk_id")
            if chunk_id:
                try:
                    valid_uuid = uuid.UUID(str(chunk_id))
                    retrieved_chunk_objects.append(
                        RetrievedChunk(
                            message=assistant_message,
                            chunk_id=valid_uuid,
                            similarity_score=citation.get("similarity_score"),
                            rank=citation.get("rank", 1),
                        )
                    )
                except (ValueError, TypeError):
                    continue

        if retrieved_chunk_objects:
            try:
                RetrievedChunk.objects.bulk_create(retrieved_chunk_objects, ignore_conflicts=True)
            except Exception as e:
                logger.warning(f"Could not persist RetrievedChunk references: {e}")

        return RAGResult(
            conversation_id=str(conversation.id),
            message_id=str(assistant_message.id),
            query=query,
            answer=answer,
            citations=citations,
            retrieved_count=len(final_state.get("retrieved_chunks", [])),
            reranked_count=len(final_state.get("reranked_chunks", [])),
            response_source=response_source,
            can_search_web=can_search_web,
            tokens_used=tokens_used,
            error=error_msg,
            metadata=meta,
        )

    @classmethod
    def ask_stream(
        cls,
        query: str,
        conversation_id: Optional[Union[str, uuid.UUID]] = None,
        domain_id: Optional[Union[str, uuid.UUID]] = None,
        allow_web_search: bool = False,
        retrieval_top_k: Optional[int] = None,
        rerank_top_k: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None,
        query_processor: Optional[BaseQueryProcessor] = None,
        reranker: Optional[BaseReranker] = None,
        llm_provider: Optional[BaseLLMProvider] = None,
        context_builder: Optional[ContextBuilder] = None,
    ) -> Iterator[str]:
        """
        Stream progressive pipeline stage events and token-by-token LLM output via SSE.
        Maintains conversational history and persists messages upon completion.
        """
        start_time = time.time()
        retrieval_k = retrieval_top_k or getattr(settings, "RAG_RETRIEVAL_TOP_K", 10)
        rerank_k = rerank_top_k or getattr(settings, "RAG_RERANK_TOP_K", 4)
        active_filters = filters or {}

        # 1. Resolve or create Conversation and load preceding multi-turn chat history
        conversation = None
        chat_history: List[Dict[str, str]] = []
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id).first()
            if conversation:
                past_messages = list(conversation.messages.order_by("-created_at")[:6])
                for m in reversed(past_messages):
                    chat_history.append({"role": m.role, "content": m.content})

        if not conversation:
            title = (query.strip()[:47] + "...") if len(query.strip()) > 50 else query.strip()
            conversation = Conversation.objects.create(
                title=title or "New Conversation",
                domain_id=domain_id,
            )

        # 2. Record User Message
        user_message = Message.objects.create(
            conversation=conversation,
            role=Message.SenderRole.USER,
            content=query,
        )

        # Yield conversation established event
        yield format_sse("conversation", {
            "conversation_id": str(conversation.id),
            "user_message_id": str(user_message.id),
            "query": query,
            "has_chat_history": len(chat_history) > 0,
        })

        # Yield initial stage
        yield format_sse("stage", {
            "stage": "router",
            "label": "Classifying query intent (Adaptive Router)...",
        })

        event_queue: queue.Queue = queue.Queue()

        def on_token_callback(token_text: str):
            event_queue.put(("token", {"token": token_text}))

        def run_langgraph_workflow():
            from apps.rag.workflow.graph import create_rag_graph, RAGState
            from apps.rag.llm.registry import get_system_ai_config, sync_langsmith_env

            try:
                ai_cfg = get_system_ai_config()
                run_config = None
                if ai_cfg.get("langsmith_api_key"):
                    sync_langsmith_env(ai_cfg)
                    run_config = {
                        "tags": ["brofessor", "chat", "rag", "stream"],
                        "metadata": {
                            "conversation_id": str(conversation.id),
                            "user_message_id": str(user_message.id),
                            "query": query[:100],
                        },
                        "run_name": f"Brofessor RAG Stream: {query[:35]}",
                    }

                app = create_rag_graph(
                    query_processor=query_processor,
                    reranker=reranker,
                    llm_provider=llm_provider,
                    context_builder=context_builder,
                    on_token=on_token_callback,
                )

                initial_state: RAGState = {
                    "query": query,
                    "conversation_id": str(conversation.id),
                    "chat_history": chat_history,
                    "allow_web_search": allow_web_search,
                    "filters": active_filters,
                    "retrieval_top_k": retrieval_k,
                    "rerank_top_k": rerank_k,
                    "metadata": {
                        "user_message_id": str(user_message.id),
                        "has_chat_history": len(chat_history) > 0,
                    },
                }

                accumulated_state: Dict[str, Any] = {}
                stream_iter = app.stream(initial_state, config=run_config) if run_config else app.stream(initial_state)
                for step in stream_iter:
                    for node_name, node_output in step.items():
                        accumulated_state.update(node_output)
                        if node_name == "router":
                            cat = node_output.get("route_decision", "RETRIEVAL")
                            event_queue.put(("stage", {
                                "stage": "router",
                                "label": f"Classified intent as {cat} (Adaptive RAG)",
                                "decision": cat,
                            }))
                        elif node_name == "query_transform":
                            trans = node_output.get("transformed_query", "")
                            event_queue.put(("stage", {
                                "stage": "transform",
                                "label": f"Search Query: \"{trans[:40]}\"",
                                "transformed_query": trans,
                            }))
                        elif node_name == "hybrid_retrieval":
                            count = len(node_output.get("retrieved_chunks", []))
                            event_queue.put(("stage", {
                                "stage": "retrieval",
                                "label": f"Retrieved {count} chunks via Hybrid Search (Dense + BM25)",
                                "retrieved_count": count,
                            }))
                        elif node_name == "reranking":
                            count = len(node_output.get("reranked_chunks", []))
                            event_queue.put(("stage", {
                                "stage": "rerank",
                                "label": f"Reranked top {count} chunks using Reciprocal Rank Fusion",
                                "reranked_count": count,
                            }))
                        elif node_name == "document_grading":
                            status = node_output.get("grading_status", "RELEVANT")
                            count = len(node_output.get("graded_chunks", []))
                            event_queue.put(("stage", {
                                "stage": "grading",
                                "label": f"Evaluated document relevance: {status} ({count} chunks)",
                                "status": status,
                                "graded_count": count,
                            }))
                        elif node_name == "crag_fallback":
                            event_queue.put(("stage", {
                                "stage": "crag_fallback",
                                "label": "Insufficient document context, prompting for web search permission",
                                "can_search_web": True,
                            }))
                        elif node_name == "build_context":
                            citations = node_output.get("citations", [])
                            event_queue.put(("citations", {"citations": citations}))
                            event_queue.put(("stage", {
                                "stage": "generation",
                                "label": "Synthesizing verified grounded response...",
                                "source": "documents",
                            }))
                        elif node_name == "web_search":
                            web_citations = node_output.get("citations", [])
                            if web_citations:
                                event_queue.put(("citations", {"citations": web_citations}))
                            event_queue.put(("stage", {
                                "stage": "generation",
                                "label": "Synthesizing response from verified web context...",
                                "source": "web",
                            }))
                        elif node_name == "parametric":
                            event_queue.put(("stage", {
                                "stage": "generation",
                                "label": "Generating direct response from core knowledge...",
                                "source": "parametric",
                            }))

                event_queue.put(("DONE", accumulated_state))
            except Exception as exc:
                logger.error(f"Error in streaming LangGraph workflow: {exc}", exc_info=True)
                event_queue.put(("ERROR", str(exc)))

        thread = threading.Thread(target=run_langgraph_workflow, daemon=True)
        thread.start()

        accumulated_tokens: List[str] = []
        final_state: Dict[str, Any] = {}
        citations_sent: List[Dict[str, Any]] = []

        while True:
            event_type, payload = event_queue.get()
            if event_type == "token":
                tok = payload.get("token", "")
                accumulated_tokens.append(tok)
                yield format_sse("token", payload)
            elif event_type == "stage":
                yield format_sse("stage", payload)
            elif event_type == "citations":
                citations_sent = payload.get("citations", [])
                yield format_sse("citations", payload)
            elif event_type == "DONE":
                final_state = payload or {}
                break
            elif event_type == "ERROR":
                yield format_sse("error", {"error": payload})
                break

        thread.join(timeout=1.0)

        # 4. Resolve final generated text and citations
        full_answer = "".join(accumulated_tokens).strip() if accumulated_tokens else final_state.get("response_text", "")
        citations = citations_sent or final_state.get("citations", [])
        response_source = final_state.get("response_source", "documents")
        can_search_web = bool(final_state.get("can_search_web", False))
        tokens_used = final_state.get("tokens_used", len(accumulated_tokens) if accumulated_tokens else None)

        meta = final_state.get("metadata", {})
        meta["total_pipeline_ms"] = round((time.time() - start_time) * 1000, 2)
        meta["response_source"] = response_source
        meta["can_search_web"] = can_search_web

        # 5. Record Assistant Message in database
        assistant_message = Message.objects.create(
            conversation=conversation,
            role=Message.SenderRole.ASSISTANT,
            content=full_answer,
            tokens_used=tokens_used,
            metadata={
                **meta,
                "retrieved_count": len(final_state.get("retrieved_chunks", [])),
                "reranked_count": len(final_state.get("reranked_chunks", [])),
            },
        )

        # 6. Persist grounding RetrievedChunk references safely
        retrieved_chunk_objects = []
        for citation in citations:
            chunk_id = citation.get("chunk_id")
            if chunk_id:
                try:
                    valid_uuid = uuid.UUID(str(chunk_id))
                    retrieved_chunk_objects.append(
                        RetrievedChunk(
                            message=assistant_message,
                            chunk_id=valid_uuid,
                            similarity_score=citation.get("similarity_score"),
                            rank=citation.get("rank", 1),
                        )
                    )
                except (ValueError, TypeError):
                    continue

        if retrieved_chunk_objects:
            try:
                RetrievedChunk.objects.bulk_create(retrieved_chunk_objects, ignore_conflicts=True)
            except Exception as e:
                logger.warning(f"Could not persist RetrievedChunk references in stream: {e}")

        # 7. Emit final done event with full metadata
        yield format_sse("done", {
            "conversation_id": str(conversation.id),
            "message_id": str(assistant_message.id),
            "answer": full_answer,
            "citations": citations,
            "response_source": response_source,
            "can_search_web": can_search_web,
            "tokens_used": tokens_used,
            "metadata": meta,
        })

