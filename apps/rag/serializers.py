from rest_framework import serializers


class VectorSearchRequestSerializer(serializers.Serializer):
    """Payload for executing a vector similarity query."""
    query = serializers.CharField(required=True, allow_blank=False, max_length=2000)
    top_k = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    source_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
        help_text="Optional filter by source types (e.g. ['note', 'pdf', 'youtube', 'article']).",
    )
    source_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="Optional list of Source UUIDs to restrict the search.",
    )
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
        help_text="Optional list of Document UUIDs to restrict the search.",
    )
    min_similarity = serializers.FloatField(
        required=False,
        default=None,
        min_value=0.0,
        max_value=1.0,
        help_text="Optional minimum similarity cutoff (0.0 to 1.0).",
    )


class SearchResultItemSerializer(serializers.Serializer):
    """Individual vector search match item."""
    chunk_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    content = serializers.CharField()
    similarity_score = serializers.FloatField()
    distance = serializers.FloatField()
    document = serializers.DictField()
    source = serializers.DictField()
    metadata = serializers.DictField()


class VectorSearchResponseSerializer(serializers.Serializer):
    """Response envelope for vector similarity search."""
    query = serializers.CharField()
    total_results = serializers.IntegerField()
    results = SearchResultItemSerializer(many=True)


class EmbedSourceResponseSerializer(serializers.Serializer):
    """Response after triggering embedding generation for a source."""
    source_id = serializers.CharField()
    embedded_chunks = serializers.IntegerField()
    status = serializers.CharField()


class CitationSerializer(serializers.Serializer):
    """Detailed attribution reference for a chunk used in answering."""
    chunk_id = serializers.CharField()
    chunk_index = serializers.IntegerField()
    document = serializers.DictField()
    source = serializers.DictField()
    rank = serializers.IntegerField()
    similarity_score = serializers.FloatField()
    rerank_score = serializers.FloatField(required=False, allow_null=True)
    page = serializers.IntegerField(required=False, allow_null=True)
    timestamp = serializers.CharField(required=False, allow_null=True)
    snippet = serializers.CharField()


class RAGChatRequestSerializer(serializers.Serializer):
    """Request payload for querying stored knowledge via the RAG pipeline."""
    query = serializers.CharField(required=True, allow_blank=False, max_length=2000)
    conversation_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    domain_id = serializers.UUIDField(required=False, allow_null=True, default=None)
    retrieval_top_k = serializers.IntegerField(required=False, default=10, min_value=1, max_value=50)
    rerank_top_k = serializers.IntegerField(required=False, default=4, min_value=1, max_value=20)
    source_types = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    source_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    document_ids = serializers.ListField(
        child=serializers.UUIDField(),
        required=False,
        default=list,
    )
    min_similarity = serializers.FloatField(
        required=False,
        default=None,
        min_value=0.0,
        max_value=1.0,
    )


class RAGChatResponseSerializer(serializers.Serializer):
    """Full response envelope containing answer, citations, and conversation linkage."""
    conversation_id = serializers.CharField()
    message_id = serializers.CharField()
    query = serializers.CharField()
    answer = serializers.CharField()
    citations = CitationSerializer(many=True)
    retrieved_count = serializers.IntegerField()
    reranked_count = serializers.IntegerField()
    tokens_used = serializers.IntegerField(allow_null=True)
    error = serializers.CharField(allow_null=True, required=False)
    metadata = serializers.DictField()


class MessageDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    role = serializers.CharField()
    content = serializers.CharField()
    tokens_used = serializers.IntegerField(allow_null=True)
    created_at = serializers.DateTimeField()
    metadata = serializers.DictField()


class ConversationDetailSerializer(serializers.Serializer):
    id = serializers.UUIDField()
    title = serializers.CharField()
    domain_id = serializers.UUIDField(allow_null=True)
    metadata = serializers.DictField()
    created_at = serializers.DateTimeField()
    updated_at = serializers.DateTimeField()
    messages = MessageDetailSerializer(many=True)


