"""
EDIS — FastAPI Backend
Exposes REST endpoints for document ingestion and querying.

Endpoints:
  POST /ingest          — Upload + ingest a file
  POST /ingest/url      — Ingest a web URL
  POST /query           — Ask a question over indexed documents
  GET  /health          — Health check
  GET  /collection/info — Qdrant collection stats
  DELETE /collection    — Wipe the Qdrant collection
"""

import os
import shutil
import tempfile
from typing import List, Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import sys
sys.path.append(os.path.dirname(__file__))

from graph.orchestrator import run_pipeline
from agents.ingestion_agent import run_ingestion


# ─── App Setup ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="EDIS — Enterprise Document Intelligence System",
    description="Multi-agent RAG system with evaluation. Ingest any document, ask anything.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Request/Response Models ──────────────────────────────────────────────────

class QueryRequest(BaseModel):
    query: str
    source_filter: Optional[str] = None
    doc_type_filter: Optional[str] = None
    skip_evaluation: bool = False
    max_tokens: int = 1024


class URLIngestRequest(BaseModel):
    url: str


class QueryResponse(BaseModel):
    query: str
    answer: str
    citations: List[dict]
    retrieval_stats: dict
    synthesis_stats: dict
    evaluation: Optional[dict] = None
    status: str


class IngestResponse(BaseModel):
    source: str
    doc_type: str
    total_chunks: int
    chunk_strategy: str
    status: str
    duration_seconds: float
    error: Optional[str] = None


# ─── Endpoints ────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "service": "EDIS"}


@app.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    """
    Upload and ingest a document (PDF, DOCX, CSV, TXT, MD).
    Saves to a temp file, runs the ingestion pipeline, then cleans up.
    """
    allowed_extensions = {".pdf", ".docx", ".doc", ".csv", ".tsv", ".txt", ".md"}
    ext = os.path.splitext(file.filename or "")[-1].lower()

    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: '{ext}'. Allowed: {', '.join(sorted(allowed_extensions))}",
        )

    # Save to temp file preserving extension
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        shutil.copyfileobj(file.file, tmp)
        tmp_path = tmp.name

    try:
        result = run_ingestion(tmp_path)
    finally:
        os.unlink(tmp_path)

    return IngestResponse(
        source=file.filename or tmp_path,
        doc_type=result.doc_type,
        total_chunks=result.total_chunks,
        chunk_strategy=result.chunk_strategy,
        status=result.status,
        duration_seconds=result.duration_seconds or 0.0,
        error=result.error,
    )


@app.post("/ingest/url", response_model=IngestResponse)
def ingest_url(request: URLIngestRequest):
    """Fetches and ingests content from a web URL."""
    result = run_ingestion(request.url)
    return IngestResponse(
        source=request.url,
        doc_type=result.doc_type,
        total_chunks=result.total_chunks,
        chunk_strategy=result.chunk_strategy,
        status=result.status,
        duration_seconds=result.duration_seconds or 0.0,
        error=result.error,
    )


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest):
    """
    Ask a question over all indexed documents.
    Runs: retrieve → synthesize → evaluate (optional).
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    state = run_pipeline(
        query=request.query,
        skip_ingestion=True,
        skip_evaluation=request.skip_evaluation,
        source_filter=request.source_filter,
        doc_type_filter=request.doc_type_filter,
    )

    retrieval = state.get("retrieval_result") or {}
    synthesis = state.get("synthesis_result") or {}

    return QueryResponse(
        query=request.query,
        answer=state.get("final_answer", "No answer generated."),
        citations=state.get("citations", []),
        retrieval_stats={
            "total_retrieved": retrieval.get("total_retrieved", 0),
            "total_reranked": retrieval.get("total_reranked", 0),
            "duration_seconds": retrieval.get("duration_seconds", 0),
            "status": retrieval.get("status", "unknown"),
        },
        synthesis_stats={
            "model_used": synthesis.get("model_used", "unknown"),
            "provider": synthesis.get("provider", "unknown"),
            "duration_seconds": synthesis.get("duration_seconds", 0),
            "status": synthesis.get("status", "unknown"),
        },
        evaluation=state.get("evaluation_result"),
        status="success" if synthesis.get("status") == "success" else "partial",
    )


@app.get("/collection/info")
def collection_info():
    """Returns Qdrant collection stats — total indexed chunks, vector count."""
    try:
        from qdrant_client import QdrantClient
        from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION

        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        existing = [c.name for c in client.get_collections().collections]
        if QDRANT_COLLECTION not in existing:
            return {
                "collection": QDRANT_COLLECTION,
                "total_vectors": 0,
                "indexed_vectors": 0,
                "status": "empty",
            }
        info = client.get_collection(QDRANT_COLLECTION)
        return {
            "collection": QDRANT_COLLECTION,
            "total_vectors": info.points_count,
            "indexed_vectors": info.indexed_vectors_count,
            "status": str(info.status),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/collection")
def wipe_collection():
    """Deletes and recreates the Qdrant collection. Wipes all indexed data."""
    try:
        from qdrant_client import QdrantClient
        from config import QDRANT_HOST, QDRANT_PORT, QDRANT_COLLECTION
        from rag.indexer import ensure_collection

        client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)
        client.delete_collection(QDRANT_COLLECTION)
        ensure_collection(client)
        return {"status": "wiped", "collection": QDRANT_COLLECTION}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
