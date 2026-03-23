"""
EDIS — Retriever
Performs semantic search against Qdrant collection.
Returns top-K chunks with scores and metadata.
"""

from typing import List
from dataclasses import dataclass

from qdrant_client import QdrantClient

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION, TOP_K
from rag.embedder import get_embedding


@dataclass
class RetrievedChunk:
    text: str
    source: str
    doc_type: str
    page_num: int
    chunk_index: int
    score: float  # cosine similarity [0, 1]


def retrieve(query: str, top_k: int = TOP_K) -> List[RetrievedChunk]:
    """
    Embeds the query and retrieves top_k most similar chunks from Qdrant.

    Args:
        query: User question string.
        top_k: Number of chunks to retrieve before reranking.

    Returns:
        List of RetrievedChunk sorted by descending similarity score.
    """
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

    query_vector = get_embedding(query)

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        limit=top_k,
        with_payload=True,
    )

    chunks = []
    for hit in response.points:
        payload = hit.payload or {}
        chunks.append(RetrievedChunk(
            text=payload.get("text", ""),
            source=payload.get("source", "unknown"),
            doc_type=payload.get("doc_type", "unknown"),
            page_num=payload.get("page_num", 0),
            chunk_index=payload.get("chunk_index", 0),
            score=round(hit.score, 4),
        ))

    return chunks


def retrieve_with_filter(
    query: str,
    source_filter: str = None,
    doc_type_filter: str = None,
    top_k: int = TOP_K,
) -> List[RetrievedChunk]:
    """
    Retrieves chunks with optional payload filters.
    Useful for scoping queries to a specific document or doc type.

    Args:
        query: User question.
        source_filter: Exact source path/URL to filter by.
        doc_type_filter: 'pdf', 'docx', 'csv', 'txt', or 'url'.
        top_k: Number of results.
    """
    from qdrant_client.models import Filter, FieldCondition, MatchValue

    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
    query_vector = get_embedding(query)

    conditions = []
    if source_filter:
        conditions.append(FieldCondition(key="source", match=MatchValue(value=source_filter)))
    if doc_type_filter:
        conditions.append(FieldCondition(key="doc_type", match=MatchValue(value=doc_type_filter)))

    qdrant_filter = Filter(must=conditions) if conditions else None

    response = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=query_vector,
        query_filter=qdrant_filter,
        limit=top_k,
        with_payload=True,
    )

    chunks = []
    for hit in response.points:
        payload = hit.payload or {}
        chunks.append(RetrievedChunk(
            text=payload.get("text", ""),
            source=payload.get("source", "unknown"),
            doc_type=payload.get("doc_type", "unknown"),
            page_num=payload.get("page_num", 0),
            chunk_index=payload.get("chunk_index", 0),
            score=round(hit.score, 4),
        ))

    return chunks
