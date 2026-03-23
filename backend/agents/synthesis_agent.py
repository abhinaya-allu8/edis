"""
EDIS — Synthesis Agent
Generates grounded answers with inline citations using retrieved context.
Routes LLM calls through litellm for BYOK support (Ollama / OpenAI / Anthropic).
"""

from dataclasses import dataclass, field
from typing import List, Optional
import time

import litellm

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import get_litellm_model_string, get_litellm_kwargs
from agents.retrieval_agent import RetrievalResult

litellm.set_verbose = False


SYSTEM_PROMPT = """You are EDIS, an Enterprise Document Intelligence System.
Your job is to answer questions strictly based on the provided context chunks.

Rules:
1. Only use information from the provided context. Do not use prior knowledge.
2. Cite your sources using inline markers like [Context 1], [Context 2], etc.
3. If the context does not contain enough information to answer, say so clearly.
4. Be concise, precise, and structured in your answers.
5. For numerical data, always mention the source document.
6. If multiple contexts contradict each other, flag the contradiction explicitly.
"""

ANSWER_PROMPT_TEMPLATE = """
Context:
{context}

---

Question: {question}

Instructions:
- Answer using only the context above.
- Use [Context N] inline citations wherever you draw from a specific chunk.
- If the answer is not in the context, respond: "The provided documents do not contain sufficient information to answer this question."

Answer:
"""


@dataclass
class SynthesisResult:
    query: str
    answer: str
    citations: List[dict]
    model_used: str
    provider: str
    duration_seconds: float
    status: str          # success | failed | no_context
    error: Optional[str] = None

    def formatted_answer(self) -> str:
        """Returns answer + formatted citation list."""
        if not self.citations:
            return self.answer

        citation_block = "\n\n**Sources:**\n"
        for c in self.citations:
            citation_block += (
                f"- [Context {c['index']}] {c['source']} "
                f"(page {c['page_num']}, score: {c['score']})\n"
            )
        return self.answer + citation_block


def run_synthesis(
    query: str,
    retrieval_result: RetrievalResult,
    max_tokens: int = 1024,
) -> SynthesisResult:
    """
    Generates a grounded answer using retrieved context via litellm.

    Args:
        query: Original user question.
        retrieval_result: Output from RetrievalAgent.
        max_tokens: Max tokens for LLM response.

    Returns:
        SynthesisResult with answer, citations, and metadata.
    """
    start = time.time()
    model = get_litellm_model_string()
    provider = model.split("/")[0] if "/" in model else "openai"
    kwargs = get_litellm_kwargs()

    # Handle empty retrieval
    if retrieval_result.status == "empty" or not retrieval_result.chunks:
        return SynthesisResult(
            query=query,
            answer="The provided documents do not contain sufficient information to answer this question.",
            citations=[],
            model_used=model,
            provider=provider,
            duration_seconds=round(time.time() - start, 2),
            status="no_context",
        )

    context_string = retrieval_result.to_context_string()
    citations = retrieval_result.to_citations()

    prompt = ANSWER_PROMPT_TEMPLATE.format(
        context=context_string,
        question=query,
    )

    try:
        print(f"[SynthesisAgent] Calling LLM: {model}")

        response = litellm.completion(
            model=model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=0.1,   # Low temp for factual grounding
            **kwargs,
        )

        answer = response.choices[0].message.content.strip()
        print(f"[SynthesisAgent] Answer generated ({len(answer)} chars).")

        return SynthesisResult(
            query=query,
            answer=answer,
            citations=citations,
            model_used=model,
            provider=provider,
            duration_seconds=round(time.time() - start, 2),
            status="success",
        )

    except Exception as e:
        return SynthesisResult(
            query=query,
            answer="",
            citations=[],
            model_used=model,
            provider=provider,
            duration_seconds=round(time.time() - start, 2),
            status="failed",
            error=str(e),
        )
