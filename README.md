# 🧠 EDIS — Enterprise Document Intelligence System

A production-grade **multi-agent RAG system** that ingests any document format, answers questions with citations, and evaluates its own response quality using RAGAS.

Built with LangGraph, LlamaIndex, Qdrant, and a BYOK (Bring Your Own Key) LLM layer supporting Ollama, OpenAI, and Anthropic.

---

## Architecture

```
User (Streamlit UI)
        ↓
   FastAPI Backend
        ↓
   LangGraph Orchestrator
    ┌───────────────────────────────────┐
    │  Ingestion Agent                  │
    │  → PDF/DOCX/CSV/TXT/URL parser   │
    │  → Semantic + fixed chunking     │
    │  → Embedding → Qdrant index      │
    ├───────────────────────────────────┤
    │  Retrieval Agent                  │
    │  → Semantic search (Qdrant)      │
    │  → Cross-encoder reranking       │
    ├───────────────────────────────────┤
    │  Synthesis Agent                  │
    │  → Grounded answer generation    │
    │  → Inline [Context N] citations  │
    ├───────────────────────────────────┤
    │  Evaluation Agent                 │
    │  → RAGAS: Faithfulness           │
    │  → RAGAS: Answer Relevancy       │
    │  → RAGAS: Context Precision      │
    └───────────────────────────────────┘
        ↓
   BYOK Layer (litellm)
   Ollama | OpenAI | Anthropic
```

---

## Features

- **Multi-format ingestion** — PDF, DOCX, CSV, TXT, Markdown, and web URLs
- **Two chunking strategies** — semantic (paragraph-aware) and fixed (token-based)
- **Cross-encoder reranking** — improves retrieval precision significantly over naive top-k
- **Grounded answers with citations** — every answer references specific context chunks
- **RAGAS evaluation** — faithfulness, answer relevancy, context precision scored per query
- **BYOK LLM routing** — litellm routes to Ollama (default), OpenAI, or Anthropic
- **Configurable embeddings** — nomic-embed-text (local) or text-embedding-3-small (OpenAI)
- **LangGraph orchestration** — clean state machine, each agent is a discrete node
- **REST API** — full FastAPI backend, usable independently of the UI

---

## Tech Stack

| Layer | Tool |
|---|---|
| Orchestration | LangGraph |
| RAG framework | LlamaIndex |
| Vector DB | Qdrant (Docker) |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` |
| LLM routing | litellm |
| Evaluation | RAGAS |
| Backend | FastAPI |
| Frontend | Streamlit |
| Document parsing | PyMuPDF, python-docx, pandas, trafilatura |

---

## Quickstart

### 1. Clone and install

```bash
git clone https://github.com/yourusername/edis.git
cd edis
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env with your preferred LLM provider and keys
```

### 3. Start Qdrant

```bash
docker compose up -d
```

### 4. Pull embedding model (Ollama default)

```bash
ollama pull nomic-embed-text
ollama pull llama3.2
```

### 5. Start the backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

### 6. Start the frontend

```bash
cd frontend
streamlit run app.py
```

Open `http://localhost:8501`

---

## Configuration

All config is driven by `.env`. Key variables:

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `ollama` | `ollama` / `openai` / `anthropic` |
| `EMBEDDING_PROVIDER` | `ollama` | `ollama` / `openai` |
| `CHUNKING_STRATEGY` | `semantic` | `semantic` / `fixed` |
| `CHUNK_SIZE` | `512` | Words per chunk |
| `TOP_K` | `10` | Chunks retrieved before reranking |
| `RERANK_TOP_N` | `4` | Chunks kept after reranking |

---

## API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/health` | GET | Health check |
| `/ingest` | POST | Upload and ingest a file |
| `/ingest/url` | POST | Ingest a web URL |
| `/query` | POST | Ask a question |
| `/collection/info` | GET | Qdrant collection stats |
| `/collection` | DELETE | Wipe all indexed data |

### Example query

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main risk factors?",
    "skip_evaluation": false
  }'
```

### Example response

```json
{
  "query": "What are the main risk factors?",
  "answer": "Based on the documents, the main risk factors include... [Context 1][Context 3]",
  "citations": [
    {
      "index": 1,
      "source": "annual_report.pdf",
      "page_num": 12,
      "score": 0.91,
      "text_preview": "The company faces significant exposure to..."
    }
  ],
  "retrieval_stats": { "total_retrieved": 10, "total_reranked": 4, "duration_seconds": 0.8 },
  "synthesis_stats": { "model_used": "ollama/llama3.2", "provider": "ollama", "duration_seconds": 2.1 },
  "evaluation": {
    "faithfulness": 0.92,
    "answer_relevancy": 0.88,
    "context_precision": 0.85
  }
}
```

---

## Project Structure

```
edis/
├── backend/
│   ├── main.py                  # FastAPI entry point
│   ├── config.py                # Central config + BYOK routing
│   ├── agents/
│   │   ├── ingestion_agent.py   # Parse → chunk → embed → index
│   │   ├── retrieval_agent.py   # Semantic search + reranking
│   │   ├── synthesis_agent.py   # LLM answer generation
│   │   └── evaluation_agent.py  # RAGAS evaluation
│   ├── graph/
│   │   └── orchestrator.py      # LangGraph state graph
│   ├── parsers/
│   │   ├── pdf_parser.py
│   │   ├── docx_parser.py
│   │   ├── csv_parser.py
│   │   ├── txt_parser.py
│   │   ├── url_parser.py
│   │   └── __init__.py          # Parser router
│   ├── rag/
│   │   ├── embedder.py
│   │   ├── indexer.py
│   │   ├── retriever.py
│   │   └── reranker.py
│   └── evals/
│       └── ragas_eval.py
├── frontend/
│   └── app.py                   # Streamlit UI
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

---

## Why EDIS stands out

Most RAG portfolios are: load PDF → top-k search → dump into prompt → answer. EDIS goes further:

1. **Reranking** — cross-encoder reranking on top of semantic search cuts hallucination significantly
2. **Multi-agent architecture** — each stage is a discrete, testable LangGraph node
3. **Self-evaluation** — RAGAS scores tell you *how good* the answer is, not just what it is
4. **BYOK** — works locally with Ollama, no API key required
5. **Production patterns** — FastAPI backend, Docker Qdrant, config-driven, no hardcoded secrets

---

## License

MIT
