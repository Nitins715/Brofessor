import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .config import ChunkingConfig


@dataclass
class ChunkData:
    """Represents a generated text chunk with metadata."""
    chunk_index: int
    content: str
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


class TextChunker:
    """
    Splits text into meaningful, size-bounded chunks using recursive separators
    while preserving page/timestamp segment provenance.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()

    def estimate_tokens(self, text: str) -> int:
        """Rough token approximation (avg 4 characters per token)."""
        return max(1, math.ceil(len(text) / 4))

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """Recursively split text by separators until pieces fit within chunk_size."""
        final_chunks: List[str] = []

        if not text:
            return final_chunks

        # Find the highest-priority separator present in text
        separator = ""
        new_separators: List[str] = []
        for i, sep in enumerate(separators):
            if sep == "":
                separator = ""
                break
            if sep in text:
                separator = sep
                new_separators = separators[i + 1 :]
                break

        splits = text.split(separator) if separator else list(text)

        current_doc: List[str] = []
        total_len = 0

        for s in splits:
            s_len = len(s) + (len(separator) if current_doc else 0)
            if total_len + s_len <= self.config.chunk_size:
                current_doc.append(s)
                total_len += s_len
            else:
                if current_doc:
                    doc_text = separator.join(current_doc).strip()
                    if doc_text:
                        final_chunks.append(doc_text)
                    current_doc = []
                    total_len = 0

                # If single split item exceeds chunk_size, recurse with next separator
                if len(s) > self.config.chunk_size:
                    if new_separators:
                        sub_chunks = self._split_text(s, new_separators)
                        final_chunks.extend(sub_chunks)
                    else:
                        # Hard character boundary split
                        for start_idx in range(0, len(s), self.config.chunk_size):
                            piece = s[start_idx : start_idx + self.config.chunk_size].strip()
                            if piece:
                                final_chunks.append(piece)
                else:
                    current_doc.append(s)
                    total_len = len(s)

        if current_doc:
            doc_text = separator.join(current_doc).strip()
            if doc_text:
                final_chunks.append(doc_text)

        return final_chunks

    def _apply_overlap(self, raw_chunks: List[str]) -> List[str]:
        """Apply sliding window overlap across adjacent chunks."""
        if self.config.chunk_overlap <= 0 or len(raw_chunks) <= 1:
            return raw_chunks

        overlapped_chunks = []
        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                prev_chunk = raw_chunks[i - 1]
                overlap_text = prev_chunk[-self.config.chunk_overlap :]
                # Break clean on space if possible
                first_space = overlap_text.find(" ")
                if first_space != -1 and first_space < len(overlap_text) - 10:
                    overlap_text = overlap_text[first_space + 1 :]

                combined = (overlap_text + "\n" + chunk).strip()
                overlapped_chunks.append(combined)

        return overlapped_chunks

    def chunk(
        self,
        text: str,
        base_metadata: Optional[Dict[str, Any]] = None,
        segments: Optional[List[Any]] = None,
    ) -> List[ChunkData]:
        """
        Produce a list of ChunkData items from text, associating segments (e.g. pages or timestamps).
        """
        base_meta = base_metadata or {}
        if not text.strip():
            return []

        # 1. Split text into chunks
        raw_pieces = self._split_text(text, self.config.separators)

        # 2. Add overlap
        chunk_strings = self._apply_overlap(raw_pieces)

        # 3. Associate segment provenance (e.g. page numbers or video timestamps)
        result: List[ChunkData] = []
        search_start_pos = 0

        for idx, chunk_text in enumerate(chunk_strings):
            chunk_meta = dict(base_meta)
            chunk_meta["char_length"] = len(chunk_text)

            # Match overlapping segments if available
            if segments:
                matching_pages = set()
                matching_timestamps = []

                # Find chunk in full text
                found_idx = text.find(chunk_text[:50], search_start_pos)
                if found_idx == -1:
                    found_idx = text.find(chunk_text[:30])
                if found_idx != -1:
                    search_start_pos = found_idx
                    chunk_end_idx = found_idx + len(chunk_text)
                else:
                    chunk_end_idx = search_start_pos + len(chunk_text)

                curr_pos = 0
                for seg in segments:
                    seg_len = len(seg.text)
                    seg_start = curr_pos
                    seg_end = curr_pos + seg_len
                    curr_pos = seg_end

                    # Check if segment overlaps with chunk
                    if not (seg_end < search_start_pos or seg_start > chunk_end_idx):
                        seg_meta = getattr(seg, "metadata", {})
                        if "page" in seg_meta:
                            matching_pages.add(seg_meta["page"])
                        if "timestamp" in seg_meta:
                            matching_timestamps.append(seg_meta["timestamp"])

                if matching_pages:
                    chunk_meta["pages"] = sorted(list(matching_pages))
                if matching_timestamps:
                    chunk_meta["timestamps"] = matching_timestamps[:3]

            result.append(
                ChunkData(
                    chunk_index=idx,
                    content=chunk_text,
                    token_count=self.estimate_tokens(chunk_text),
                    metadata=chunk_meta,
                )
            )

        return result
