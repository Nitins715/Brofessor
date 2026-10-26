import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import uuid

from apps.sources.models import DocumentChunk
from apps.rag.services.retrieval import RetrievalService, SearchResult


class BM25Scorer:
    """
    Lightweight, high-performance in-memory BM25 scorer.
    Ideal for local-first execution across all databases (SQLite / PostgreSQL)
    without needing external search servers.
    """
    def __init__(self, k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """
        Tokenizes text into words and programming identifiers.
        Splits camelCase, snake_case, and extracts both individual terms and sub-words.
        """
        if not text:
            return []
        # Expand camelCase: calculateFibonacci -> calculate Fibonacci
        text_expanded = re.sub(r"([a-z])([A-Z])", r"\1 \2", text)
        # Also split on underscores so calculate_fibonacci yields calculate and fibonacci
        text_with_spaces = text_expanded.replace("_", " ")
        words = re.findall(r"\b[a-zA-Z0-9\-\.]{2,}\b", text_with_spaces.lower())
        return words

    def score_corpus(
        self,
        query: str,
        chunks: List[Any],
    ) -> List[Tuple[float, Any]]:
        """
        Computes BM25 scores for a list of document chunks against the query.
        Returns list of (score, chunk) tuples sorted descending by score.
        """
        query_tokens = self.tokenize(query)
        if not query_tokens or not chunks:
            return [(0.0, c) for c in chunks]

        doc_tokens_list = [self.tokenize(c.content) for c in chunks]
        N = len(chunks)
        doc_lens = [len(dt) for dt in doc_tokens_list]
        avgdl = (sum(doc_lens) / N) if N > 0 else 1.0

        # Calculate Document Frequency (DF) for each query term
        df: Counter = Counter()
        for dt in doc_tokens_list:
            unique_terms: Set[str] = set(dt)
            for term in query_tokens:
                if term in unique_terms:
                    df[term] += 1

        # Calculate IDF for each query term
        idf: Dict[str, float] = {}
        for term in query_tokens:
            n_q = df[term]
            idf[term] = math.log(1.0 + (N - n_q + 0.5) / (n_q + 0.5))

        # Score each document
        scored: List[Tuple[float, Any]] = []
        for idx, chunk in enumerate(chunks):
            dt = doc_tokens_list[idx]
            d_len = doc_lens[idx]
            term_counts = Counter(dt)
            score = 0.0

            for term in query_tokens:
                tf = term_counts[term]
                if tf > 0:
                    numerator = tf * (self.k1 + 1.0)
                    denominator = tf + self.k1 * (1.0 - self.b + self.b * (d_len / avgdl))
                    score += idf[term] * (numerator / denominator)

            scored.append((score, chunk))

        scored.sort(key=lambda x: x[0], reverse=True)
        return scored


class HybridRetrievalService:
    """
    Hybrid Search combining:
    1. Dense Vector Embeddings (Semantic Recall)
    2. BM25 Sparse Lexical Matching (Exact Keyword / Code Symbol Precision)
    3. Reciprocal Rank Fusion (RRF) for robust multi-modal merging
    """

    RRF_K = 60  # Standard constant in information retrieval

    @classmethod
    def search(
        cls,
        query: str,
        top_k: int = 10,
        dense_weight: float = 0.7,
        sparse_weight: float = 0.3,
        source_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        document_ids: Optional[List[Union[str, uuid.UUID]]] = None,
        source_types: Optional[List[str]] = None,
        min_similarity: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Execute Hybrid Dense + Lexical Search with Reciprocal Rank Fusion.
        """
        if not query or not query.strip():
            return []

        # 1. Dense Vector Search (fetches top candidate pool)
        dense_candidates = RetrievalService.search(
            query=query,
            top_k=max(top_k * 2, 20),
            source_ids=source_ids,
            document_ids=document_ids,
            source_types=source_types,
            min_similarity=min_similarity,
        )

        # 2. Sparse / Keyword Candidates via BM25
        # Retrieve candidate chunk records for BM25 ranking
        queryset = DocumentChunk.objects.select_related("document", "document__source")
        if source_ids:
            queryset = queryset.filter(document__source_id__in=source_ids)
        if document_ids:
            queryset = queryset.filter(document_id__in=document_ids)
        if source_types:
            clean_types = [t.lower() for t in source_types]
            queryset = queryset.filter(document__source__source_type__in=clean_types)

        all_candidate_chunks = list(queryset[:100])
        bm25_scorer = BM25Scorer()
        bm25_ranked = bm25_scorer.score_corpus(query, all_candidate_chunks)

        # 3. Reciprocal Rank Fusion (RRF)
        # dense_ranks: chunk_id -> rank (1-indexed)
        dense_ranks: Dict[str, int] = {
            res.chunk_id: (idx + 1) for idx, res in enumerate(dense_candidates)
        }

        # sparse_ranks: chunk_id -> rank (1-indexed)
        sparse_ranks: Dict[str, int] = {
            str(chunk.id): (idx + 1) for idx, (score, chunk) in enumerate(bm25_ranked) if score > 0
        }

        # Master lookup for SearchResult objects
        chunk_map: Dict[str, SearchResult] = {res.chunk_id: res for res in dense_candidates}

        for score, chunk in bm25_ranked:
            cid = str(chunk.id)
            if cid not in chunk_map:
                doc = chunk.document
                src = doc.source if doc else None
                chunk_map[cid] = SearchResult(
                    chunk_id=cid,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    similarity_score=min(1.0, score / 10.0),
                    distance=1.0,
                    document_id=str(doc.id) if doc else "",
                    document_title=doc.title if doc else "",
                    source_id=str(src.id) if src else "",
                    source_name=src.name if src else "",
                    source_type=src.source_type if src else "",
                    source_uri=src.uri if src else "",
                    metadata={
                        **(chunk.metadata or {}),
                        "token_count": chunk.token_count,
                        "bm25_score": round(score, 4),
                    },
                )

        # Calculate Combined RRF Score for all pooled items
        all_chunk_ids = set(dense_ranks.keys()) | set(sparse_ranks.keys())
        scored_results: List[Tuple[float, SearchResult]] = []

        for cid in all_chunk_ids:
            dense_rank = dense_ranks.get(cid)
            sparse_rank = sparse_ranks.get(cid)

            rrf_score = 0.0
            if dense_rank:
                rrf_score += dense_weight * (1.0 / (cls.RRF_K + dense_rank))
            if sparse_rank:
                rrf_score += sparse_weight * (1.0 / (cls.RRF_K + sparse_rank))

            item = chunk_map[cid]
            item.metadata["rrf_score"] = round(rrf_score, 6)
            item.similarity_score = max(item.similarity_score, round(rrf_score * 10.0, 4))
            scored_results.append((rrf_score, item))

        scored_results.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored_results[:top_k]]
