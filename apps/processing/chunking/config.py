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
