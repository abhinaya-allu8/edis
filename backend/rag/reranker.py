"""
EDIS — Reranker
Cross-encoder reranking on top of retrieved chunks.
Takes top_k semantic results, scores each (query, chunk) pair,
and returns top_n highest-relevance chunks.

Model: cross-encoder/ms-marco-MiniLM-L-6-v2
Fast, accurate, well-tested for passage reranking.
"""

from typing import List

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import RERANKER_MODEL, RERANK_TOP_N
from rag.retriever import RetrievedChunk


_reranker = None  # Lazy-loaded singleton


def _get_reranker():
    """Lazy-loads the cross-encoder to avoid startup overhead."""
    global _reranker
    if _reranker is None:
        from sentence_transformers import CrossEncoder
        print(f"[Reranker] Loading cross-encoder: {RERANKER_MODEL}")
        _reranker = CrossEncoder(RERANKER_MODEL)
    return _reranker


def rerank(query: str, chunks: List[RetrievedChunk], top_n: int = RERANK_TOP_N) -> List[RetrievedChunk]:
    """
    Reranks retrieved chunks using a cross-encoder model.

    Args:
        query: Original user question.
        chunks: List of RetrievedChunk from semantic search.
        top_n: Number of chunks to return after reranking.

    Returns:
        top_n chunks sorted by cross-encoder score (descending).
        Each chunk has its score updated to the cross-encoder score.
    """
    if not chunks:
        return []

    if len(chunks) <= 1:
        return chunks[:top_n]

    model = _get_reranker()

    pairs = [(query, chunk.text) for chunk in chunks]
    scores = model.predict(pairs)

    ranked = sorted(
        zip(chunks, scores),
        key=lambda x: x[1],
        reverse=True,
    )

    result = []
    for chunk, score in ranked[:top_n]:
        chunk.score = round(float(score), 4)
        result.append(chunk)

    return result
