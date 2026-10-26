from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ContentSegment:
    """Sub-unit of extracted content with localized metadata (e.g. page number or timestamp)."""
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExtractionResult:
    """Normalized payload resulting from extracting content from a Source."""
    title: str
    text: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    segments: List[ContentSegment] = field(default_factory=list)


class BaseExtractor(ABC):
    """Abstract interface for all source content extractors."""

    @abstractmethod
    def extract(self, source: Any) -> ExtractionResult:
        """
        Extract raw content from the given Source model instance.
        Must return an ExtractionResult or raise an informative Exception.
        """
        pass
