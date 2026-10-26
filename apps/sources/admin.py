from django.contrib import admin
from .models import Source, Document, DocumentChunk


@admin.register(Source)
class SourceAdmin(admin.ModelAdmin):
    list_display = ("name", "source_type", "status", "created_at")
    list_filter = ("source_type", "status")
    search_fields = ("name", "uri")


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "source", "content_hash", "created_at")
    list_filter = ("source__source_type",)
    search_fields = ("title", "content_hash")


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ("document", "chunk_index", "token_count", "created_at")
    search_fields = ("content",)
