from typing import Dict, Type
from .base import BaseExtractor
from .text import TextExtractor
from .pdf import PDFExtractor
from .article import ArticleExtractor
from .youtube import YouTubeExtractor

EXTRACTOR_MAPPING: Dict[str, Type[BaseExtractor]] = {
    "note": TextExtractor,
    "manual": TextExtractor,
    "pdf": PDFExtractor,
    "article": ArticleExtractor,
    "youtube": YouTubeExtractor,
}


def get_extractor_for_source(source_type: str) -> BaseExtractor:
    """Resolve and instantiate the proper content extractor for a source type."""
    extractor_cls = EXTRACTOR_MAPPING.get(source_type.lower())
    if not extractor_cls:
        raise NotImplementedError(
            f"No extractor registered for source type '{source_type}'. "
            f"Supported types: {list(EXTRACTOR_MAPPING.keys())}"
        )
    return extractor_cls()
