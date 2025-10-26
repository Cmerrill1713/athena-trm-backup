"""
Chat endpoint with Weaviate vector search (semantic RAG)
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import time
import logging
import hashlib
from typing import List

# ASI Safety - Judicial oversight
from api.judicial_client import submit_judicial_event

# Athena's personality
from api.athena_personality import get_athena_system_prompt

router = APIRouter()
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://athena-weaviate:8080")
DEFAULT_MODEL = os.getenv("LLM_MODEL", "qwen2.5:7b")

# Prometheus metrics (lazy-loaded)
uai_llm_calls = None
uai_llm_fail = None
uai_llm_lat_s = None
uai_rag_calls = None

def _init_metrics():
    global uai_llm_calls, uai_llm_fail, uai_llm_lat_s, uai_rag_calls
    try:
        from prometheus_client import Counter, Histogram
        uai_llm_calls = Counter("uai_llm_calls_total", "LLM calls", ["model"])
        uai_llm_fail = Counter("uai_llm_fail_total", "LLM fails", ["model", "reason"])
        uai_llm_lat_s = Histogram("uai_llm_latency_seconds", "LLM latency", ["model"])
        uai_rag_calls = Counter("uai_rag_calls_total", "RAG enrichment calls")
    except ImportError:
        logger.warning("prometheus_client not available")

_init_metrics()


async def get_embedding(text: str) -> List[float]:
    """Get text embedding from Ollama"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text[:2000]}
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def semantic_search(query: str, limit: int = 3) -> str:
    """
    Semantic RAG: Search Weaviate vector database
    """
    try:
        # Get query embedding
        query_embedding = await get_embedding(query)
        
        # Search Weaviate
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json={
                    "query": f"""
                    {{
                      Get {{
                        DocsV2(
                          nearVector: {{
                            vector: {query_embedding}
                          }}
                          limit: {limit}
                        ) {{
                          source
                          content
                          _additional {{
                            distance
                          }}
                        }}
                      }}
                    }}
                    """
                }
            )
            response.raise_for_status()
            
            results = response.json()["data"]["Get"]["DocsV2"]
            
            if not results:
                return ""
            
            # Format context with similarity scores
            context_parts = []
            for r in results:
                if r and r.get("content"):
                    similarity = 1 - r["_additional"]["distance"]
                    if similarity > 0.5:  # Only include if >50% similar
                        context_parts.append(
                            f"**From {r['source']}** (relevance: {similarity:.0%})\n{r['content']}"
                        )
            
            if not context_parts:
                return ""
            
            context = "\n\n".join(context_parts)
            
            return f"""
<knowledge_base>
{context}
</knowledge_base>

Use the above knowledge base to answer accurately. Cite sources when possible.
"""
    
    except Exception as e:
        logger.warning(f"Semantic search failed: {e}")
        return ""  # Fail gracefully


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
    OpenAI-compatible chat completions with semantic RAG + Athena's personality
    """
    model = req.model or DEFAULT_MODEL
    
    # Extract user query
    user_query = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_query = msg.content
            break
    
    # Semantic RAG enrichment
    rag_context = ""
    if user_query:
        rag_context = await semantic_search(user_query)
        if rag_context and uai_rag_calls:
            uai_rag_calls.inc()
    
    # Build enriched messages with Athena's personality
    enriched_messages = []
    
    # 1. Athena's personality (ALWAYS FIRST)
    enriched_messages.append({
        "role": "system",
        "content": get_athena_system_prompt()
    })
    
    # 2. RAG context (if available)
    if rag_context:
        enriched_messages.append({
            "role": "system",
            "content": rag_context
        })
    
    # 3. User conversation history
    for m in req.messages:
        enriched_messages.append({
            "role": m.role,
            "content": m.content
        })
    
    # Build Ollama request
    payload = {
        "model": model,
        "messages": enriched_messages,
        "stream": False,
        "options": {
            "temperature": req.temperature or 0.7,  # Increased for more natural responses
            "num_predict": 512
        }
    }
    
    t0 = time.time()
    
    try:
        logger.info(f"Calling Ollama as Athena (RAG: {bool(rag_context)})")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
        
        content = (data.get("message") or {}).get("content", "")
        
        # Metrics
        if uai_llm_calls:
            uai_llm_calls.labels(model).inc()
            uai_llm_lat_s.labels(model).observe(time.time() - t0)
        
        logger.info(f"Success: {len(content)} chars in {time.time()-t0:.2f}s (RAG: {bool(rag_context)})")
        
        # ASI Safety: Submit chat decision to judicial oversight
        try:
            event_id = f"chat-{hashlib.md5(req.messages[-1].content.encode()).hexdigest()[:8]}-{int(time.time())}"
            severity = 0.15 if rag_context else 0.05  # Higher if using RAG
            
            await submit_judicial_event(
                event_id=event_id,
                actor_id="uai-chat-agent",
                article="II",  # Data access compliance
                severity=severity,
                confidence=0.85,
                classification="chat_completion",
                details={
                    "model": model,
                    "rag_used": bool(rag_context),
                    "tokens": len(content.split()),
                    "latency_ms": (time.time() - t0) * 1000
                }
            )
        except Exception as e:
            logger.debug(f"Judicial oversight failed (non-critical): {e}")
        
        
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
        logger.error(f"Ollama HTTP error: {e.response.status_code}")
        if uai_llm_fail:
            uai_llm_fail.labels(model, "http_error").inc()
        raise HTTPException(status_code=502, detail=f"Ollama error: {e.response.status_code}")
    except httpx.TimeoutException:
        logger.error("Ollama timeout")
        if uai_llm_fail:
            uai_llm_fail.labels(model, "timeout").inc()
        raise HTTPException(status_code=504, detail="Request timeout")
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        if uai_llm_fail:
            uai_llm_fail.labels(model, type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))
