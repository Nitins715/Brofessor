from django.urls import path
from .views import (
    ConversationListView,
    ConversationDetailView,
)

urlpatterns = [
    path("", ConversationListView.as_view(), name="conversation-list"),
    path("<uuid:pk>/", ConversationDetailView.as_view(), name="conversation-detail"),
]
