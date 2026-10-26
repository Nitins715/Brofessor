"""Embedding provider abstraction and registry."""

from .base import BaseEmbeddingProvider
from .huggingface import HuggingFaceEmbeddingProvider
from .mock import MockEmbeddingProvider
from .registry import get_embedding_provider

__all__ = [
    "BaseEmbeddingProvider",
    "HuggingFaceEmbeddingProvider",
    "MockEmbeddingProvider",
    "get_embedding_provider",
]
