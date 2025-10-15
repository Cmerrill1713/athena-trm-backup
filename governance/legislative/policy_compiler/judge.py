# bridge/judge.py - LLM Self-Evaluation (flagged)
import os
import httpx
from typing import Dict

EVAL_ENABLED = os.getenv("EVAL_ENABLED", "false").lower() == "true"
EVAL_MODEL = os.getenv("EVAL_MODEL", "qwen2.5:7b")
OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")

async def evaluate_reply(reply: str, user_prompt: str) -> Dict[str, float]:
    """Evaluate reply for helpfulness, factuality, clarity (1-10)"""
    if not EVAL_ENABLED:
        return {}

    prompt = f"""
    Evaluate this AI response on a scale of 1-10:
    User prompt: {user_prompt}
    AI response: {reply}

    Return JSON: {{"helpfulness": int, "factuality": int, "clarity": int}}
    """

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": EVAL_MODEL, "prompt": prompt, "stream": False}
            )
            if response.status_code == 200:
                data = response.json()
                # Parse JSON from response
                import json
                scores = json.loads(data["response"])
                return scores
    except Exception as e:
        print(f"Judge evaluation failed: {e}")

    return {}
