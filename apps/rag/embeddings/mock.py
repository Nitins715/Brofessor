import hashlib
import math
from typing import List, Optional
from django.conf import settings
from .base import BaseEmbeddingProvider


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic mock embedding provider for fast unit tests and offline testing.
    Generates consistent, unit-normalized 384-dimensional vectors based on text hashes.
    """

    def __init__(self, dimension: Optional[int] = None):
        self._dimension = dimension or getattr(settings, "EMBEDDING_DIMENSIONS", 384)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return "mock-deterministic-bge-384"

    def embed_text(self, text: str) -> List[float]:
        if not text or not text.strip():
            return [0.0] * self._dimension

        # Derive seed from text
        h = hashlib.sha256(text.encode("utf-8")).digest()
        raw_vec = []
        for i in range(self._dimension):
            byte_val = h[i % len(h)]
            multiplier = 1.0 if (i % 2 == 0) else -1.0
            raw_vec.append(multiplier * (byte_val / 255.0))

        # L2-normalize to unit length for accurate cosine distance testing
        norm = math.sqrt(sum(x * x for x in raw_vec)) or 1.0
        return [float(x / norm) for x in raw_vec]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        return [self.embed_text(t) for t in texts]
