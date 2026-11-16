import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from django.http import StreamingHttpResponse
from drf_spectacular.utils import extend_schema

logger = logging.getLogger("brofessor")


from .models import Conversation, Message
from .serializers import (
    VectorSearchRequestSerializer,
    VectorSearchResponseSerializer,
    RAGChatRequestSerializer,
    RAGChatResponseSerializer,
    ConversationDetailSerializer,
)
from .services import RetrievalService, RAGService


class RagIndexView(APIView):
    """Overview endpoint for RAG module."""
    @extend_schema(summary="RAG Module Overview")
    def get(self, request):
        return Response({
            "module": "rag",
            "status": "ready",
            "endpoints": {
                "search": request.build_absolute_uri("search/"),
                "chat": request.build_absolute_uri("chat/"),
                "conversations": request.build_absolute_uri("conversations/"),
            },
        })


class VectorSearchView(APIView):
    """
    Execute vector similarity search across ingested document chunks.
    Uses PostgreSQL pgvector with cosine distance ordering.
    """

    @extend_schema(
        summary="Vector Similarity Search",
        description="Search stored document chunks using dense embeddings and cosine similarity.",
        request=VectorSearchRequestSerializer,
        responses={200: VectorSearchResponseSerializer},
    )
    def post(self, request):
        serializer = VectorSearchRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        results = RetrievalService.search(
            query=data["query"],
            top_k=data.get("top_k", 10),
            source_ids=[str(s) for s in data.get("source_ids", [])] if data.get("source_ids") else None,
            document_ids=[str(d) for d in data.get("document_ids", [])] if data.get("document_ids") else None,
            source_types=data.get("source_types") or None,
            min_similarity=data.get("min_similarity"),
        )

        return Response(
            {
                "query": data["query"],
                "total_results": len(results),
                "results": [r.to_dict() for r in results],
            },
            status=status.HTTP_200_OK,
        )


class RAGChatView(APIView):
    """
    RAG Chat endpoint for questioning stored knowledge.
    Executes: Query Processing -> Retrieval (Top 10) -> Reranking (Top 4) -> Context -> LLM -> Answer + Citations.
    Persists user query, assistant response, and grounding chunk citations.
    """

    @extend_schema(
        summary="RAG Chat Question & Answer",
        description="Ask a question against stored knowledge using the full LangGraph RAG pipeline.",
        request=RAGChatRequestSerializer,
        responses={200: RAGChatResponseSerializer},
    )
    def post(self, request):
        serializer = RAGChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        filters = {
            "source_types": data.get("source_types") or None,
            "source_ids": [str(s) for s in data.get("source_ids", [])] if data.get("source_ids") else None,
            "document_ids": [str(d) for d in data.get("document_ids", [])] if data.get("document_ids") else None,
            "min_similarity": data.get("min_similarity"),
        }

        try:
            rag_result = RAGService.ask(
                query=data["query"],
                conversation_id=data.get("conversation_id"),
                domain_id=data.get("domain_id"),
                allow_web_search=data.get("allow_web_search", False),
                retrieval_top_k=data.get("retrieval_top_k"),
                rerank_top_k=data.get("rerank_top_k"),
                filters=filters,
            )
            return Response(rag_result.to_dict(), status=status.HTTP_200_OK)
        except Exception as e:
            logger.error(f"Error executing RAG pipeline for query '{data['query'][:40]}': {e}", exc_info=True)
            return Response(
                {
                    "conversation_id": str(data.get("conversation_id") or ""),
                    "message_id": "",
                    "query": data["query"],
                    "answer": f"⚠️ An error occurred during RAG pipeline execution: {str(e)}",
                    "citations": [],
                    "retrieved_count": 0,
                    "reranked_count": 0,
                    "response_source": "documents",
                    "can_search_web": True,
                    "error": str(e),
                    "metadata": {},
                },
                status=status.HTTP_200_OK,
            )


