from django.urls import path
from .views import (
    RagIndexView,
    VectorSearchView,
    RAGChatView,
    RAGChatStreamView,
    ConversationListView,
    ConversationDetailView,
    IntegrationsStatusView,
    IntegrationsVerifyView,
)

urlpatterns = [
    path("", RagIndexView.as_view(), name="rag-index"),
    path("search/", VectorSearchView.as_view(), name="rag-vector-search"),
    path("chat/", RAGChatView.as_view(), name="rag-chat"),
    path("chat/stream/", RAGChatStreamView.as_view(), name="rag-chat-stream"),
    path("conversations/", ConversationListView.as_view(), name="rag-conversations-list"),
    path("conversations/<uuid:pk>/", ConversationDetailView.as_view(), name="rag-conversation-detail"),
    path("integrations/status/", IntegrationsStatusView.as_view(), name="rag-integrations-status"),
    path("integrations/verify/", IntegrationsVerifyView.as_view(), name="rag-integrations-verify"),
]
