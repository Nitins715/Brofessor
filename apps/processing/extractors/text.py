from typing import Any
from .base import BaseExtractor, ExtractionResult, ContentSegment


class TextExtractor(BaseExtractor):
    """Extractor for user-provided text, notes, and manual knowledge."""

    def extract(self, source: Any) -> ExtractionResult:
        metadata = source.metadata or {}
        raw_text = (
            metadata.get("content")
            or metadata.get("text")
            or metadata.get("note")
            or metadata.get("body")
            or ""
        )

        if not raw_text.strip():
            raise ValueError(
                f"No text content found in metadata for Source '{source.name}' ({source.id}). "
                "Expected 'content' or 'text' field."
            )

        title = metadata.get("title") or source.name or "Untitled Note"

        return ExtractionResult(
            title=title,
            text=raw_text,
            metadata={
                "source_type": source.source_type,
                "author": metadata.get("author", "User"),
                "tags": metadata.get("tags", []),
            },
            segments=[
                ContentSegment(
                    text=raw_text,
                    metadata={"segment_index": 0},
                )
            ],
        )
