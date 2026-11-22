from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union
import uuid
from django.conf import settings
from pgvector.django import CosineDistance

from apps.sources.models import DocumentChunk
from apps.rag.embeddings import get_embedding_provider, BaseEmbeddingProvider


@dataclass
class SearchResult:
    """Standardized vector retrieval result item with provenance and hierarchical metadata."""
    chunk_id: str
    chunk_index: int
    content: str
    similarity_score: float
    distance: float
    document_id: str
    document_title: str
    source_id: str
    source_name: str
    source_type: str
    source_uri: str
    heading: str = ""
    chunk_level: str = "child"
    parent_chunk_id: Optional[str] = None
    parent_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "chunk_index": self.chunk_index,
            "content": self.content,
            "heading": self.heading,
            "chunk_level": self.chunk_level,
            "parent_chunk_id": self.parent_chunk_id,
            "parent_content": self.parent_content,
            "similarity_score": round(self.similarity_score, 4),
            "distance": round(self.distance, 4),
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
            "metadata": self.metadata,
        }


class RetrievalService:
    """
    Core vector retrieval service.
    Converts query text to embeddings, executes cosine distance search in pgvector,
    and returns top_k ranked chunks with metadata.
    """

    @classmethod
    def search(
        cls,
        query: str,
        top_k: int = 10,
        source_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        document_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        source_types: Optional[List[str]] = None,
        min_similarity: Optional[float] = None,
        provider: Optional[BaseEmbeddingProvider] = None,
    ) -> List[SearchResult]:
        """
        Execute vector similarity search for a query string.
        """
        if not query or not query.strip():
            return []

        active_provider = provider or get_embedding_provider()
        query_vector = active_provider.embed_text(query.strip())

        # Filter chunks that have valid embeddings
        queryset = DocumentChunk.objects.filter(embedding__isnull=False)

        # Apply source & document filters
        if source_ids:
            queryset = queryset.filter(document__source_id__in=source_ids)
        if document_ids:
            queryset = queryset.filter(document_id__in=document_ids)
        if source_types:
            clean_types = [t.lower() for t in source_types]
            queryset = queryset.filter(document__source__source_type__in=clean_types)

        from django.db import connection
        import math

        results: List[SearchResult] = []

        if connection.vendor == "postgresql":
            # Native PostgreSQL pgvector cosine distance query
            annotated_qs = (
                queryset.annotate(distance=CosineDistance("embedding", query_vector))
                .select_related("document", "document__source", "parent_chunk")
                .order_by("distance")[:top_k]
            )

            for chunk in annotated_qs:
                dist = float(chunk.distance) if chunk.distance is not None else 1.0
                # Cosine similarity in range [0.0, 1.0]
                similarity = max(0.0, min(1.0, 1.0 - dist))

                if min_similarity is not None and similarity < min_similarity:
                    continue

                doc = chunk.document
                src = doc.source if doc else None
                parent_chunk = chunk.parent_chunk

                enriched_meta = {
                    **(chunk.metadata or {}),
                    "token_count": chunk.token_count,
                    "chunk_level": chunk.chunk_level,
                }

                chunk_heading = getattr(chunk, "heading", "") or (chunk.metadata or {}).get("heading", "")
                results.append(
                    SearchResult(
                        chunk_id=str(chunk.id),
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        similarity_score=similarity,
                        distance=dist,
                        document_id=str(doc.id) if doc else "",
                        document_title=doc.title if doc else "",
                        source_id=str(src.id) if src else "",
                        source_name=src.name if src else "",
                        source_type=src.source_type if src else "",
                        source_uri=src.uri if src else "",
                        heading=chunk_heading,
                        chunk_level=chunk.chunk_level,
                        parent_chunk_id=str(parent_chunk.id) if parent_chunk else None,
                        parent_content=parent_chunk.content if parent_chunk else None,
                        metadata=enriched_meta,
                    )
                )
        else:
            # SQLite / Local-First Python in-memory vector search
            def compute_cosine_distance(vec_a, vec_b) -> float:
                if not vec_a or not vec_b:
                    return 1.0
                if isinstance(vec_a, str):
                    try:
                        import json
                        vec_a = json.loads(vec_a)
                    except Exception:
                        return 1.0
                dot = 0.0
                norm_a = 0.0
                norm_b = 0.0
                for a, b in zip(vec_a, vec_b):
                    dot += a * b
                    norm_a += a * a
                    norm_b += b * b
                if norm_a <= 0.0 or norm_b <= 0.0:
                    return 1.0
                cos_sim = dot / (math.sqrt(norm_a) * math.sqrt(norm_b))
                return float(max(0.0, min(1.0, 1.0 - cos_sim)))

            scored_chunks = []
            for chunk in queryset.select_related("document", "document__source", "parent_chunk"):
                dist = compute_cosine_distance(chunk.embedding, query_vector)
                similarity = max(0.0, min(1.0, 1.0 - dist))
                if min_similarity is not None and similarity < min_similarity:
                    continue
                scored_chunks.append((dist, similarity, chunk))

            scored_chunks.sort(key=lambda item: item[0])

            for dist, similarity, chunk in scored_chunks[:top_k]:
                doc = chunk.document
                src = doc.source if doc else None
                parent_chunk = chunk.parent_chunk

                enriched_meta = {
                    **(chunk.metadata or {}),
                    "token_count": chunk.token_count,
                    "chunk_level": chunk.chunk_level,
                }

                chunk_heading = getattr(chunk, "heading", "") or (chunk.metadata or {}).get("heading", "")
                results.append(
                    SearchResult(
                        chunk_id=str(chunk.id),
                        chunk_index=chunk.chunk_index,
                        content=chunk.content,
                        similarity_score=similarity,
                        distance=dist,
                        document_id=str(doc.id) if doc else "",
                        document_title=doc.title if doc else "",
                        source_id=str(src.id) if src else "",
                        source_name=src.name if src else "",
                        source_type=src.source_type if src else "",
                        source_uri=src.uri if src else "",
                        heading=chunk_heading,
                        chunk_level=chunk.chunk_level,
                        parent_chunk_id=str(parent_chunk.id) if parent_chunk else None,
                        parent_content=parent_chunk.content if parent_chunk else None,
                        metadata=enriched_meta,
                    )
                )

        return results

