import os
import json
from typing import Dict
import httpx

EVAL_ENABLED = os.getenv("EVAL_ENABLED", "false").lower() == "true"
EVAL_MODEL = os.getenv("EVAL_MODEL", "qwen2.5:7b")
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")

_prompt_tpl = """SYSTEM: Score assistant answer with 1–10 integers.
- Helpfulness: actionable vs. vague
- Factuality: likely correct given context
- Clarity: concise, well-structured

USER:
{user}

CONTEXT:
{ctx}

ASSISTANT:
{reply}

Return strict JSON: {{"helpfulness":7,"factuality":7,"clarity":7,"notes":"<=240 chars"}}"""

async def judge_response(user_text: str, reply_text: str, context: str|None) -> Dict[str, float|str]:
    payload = {"model": EVAL_MODEL, "format": "json", "prompt": _prompt_tpl.format(
        user=user_text, ctx=context or "(none)", reply=reply_text)}
    try:
        async with httpx.AsyncClient(timeout=30) as cx:
            r = await cx.post(f"{OLLAMA_HOST}/api/generate", json=payload)
            r.raise_for_status()
            data = r.json()
            out = json.loads(data.get("response","{}"))
            return {
                "helpfulness": float(out.get("helpfulness", 5)),
                "factuality":  float(out.get("factuality",  5)),
                "clarity":     float(out.get("clarity",     5)),
                "notes":       str(out.get("notes", ""))[:240]
            }
    except Exception:
        return {"helpfulness":5.0,"factuality":5.0,"clarity":5.0,"notes":"eval_error"}
