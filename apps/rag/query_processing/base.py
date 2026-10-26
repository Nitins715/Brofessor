from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class ProcessedQuery:
    """Represents a sanitized and optionally expanded/transformed query for retrieval."""
    original_query: str
    retrieval_query: str
    is_rewritten: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class BaseQueryProcessor(ABC):
    """Abstract interface for query processing, cleaning, and rewriting."""

    @abstractmethod
    def process(self, query: str, **kwargs) -> ProcessedQuery:
        """Process and transform the user query for downstream retrieval."""
        pass
