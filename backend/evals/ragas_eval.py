"""
EDIS — RAGAS Evaluation
Evaluates synthesis output on three metrics:
  - Faithfulness: Is the answer grounded in the context?
  - Answer Relevancy: Does the answer address the question?
  - Context Precision: Are the retrieved chunks actually relevant?

Uses the RAGAS library with the configured LLM backend.
"""

from typing import List, Optional
import time
import nest_asyncio
nest_asyncio.apply()

import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config import get_litellm_model_string, get_litellm_kwargs, LLM_PROVIDER


def run_ragas_eval(
    question: str,
    answer: str,
    contexts: List[str],
    ground_truth: Optional[str] = None,
) -> dict:
    """
    Runs RAGAS evaluation on a single QA sample.

    Args:
        question: The user query.
        answer: The generated answer from synthesis agent.
        contexts: List of retrieved context strings used for generation.
        ground_truth: Optional reference answer for additional metrics.

    Returns:
        Dict with metric scores and metadata.
    """
    start = time.time()

    if not contexts:
        return {
            "status": "skipped",
            "reason": "No context chunks available for evaluation.",
            "duration_seconds": 0,
        }

    try:
        from ragas import evaluate
        from ragas.metrics import faithfulness, answer_relevancy, context_precision
        from datasets import Dataset

        # Build RAGAS dataset — ragas 0.2.x schema
        data = {
            "question": [question],
            "answer": [answer],
            "contexts": [contexts],
        }
        if ground_truth:
            data["ground_truth"] = [ground_truth]

        dataset = Dataset.from_dict(data)

        # Build LangChain LLM wrapper for RAGAS
        if LLM_PROVIDER == "ollama":
            from langchain_community.chat_models import ChatOllama
            from config import OLLAMA_BASE_URL, OLLAMA_MODEL
            ragas_llm = ChatOllama(model=OLLAMA_MODEL, base_url=OLLAMA_BASE_URL)
        elif LLM_PROVIDER == "openai":
            from langchain_openai import ChatOpenAI
            from config import OPENAI_API_KEY, OPENAI_MODEL
            ragas_llm = ChatOpenAI(model=OPENAI_MODEL, api_key=OPENAI_API_KEY)
        elif LLM_PROVIDER == "anthropic":
            from langchain_anthropic import ChatAnthropic
            from config import ANTHROPIC_API_KEY, ANTHROPIC_MODEL
            ragas_llm = ChatAnthropic(model=ANTHROPIC_MODEL, api_key=ANTHROPIC_API_KEY)
        else:
            raise ValueError(f"Unsupported LLM_PROVIDER for RAGAS: {LLM_PROVIDER}")

        # ragas 0.2.x: pass llm directly to evaluate()
        result = evaluate(
            dataset=dataset,
            metrics=[faithfulness, answer_relevancy, context_precision],
            llm=ragas_llm,
            raise_exceptions=False,
        )

        # ragas 0.2.x returns an EvaluationResult — convert to dict via pandas
        scores = result.to_pandas().iloc[0].to_dict()

        return {
            "status": "success",
            "faithfulness": round(float(scores.get("faithfulness", 0)), 4),
            "answer_relevancy": round(float(scores.get("answer_relevancy", 0)), 4),
            "context_precision": round(float(scores.get("context_precision", 0)), 4),
            "duration_seconds": round(time.time() - start, 2),
        }

    except Exception as e:
        return {
            "status": "failed",
            "error": str(e),
            "faithfulness": None,
            "answer_relevancy": None,
            "context_precision": None,
            "duration_seconds": round(time.time() - start, 2),
        }
