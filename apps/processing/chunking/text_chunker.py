import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from .config import ChunkingConfig


@dataclass
class ChunkData:
    """Represents a generated text chunk with metadata and hierarchy info."""
    chunk_index: int
    content: str
    token_count: int
    heading: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    chunk_level: str = "child"  # "parent" or "child"
    parent_index: Optional[int] = None


class TextChunker:
    """
    Splits text into meaningful, size-bounded chunks using recursive separators
    while preserving heading breadcrumbs and page/timestamp segment provenance.
    """

    def __init__(self, config: Optional[ChunkingConfig] = None):
        self.config = config or ChunkingConfig()

    def estimate_tokens(self, text: str) -> int:
        """Rough token approximation (avg 4 characters per token)."""
        return max(1, math.ceil(len(text) / 4))

    def _extract_blocks(self, text: str) -> List[Dict[str, Any]]:
        """
        Decomposes document into semantic blocks: headings, code blocks, and natural paragraphs.
        Preserves complete code blocks and markdown sections without fragmentation while
        tracking active heading hierarchy stacks (# H1 > ## H2 > ### H3).
        """
        # Identify fenced code blocks first to protect them from splitting
        code_block_pattern = re.compile(r"(```[\s\S]*?```)", re.MULTILINE)
        parts = code_block_pattern.split(text)

        blocks: List[Dict[str, Any]] = []
        heading_stack: Dict[int, str] = {}
        current_breadcrumb = ""
        current_hierarchy: List[str] = []

        for part in parts:
            if not part:
                continue
            if part.startswith("```") and part.endswith("```"):
                # Treat entire code block as an indivisible semantic block
                blocks.append({
                    "type": "code",
                    "text": part.strip(),
                    "heading": current_breadcrumb,
                    "heading_hierarchy": list(current_hierarchy),
                })
            else:
                # Split text into paragraphs by blank lines
                raw_paragraphs = re.split(r"\n\s*\n", part)
                for para in raw_paragraphs:
                    cleaned_para = para.strip()
                    if not cleaned_para:
                        continue

                    # Check for markdown heading (# H1 to ###### H6) or module/chapter heading
                    first_line = cleaned_para.split("\n")[0].strip()
                    md_match = re.match(r"^(#{1,6})\s+(.+)$", first_line)
                    sec_match = re.match(
                        r"^(Module\s+\d+|Chapter\s+\d+|Section\s+\d+)[:\s]+(.+)$",
                        first_line,
                        re.IGNORECASE,
                    )

                    if md_match:
                        level = len(md_match.group(1))
                        title = md_match.group(2).strip()
                        # Prune equal or deeper levels from stack
                        heading_stack = {k: v for k, v in heading_stack.items() if k < level}
                        heading_stack[level] = title
                        current_breadcrumb = " > ".join(heading_stack[k] for k in sorted(heading_stack.keys()))
                        current_hierarchy = [heading_stack[k] for k in sorted(heading_stack.keys())]
                    elif sec_match:
                        level = 2
                        title = first_line
                        heading_stack = {k: v for k, v in heading_stack.items() if k < level}
                        heading_stack[level] = title
                        current_breadcrumb = " > ".join(heading_stack[k] for k in sorted(heading_stack.keys()))
                        current_hierarchy = [heading_stack[k] for k in sorted(heading_stack.keys())]

                    blocks.append({
                        "type": "text",
                        "text": cleaned_para,
                        "heading": current_breadcrumb,
                        "heading_hierarchy": list(current_hierarchy),
                    })
        return blocks

    def _group_blocks(
        self,
        blocks: List[Dict[str, Any]],
        target_size: int,
    ) -> List[Dict[str, Any]]:
        """
        Groups blocks up to target_size while tracking active heading breadcrumbs.
        Returns a list of dicts: {"text": str, "heading": str, "heading_hierarchy": List[str]}
        """
        if not blocks:
            return []

        chunks: List[Dict[str, Any]] = []
        current_chunk_parts: List[str] = []
        current_chunk_len = 0
        current_heading = ""
        current_hierarchy: List[str] = []

        for block in blocks:
            b_text = block["text"]
            b_len = len(b_text)
            b_heading = block.get("heading", "")
            b_hierarchy = block.get("heading_hierarchy", [])

            # If a single block exceeds target_size
            if b_len > target_size:
                if current_chunk_parts:
                    chunks.append({
                        "text": "\n\n".join(current_chunk_parts).strip(),
                        "heading": current_heading,
                        "heading_hierarchy": current_hierarchy,
                    })
                    current_chunk_parts = []
                    current_chunk_len = 0
                    current_heading = ""
                    current_hierarchy = []

                sub_lines = b_text.split("\n")
                sub_accum: List[str] = []
                sub_len = 0
                for line in sub_lines:
                    if sub_len + len(line) + 1 <= target_size:
                        sub_accum.append(line)
                        sub_len += len(line) + 1
                    else:
                        if sub_accum:
                            chunks.append({
                                "text": "\n".join(sub_accum).strip(),
                                "heading": b_heading,
                                "heading_hierarchy": b_hierarchy,
                            })
                            sub_accum = []
                            sub_len = 0
                        sub_accum.append(line)
                        sub_len = len(line)
                if sub_accum:
                    chunks.append({
                        "text": "\n".join(sub_accum).strip(),
                        "heading": b_heading,
                        "heading_hierarchy": b_hierarchy,
                    })
                continue

            projected_len = current_chunk_len + (2 if current_chunk_parts else 0) + b_len
            if projected_len <= target_size:
                if not current_chunk_parts:
                    current_heading = b_heading
                    current_hierarchy = b_hierarchy
                elif not current_heading and b_heading:
                    current_heading = b_heading
                    current_hierarchy = b_hierarchy
                current_chunk_parts.append(b_text)
                current_chunk_len = projected_len
            else:
                if current_chunk_parts:
                    chunks.append({
                        "text": "\n\n".join(current_chunk_parts).strip(),
                        "heading": current_heading,
                        "heading_hierarchy": current_hierarchy,
                    })
                current_chunk_parts = [b_text]
                current_chunk_len = b_len
                current_heading = b_heading
                current_hierarchy = b_hierarchy

        if current_chunk_parts:
            chunks.append({
                "text": "\n\n".join(current_chunk_parts).strip(),
                "heading": current_heading,
                "heading_hierarchy": current_hierarchy,
            })

        return chunks

    def _split_text(self, text: str, separators: Optional[List[str]] = None, chunk_size: Optional[int] = None) -> List[str]:
        """
        Paragraph & Semantic-Aware chunking:
        Groups cohesive paragraphs up to chunk_size without arbitrary mid-sentence cuts.
        """
        target_size = chunk_size or self.config.chunk_size
        blocks = self._extract_blocks(text)
        grouped = self._group_blocks(blocks, target_size)
        return [c["text"] for c in grouped]

    def _apply_overlap_to_chunks(
        self,
        raw_chunks: List[Dict[str, Any]],
        chunk_overlap: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Apply sliding window overlap across adjacent chunk dictionaries while preserving headings."""
        target_overlap = chunk_overlap if chunk_overlap is not None else self.config.chunk_overlap
        if target_overlap <= 0 or len(raw_chunks) <= 1:
            return raw_chunks

        overlapped = []
        for i, item in enumerate(raw_chunks):
            chunk_text = item["text"]
            if i == 0:
                overlapped.append(item)
            else:
                prev_text = raw_chunks[i - 1]["text"]
                overlap_text = prev_text[-target_overlap:]
                first_space = overlap_text.find(" ")
                if first_space != -1 and first_space < len(overlap_text) - 10:
                    overlap_text = overlap_text[first_space + 1 :]

                combined = (overlap_text + "\n" + chunk_text).strip()
                overlapped.append({
                    "text": combined,
                    "heading": item.get("heading", ""),
                    "heading_hierarchy": item.get("heading_hierarchy", []),
                })
        return overlapped

    def _apply_overlap(self, raw_chunks: List[str], chunk_overlap: Optional[int] = None) -> List[str]:
        """Apply sliding window overlap across adjacent string chunks."""
        target_overlap = chunk_overlap if chunk_overlap is not None else self.config.chunk_overlap
        if target_overlap <= 0 or len(raw_chunks) <= 1:
            return raw_chunks

        overlapped_chunks = []
        for i, chunk in enumerate(raw_chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
            else:
                prev_chunk = raw_chunks[i - 1]
                overlap_text = prev_chunk[-target_overlap:]
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
        Produce a list of ChunkData items from text, associating segments and hierarchical headings.
        """
        base_meta = base_metadata or {}
        if not text.strip():
            return []

        # 1. Split text into semantic blocks and group with heading tracking
        blocks = self._extract_blocks(text)
        raw_groups = self._group_blocks(blocks, self.config.chunk_size)

        # 2. Add overlap
        overlapped_groups = self._apply_overlap_to_chunks(raw_groups)

        # 3. Associate segment provenance and construct ChunkData
        result: List[ChunkData] = []
        search_start_pos = 0

        for idx, item in enumerate(overlapped_groups):
            chunk_text = item["text"]
            chunk_heading = item.get("heading", "")
            chunk_hierarchy = item.get("heading_hierarchy", [])

            chunk_meta = dict(base_meta)
            chunk_meta["char_length"] = len(chunk_text)
            chunk_meta["heading"] = chunk_heading
            chunk_meta["heading_hierarchy"] = chunk_hierarchy

            # Match overlapping segments if available
            if segments:
                matching_pages = set()
                matching_timestamps = []

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
                    heading=chunk_heading,
                    metadata=chunk_meta,
                )
            )

        return result

    def chunk_hierarchical(
        self,
        text: str,
        base_metadata: Optional[Dict[str, Any]] = None,
        segments: Optional[List[Any]] = None,
    ) -> Tuple[List[ChunkData], List[ChunkData]]:
        """
        Produce two-tier hierarchical chunks ("Small-to-Big" Retrieval):
        1. Parent Chunks: Larger context sections (e.g. 1200 chars) preserving section headings.
        2. Child Chunks: Tightly focused sub-chunks (e.g. 300 chars) retaining subsection breadcrumbs.

        Returns:
            Tuple[List[ChunkData], List[ChunkData]]: (parent_chunks, child_chunks)
        """
        base_meta = base_metadata or {}
        if not text.strip():
            return [], []

        # 1. Generate Parent Chunks with heading breadcrumb preservation
        blocks = self._extract_blocks(text)
        raw_parents = self._group_blocks(blocks, self.config.parent_chunk_size)
        overlapped_parents = self._apply_overlap_to_chunks(
            raw_parents, chunk_overlap=self.config.parent_chunk_overlap
        )

        parent_chunks: List[ChunkData] = []
        child_chunks: List[ChunkData] = []
        child_global_idx = 0

        for p_idx, p_item in enumerate(overlapped_parents):
            p_text = p_item["text"]
            p_heading = p_item.get("heading", "")
            p_hierarchy = p_item.get("heading_hierarchy", [])

            p_meta = dict(base_meta)
            p_meta["chunk_level"] = "parent"
            p_meta["char_length"] = len(p_text)
            p_meta["parent_index"] = p_idx
            p_meta["heading"] = p_heading
            p_meta["heading_hierarchy"] = p_hierarchy

            p_chunk = ChunkData(
                chunk_index=p_idx,
                content=p_text,
                token_count=self.estimate_tokens(p_text),
                heading=p_heading,
                metadata=p_meta,
                chunk_level="parent",
                parent_index=None,
            )
            parent_chunks.append(p_chunk)

            # 2. Generate Child Sub-Chunks from this Parent Chunk
            child_blocks = self._extract_blocks(p_text)
            raw_children = self._group_blocks(child_blocks, self.config.child_chunk_size)
            overlapped_children = self._apply_overlap_to_chunks(
                raw_children, chunk_overlap=self.config.child_chunk_overlap
            )

            if not overlapped_children:
                overlapped_children = [{
                    "text": p_text,
                    "heading": p_heading,
                    "heading_hierarchy": p_hierarchy,
                }]

            for c_idx, c_item in enumerate(overlapped_children):
                c_text = c_item["text"]
                # Child chunk retains its own detected subheading or inherits parent's heading
                c_heading = c_item.get("heading") or p_heading
                c_hierarchy = c_item.get("heading_hierarchy") or p_hierarchy

                c_meta = dict(base_meta)
                c_meta["chunk_level"] = "child"
                c_meta["char_length"] = len(c_text)
                c_meta["parent_chunk_index"] = p_idx
                c_meta["child_local_index"] = c_idx
                c_meta["heading"] = c_heading
                c_meta["heading_hierarchy"] = c_hierarchy

                c_chunk = ChunkData(
                    chunk_index=child_global_idx,
                    content=c_text,
                    token_count=self.estimate_tokens(c_text),
                    heading=c_heading,
                    metadata=c_meta,
                    chunk_level="child",
                    parent_index=p_idx,
                )
                child_chunks.append(c_chunk)
                child_global_idx += 1

        return parent_chunks, child_chunks
