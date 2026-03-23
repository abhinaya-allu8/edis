"""
EDIS — LangGraph Orchestrator
Defines the agent state graph and wires all agents together.

Graph flow:
    START
      ↓
  [ingest_node]      ← triggered only on document upload
      ↓
  [retrieve_node]    ← semantic search + reranking
      ↓
  [synthesize_node]  ← LLM answer generation with citations
      ↓
  [evaluate_node]    ← RAGAS evaluation (faithfulness, relevancy, precision)
      ↓
    END

For query-only flows (documents already indexed), ingest_node is skipped.
"""

from typing import Optional, List, TypedDict
from langgraph.graph import StateGraph, END

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from agents.ingestion_agent import run_ingestion, run_batch_ingestion, IngestionResult
from agents.retrieval_agent import run_retrieval, RetrievalResult
from agents.synthesis_agent import run_synthesis, SynthesisResult
from config import TOP_K, RERANK_TOP_N


# ─── Graph State ─────────────────────────────────────────────────────────────

class EDISState(TypedDict, total=False):
    # Input
    query: str
    sources: List[str]              # File paths or URLs to ingest (optional)
    source_filter: Optional[str]    # Scope retrieval to one document
    doc_type_filter: Optional[str]  # Scope retrieval to one doc type

    # Agent outputs
    ingestion_results: List[dict]   # Serialized IngestionResult list
    retrieval_result: Optional[dict]
    synthesis_result: Optional[dict]
    evaluation_result: Optional[dict]

    # Control
    skip_ingestion: bool            # True if documents already indexed
    skip_evaluation: bool           # True if RAGAS eval not needed

    # Final output
    final_answer: str
    citations: List[dict]
    error: Optional[str]


# ─── Nodes ───────────────────────────────────────────────────────────────────

def ingest_node(state: EDISState) -> EDISState:
    """Runs ingestion pipeline for all provided sources."""
    sources = state.get("sources", [])
    if not sources or state.get("skip_ingestion", False):
        print("[Orchestrator] Skipping ingestion.")
        return {**state, "ingestion_results": []}

    results = run_batch_ingestion(sources)
    serialized = [
        {
            "source": r.source,
            "doc_type": r.doc_type,
            "total_chunks": r.total_chunks,
            "chunk_strategy": r.chunk_strategy,
            "status": r.status,
            "error": r.error,
            "duration_seconds": r.duration_seconds,
        }
        for r in results
    ]

    failed = [r for r in results if r.status == "failed"]
    if failed and len(failed) == len(results):
        return {**state, "ingestion_results": serialized, "error": "All sources failed to ingest."}

    return {**state, "ingestion_results": serialized}


def retrieve_node(state: EDISState) -> EDISState:
    """Runs semantic search + reranking for the user query."""
    query = state.get("query", "")
    if not query:
        return {**state, "error": "No query provided."}

    result = run_retrieval(
        query=query,
        source_filter=state.get("source_filter"),
        doc_type_filter=state.get("doc_type_filter"),
        top_k=TOP_K,
        top_n=RERANK_TOP_N,
    )

    return {**state, "retrieval_result": _serialize_retrieval(result)}


def synthesize_node(state: EDISState) -> EDISState:
    """Generates a grounded answer from retrieved context."""
    query = state.get("query", "")
    raw = state.get("retrieval_result")

    if not raw:
        return {**state, "final_answer": "No context retrieved.", "citations": []}

    retrieval_result = _deserialize_retrieval(raw)
    result = run_synthesis(query=query, retrieval_result=retrieval_result)

    return {
        **state,
        "synthesis_result": {
            "answer": result.answer,
            "citations": result.citations,
            "model_used": result.model_used,
            "provider": result.provider,
            "status": result.status,
            "error": result.error,
            "duration_seconds": result.duration_seconds,
        },
        "final_answer": result.formatted_answer(),
        "citations": result.citations,
    }


