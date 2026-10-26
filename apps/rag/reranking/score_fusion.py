from __future__ import annotations
import re
from typing import TYPE_CHECKING, Any, List, Set
if TYPE_CHECKING:
    from apps.rag.services.retrieval import SearchResult
from .base import BaseReranker, RerankResult


class LexicalVectorReranker(BaseReranker):
    """
    Hybrid scoring reranker combining dense vector similarity with lexical keyword overlap.
    Boosts chunks that have both high semantic vector similarity and exact keyword matches,
    then returns the top_k most relevant chunks.
    """

    def __init__(self, vector_weight: float = 0.65):
        self.vector_weight = vector_weight
        self.lexical_weight = 1.0 - vector_weight

    def _tokenize(self, text: str) -> Set[str]:
        """Extract lowercase alphanumeric tokens."""
        if not text:
            return set()
        return set(re.findall(r"\b\w{2,}\b", text.lower()))

    def _compute_lexical_overlap(self, query_tokens: Set[str], content: str) -> float:
        """Compute proportion of query terms matched in candidate content."""
        if not query_tokens:
            return 0.0
        content_tokens = self._tokenize(content)
        if not content_tokens:
            return 0.0
        matched = query_tokens.intersection(content_tokens)
        return len(matched) / len(query_tokens)

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 4,
    ) -> List[RerankResult]:
        if not results:
            return []

        query_tokens = self._tokenize(query)
        scored: List[RerankResult] = []

        for idx, item in enumerate(results):
            original_rank = idx + 1
            lex_score = self._compute_lexical_overlap(query_tokens, item.content)
            vec_score = max(0.0, min(1.0, item.similarity_score))

            fused_score = (self.vector_weight * vec_score) + (self.lexical_weight * lex_score)

            scored.append(
                RerankResult(
                    search_result=item,
                    rerank_score=fused_score,
                    original_rank=original_rank,
                    new_rank=0,
                )
            )

        # Sort descending by fused rerank score
        scored.sort(key=lambda x: x.rerank_score, reverse=True)

        # Slice to top_k and assign final ranks
        top_results = scored[:top_k]
        for rank_idx, res in enumerate(top_results, start=1):
            res.new_rank = rank_idx

        return top_results
