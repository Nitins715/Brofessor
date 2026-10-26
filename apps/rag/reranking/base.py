from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from apps.rag.services.retrieval import SearchResult


@dataclass
class RerankResult:
    """Represents a reranked search result with updated relevance ranking and score."""
    search_result: Any
    rerank_score: float
    original_rank: int
    new_rank: int

    def to_dict(self) -> Dict[str, Any]:
        data = self.search_result.to_dict()
        data["rerank_score"] = round(self.rerank_score, 4)
        data["original_rank"] = self.original_rank
        data["rank"] = self.new_rank
        return data


class BaseReranker(ABC):
    """Abstract interface for reranking candidate search results."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        results: List[SearchResult],
        top_k: int = 4,
    ) -> List[RerankResult]:
        """Rerank candidate search results and return top_k items."""
        pass
