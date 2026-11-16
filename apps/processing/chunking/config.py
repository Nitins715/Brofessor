from dataclasses import dataclass, field
from typing import List
from django.conf import settings


@dataclass
class ChunkingConfig:
    """Configurable settings for document splitting and overlap."""
    chunk_size: int = field(
        default_factory=lambda: getattr(settings, "CHUNK_SIZE", 1000)
    )
    chunk_overlap: int = field(
        default_factory=lambda: getattr(settings, "CHUNK_OVERLAP", 200)
    )
    separators: List[str] = field(
        default_factory=lambda: ["\n\n", "\n", ". ", "! ", "? ", "; ", " ", ""]
    )
    min_chunk_size: int = 50

    # Hierarchical / Small-to-Big Retrieval settings
    enable_hierarchical: bool = field(
        default_factory=lambda: getattr(settings, "RAG_ENABLE_HIERARCHICAL", True)
    )
    parent_chunk_size: int = field(
        default_factory=lambda: getattr(settings, "RAG_PARENT_CHUNK_SIZE", 1200)
    )
    parent_chunk_overlap: int = field(
        default_factory=lambda: getattr(settings, "RAG_PARENT_CHUNK_OVERLAP", 150)
    )
    child_chunk_size: int = field(
        default_factory=lambda: getattr(settings, "RAG_CHILD_CHUNK_SIZE", 300)
    )
    child_chunk_overlap: int = field(
        default_factory=lambda: getattr(settings, "RAG_CHILD_CHUNK_OVERLAP", 50)
    )
