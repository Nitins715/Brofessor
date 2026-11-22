from pathlib import Path
from typing import Any
from django.conf import settings
from .base import BaseExtractor, ExtractionResult, ContentSegment


class TextExtractor(BaseExtractor):
    """Extractor for user-provided text, notes, markdown files, and manual knowledge."""

    def extract(self, source: Any) -> ExtractionResult:
        metadata = source.metadata or {}
        raw_text = (
            metadata.get("content")
            or metadata.get("text")
            or metadata.get("note")
            or metadata.get("body")
            or ""
        )

        # If metadata text is empty, check if source.file_path points to an on-disk markdown/text file
        if not raw_text.strip() and getattr(source, "file_path", None):
            file_path = Path(source.file_path)
            if not file_path.is_absolute():
                candidate = Path(settings.MEDIA_ROOT) / source.file_path
                if candidate.exists():
                    file_path = candidate
                elif (Path(settings.BASE_DIR) / source.file_path).exists():
                    file_path = Path(settings.BASE_DIR) / source.file_path
                elif file_path.exists():
                    file_path = file_path.resolve()
                else:
                    file_path = candidate

            if file_path.exists():
                try:
                    raw_text = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception as exc:
                    raise ValueError(f"Failed to read file at {file_path}: {exc}") from exc

        if not raw_text.strip():
            raise ValueError(
                f"No text content found in metadata or file for Source '{source.name}' ({source.id}). "
                "Expected 'content'/'text' in metadata or valid 'file_path'."
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
