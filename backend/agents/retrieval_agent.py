"""
EDIS — Retrieval Agent
Orchestrates the full retrieval pipeline: semantic search → cross-encoder reranking.
Returns a clean context payload ready for the Synthesis Agent.
"""

from dataclasses import dataclass, field
from typing import List, Optional
import time

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import TOP_K, RERANK_TOP_N
from rag.retriever import retrieve, retrieve_with_filter, RetrievedChunk
from rag.reranker import rerank


@dataclass
class RetrievalResult:
    query: str
    chunks: List[RetrievedChunk]
    total_retrieved: int       # before reranking
    total_reranked: int        # after reranking
    duration_seconds: float
    status: str                # success | empty | failed
    error: Optional[str] = None

    def to_context_string(self) -> str:
        """
        Formats retrieved chunks into a clean context block for the LLM.
        Each chunk is labeled with its source and page number.
        """
        if not self.chunks:
            return "No relevant context found."

        parts = []
        for i, chunk in enumerate(self.chunks, start=1):
            source_label = f"{chunk.source} (page {chunk.page_num})"
            parts.append(
                f"[Context {i}] Source: {source_label}\n"
                f"Relevance score: {chunk.score}\n"
                f"{chunk.text}"
            )
        return "\n\n---\n\n".join(parts)

    def to_citations(self) -> List[dict]:
        """
        Returns structured citation metadata for the Synthesis Agent to embed.
        """
        return [
            {
                "index": i + 1,
                "source": chunk.source,
                "doc_type": chunk.doc_type,
                "page_num": chunk.page_num,
                "score": chunk.score,
                "text_preview": chunk.text[:200],
            }
            for i, chunk in enumerate(self.chunks)
        ]


def run_retrieval(
    query: str,
    source_filter: Optional[str] = None,
    doc_type_filter: Optional[str] = None,
    top_k: int = TOP_K,
    top_n: int = RERANK_TOP_N,
) -> RetrievalResult:
    """
    Full retrieval pipeline: semantic search → cross-encoder reranking.

    Args:
        query: User question.
        source_filter: Restrict retrieval to a specific document source.
        doc_type_filter: Restrict by doc type (pdf, docx, csv, txt, url).
        top_k: Number of chunks to retrieve from Qdrant before reranking.
        top_n: Number of chunks to keep after reranking.

    Returns:
        RetrievalResult with ranked chunks and context string.
    """
    start = time.time()

    try:
        print(f"[RetrievalAgent] Query: '{query}'")

        # Step 1: Semantic search
        if source_filter or doc_type_filter:
            chunks = retrieve_with_filter(
                query,
                source_filter=source_filter,
                doc_type_filter=doc_type_filter,
                top_k=top_k,
            )
        else:
            chunks = retrieve(query, top_k=top_k)

        total_retrieved = len(chunks)
        print(f"[RetrievalAgent] Retrieved {total_retrieved} chunks from Qdrant.")

        if not chunks:
            return RetrievalResult(
                query=query,
                chunks=[],
                total_retrieved=0,
                total_reranked=0,
                duration_seconds=round(time.time() - start, 2),
                status="empty",
                error="No chunks found. Check if documents are indexed.",
            )

        # Step 2: Cross-encoder reranking
        reranked = rerank(query, chunks, top_n=top_n)
        print(f"[RetrievalAgent] Reranked to top {len(reranked)} chunks.")

        return RetrievalResult(
            query=query,
            chunks=reranked,
            total_retrieved=total_retrieved,
            total_reranked=len(reranked),
            duration_seconds=round(time.time() - start, 2),
            status="success",
        )

    except Exception as e:
        return RetrievalResult(
            query=query,
            chunks=[],
            total_retrieved=0,
            total_reranked=0,
            duration_seconds=round(time.time() - start, 2),
            status="failed",
            error=str(e),
        )
