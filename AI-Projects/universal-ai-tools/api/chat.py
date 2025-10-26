"""
Chat endpoint - Athena with PERSISTENT LEARNING
Stores corrections in PostgreSQL JSONB - remembers FOREVER
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import os
import httpx
import time
import logging
import hashlib
from typing import List, Dict, Any, Optional
import asyncpg
import json

# ASI Safety - Judicial oversight
from api.judicial_client import submit_judicial_event

# Athena's base personality
from api.athena_personality import get_athena_system_prompt

router = APIRouter()
logger = logging.getLogger(__name__)

OLLAMA_URL = os.getenv("OLLAMA_URL", "http://host.docker.internal:11434")
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://athena-weaviate:8080")

# Database connection
DB_HOST = os.getenv("DB_HOST", "athena-postgres")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "athena")
DB_USER = os.getenv("DB_USER", "athena")
DB_PASS = os.getenv("DB_PASS", "athena_local_2024")

OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen2.5:7b")

# In-memory conversation tracking
conversations: Dict[str, List[Dict]] = {}

# Prometheus metrics
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


async def get_db_connection():
    """Get PostgreSQL connection"""
    return await asyncpg.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASS
    )


async def load_user_preferences(user_id: str = "default") -> Dict[str, Any]:
    """Load user's learned preferences from PostgreSQL"""
    try:
        conn = await get_db_connection()
        try:
            row = await conn.fetchrow("""
                SELECT preferences FROM user_preferences WHERE user_id = $1
            """, user_id)
            
            if row and row["preferences"]:
                prefs = json.loads(row["preferences"]) if isinstance(row["preferences"], str) else row["preferences"]
                logger.info(f"📚 Loaded preferences for {user_id}: {prefs}")
                return prefs
            else:
                return {}
                
        finally:
            await conn.close()
    except Exception as e:
        logger.warning(f"Failed to load preferences: {e}")
        return {}


async def save_user_correction(user_id: str, correction: str):
    """Save user correction to PostgreSQL PERMANENTLY"""
    try:
        conn = await get_db_connection()
        try:
            # Load existing preferences
            prefs = await load_user_preferences(user_id)
            
            # Add new correction
            prefs["communication_style"] = correction
            prefs["last_correction_time"] = time.time()
            prefs["correction_count"] = prefs.get("correction_count", 0) + 1
            
            # Save back to database
            await conn.execute("""
                INSERT INTO user_preferences (user_id, preferences, updated_at)
                VALUES ($1, $2, NOW())
                ON CONFLICT (user_id) 
                DO UPDATE SET preferences = $2, updated_at = NOW()
            """, user_id, json.dumps(prefs))
            
            logger.info(f"💾 PERMANENTLY SAVED correction for {user_id}: {correction}")
        finally:
            await conn.close()
    except Exception as e:
        logger.error(f"Failed to save correction: {e}")


def detect_user_correction(messages: List[Dict]) -> Optional[str]:
    """Detect if user is correcting Athena's behavior"""
    if len(messages) < 2:
        return None
    
    last_user_msg = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "").lower()
            break
    
    corrections = {
        "be brief": "ALWAYS respond in 1-2 sentences maximum. No lists. No explanations unless asked.",
        "be casual": "Use casual, friendly language like texting. Contractions, brief, relaxed.",
        "be simple": "Give simple, direct answers. Don't over-explain.",
        "just say": "Match the user's exact style. Minimal responses.",
        "be super brief": "ONE sentence responses only. Extremely concise.",
        "one word": "Respond with 1-2 words when possible.",
        "don't": "Stop the behavior user mentioned.",
        "be more": "Amplify the mentioned trait.",
        "i'm suggesting": "Follow this instruction precisely."
    }
    
    for pattern, instruction in corrections.items():
        if pattern in last_user_msg:
            return instruction
    
    return None


