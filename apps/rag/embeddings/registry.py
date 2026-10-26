from typing import Dict, Optional, Type
from django.conf import settings
from .base import BaseEmbeddingProvider
from .huggingface import HuggingFaceEmbeddingProvider
from .mock import MockEmbeddingProvider

PROVIDER_REGISTRY: Dict[str, Type[BaseEmbeddingProvider]] = {
    "huggingface": HuggingFaceEmbeddingProvider,
    "hf": HuggingFaceEmbeddingProvider,
    "mock": MockEmbeddingProvider,
}


def get_embedding_provider(provider_type: Optional[str] = None) -> BaseEmbeddingProvider:
    """
    Factory function to retrieve the configured embedding provider.
    Defaults to settings.EMBEDDING_PROVIDER ('huggingface').
    """
    key = (provider_type or getattr(settings, "EMBEDDING_PROVIDER", "huggingface")).lower()
    provider_cls = PROVIDER_REGISTRY.get(key)
    if not provider_cls:
        raise ValueError(
            f"Unknown embedding provider '{key}'. Registered providers: {list(PROVIDER_REGISTRY.keys())}"
        )
    return provider_cls()
