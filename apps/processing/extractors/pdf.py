import os
from pathlib import Path
from typing import Any
from django.conf import settings
from pypdf import PdfReader
from .base import BaseExtractor, ExtractionResult, ContentSegment


class PDFExtractor(BaseExtractor):
    """Extractor for local PDF files with page-level metadata preservation."""

    def extract(self, source: Any) -> ExtractionResult:
        file_path_str = source.file_path
        if not file_path_str:
            raise ValueError(f"Source '{source.name}' ({source.id}) has no file_path specified.")

        # Resolve path against MEDIA_ROOT if relative
        file_path = Path(file_path_str)
        if not file_path.is_absolute():
            file_path = Path(settings.MEDIA_ROOT) / file_path_str

        if not file_path.exists():
            raise FileNotFoundError(f"PDF file does not exist at resolved path: {file_path}")

        try:
            reader = PdfReader(str(file_path))
        except Exception as e:
            raise ValueError(f"Failed to open/parse PDF at {file_path}: {str(e)}") from e

        total_pages = len(reader.pages)
        if total_pages == 0:
            raise ValueError(f"PDF at {file_path} contains 0 pages.")

        page_segments = []
        full_text_parts = []

        for idx, page in enumerate(reader.pages, start=1):
            try:
                page_text = page.extract_text() or ""
            except Exception:
                page_text = ""

            page_text_clean = page_text.strip()
            if page_text_clean:
                full_text_parts.append(page_text_clean)
                page_segments.append(
                    ContentSegment(
                        text=page_text_clean,
                        metadata={
                            "page": idx,
                            "page_count": total_pages,
                        },
                    )
                )

        full_text = "\n\n".join(full_text_parts)
        if not full_text.strip():
            raise ValueError(
                f"PDF at {file_path} could not be extracted into readable text (empty or scanned/image-only)."
            )

        # Extract title from PDF metadata if available, else source.name
        pdf_meta = reader.metadata or {}
        extracted_title = pdf_meta.title if getattr(pdf_meta, "title", None) else None
        title = extracted_title or source.name or file_path.stem

        return ExtractionResult(
            title=title,
            text=full_text,
            metadata={
                "file_path": str(file_path),
                "file_name": file_path.name,
                "file_size_bytes": file_path.stat().st_size,
                "page_count": total_pages,
                "author": getattr(pdf_meta, "author", None),
            },
            segments=page_segments,
        )