class RAGChatStreamView(APIView):
    """
    Server-Sent Events (SSE) streaming endpoint for RAG question answering.
    Streams real-time pipeline stage telemetry and token-by-token LLM output.
    """

    @extend_schema(
        summary="RAG Chat Question & Answer (SSE Stream)",
        description="Stream real-time pipeline stage telemetry and progressive token output via Server-Sent Events.",
        request=RAGChatRequestSerializer,
    )
    def post(self, request):
        serializer = RAGChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        filters = {
            "source_types": data.get("source_types") or None,
            "source_ids": [str(s) for s in data.get("source_ids", [])] if data.get("source_ids") else None,
            "document_ids": [str(d) for d in data.get("document_ids", [])] if data.get("document_ids") else None,
            "min_similarity": data.get("min_similarity"),
        }

        stream_gen = RAGService.ask_stream(
            query=data["query"],
            conversation_id=data.get("conversation_id"),
            domain_id=data.get("domain_id"),
            allow_web_search=data.get("allow_web_search", False),
            retrieval_top_k=data.get("retrieval_top_k"),
            rerank_top_k=data.get("rerank_top_k"),
            filters=filters,
        )

        response = StreamingHttpResponse(stream_gen, content_type="text/event-stream")
        response["Cache-Control"] = "no-cache"
        response["X-Accel-Buffering"] = "no"
        return response



class ConversationListView(APIView):
    """List recent conversations or create a new conversation."""

    @extend_schema(summary="List Conversations")
    def get(self, request):
        conversations = Conversation.objects.all().order_by("-updated_at")[:50]
        data = [
            {
                "id": str(c.id),
                "title": c.title,
                "domain_id": str(c.domain_id) if c.domain_id else None,
                "created_at": c.created_at,
                "updated_at": c.updated_at,
                "message_count": c.messages.count(),
            }
            for c in conversations
        ]
        return Response(data, status=status.HTTP_200_OK)

    @extend_schema(summary="Create Conversation")
    def post(self, request):
        title = request.data.get("title", "New Conversation") if isinstance(request.data, dict) else "New Conversation"
        domain_id = request.data.get("domain_id") if isinstance(request.data, dict) else None
        conv = Conversation.objects.create(title=title, domain_id=domain_id)
        return Response({
            "id": str(conv.id),
            "title": conv.title,
            "domain_id": str(conv.domain_id) if conv.domain_id else None,
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "messages": [],
        }, status=status.HTTP_201_CREATED)

    @extend_schema(summary="Clear All Conversations")
    def delete(self, request):
        count, _ = Conversation.objects.all().delete()
        return Response({
            "deleted": count,
            "message": "All chat history removed completely",
        }, status=status.HTTP_200_OK)


class ConversationDetailView(APIView):
    """Retrieve complete message history and grounding citations for a Conversation."""

    @extend_schema(summary="Conversation Details & Messages")
    def get(self, request, pk):
        conv = Conversation.objects.filter(id=pk).first()
        if not conv:
            raise NotFound(detail=f"Conversation {pk} not found")

        messages = conv.messages.all().order_by("created_at")
        msg_data = []
        for m in messages:
            msg_data.append({
                "id": str(m.id),
                "role": m.role,
                "content": m.content,
                "tokens_used": m.tokens_used,
                "created_at": m.created_at,
                "metadata": m.metadata,
            })

        return Response(
            {
                "id": str(conv.id),
                "title": conv.title,
                "domain_id": str(conv.domain_id) if conv.domain_id else None,
                "metadata": conv.metadata,
                "created_at": conv.created_at,
                "updated_at": conv.updated_at,
                "messages": msg_data,
            },
            status=status.HTTP_200_OK,
        )

    @extend_schema(summary="Delete Single Conversation")
    def delete(self, request, pk):
        conv = Conversation.objects.filter(id=pk).first()
        if not conv:
            raise NotFound(detail=f"Conversation {pk} not found")
        conv.delete()
        return Response(
            {"message": f"Conversation {pk} deleted successfully"},
            status=status.HTTP_200_OK,
        )


