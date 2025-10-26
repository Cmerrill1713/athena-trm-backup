"""
Chat endpoint - Athena with dual-model intelligence (MLX + Ollama)
Uses MLX for fast responses, Ollama for complex reasoning
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
MLX_URL = os.getenv("MLX_URL", "http://localhost:8001")

# Model selection
MLX_MODEL = os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-0.5B-Instruct-4bit")  # Fast
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")  # Capable

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


def assess_complexity(query: str, has_rag: bool) -> str:
    """
    Assess if query needs MLX (fast) or Ollama (capable)
    
    Returns: "mlx" or "ollama"
    """
    query_lower = query.lower()
    
    # Complex queries → Ollama
    complex_indicators = [
        "explain", "why", "how does", "what is the difference",
        "compare", "analyze", "solve", "calculate", "reason",
        "multi-step", "detailed", "comprehensive"
    ]
    
    if any(indicator in query_lower for indicator in complex_indicators):
        return "ollama"
    
    # Has RAG context → Use Ollama for better synthesis
    if has_rag:
        return "ollama"
    
    # Long queries → Ollama
    if len(query.split()) > 15:
        return "ollama"
    
    # Simple/fast queries → MLX
    return "mlx"


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
    """Semantic RAG: Search Weaviate vector database"""
    try:
        query_embedding = await get_embedding(query)
        
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
            
            context_parts = []
            for r in results:
                if r and r.get("content"):
                    similarity = 1 - r["_additional"]["distance"]
                    if similarity > 0.5:
                        context_parts.append(
                            f"**From {r['source']}** (relevance: {similarity:.0%})\n{r['content']}"
                        )
            
            if not context_parts:
                return ""
            
            context = "\n\n".join(context_parts)
            return f"""<knowledge_base>
{context}
</knowledge_base>

Use the above knowledge base to answer accurately. Cite sources when possible."""
    
    except Exception as e:
        logger.warning(f"Semantic search failed: {e}")
        return ""


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str | None = None
    messages: list[Message]
    stream: bool | None = False
    temperature: float | None = 0.7


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    Athena conversational AI with dual-model intelligence
    
    - MLX (mlx-community/Qwen2.5-0.5B-4bit) for fast, simple queries
    - Ollama (qwen2.5:7b) for complex reasoning
    - Automatic selection based on complexity
    - Always includes personality + RAG
    """
    
    # Extract user query for RAG
    user_query = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_query = msg.content
            break
    
    # RAG: Semantic search
    rag_context = ""
    if user_query:
        rag_context = await semantic_search(user_query)
        if rag_context and uai_rag_calls:
            uai_rag_calls.inc()
    
    # Assess complexity and choose model
    preferred_backend = assess_complexity(user_query, bool(rag_context))
    
    # Build messages with Athena's personality
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
    
    # 3. Conversation history
    for m in req.messages:
        enriched_messages.append({
            "role": m.role,
            "content": m.content
        })
    
    t0 = time.time()
    
    # Try preferred backend first, fallback to alternate
    backends = [preferred_backend, "ollama" if preferred_backend == "mlx" else "mlx"]
    
    for backend in backends:
        try:
            if backend == "mlx":
                # Call MLX directly
                logger.info(f"Athena → MLX (fast, RAG: {bool(rag_context)})")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{MLX_URL}/v1/chat/completions",
                        json={
                            "model": MLX_MODEL,
                            "messages": enriched_messages,
                            "temperature": req.temperature or 0.7,
                            "max_tokens": 512
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                model_used = "mlx"
                
            else:  # ollama
                # Call Ollama directly
                logger.info(f"Athena → Ollama (capable, RAG: {bool(rag_context)})")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        f"{OLLAMA_URL}/api/chat",
                        json={
                            "model": OLLAMA_MODEL,
                            "messages": enriched_messages,
                            "stream": False,
                            "options": {
                                "temperature": req.temperature or 0.7,
                                "num_predict": 512
                            }
                        }
                    )
                    response.raise_for_status()
                    data = response.json()
                
                content = (data.get("message") or {}).get("content", "")
                model_used = "ollama"
            
            # Success! Break out of fallback loop
            latency_ms = (time.time() - t0) * 1000
            
            # Metrics
            if uai_llm_calls:
                uai_llm_calls.labels(model_used).inc()
                uai_llm_lat_s.labels(model_used).observe(time.time() - t0)
            
            logger.info(f"Success: {len(content)} chars in {latency_ms:.0f}ms (backend: {model_used})")
            
            # ASI Safety
            try:
                event_id = f"chat-{hashlib.md5(req.messages[-1].content.encode()).hexdigest()[:8]}-{int(time.time())}"
                severity = 0.15 if rag_context else 0.05
                
                await submit_judicial_event(
                    event_id=event_id,
                    actor_id="uai-chat-agent",
                    article="II",
                    severity=severity,
                    confidence=0.85,
                    classification="chat_completion",
                    details={
                        "backend": model_used,
                        "rag_used": bool(rag_context),
                        "tokens": len(content.split()),
                        "latency_ms": latency_ms
                    }
                )
            except Exception as e:
                logger.debug(f"Judicial oversight failed (non-critical): {e}")
            
            
            return {
                "object": "chat.completion",
                "model": model_used,
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
                },
                "_athena": {
                    "backend": model_used,
                    "rag_enabled": bool(rag_context),
                    "personality": True,
                    "latency_ms": latency_ms,
                    "preferred": backend == preferred_backend
                }
            }
            
        except Exception as e:
            logger.warning(f"{backend.upper()} failed: {e}, trying fallback...")
            continue
    
    # Both backends failed
    logger.error("Both MLX and Ollama failed")
    if uai_llm_fail:
        uai_llm_fail.labels("both", "all_failed").inc()
    raise HTTPException(status_code=502, detail="All AI backends unavailable")