def evaluate_node(state: EDISState) -> EDISState:
    """
    Runs RAGAS evaluation on the synthesis output.
    Skipped if skip_evaluation=True or synthesis failed.
    """
    if state.get("skip_evaluation", False):
        print("[Orchestrator] Skipping evaluation.")
        return {**state, "evaluation_result": None}

    synthesis = state.get("synthesis_result", {})
    if not synthesis or synthesis.get("status") != "success":
        return {**state, "evaluation_result": None}

    try:
        from evals.ragas_eval import run_ragas_eval
        from rag.retriever import RetrievedChunk

        raw_retrieval = state.get("retrieval_result", {})
        context_texts = [c["text"] for c in raw_retrieval.get("chunks", [])]

        eval_result = run_ragas_eval(
            question=state.get("query", ""),
            answer=synthesis.get("answer", ""),
            contexts=context_texts,
        )
        return {**state, "evaluation_result": eval_result}

    except Exception as e:
        print(f"[Orchestrator] Evaluation failed (non-critical): {e}")
        return {**state, "evaluation_result": {"error": str(e)}}


# ─── Routing ─────────────────────────────────────────────────────────────────

def should_ingest(state: EDISState) -> str:
    """Routes to ingest only if sources are provided and not skipped."""
    if state.get("sources") and not state.get("skip_ingestion", False):
        return "ingest"
    return "retrieve"


# ─── Graph Construction ───────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(EDISState)

    graph.add_node("ingest", ingest_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("synthesize", synthesize_node)
    graph.add_node("evaluate", evaluate_node)

    # Conditional entry: ingest or skip straight to retrieve
    graph.set_conditional_entry_point(
        should_ingest,
        {"ingest": "ingest", "retrieve": "retrieve"},
    )

    graph.add_edge("ingest", "retrieve")
    graph.add_edge("retrieve", "synthesize")
    graph.add_edge("synthesize", "evaluate")
    graph.add_edge("evaluate", END)

    return graph.compile()


# ─── Public API ──────────────────────────────────────────────────────────────

_graph = None  # singleton


def get_graph():
    global _graph
    if _graph is None:
        _graph = build_graph()
    return _graph


def run_pipeline(
    query: str,
    sources: Optional[List[str]] = None,
    skip_ingestion: bool = False,
    skip_evaluation: bool = False,
    source_filter: Optional[str] = None,
    doc_type_filter: Optional[str] = None,
) -> EDISState:
    """
    Main entry point for the full EDIS pipeline.

    Args:
        query: User question.
        sources: Optional list of file paths/URLs to ingest first.
        skip_ingestion: If True, skips ingestion (docs already indexed).
        skip_evaluation: If True, skips RAGAS evaluation.
        source_filter: Scope retrieval to a specific source.
        doc_type_filter: Scope retrieval to a specific doc type.

    Returns:
        Final EDISState with answer, citations, and eval scores.
    """
    graph = get_graph()

    initial_state: EDISState = {
        "query": query,
        "sources": sources or [],
        "skip_ingestion": skip_ingestion,
        "skip_evaluation": skip_evaluation,
        "source_filter": source_filter,
        "doc_type_filter": doc_type_filter,
    }

    return graph.invoke(initial_state)


# ─── Serialization Helpers ───────────────────────────────────────────────────

def _serialize_retrieval(result: RetrievalResult) -> dict:
    return {
        "query": result.query,
        "chunks": [
            {
                "text": c.text,
                "source": c.source,
                "doc_type": c.doc_type,
                "page_num": c.page_num,
                "chunk_index": c.chunk_index,
                "score": c.score,
            }
            for c in result.chunks
        ],
        "total_retrieved": result.total_retrieved,
        "total_reranked": result.total_reranked,
        "status": result.status,
        "error": result.error,
        "duration_seconds": result.duration_seconds,
    }


def _deserialize_retrieval(raw: dict) -> RetrievalResult:
    from rag.retriever import RetrievedChunk

    chunks = [
        RetrievedChunk(
            text=c["text"],
            source=c["source"],
            doc_type=c["doc_type"],
            page_num=c["page_num"],
            chunk_index=c["chunk_index"],
            score=c["score"],
        )
        for c in raw.get("chunks", [])
    ]

    return RetrievalResult(
        query=raw["query"],
        chunks=chunks,
        total_retrieved=raw["total_retrieved"],
        total_reranked=raw["total_reranked"],
        duration_seconds=raw["duration_seconds"],
        status=raw["status"],
        error=raw.get("error"),
    )
