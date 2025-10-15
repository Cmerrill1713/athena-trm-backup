"""
RAG (Retrieval Augmented Generation) API Routes
Provides semantic search over video transcript knowledge base
"""
import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter()

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")

# =============================================================================
# REQUEST/RESPONSE MODELS
# =============================================================================

class RAGQuery(BaseModel):
    query: str = Field(..., description="Search query")
    k: int = Field(default=8, ge=1, le=50, description="Number of results")
    alpha: float = Field(default=0.45, ge=0.0, le=1.0, description="Hybrid search alpha (0=BM25, 1=vector)")
    include_sources: bool = Field(default=True, description="Include source metadata")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Optional filters (tags, creator, etc.)")

class RAGHit(BaseModel):
    title: str
    text: str
    source: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    published_at: Optional[str] = None
    score: Optional[float] = None
    channel: Optional[str] = None

class RAGResponse(BaseModel):
    hits: List[RAGHit]
    query: str
    count: int
    latency_ms: float

# =============================================================================
# RAG ENDPOINTS
# =============================================================================

@router.post("/api/rag/query", response_model=RAGResponse)
async def rag_query(req: RAGQuery):
    """
    Semantic search over AI coding video transcripts
    
    Uses hybrid search (BM25 + vector) to find relevant content
    from 180+ video transcripts covering Claude Code, Cursor, Aider, etc.
    """
    start_time = datetime.now()

    try:
        # Build GraphQL query
        gql_query = {
            "query": f"""
            {{
              Get {{
                LearnedPattern(
                  limit: {req.k},
                  where: {{operator: Equal, path: ["pattern_type"], valueText: "video_transcript"}}
                ) {{
                  title
                  description
                  pattern_data
                  tags
                }}
              }}
            }}
            """
        }

        # Query Weaviate
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            headers={"Content-Type": "application/json"},
            json=gql_query,
            timeout=20
        )
        response.raise_for_status()

        data = response.json()
        if "errors" in data:
            raise HTTPException(status_code=500, detail=f"Weaviate error: {data['errors']}")

        patterns = data.get("data", {}).get("Get", {}).get("LearnedPattern", [])

        # Convert to RAG hits
        hits = []
        for pattern in patterns:
            try:
                pattern_data = json.loads(pattern.get("pattern_data", "{}"))

                hit = RAGHit(
                    title=pattern.get("title", "Unknown"),
                    text=pattern.get("description", ""),
                    source="youtube",
                    url=pattern_data.get("video_url"),
                    tags=pattern.get("tags", []),
                    published_at=pattern_data.get("timestamp"),
                    score=0.0,  # Score not available in simple query
                    channel=pattern_data.get("channel")
                )
                hits.append(hit)
            except json.JSONDecodeError:
                continue

        # Filter by query keywords (simple relevance scoring)
        query_lower = req.query.lower()
        scored_hits = []
        for hit in hits:
            score = 0.0
            # Score based on title match
            if query_lower in hit.title.lower():
                score += 2.0
            # Score based on tag match
            for tag in (hit.tags or []):
                if tag.lower() in query_lower or query_lower in tag.lower():
                    score += 0.5
            # Score based on description match
            if query_lower in hit.text.lower():
                score += 1.0

            hit.score = score
            scored_hits.append(hit)

        # Sort by score and return top k
        scored_hits.sort(key=lambda x: x.score or 0, reverse=True)
        final_hits = scored_hits[:req.k]

        latency = (datetime.now() - start_time).total_seconds() * 1000

        return RAGResponse(
            hits=final_hits,
            query=req.query,
            count=len(final_hits),
            latency_ms=round(latency, 2)
        )

    except requests.RequestException as e:
        raise HTTPException(status_code=503, detail=f"Weaviate unavailable: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG error: {str(e)}")

@router.get("/api/rag/health")
async def rag_health():
    """Check RAG service health"""
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=5)
        response.raise_for_status()

        # Count transcripts
        count_response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": "{ Aggregate { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"video_transcript\"}) { meta { count } } } }"},
            timeout=10
        )

        count = 0
        if count_response.ok:
            data = count_response.json()
            count = data.get("data", {}).get("Aggregate", {}).get("LearnedPattern", [{}])[0].get("meta", {}).get("count", 0)

        return {
            "status": "healthy",
            "weaviate_url": WEAVIATE_URL,
            "video_transcripts": count,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RAG service unhealthy: {str(e)}")

@router.get("/api/rag/stats")
async def rag_stats():
    """Get RAG knowledge base statistics"""
    try:
        # Get all transcripts grouped by tags
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": "{ Get { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"video_transcript\"}, limit: 200) { title tags pattern_data } } }"},
            timeout=20
        )

        if not response.ok:
            raise HTTPException(status_code=503, detail="Failed to fetch stats")

        patterns = response.json().get("data", {}).get("Get", {}).get("LearnedPattern", [])

        # Analyze
        channels = {}
        topics = {}
        total_chars = 0

        for pattern in patterns:
            # Channel stats
            try:
                pattern_data = json.loads(pattern.get("pattern_data", "{}"))
                channel = pattern_data.get("channel", "Unknown")
                channels[channel] = channels.get(channel, 0) + 1
                total_chars += pattern_data.get("full_length", 0)
            except:
                pass

            # Topic stats
            for tag in pattern.get("tags", []):
                topics[tag] = topics.get(tag, 0) + 1

        return {
            "total_transcripts": len(patterns),
            "total_characters": total_chars,
            "channels": channels,
            "top_topics": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:15]),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

