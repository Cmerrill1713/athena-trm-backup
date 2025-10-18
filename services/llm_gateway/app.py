#!/usr/bin/env python3
"""
LLM Gateway - Minimal, undeniable Ollama caller
Port 8015 - OpenAI-style API that actually calls Ollama

Bypasses broken router/UAT complexity.
Simple, proven, observable.
"""

import os
import time
import uuid
import logging
from typing import List, Optional, Literal
from fastapi import FastAPI, Body
from pydantic import BaseModel
import httpx
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
MODEL = os.getenv("MODEL", "qwen2.5:0.5b")
BUILD_SHA = os.getenv("BUILD_SHA", "dev")

log = logging.getLogger("llm.gateway")
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

llm_calls_total = Counter("llm_gateway_calls_total", "LLM calls", ["provider", "model"])
llm_fail_total = Counter("llm_gateway_fail_total", "LLM failures", ["provider", "model", "reason"])
llm_latency_s = Histogram("llm_gateway_latency_seconds", "LLM latency", ["provider", "model"])

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str

class ChatCompletionRequest(BaseModel):
    model: Optional[str] = None
    messages: List[Message]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = 0.7
    stream: Optional[bool] = False

app = FastAPI(title="LLM Gateway", description="Minimal Ollama caller with OpenAI-style API")

@app.get("/health")
def health():
    return {"ok": True, "service": "llm-gateway", "model": MODEL}

@app.get("/ready")
def ready():
    """Check if Ollama is reachable."""
    try:
        with httpx.Client(timeout=2.0) as c:
            r = c.get(f"{OLLAMA_URL}/api/tags")
            r.raise_for_status()
            models = r.json().get("models", [])
            return {"ready": True, "ollama": OLLAMA_URL, "models_available": len(models)}
    except Exception as e:
        log.error(f"Ollama not ready: {e}")
        return {"ready": False, "error": str(e), "ollama": OLLAMA_URL}

@app.get("/version")
def version():
    return {"build": BUILD_SHA, "model": MODEL, "ollama": OLLAMA_URL}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.post("/v1/chat/completions")
def chat(req: ChatCompletionRequest = Body(...)):
    """OpenAI-compatible chat endpoint that calls Ollama."""
    rid = str(uuid.uuid4())[:8]
    model = req.model or MODEL
    
    # Build Ollama payload
    payload = {
        "model": model,
        "messages": [m.model_dump() for m in req.messages],
        "stream": False,
        "options": {"temperature": req.temperature}
    }
    
    log.info(f"[{rid}] Chat request: model={model}, messages={len(req.messages)}")
    
    t0 = time.time()
    try:
        with httpx.Client(timeout=30.0) as c:
            r = c.post(f"{OLLAMA_URL}/api/chat", json=payload)
            r.raise_for_status()
            resp = r.json()
        
        dt = time.time() - t0
        llm_calls_total.labels(provider="ollama", model=model).inc()
        llm_latency_s.labels(provider="ollama", model=model).observe(dt)
        
        # Extract content from Ollama response
        content = resp.get("message", {}).get("content", "")
        
        log.info(f"[{rid}] Success: {len(content)} chars in {dt:.2f}s")
        
        # Return OpenAI-style response
        return {
            "id": f"cmpl-{rid}",
            "object": "chat.completion",
            "model": model,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": resp.get("prompt_eval_count"),
                "completion_tokens": resp.get("eval_count"),
                "total_tokens": resp.get("prompt_eval_count", 0) + resp.get("eval_count", 0)
            }
        }
        
    except httpx.TimeoutException as e:
        llm_fail_total.labels(provider="ollama", model=model, reason="timeout").inc()
        log.error(f"[{rid}] Timeout: {e}")
        return {"error": {"message": f"Ollama timeout: {e}", "type": "timeout"}}, 504
        
    except Exception as e:
        llm_fail_total.labels(provider="ollama", model=model, reason=type(e).__name__).inc()
        log.error(f"[{rid}] LLM error: {e}")
        return {"error": {"message": str(e), "type": "llm_error"}}, 502

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8015"))
    host = os.getenv("HOST", "127.0.0.1")
    log.info(f"🚀 Starting LLM Gateway on {host}:{port}")
    log.info(f"   Ollama: {OLLAMA_URL}")
    log.info(f"   Model: {MODEL}")
    uvicorn.run(app, host=host, port=port, log_level="info")

