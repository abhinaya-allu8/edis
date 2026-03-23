"""
EDIS — Ingestion Agent
Orchestrates the full ingestion pipeline: parse → chunk → embed → index.
This is the entry point called by the LangGraph orchestrator in Phase 4.
"""

from dataclasses import dataclass
from typing import List, Optional
import time


@dataclass
class IngestionResult:
    source: str
    doc_type: str
    total_chunks: int
    chunk_strategy: str
    status: str  # indexed | failed | empty
    error: Optional[str] = None
    duration_seconds: Optional[float] = None


def run_ingestion(source: str, **parser_kwargs) -> IngestionResult:
    """
    Full ingestion pipeline for a single source (file path or URL).

    Steps:
        1. Route to correct parser
        2. Chunk all pages
        3. Embed chunks
        4. Upsert into Qdrant

    Args:
        source: File path or URL string.
        **parser_kwargs: Forwarded to parsers (e.g., max_rows for CSV).

    Returns:
        IngestionResult with status and stats.
    """
    import sys, os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))

    from parsers import parse
    from rag.indexer import index_document

    start = time.time()

    try:
        print(f"[IngestionAgent] Parsing: {source}")
        parsed_doc = parse(source, **parser_kwargs)

        if not parsed_doc.pages or not parsed_doc.full_text.strip():
            return IngestionResult(
                source=source,
                doc_type=parsed_doc.doc_type,
                total_chunks=0,
                chunk_strategy="N/A",
                status="empty",
                error="No extractable text found.",
                duration_seconds=round(time.time() - start, 2),
            )

        print(f"[IngestionAgent] Parsed {len(parsed_doc.pages)} page(s). Indexing...")
        result = index_document(parsed_doc)

        return IngestionResult(
            source=source,
            doc_type=result["doc_type"],
            total_chunks=result["total_chunks"],
            chunk_strategy=result["chunk_strategy"],
            status=result["status"],
            duration_seconds=round(time.time() - start, 2),
        )

    except Exception as e:
        return IngestionResult(
            source=source,
            doc_type="unknown",
            total_chunks=0,
            chunk_strategy="N/A",
            status="failed",
            error=str(e),
            duration_seconds=round(time.time() - start, 2),
        )


def run_batch_ingestion(sources: List[str], **parser_kwargs) -> List[IngestionResult]:
    """
    Runs ingestion for multiple sources sequentially.
    Returns one IngestionResult per source.
    """
    results = []
    for source in sources:
        print(f"\n[IngestionAgent] Processing source {sources.index(source)+1}/{len(sources)}: {source}")
        result = run_ingestion(source, **parser_kwargs)
        results.append(result)
        print(f"[IngestionAgent] ✓ {result.status.upper()} | chunks={result.total_chunks} | time={result.duration_seconds}s")

    success = sum(1 for r in results if r.status == "indexed")
    print(f"\n[IngestionAgent] Batch complete: {success}/{len(results)} successful.")
    return results
