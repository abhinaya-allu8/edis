"""
EDIS — Config
Centralizes all environment-driven config. Single source of truth.
"""

import os
from dotenv import load_dotenv

load_dotenv()


# ─── LLM ────────────────────────────────────────────────────────────────────

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "ollama").lower()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def get_litellm_model_string() -> str:
    """Returns the litellm-compatible model string based on LLM_PROVIDER."""
    if LLM_PROVIDER == "openai":
        return OPENAI_MODEL
    elif LLM_PROVIDER == "anthropic":
        return f"anthropic/{ANTHROPIC_MODEL}"
    elif LLM_PROVIDER == "ollama":
        return f"ollama/{OLLAMA_MODEL}"
    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")


def get_litellm_kwargs() -> dict:
    """Returns extra kwargs for litellm.completion depending on provider."""
    if LLM_PROVIDER == "openai":
        return {"api_key": OPENAI_API_KEY}
    elif LLM_PROVIDER == "anthropic":
        return {"api_key": ANTHROPIC_API_KEY}
    elif LLM_PROVIDER == "ollama":
        return {"api_base": OLLAMA_BASE_URL}
    return {}


# ─── Embeddings ──────────────────────────────────────────────────────────────

EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "ollama").lower()
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")


# ─── Qdrant ──────────────────────────────────────────────────────────────────

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", 6333))
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "edis_docs")


# ─── Chunking ────────────────────────────────────────────────────────────────

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 512))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 64))
CHUNKING_STRATEGY = os.getenv("CHUNKING_STRATEGY", "semantic").lower()  # semantic | fixed


# ─── Retrieval ───────────────────────────────────────────────────────────────

TOP_K = int(os.getenv("TOP_K", 10))
RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", 4))
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2")
