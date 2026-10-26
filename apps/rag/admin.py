from django.contrib import admin
from .models import Conversation, Message, RetrievedChunk


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ("title", "domain", "skill", "updated_at", "created_at")
    search_fields = ("title",)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("conversation", "role", "tokens_used", "created_at")
    list_filter = ("role",)


@admin.register(RetrievedChunk)
class RetrievedChunkAdmin(admin.ModelAdmin):
    list_display = ("message", "chunk", "similarity_score", "rank")
