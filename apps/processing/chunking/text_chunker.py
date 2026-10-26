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

    def _extract_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Decomposes document into semantic blocks: headings, code blocks, and natural paragraphs.
        Preserves complete code blocks and markdown sections without fragmentation.
        """
        import re

        # Identify fenced code blocks first to protect them from splitting
        code_block_pattern = re.compile(r"(```[\s\S]*?```)", re.MULTILINE)
        parts = code_block_pattern.split(text)

        blocks: List[Dict[str, Any]] = []
        current_heading = ""

        for part in parts:
            if not part:
                continue
            if part.startswith("```") and part.endswith("```"):
                # Treat entire code block as an indivisible semantic block
                blocks.append({
                    "type": "code",
                    "text": part.strip(),
                    "heading": current_heading,
                })
            else:
                # Split text into paragraphs by blank lines
                raw_paragraphs = re.split(r"\n\s*\n", part)
                for para in raw_paragraphs:
                    cleaned_para = para.strip()
                    if not cleaned_para:
                        continue
                    # Check if paragraph is a markdown heading
                    if cleaned_para.startswith("#"):
                        current_heading = cleaned_para.split("\n")[0].strip("# \t")
                    blocks.append({
                        "type": "text",
                        "text": cleaned_para,
                        "heading": current_heading,
                    })
        return blocks

    def _split_text(self, text: str, separators: List[str]) -> List[str]:
        """
        Paragraph & Semantic-Aware chunking:
        Groups cohesive paragraphs up to chunk_size without arbitrary mid-sentence cuts.
        """
        blocks = self._extract_blocks(text)
        if not blocks:
            return []

        chunks: List[str] = []
        current_chunk_parts: List[str] = []
        current_chunk_len = 0

        for block in blocks:
            b_text = block["text"]
            b_len = len(b_text)

            # If a single block (e.g. large code block or huge paragraph) exceeds chunk_size
            if b_len > self.config.chunk_size:
                # Flush existing chunk parts
                if current_chunk_parts:
                    chunks.append("\n\n".join(current_chunk_parts).strip())
                    current_chunk_parts = []
                    current_chunk_len = 0

                # Split large block by sentence or newline boundaries
                sub_lines = b_text.split("\n")
                sub_accum: List[str] = []
                sub_len = 0
                for line in sub_lines:
                    if sub_len + len(line) + 1 <= self.config.chunk_size:
                        sub_accum.append(line)
                        sub_len += len(line) + 1
                    else:
                        if sub_accum:
                            chunks.append("\n".join(sub_accum).strip())
                            sub_accum = []
                            sub_len = 0
                        sub_accum.append(line)
                        sub_len = len(line)
                if sub_accum:
                    chunks.append("\n".join(sub_accum).strip())
                continue

            # Check if adding this block fits within the chunk size
            projected_len = current_chunk_len + (2 if current_chunk_parts else 0) + b_len
            if projected_len <= self.config.chunk_size:
                current_chunk_parts.append(b_text)
                current_chunk_len = projected_len
            else:
                if current_chunk_parts:
                    chunks.append("\n\n".join(current_chunk_parts).strip())
                current_chunk_parts = [b_text]
                current_chunk_len = b_len

        if current_chunk_parts:
            chunks.append("\n\n".join(current_chunk_parts).strip())

        return chunks

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
