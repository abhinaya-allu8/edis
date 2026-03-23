#!/bin/bash
# EDIS — Sequential installer
# Run from the edis/ root directory: bash install.sh

set -e
echo "=== EDIS Installer ==="

echo "[1/8] Core..."
pip install fastapi uvicorn python-dotenv pydantic python-multipart aiofiles httpx

echo "[2/8] LangChain stack..."
pip install "langchain==1.2.13" "langchain-core==1.2.20" "langchain-community==0.4.1" "langgraph==1.1.3"

echo "[3/8] LangChain integrations..."
pip install langchain-openai langchain-anthropic

echo "[4/8] LiteLLM..."
pip install litellm

echo "[5/8] Document parsers..."
pip install pymupdf python-docx pandas trafilatura requests

echo "[6/8] Vector DB + Reranker..."
pip install qdrant-client sentence-transformers

echo "[7/8] RAGAS + datasets..."
pip install "ragas==0.2.15" datasets nest-asyncio

echo "[8/8] Streamlit + LlamaIndex..."
pip install streamlit llama-index llama-index-vector-stores-qdrant llama-index-embeddings-ollama llama-index-embeddings-openai python-dotenv

echo ""
echo "=== Install complete ==="
echo ""
echo "Next steps:"
echo "  1. cp .env.example .env  (then edit with your config)"
echo "  2. docker compose up -d  (start Qdrant)"
echo "  3. ollama pull nomic-embed-text && ollama pull llama3.2"
echo "  4. cd backend && uvicorn main:app --reload --port 8000"
echo "  5. cd frontend && streamlit run app.py"
