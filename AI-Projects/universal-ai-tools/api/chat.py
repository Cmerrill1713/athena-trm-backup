"""
Chat endpoint - Athena with REAL-TIME LEARNING from conversation
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import time
import logging
import hashlib
from typing import List, Dict, Any
import json

# ASI Safety - Judicial oversight
from api.judicial_client import submit_judicial_event

# Athena's base personality
from api.athena_personality import get_athena_system_prompt

router = APIRouter()
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://athena-weaviate:8080")
MLX_URL = os.getenv("MLX_URL", "http://localhost:8001")

# Model selection
MLX_MODEL = os.getenv("MLX_MODEL", "mlx-community/Qwen2.5-0.5B-Instruct-4bit")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# In-memory conversation tracking (should be Redis in production)
conversations: Dict[str, List[Dict]] = {}
user_preferences: Dict[str, Dict[str, Any]] = {}

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


def detect_user_correction(messages: List[Dict]) -> str:
    """
    Detect if user is correcting Athena's behavior
    Returns: correction instruction or empty string
    """
    if len(messages) < 2:
        return ""
    
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").lower()
            break
    
    # Correction patterns
    corrections = {
        "be brief": "The user wants VERY brief responses (1-2 sentences max). No lists, no explanations unless asked.",
        "be simple": "The user wants simple, direct answers. Don't over-explain.",
        "just say": "Match the user's style exactly. If they say 'hi', you say 'hi' back - nothing more.",
        "don't have to": "The user is telling you to stop doing something. Adapt immediately.",
        "you're being": "The user is giving feedback on your tone/style. Adjust now.",
        "stop": "The user wants you to stop your current behavior immediately.",
        "i'm suggesting": "The user is giving you explicit direction. Follow it precisely.",
        "you only need": "The user is setting a boundary. Respect it."
    }
    
    for pattern, instruction in corrections.items():
        if pattern in last_user_msg:
            logger.info(f"🎯 Detected user correction: '{pattern}' → adjusting behavior")
            return f"\n\n🚨 IMPORTANT CORRECTION: {instruction}\nApply this change to your NEXT response!"
    
    return ""


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

Use the above knowledge base to answer accurately."""
    
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
    conversation_id: str | None = "default"  # Track conversations


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    Athena with REAL-TIME LEARNING
    
    - Detects user corrections and adapts IMMEDIATELY
    - Tracks conversation history
    - Learns user preferences
    - Adjusts behavior based on feedback
    """
    
    conversation_id = req.conversation_id or "default"
    
    # Track conversation history
    if conversation_id not in conversations:
        conversations[conversation_id] = []
        user_preferences[conversation_id] = {"style": "default"}
    
    # Extract user query
    user_query = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_query = msg.content
            break
    
    # LEARNING: Detect if user is correcting Athena's behavior
    correction = detect_user_correction([m.dict() for m in req.messages])
    if correction:
        # Store this preference
        user_preferences[conversation_id]["last_correction"] = correction
        user_preferences[conversation_id]["correction_count"] = user_preferences[conversation_id].get("correction_count", 0) + 1
        
        # Send to learning system
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                await client.post(
                    "http://athena-learning:8098/v1/feedback/analyze",
                    json={
                        "message_id": hashlib.md5(user_query.encode()).hexdigest()[:8],
                        "sentiment": "corrective",
                        "user_message": user_query,
                        "context": {"correction": correction}
                    }
                )
                logger.info("📚 User correction sent to learning system")
        except Exception as e:
            logger.debug(f"Learning system unavailable: {e}")
    
    # RAG: Semantic search (only if not a greeting/correction)
    rag_context = ""
    if user_query and len(user_query.split()) > 3 and not correction:
        rag_context = await semantic_search(user_query)
        if rag_context and uai_rag_calls:
            uai_rag_calls.inc()
    
    # Build messages with adaptive personality
    enriched_messages = []
    
    # 1. Base personality
    base_personality = get_athena_system_prompt()
    
    # 2. Apply learned corrections
    if conversation_id in user_preferences:
        prefs = user_preferences[conversation_id]
        if "last_correction" in prefs:
            base_personality += prefs["last_correction"]
    
    enriched_messages.append({
        "role": "system",
        "content": base_personality
    })
    
    # 3. RAG context (if available)
    if rag_context:
        enriched_messages.append({
            "role": "system",
            "content": rag_context
        })
    
    # 4. Conversation history (last 6 messages for context)
    recent_history = conversations[conversation_id][-6:]
    for msg in recent_history:
        enriched_messages.append(msg)
    
    # 5. Current user message
    enriched_messages.append({
        "role": "user",
        "content": user_query
    })
    
    # Choose model (Ollama for now - MLX later)
    model_used = "ollama"
    
    t0 = time.time()
    
    try:
        logger.info(f"Athena → Ollama (corrections applied: {bool(correction)})")
        
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
        latency_ms = (time.time() - t0) * 1000
        
        # Store in conversation history
        conversations[conversation_id].append({"role": "user", "content": user_query})
        conversations[conversation_id].append({"role": "assistant", "content": content})
        
        # Keep history bounded
        if len(conversations[conversation_id]) > 20:
            conversations[conversation_id] = conversations[conversation_id][-20:]
        
        # Metrics
        if uai_llm_calls:
            uai_llm_calls.labels(model_used).inc()
            uai_llm_lat_s.labels(model_used).observe(time.time() - t0)
        
        logger.info(f"Success: {len(content)} chars in {latency_ms:.0f}ms (learning: {bool(correction)})")
        
        # ASI Safety
        try:
            event_id = f"chat-{hashlib.md5(user_query.encode()).hexdigest()[:8]}-{int(time.time())}"
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
                    "correction_detected": bool(correction),
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
                "learning_active": bool(correction),
                "conversation_id": conversation_id,
                "latency_ms": latency_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        if uai_llm_fail:
            uai_llm_fail.labels(model_used, type(e).__name__).inc()
        raise HTTPException(status_code=500, detail=str(e))
