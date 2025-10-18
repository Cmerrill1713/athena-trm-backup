"""
Chat endpoint for UAI → Ollama
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import time
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")

# Prometheus metrics (will be lazy-loaded to avoid import errors)
uai_llm_calls = None
uai_llm_fail = None
uai_llm_lat_s = None

def _init_metrics():
    global uai_llm_calls, uai_llm_fail, uai_llm_lat_s
    try:
        from prometheus_client import Counter, Histogram
        uai_llm_calls = Counter("uai_llm_calls_total", "LLM calls", ["model"])
        uai_llm_fail = Counter("uai_llm_fail_total", "LLM fails", ["model", "reason"])
        uai_llm_lat_s = Histogram("uai_llm_latency_seconds", "LLM latency", ["model"])
    except ImportError:
        logger.warning("prometheus_client not available, metrics disabled")

_init_metrics()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    stream: bool | None = False
    temperature: float | None = 0.2


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    OpenAI-compatible chat completions endpoint that proxies to Ollama
    """
    model = req.model or DEFAULT_MODEL
    
    # Build Ollama request
    payload = {
        "model": model,
        "messages": [{"role": m.role, "content": m.content} for m in req.messages],
        "stream": False,
        "options": {
            "temperature": req.temperature or 0.2,
            "num_predict": 512
        }
    }
    
    t0 = time.time()
    
    try:
        logger.info(f"Calling Ollama at {OLLAMA_URL} with model {model}")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        # Extract response
        content = (data.get("message") or {}).get("content", "")
        
        # Metrics
        if uai_llm_calls:
            uai_llm_calls.labels(model).inc()
            uai_llm_lat_s.labels(model).observe(time.time() - t0)
        
        logger.info(f"Success: {len(content)} chars in {time.time()-t0:.2f}s")
        
        # Return OpenAI-compatible format
        return {
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": content
                },
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(m.content.split()) for m in req.messages),
                "completion_tokens": len(content.split()),
                "total_tokens": sum(len(m.content.split()) for m in req.messages) + len(content.split())
            }
        }
        
    except httpx.HTTPStatusError as e:
        logger.error(f"Ollama HTTP error: {e.response.status_code} - {e.response.text}")
        if uai_llm_fail:
            uai_llm_fail.labels(model, "http_error").inc()
        raise HTTPException(
            status_code=502,
            detail=f"Ollama returned {e.response.status_code}: {e.response.text}"
        )
    except httpx.TimeoutException:
        logger.error("Ollama request timed out")
        if uai_llm_fail:
            uai_llm_fail.labels(model, "timeout").inc()
        raise HTTPException(status_code=504, detail="Request to Ollama timed out")
    except Exception as e:
        logger.error(f"Unexpected error: {type(e).__name__}: {e}")
        if uai_llm_fail:
            uai_llm_fail.labels(model, type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))
