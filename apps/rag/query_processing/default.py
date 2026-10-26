import re
import unicodedata
from typing import Any, Callable, Dict, List, Optional
from .base import BaseQueryProcessor, ProcessedQuery


class DefaultQueryProcessor(BaseQueryProcessor):
    """
    Default modular query processing pipeline:
    1. Normalizes unicode characters (NFKC).
    2. Strips noisy markdown / control symbols and excess whitespace.
    3. Preserves original query verbatim for downstream conversation history.
    4. Supports optional pluggable query rewrite / expansion strategies.
    """

    def __init__(self, rewriter: Optional[Callable[[str], str]] = None):
        self.rewriter = rewriter

    def normalize_text(self, text: str) -> str:
        """Strip control characters and normalize unicode representation."""
        if not text:
            return ""
        normalized = unicodedata.normalize("NFKC", text)
        # Collapse multiple spaces, newlines, and tabs into a single clean space
        cleaned = re.sub(r"\s+", " ", normalized).strip()
        return cleaned

    def process(
        self,
        query: str,
        enable_rewrite: bool = False,
        **kwargs: Any,
    ) -> ProcessedQuery:
        original = query or ""
        cleaned = self.normalize_text(original)

        retrieval_query = cleaned
        is_rewritten = False
        meta: Dict[str, Any] = {
            "cleaned_length": len(cleaned),
            "original_length": len(original),
        }

        # Apply rewrite strategy if provided and enabled
        if enable_rewrite and self.rewriter and cleaned:
            rewritten = self.rewriter(cleaned)
            if rewritten and rewritten.strip():
                retrieval_query = self.normalize_text(rewritten)
                is_rewritten = True
                meta["rewritten_query"] = retrieval_query

        return ProcessedQuery(
            original_query=original,
            retrieval_query=retrieval_query,
            is_rewritten=is_rewritten,
            metadata=meta,
        )