class IntegrationsStatusView(APIView):
    """
    Get live connection and health status for external observability (LangSmith)
    and LLM providers (Gemini / Ollama).
    """

    @extend_schema(summary="Integrations & API Keys Health Status")
    def get(self, request):
        from apps.rag.services.integrations import get_current_integrations_status
        status_data = get_current_integrations_status(include_secrets=False)
        return Response(status_data, status=status.HTTP_200_OK)


class IntegrationsVerifyView(APIView):
    """
    Verify / Ping connection for LangSmith and LLM API keys.
    Optionally saves the credentials to persistent ai_config.json.
    """

    @extend_schema(summary="Verify and Test Integrations Connection (Ping)")
    def post(self, request):
        from apps.rag.services.integrations import (
            verify_langsmith_key,
            verify_gemini_key,
            verify_ollama_status,
            get_current_integrations_status,
            mask_key,
        )
        from apps.rag.llm.registry import get_system_ai_config, save_system_ai_config

        payload = request.data or {}
        save_changes = bool(payload.get("save", False))

        ai_cfg = get_system_ai_config()

        # Keys can be explicitly supplied or fallback to existing configured keys
        langsmith_key = payload.get("langsmith_api_key")
        if langsmith_key is None:
            langsmith_key = ai_cfg.get("langsmith_api_key", "")
        langsmith_key = langsmith_key.strip()

        langsmith_project = payload.get("langsmith_project")
        if langsmith_project is None:
            langsmith_project = ai_cfg.get("langsmith_project", "brofessor-rag")
        langsmith_project = (langsmith_project or "brofessor-rag").strip()

        gemini_key = payload.get("gemini_api_key")
        if gemini_key is None:
            gemini_key = ai_cfg.get("gemini_api_key", "")
        gemini_key = gemini_key.strip()

        gemini_model = payload.get("gemini_model")
        if gemini_model is None:
            gemini_model = ai_cfg.get("gemini_model", "gemini-3.6-flash")
        gemini_model = (gemini_model or "gemini-3.6-flash").strip()

        # Run verification checks
        langsmith_result = verify_langsmith_key(langsmith_key, project_name=langsmith_project)
        gemini_result = verify_gemini_key(gemini_key, model_name=gemini_model)
        ollama_result = verify_ollama_status(
            ai_cfg.get("ollama_base_url", "http://127.0.0.1:11434"),
            ai_cfg.get("ollama_model", "llama3.2"),
        )

        if save_changes:
            updates = {
                "langsmith_api_key": langsmith_key,
                "langsmith_project": langsmith_project,
                "langsmith_tracing": bool(langsmith_key),
                "gemini_api_key": gemini_key,
                "gemini_model": gemini_model,
            }
            save_system_ai_config(updates)
            logger.info("Saved updated integrations config via API verify.")

        # Resolve active LLM display
        if gemini_key:
            active_llm = {
                "provider": "gemini",
                "name": f"Gemini ({gemini_model})",
                "connected": gemini_result["connected"],
                "status": gemini_result["status"],
                "message": gemini_result["message"],
            }
        else:
            active_llm = {
                "provider": "ollama",
                "name": f"Ollama ({ai_cfg.get('ollama_model', 'llama3.2')})",
                "connected": ollama_result["connected"],
                "status": ollama_result["status"],
                "message": ollama_result["message"],
            }

        return Response(
            {
                "success": True,
                "saved": save_changes,
                "langsmith": {
                    **langsmith_result,
                    "api_key_masked": mask_key(langsmith_key),
                    "project": langsmith_project,
                    "tracing_enabled": bool(langsmith_key),
                },
                "gemini": {
                    **gemini_result,
                    "api_key_masked": mask_key(gemini_key),
                    "model": gemini_model,
                },
                "ollama": ollama_result,
                "active_llm": active_llm,
            },
            status=status.HTTP_200_OK,
        )

