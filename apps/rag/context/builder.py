from __future__ import annotations
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Set, Union
from django.conf import settings

if TYPE_CHECKING:
    from apps.rag.services.retrieval import SearchResult
    from apps.rag.reranking.base import RerankResult


@dataclass
class Citation:
    """Detailed attribution and provenance for a chunk used in context construction."""
    chunk_id: str
    chunk_index: int
    document_id: str
    document_title: str
    source_id: str
    source_name: str
    source_type: str
    source_uri: str
    rank: int
    similarity_score: float
    rerank_score: Optional[float] = None
    page: Optional[int] = None
    timestamp: Optional[str] = None
    snippet: str = ""
    content: str = ""
    parent_chunk_id: Optional[str] = None
    parent_content: Optional[str] = None
    chunk_level: str = "child"
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "document": {
                "id": self.document_id,
                "title": self.document_title,
            },
            "source": {
                "id": self.source_id,
                "name": self.source_name,
                "source_type": self.source_type,
                "uri": self.source_uri,
            },
            "rank": self.rank,
            "similarity_score": round(self.similarity_score, 4),
            "snippet": self.snippet,
            "content": self.content or self.snippet,
            "parent_chunk_id": self.parent_chunk_id,
            "chunk_level": self.chunk_level,
        }

        if self.rerank_score is not None:
            data["rerank_score"] = round(self.rerank_score, 4)
        if self.page is not None:
            data["page"] = self.page
        if self.timestamp is not None:
            data["timestamp"] = self.timestamp
        return data


@dataclass
class ConstructedContext:
    """Structured context ready for LLM prompt injection with provenance."""
    formatted_text: str
    citations: List[Citation]
    total_chunks: int
    total_chars: int
    truncated: bool = False


class ContextBuilder:
    """
    Assembles, deduplicates, and limits context chunks for LLM consumption.
    Implements Hierarchical / Small-to-Big Retrieval:
    Injects full parent section context while preserving fine-grained child citations.
    """

    def __init__(self, max_chars: Optional[int] = None, enable_small_to_big: bool = True):
        self.max_chars = max_chars or getattr(settings, "RAG_MAX_CONTEXT_CHARS", 4000)
        self.enable_small_to_big = enable_small_to_big

    def build(
        self,
        items: List[Any],
        graph_context: Optional[str] = None,
    ) -> ConstructedContext:
        if not items and not graph_context:
            return ConstructedContext(
                formatted_text="",
                citations=[],
                total_chunks=0,
                total_chars=0,
                truncated=False,
            )

        citations: List[Citation] = []
        context_blocks: List[str] = []
        seen_parent_keys: Set[str] = set()
        current_chars = 0
        is_truncated = False

        # 1. Prepend Multi-Hop Knowledge Graph relational context if available
        if graph_context and graph_context.strip():
            graph_block = f"--- Knowledge Graph Relational Connections ---\n{graph_context.strip()}\n"
            context_blocks.append(graph_block)
            current_chars += len(graph_block)

        for rank_idx, item in enumerate(items, start=1):
            # Normalize item access whether RerankResult or SearchResult
            if hasattr(item, "search_result"):
                search_res = item.search_result
                rerank_score = getattr(item, "rerank_score", None)
                rank = getattr(item, "new_rank", None) or rank_idx
            else:
                search_res = item
                rerank_score = None
                rank = rank_idx

            clean_content = search_res.content.strip()
            parent_content = (getattr(search_res, "parent_content", None) or "").strip() if self.enable_small_to_big else ""
            parent_id = getattr(search_res, "parent_chunk_id", None)

            # Small-to-Big: expand to comprehensive parent section context if available
            use_parent = bool(parent_content and parent_id)
            effective_content = parent_content if use_parent else clean_content

            parent_key = f"parent_{parent_id}" if use_parent else f"chunk_{clean_content.lower()}"
            is_parent_already_included = parent_key in seen_parent_keys
            seen_parent_keys.add(parent_key)

            # Extract page / timestamp metadata
            metadata = search_res.metadata or {}
            page = metadata.get("page")
            timestamp = metadata.get("timestamp") or metadata.get("start")
            if timestamp is not None and isinstance(timestamp, (int, float)):
                mins = int(timestamp // 60)
                secs = int(timestamp % 60)
                timestamp = f"{mins:02d}:{secs:02d}"

            # Always record the precise citation provenance
            citations.append(
                Citation(
                    chunk_id=search_res.chunk_id,
                    chunk_index=search_res.chunk_index,
                    document_id=search_res.document_id,
                    document_title=search_res.document_title,
                    source_id=search_res.source_id,
                    source_name=search_res.source_name,
                    source_type=search_res.source_type,
                    source_uri=search_res.source_uri,
                    rank=rank,
                    similarity_score=search_res.similarity_score,
                    rerank_score=rerank_score,
                    page=page,
                    timestamp=str(timestamp) if timestamp is not None else None,
                    snippet=clean_content[:200] + ("..." if len(clean_content) > 200 else ""),
                    content=effective_content,
                    parent_chunk_id=parent_id,
                    parent_content=parent_content if use_parent else None,
                    chunk_level=getattr(search_res, "chunk_level", "child"),
                    metadata=metadata,
                )
            )

            # If parent section was already included from a previous child chunk, skip duplicate text in prompt
            if is_parent_already_included:
                continue

            # Format source header line
            header_parts = [
                f"Source [{rank}]: {search_res.source_name}",
                f"Document: {search_res.document_title}",
                f"Type: {search_res.source_type}",
            ]
            if use_parent:
                header_parts.append("Hierarchical Section Context")
            if page is not None:
                header_parts.append(f"Page: {page}")
            if timestamp is not None:
                header_parts.append(f"Timestamp: {timestamp}")

            header_str = " | ".join(header_parts)
            chunk_block = f"--- {header_str} ---\n{effective_content}\n"

            # Check character limit
            if current_chars + len(chunk_block) > self.max_chars:
                is_truncated = True
                # If nothing added yet, truncate first block to fit
                if not context_blocks and len(chunk_block) > self.max_chars:
                    truncated_content = effective_content[: self.max_chars - len(header_str) - 20]
                    chunk_block = f"--- {header_str} ---\n{truncated_content}...\n"
                    context_blocks.append(chunk_block)
                    current_chars += len(chunk_block)
                break

            context_blocks.append(chunk_block)
            current_chars += len(chunk_block)

        formatted_text = "\n".join(context_blocks)
        return ConstructedContext(
            formatted_text=formatted_text,
            citations=citations,
            total_chunks=len(citations),
            total_chars=len(formatted_text),
            truncated=is_truncated,
        )
