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
    Preserves document, source, page, and timestamp metadata.
    """

    def __init__(self, max_chars: Optional[int] = None):
        self.max_chars = max_chars or getattr(settings, "RAG_MAX_CONTEXT_CHARS", 4000)

    def build(
        self,
        items: List[Any],
    ) -> ConstructedContext:
        if not items:
            return ConstructedContext(
                formatted_text="",
                citations=[],
                total_chunks=0,
                total_chars=0,
                truncated=False,
            )

        citations: List[Citation] = []
        context_blocks: List[str] = []
        seen_contents: Set[str] = set()
        current_chars = 0
        is_truncated = False

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
            # Deduplicate identical chunk content
            content_hash = clean_content.lower()
            if content_hash in seen_contents:
                continue
            seen_contents.add(content_hash)

            # Extract page / timestamp metadata
            metadata = search_res.metadata or {}
            page = metadata.get("page")
            timestamp = metadata.get("timestamp") or metadata.get("start")
            if timestamp is not None and isinstance(timestamp, (int, float)):
                # Convert seconds to mm:ss format
                mins = int(timestamp // 60)
                secs = int(timestamp % 60)
                timestamp = f"{mins:02d}:{secs:02d}"

            # Format source header line
            header_parts = [
                f"Source [{rank}]: {search_res.source_name}",
                f"Document: {search_res.document_title}",
                f"Type: {search_res.source_type}",
            ]
            if page is not None:
                header_parts.append(f"Page: {page}")
            if timestamp is not None:
                header_parts.append(f"Timestamp: {timestamp}")

            header_str = " | ".join(header_parts)
            chunk_block = f"--- {header_str} ---\n{clean_content}\n"

            # Check character limit
            if current_chars + len(chunk_block) > self.max_chars:
                is_truncated = True
                # If nothing added yet, truncate first block to fit
                if not context_blocks and len(chunk_block) > self.max_chars:
                    truncated_content = clean_content[: self.max_chars - len(header_str) - 20]
                    chunk_block = f"--- {header_str} ---\n{truncated_content}...\n"
                    context_blocks.append(chunk_block)
                    current_chars += len(chunk_block)
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
                            snippet=clean_content[:150] + "...",
                            metadata=metadata,
                        )
                    )
                break

            context_blocks.append(chunk_block)
            current_chars += len(chunk_block)

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
                    snippet=clean_content[:150] + ("..." if len(clean_content) > 150 else ""),
                    metadata=metadata,
                )
            )

        formatted_text = "\n".join(context_blocks)
        return ConstructedContext(
            formatted_text=formatted_text,
            citations=citations,
            total_chunks=len(citations),
            total_chars=len(formatted_text),
            truncated=is_truncated,
        )
