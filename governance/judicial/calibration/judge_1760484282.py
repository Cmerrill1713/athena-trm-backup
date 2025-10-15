# LLM Self-Evaluation Layer
# Automated quality assessment for response optimization

import json
import logging
import os
from typing import Dict, Optional

import httpx

logger = logging.getLogger(__name__)

# Configuration
EVAL_ENABLED = os.getenv("EVAL_ENABLED", "false").lower() == "true"
EVAL_MODEL = os.getenv("EVAL_MODEL", "qwen2.5:7b")  # Use a small, fast model
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://127.0.0.1:11434")


async def call_ollama_json(model: str, prompt: str) -> Dict:
    """Call Ollama and parse JSON response."""
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",  # Request JSON format
                    "options": {
                        "temperature": 0.1,  # Low temperature for consistent scoring
                        "top_p": 0.9
                    }
                }
            )

            if response.status_code == 200:
                data = response.json()
                response_text = data.get("response", "")

                # Parse JSON from response
                try:
                    return json.loads(response_text.strip())
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response: {response_text[:200]}...")
                    return {}
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return {}

    except Exception as e:
        logger.error(f"LLM judge call failed: {e}")
        return {}


async def judge_response(user_text: str, reply_text: str, context: Optional[str] = None) -> Dict[str, float]:
    """
    Evaluate a response using LLM-based quality assessment.

    Returns dict with helpfulness, factuality, clarity scores (1-10) and notes.
    """
    if not EVAL_ENABLED:
        return {"helpfulness": 5.0, "factuality": 5.0, "clarity": 5.0, "notes": "eval_disabled"}

    # Create evaluation prompt
    prompt = f"""SYSTEM: You score assistant answers with 3 metrics from 1–10.
- Helpfulness: Did it directly address the user's need with actionable detail?
- Factuality: Is it likely correct and non-hallucinatory given the provided context?
- Clarity: Is it concise, structured, and easy to follow?

USER MESSAGE:
{user_text}

CONTEXT (if any):
{context or "(none)"}

ASSISTANT REPLY:
{reply_text}

Return strict JSON:
{{"helpfulness": 1, "factuality": 1, "clarity": 1, "notes": "..."}}"""

    try:
        # Call LLM for evaluation
        result = await call_ollama_json(EVAL_MODEL, prompt)

        if not result:
            return {"helpfulness": 5.0, "factuality": 5.0, "clarity": 5.0, "notes": "eval_failed"}

        # Extract and validate scores
        helpfulness = float(result.get("helpfulness", 5))
        factuality = float(result.get("factuality", 5))
        clarity = float(result.get("clarity", 5))
        notes = str(result.get("notes", ""))[:240]  # Limit notes length

        # Clamp scores to 1-10 range
        helpfulness = max(1, min(10, helpfulness))
        factuality = max(1, min(10, factuality))
        clarity = max(1, min(10, clarity))

        return {
            "helpfulness": helpfulness,
            "factuality": factuality,
            "clarity": clarity,
            "notes": notes
        }

    except Exception as e:
        logger.error(f"Response evaluation failed: {e}")
        return {"helpfulness": 5.0, "factuality": 5.0, "clarity": 5.0, "notes": f"eval_error: {str(e)[:200]}"}


def save_eval_results(interaction_id: str, evaluator: str, metrics: Dict[str, float]):
    """Save evaluation results to database."""
    try:
        # Note: In production, use proper DB connection pooling
        # For now, we'll log the results for processing
        logger.info("eval_results_saved", {
            "interaction_id": interaction_id,
            "evaluator": evaluator,
            "helpfulness": metrics["helpfulness"],
            "factuality": metrics["factuality"],
            "clarity": metrics["clarity"],
            "notes": metrics["notes"][:100]  # Truncate for logging
        })

        # TODO: Implement actual DB insert
        # INSERT INTO eval_results (interaction_id, evaluator, metric, score, details)
        # VALUES ($1, $2, $3, $4, $5) for each metric

    except Exception as e:
        logger.error(f"Failed to save eval results: {e}")


# Convenience functions
async def evaluate_and_save(user_text: str, reply_text: str, interaction_id: str, context: Optional[str] = None):
    """Evaluate response and save results."""
    if not EVAL_ENABLED:
        return

    metrics = await judge_response(user_text, reply_text, context)
    save_eval_results(interaction_id, "llm-judge:v1", metrics)
    return metrics
