"""
EDIS — Embedder
Wraps embedding generation. Routes to Ollama or OpenAI based on config.
Returns raw float vectors for indexing.
"""

from typing import List

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import EMBEDDING_PROVIDER, EMBEDDING_MODEL, OLLAMA_BASE_URL, OPENAI_API_KEY


def get_embedding(text: str) -> List[float]:
    """Embed a single string. Returns a float vector."""
    return get_embeddings([text])[0]


def get_embeddings(texts: List[str]) -> List[List[float]]:
    """
    Embed a batch of strings.
    Routes to Ollama or OpenAI based on EMBEDDING_PROVIDER.
    """
    if not texts:
        return []

    if EMBEDDING_PROVIDER == "ollama":
        return _ollama_embed(texts)
    elif EMBEDDING_PROVIDER == "openai":
        return _openai_embed(texts)
    else:
        raise ValueError(f"Unsupported EMBEDDING_PROVIDER: {EMBEDDING_PROVIDER}")


def _ollama_embed(texts: List[str]) -> List[List[float]]:
    import requests

    vectors = []
    for text in texts:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/embeddings",
            json={"model": EMBEDDING_MODEL, "prompt": text},
            timeout=60,
        )
        response.raise_for_status()
        vectors.append(response.json()["embedding"])

    return vectors


def _openai_embed(texts: List[str]) -> List[List[float]]:
    from openai import OpenAI

    client = OpenAI(api_key=OPENAI_API_KEY)
    response = client.embeddings.create(model=EMBEDDING_MODEL, input=texts)
    return [item.embedding for item in response.data]


def get_embedding_dimension() -> int:
    """
    Returns the embedding dimension for the configured model.
    Needed to create the Qdrant collection with the right vector size.
    """
    dimensions = {
        # Ollama models
        "nomic-embed-text": 768,
        "mxbai-embed-large": 1024,
        "bge-m3": 1024,
        # OpenAI models
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }
    dim = dimensions.get(EMBEDDING_MODEL)
    if dim is None:
        # Fallback: generate one test embedding and measure
        test_vec = get_embedding("dimension probe")
        return len(test_vec)
    return dim
