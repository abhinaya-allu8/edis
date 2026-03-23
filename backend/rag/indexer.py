"""
EDIS — Indexer
Chunks ParsedDocument pages and upserts embeddings into Qdrant.
Supports two chunking strategies: fixed (token-based) and semantic (paragraph-aware).
"""

import uuid
from typing import List

from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    PointStruct,
    VectorParams,
)

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import (
    QDRANT_HOST,
    QDRANT_PORT,
    QDRANT_COLLECTION,
    CHUNK_SIZE,
    CHUNK_OVERLAP,
    CHUNKING_STRATEGY,
)
from rag.embedder import get_embedding, get_embedding_dimension


def get_qdrant_client() -> QdrantClient:
    return QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)


def ensure_collection(client: QdrantClient) -> None:
    """Creates the Qdrant collection if it doesn't exist."""
    existing = [c.name for c in client.get_collections().collections]
    if QDRANT_COLLECTION not in existing:
        dim = get_embedding_dimension()
        client.create_collection(
            collection_name=QDRANT_COLLECTION,
            vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
        )
        print(f"[Indexer] Created collection '{QDRANT_COLLECTION}' with dim={dim}")
    else:
        print(f"[Indexer] Collection '{QDRANT_COLLECTION}' already exists.")


# ─── Chunking ────────────────────────────────────────────────────────────────

def _fixed_chunk(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> List[str]:
    """
    Splits text into overlapping fixed-size word chunks.
    Simple and fast. Best for structured or uniform documents.
    """
    words = text.split()
    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunk = " ".join(words[start:end])
        if chunk.strip():
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def _semantic_chunk(text: str, chunk_size: int = CHUNK_SIZE) -> List[str]:
    """
    Splits on paragraph boundaries first, then enforces max chunk size.
    Preserves semantic coherence better than fixed chunking.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks = []
    current_words = []

    for para in paragraphs:
        para_words = para.split()
        if len(current_words) + len(para_words) <= chunk_size:
            current_words.extend(para_words)
        else:
            if current_words:
                chunks.append(" ".join(current_words))
            # If single paragraph exceeds chunk_size, hard-split it
            if len(para_words) > chunk_size:
                sub_chunks = _fixed_chunk(para, chunk_size, overlap=0)
                chunks.extend(sub_chunks[:-1])
                current_words = sub_chunks[-1].split() if sub_chunks else []
            else:
                current_words = para_words

    if current_words:
        chunks.append(" ".join(current_words))

    return chunks


def chunk_text(text: str) -> List[str]:
    """Routes to the configured chunking strategy."""
    if CHUNKING_STRATEGY == "semantic":
        return _semantic_chunk(text)
    else:
        return _fixed_chunk(text)


# ─── Indexing ────────────────────────────────────────────────────────────────

def index_document(parsed_doc) -> dict:
    """
    Takes a ParsedDocument, chunks all pages, embeds chunks, upserts to Qdrant.

    Returns:
        Summary dict with source, total_chunks, chunk_strategy.
    """
    client = get_qdrant_client()
    ensure_collection(client)

    all_chunks: List[str] = []
    chunk_metadata: List[dict] = []

    for page in parsed_doc.pages:
        text = page["text"]
        if not text.strip():
            continue
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            chunk_metadata.append({
                "source": parsed_doc.source,
                "doc_type": parsed_doc.doc_type,
                "page_num": page["page_num"],
                "chunk_index": i,
                "text": chunk,
            })

    if not all_chunks:
        return {"source": parsed_doc.source, "total_chunks": 0, "status": "empty"}

    print(f"[Indexer] Embedding {len(all_chunks)} chunks from '{parsed_doc.source}'...")
    vectors = []
    batch_size = 32
    for i in range(0, len(all_chunks), batch_size):
        batch = all_chunks[i: i + batch_size]
        from rag.embedder import get_embeddings
        batch_vectors = get_embeddings(batch)
        vectors.extend(batch_vectors)

    points = [
        PointStruct(
            id=str(uuid.uuid4()),
            vector=vectors[i],
            payload=chunk_metadata[i],
        )
        for i in range(len(all_chunks))
    ]

    client.upsert(collection_name=QDRANT_COLLECTION, points=points)
    print(f"[Indexer] Upserted {len(points)} points into '{QDRANT_COLLECTION}'.")

    return {
        "source": parsed_doc.source,
        "doc_type": parsed_doc.doc_type,
        "total_chunks": len(points),
        "chunk_strategy": CHUNKING_STRATEGY,
        "status": "indexed",
    }
