from dataclasses import dataclass, field
import logging
import time
from typing import Any, Dict, List, Optional, Union
import uuid

from django.conf import settings
from apps.rag.models import Conversation, Message, RetrievedChunk
from apps.rag.workflow import create_rag_graph, RAGState
from apps.rag.query_processing import BaseQueryProcessor
from apps.rag.reranking import BaseReranker
from apps.rag.llm import BaseLLMProvider
from apps.rag.context import ContextBuilder

logger = logging.getLogger("brofessor")


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
    Executes the LangGraph pipeline and manages conversation, message,
    and grounding chunk persistence.
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

        # 1. Resolve or create Conversation
        conversation = None
        if conversation_id:
            conversation = Conversation.objects.filter(id=conversation_id).first()
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
        app = create_rag_graph(
            query_processor=query_processor,
            reranker=reranker,
            llm_provider=llm_provider,
            context_builder=context_builder,
        )

        initial_state: RAGState = {
            "query": query,
            "conversation_id": str(conversation.id),
            "allow_web_search": allow_web_search,
            "filters": active_filters,
            "retrieval_top_k": retrieval_k,
            "rerank_top_k": rerank_k,
            "metadata": {
                "user_message_id": str(user_message.id),
            },
        }

        logger.info(f"Invoking LangGraph RAG workflow for query: '{query[:50]}'...")
        final_state: RAGState = app.invoke(initial_state)

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

        # 5. Persist grounding RetrievedChunk references
        retrieved_chunk_objects = []
        for citation in citations:
            chunk_id = citation.get("chunk_id")
            if chunk_id:
                retrieved_chunk_objects.append(
                    RetrievedChunk(
                        message=assistant_message,
                        chunk_id=chunk_id,
                        similarity_score=citation.get("similarity_score"),
                        rank=citation.get("rank", 1),
                    )
                )

        if retrieved_chunk_objects:
            RetrievedChunk.objects.bulk_create(retrieved_chunk_objects)

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
