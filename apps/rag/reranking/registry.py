from typing import Optional
from django.conf import settings
from .base import BaseReranker
from .score_fusion import LexicalVectorReranker
from .mock import MockReranker


def get_reranker(provider_name: Optional[str] = None) -> BaseReranker:
    """
    Factory resolving the active reranker provider.
    Supported: 'lexical_vector', 'mock'.
    """
    provider = provider_name or getattr(settings, "RAG_RERANKER_PROVIDER", "lexical_vector")
    normalized = provider.lower().strip()

    if normalized in ("mock", "test"):
        return MockReranker()
    elif normalized in ("lexical_vector", "score_fusion", "default"):
        return LexicalVectorReranker()
    else:
        return LexicalVectorReranker()
