from abc import ABC, abstractmethod
from typing import List


class BaseEmbeddingProvider(ABC):
    """Abstract interface for all embedding model providers."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector dimensionality of the output embeddings."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Canonical model name or identifier."""
        pass

    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate a dense vector embedding for a single text query or chunk."""
        pass

    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vector embeddings for a batch of texts."""
        pass
