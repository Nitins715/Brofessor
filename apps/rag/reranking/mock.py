from __future__ import annotations
from typing import TYPE_CHECKING, Any, List, Optional
if TYPE_CHECKING:
    from apps.rag.services.retrieval import SearchResult
from .base import BaseReranker, RerankResult


class MockReranker(BaseReranker):
    """
    Deterministic mock reranker for testing.
    Can optionally reverse rankings, apply custom fixed scores, or select top_k.
    """

    def __init__(self, reverse: bool = False, fixed_score: Optional[float] = None):
        self.reverse = reverse
        self.fixed_score = fixed_score

    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 4,
    ) -> List[RerankResult]:
        if not results:
            return []

        candidates = list(results)
        if self.reverse:
            candidates.reverse()

        reranked: List[RerankResult] = []
        for new_idx, item in enumerate(candidates[:top_k], start=1):
            score = (
                self.fixed_score
                if self.fixed_score is not None
                else item.similarity_score
            )
            # Find original rank (1-indexed) in unreversed results
            orig_idx = results.index(item) + 1 if item in results else new_idx
            reranked.append(
                RerankResult(
                    search_result=item,
                    rerank_score=score,
                    original_rank=orig_idx,
                    new_rank=new_idx,
                )
            )

        return reranked
