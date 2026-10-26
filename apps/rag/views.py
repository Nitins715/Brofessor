from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

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
