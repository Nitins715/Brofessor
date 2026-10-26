from django.urls import path
from .views import (
    RagIndexView,
    VectorSearchView,
    RAGChatView,
    ConversationListView,
    ConversationDetailView,
)

urlpatterns = [
    path("", RagIndexView.as_view(), name="rag-index"),
    path("search/", VectorSearchView.as_view(), name="rag-vector-search"),
    path("chat/", RAGChatView.as_view(), name="rag-chat"),
    path("conversations/", ConversationListView.as_view(), name="rag-conversations-list"),
    path("conversations/<uuid:pk>/", ConversationDetailView.as_view(), name="rag-conversation-detail"),
]
