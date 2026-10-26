import logging
from typing import List, Optional
from django.conf import settings
from .base import BaseEmbeddingProvider

logger = logging.getLogger("brofessor")


class HuggingFaceEmbeddingProvider(BaseEmbeddingProvider):
    """
    Default embedding provider using local ONNX execution via fastembed.
    Model: BAAI/bge-small-en-v1.5 (384 dimensions).
    """

    _model_instance = None

    def __init__(self, model_name: Optional[str] = None):
        self._model_name = model_name or getattr(
            settings, "EMBEDDING_MODEL", "BAAI/bge-small-en-v1.5"
        )
        self._dimension = getattr(settings, "EMBEDDING_DIMENSIONS", 384)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model_name

    def _get_model(self):
        """Lazy-load and cache the embedding model instance."""
        if HuggingFaceEmbeddingProvider._model_instance is None:
            logger.info(f"Loading local HuggingFace embedding model: {self._model_name}")
            try:
                from fastembed import TextEmbedding
                HuggingFaceEmbeddingProvider._model_instance = TextEmbedding(
                    model_name=self._model_name
                )
            except Exception as e:
                logger.error(f"Failed to load fastembed model '{self._model_name}': {e}", exc_info=True)
                raise
        return HuggingFaceEmbeddingProvider._model_instance

    def embed_text(self, text: str) -> List[float]:
        """Embed a single text string."""
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * self._dimension

        batch_result = self.embed_batch([text])
        return batch_result[0]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of text strings."""
        if not texts:
            return []

        # Sanitize texts: replace empty or whitespace-only strings with a space
        cleaned_texts = [t if (t and t.strip()) else " " for t in texts]

        model = self._get_model()
        try:
            # model.embed returns a generator of numpy arrays
            raw_embeddings = model.embed(cleaned_texts)
            results = [[float(v) for v in vector] for vector in raw_embeddings]
            return results
        except Exception as e:
            logger.error(f"Error generating embeddings for batch size {len(texts)}: {e}", exc_info=True)
            raise