async def get_embedding(text: str) -> List[float]:
    """Get text embedding"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.post(
            f"{OLLAMA_URL}/api/embeddings",
            json={"model": "nomic-embed-text", "prompt": text[:2000]}
        )
        response.raise_for_status()
        return response.json()["embedding"]


async def semantic_search(query: str, limit: int = 3) -> str:
    """Semantic RAG"""
    try:
        query_embedding = await get_embedding(query)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                f"{WEAVIATE_URL}/v1/graphql",
                json={
                    "query": f"""
                    {{
                      Get {{
                        DocsV2(nearVector: {{vector: {query_embedding}}} limit: {limit}) {{
                          source content _additional {{distance}}
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
                        context_parts.append(f"{r['content']}")
            
            return "\n\n".join(context_parts) if context_parts else ""
    
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
    user_id: str | None = "default"


@router.post("/v1/chat/completions")
async def chat_completions(req: ChatRequest):
    """
    Athena with PERMANENT LEARNING
    
    Corrections stored in PostgreSQL - NEVER FORGOTTEN!
    """
    
    user_id = req.user_id or "default"
    
    # Load PERMANENT preferences from database
    user_prefs = await load_user_preferences(user_id)
    
    if user_id not in conversations:
        conversations[user_id] = []
    
    # Extract user query
    user_query = ""
    for msg in reversed(req.messages):
        if msg.role == "user":
            user_query = msg.content
            break
    
    # Detect correction
    correction = detect_user_correction([m.dict() for m in req.messages])
    if correction:
        await save_user_correction(user_id, correction)
        user_prefs["communication_style"] = correction
        logger.info(f"🧠 Correction SAVED PERMANENTLY for {user_id}")
    
    # RAG
    rag_context = ""
    if user_query and len(user_query.split()) > 3 and not correction:
        rag_context = await semantic_search(user_query)
    
    # Build adaptive prompt
    system_prompt = get_athena_system_prompt()
    
    # Apply PERMANENT learned preferences
    if user_prefs.get("communication_style"):
        system_prompt += f"\n\n🧠 PERMANENT USER PREFERENCE: {user_prefs['communication_style']}"
        logger.info(f"📖 Applying permanent preference for {user_id}")
    
    enriched_messages = [{"role": "system", "content": system_prompt}]
    
    if rag_context:
        enriched_messages.append({"role": "system", "content": f"<knowledge>{rag_context}</knowledge>"})
    
    for msg in conversations[user_id][-6:]:
        enriched_messages.append(msg)
    
    enriched_messages.append({"role": "user", "content": user_query})
    
    t0 = time.time()
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": enriched_messages,
                    "stream": False,
                    "options": {"temperature": req.temperature or 0.7, "num_predict": 512}
                }
            )
            response.raise_for_status()
            data = response.json()
        
        content = (data.get("message") or {}).get("content", "")
        latency_ms = (time.time() - t0) * 1000
        
        # Store in session history
        conversations[user_id].append({"role": "user", "content": user_query})
        conversations[user_id].append({"role": "assistant", "content": content})
        
        if len(conversations[user_id]) > 20:
            conversations[user_id] = conversations[user_id][-20:]
        
        # Metrics
        if uai_llm_calls:
            uai_llm_calls.labels(OLLAMA_MODEL).inc()
            uai_llm_lat_s.labels(OLLAMA_MODEL).observe(time.time() - t0)
        
        logger.info(f"✅ {len(content)} chars, {latency_ms:.0f}ms (permanent_prefs: {bool(user_prefs.get('communication_style'))})")
        
        return {
            "object": "chat.completion",
            "model": OLLAMA_MODEL,
            "choices": [{
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop"
            }],
            "usage": {
                "prompt_tokens": sum(len(m.content.split()) for m in req.messages),
                "completion_tokens": len(content.split()),
                "total_tokens": sum(len(m.content.split()) for m in req.messages) + len(content.split())
            },
            "_athena": {
                "user_id": user_id,
                "permanent_learning_active": bool(user_prefs.get("communication_style")),
                "correction_saved_to_db": bool(correction),
                "rag_enabled": bool(rag_context),
                "latency_ms": latency_ms
            }
        }
        
    except Exception as e:
        logger.error(f"Error: {type(e).__name__}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
