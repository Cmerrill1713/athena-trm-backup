#!/usr/bin/env python3
"""
Standalone RAG Service - Semantic search over AI coding video transcripts
Runs on port 8015
"""
import json
import os
import sys
from datetime import datetime
from typing import List, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add path for common imports
# Need to go up to GitHub root: universal-ai-tools -> AI-Projects -> GitHub
github_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, github_root)

import hashlib

from common.ops import add_health_endpoints

# Prometheus metrics
from prometheus_client import Counter, Gauge, Histogram

# Bandit routing integration
from ce_bandit_router import route_with_bandit_enhancement

# Personalization integration
from personalization import get_user_preferences, personalize_rag_selection

# RAG reranker integration
from rag.rerank import RAG_RERANK_ENABLED, rerank
from rag.store import log_retrieval

app = FastAPI(title="RAG Knowledge Base Service", version="1.0.0")

# Add standard health + metrics endpoints
add_health_endpoints(app)

# Custom Prometheus metrics
RAG_REQUESTS = Counter('rag_requests_total', 'Total RAG requests', ['status'])
RAG_LATENCY = Histogram('rag_request_duration_seconds', 'RAG request latency')
RAG_HITS = Histogram('rag_hits_count', 'Number of RAG hits returned')

# RAG Reranker metrics
RAG_RERANK_ENABLED_GAUGE = Gauge('rag_rerank_enabled', 'RAG reranker enabled status')
RAG_CANARY_PERCENTAGE_GAUGE = Gauge('rag_canary_percentage', 'RAG reranker canary rollout percentage')
RAG_DOCS_USED = Histogram('rag_docs_used_count', 'Number of documents used after reranking')
RAG_THRESHOLD = Gauge('rag_threshold_current', 'Current RAG reranking threshold')

# Cross-encoder precision mode metrics
RAG_CE_REQUESTS = Counter('rag_ce_requests_total', 'Total requests using cross-encoder reranking', ['intent'])
RAG_CE_LATENCY = Histogram('rag_ce_request_duration_seconds', 'Cross-encoder reranking latency')
RAG_CE_ENABLED_GAUGE = Gauge('rag_ce_enabled', 'Cross-encoder reranker enabled status')

# Personalization metrics
RAG_PERSONALIZATION_REQUESTS = Counter('rag_personalization_requests_total', 'Total requests with personalization applied')
RAG_PERSONALIZATION_ENABLED_GAUGE = Gauge('rag_personalization_enabled', 'Personalization enabled status')
RAG_USER_PROFILES_ACTIVE = Gauge('rag_user_profiles_active', 'Number of active user profiles')

# Cross-encoder model metrics
RAG_CE_MODEL_LOADED = Gauge('rag_ce_model_loaded', 'Cross-encoder model loaded status')
RAG_CE_MODEL_CACHE_SIZE = Gauge('rag_ce_model_cache_size', 'Cross-encoder prediction cache size')
RAG_CE_MODEL_CACHE_HITS = Counter('rag_ce_model_cache_hits_total', 'Cross-encoder cache hits')
RAG_CE_MODEL_CACHE_MISSES = Counter('rag_ce_model_cache_misses_total', 'Cross-encoder cache misses')
RAG_CE_MODEL_INFERENCE_TIME = Histogram('rag_ce_model_inference_duration_seconds', 'Cross-encoder inference latency')

# Neural routing metrics
RAG_ROUTER_DECISIONS = Counter('rag_router_decisions_total', 'Neural routing decisions', ['decision_type', 'confidence_range'])
RAG_ROUTER_NEURAL_USED = Counter('rag_router_neural_used_total', 'Neural router usage')
RAG_ROUTER_HEURISTIC_FALLBACK = Counter('rag_router_heuristic_fallback_total', 'Heuristic routing fallbacks')

# Bandit routing metrics
RAG_BANDIT_DECISIONS = Counter('rag_bandit_decisions_total', 'Bandit routing decisions', ['arm_used', 'exploration_used'])
RAG_BANDIT_EXPLORATION_RATE = Gauge('rag_bandit_exploration_rate', 'Current bandit exploration rate')
RAG_BANDIT_ARM_WIN_RATES = Gauge('rag_bandit_arm_win_rates', 'Bandit arm win rates', ['arm_name'])

# Federation metrics
RAG_FEDERATION_ENABLED = Gauge('rag_federation_enabled', 'Federation learning enabled')
RAG_FEDERATION_SYNC_SUCCESS = Counter('rag_federation_sync_success_total', 'Successful federation syncs')
RAG_FEDERATION_SYNC_FAILURE = Counter('rag_federation_sync_failure_total', 'Failed federation syncs')
RAG_FEDERATION_CONTRIBUTIONS = Counter('rag_federation_contributions_total', 'Federation contributions made')
RAG_FEDERATION_UPDATES_RECEIVED = Counter('rag_federation_updates_received_total', 'Federation knowledge updates received')

# Governance metrics
RAG_GOVERNANCE_VALIDATIONS = Counter('rag_governance_validations_total', 'Total constitutional validations')
RAG_GOVERNANCE_VIOLATIONS = Counter('rag_governance_violations_total', 'Constitutional violations detected', ['violation_type'])
RAG_GOVERNANCE_COMPLIANCE_RATE = Gauge('rag_governance_compliance_rate', 'Constitutional compliance rate')
RAG_GOVERNANCE_FEDERATION_BLOCKED = Counter('rag_governance_federation_blocked_total', 'Federation contributions blocked by governance')

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
WEAVIATE_TOKEN = os.getenv("WEAVIATE_TOKEN", "anonymous")
FALLBACK_MODE = os.getenv("RAG_FALLBACK_MODE", "true").lower() == "true"

# RAG canary rollout
RAG_CANARY_PERCENTAGE = int(os.getenv("RAG_CANARY_PERCENTAGE", "100"))

def should_use_reranker(query: str, user_id: str = None) -> bool:
    """Determine if this request should use RAG reranking based on canary percentage."""
    if not RAG_RERANK_ENABLED:
        return False

    if RAG_CANARY_PERCENTAGE >= 100:
        return True

    if RAG_CANARY_PERCENTAGE <= 0:
        return False

    # Use query + user_id for consistent canary assignment
    canary_key = f"{query}:{user_id or 'anonymous'}"
    canary_hash = int(hashlib.md5(canary_key.encode()).hexdigest(), 16)
    canary_value = canary_hash % 100

    return canary_value < RAG_CANARY_PERCENTAGE

# Models
class RAGQuery(BaseModel):
    query: str
    k: int = 8
    alpha: float = 0.45
    include_sources: bool = True
    user_id: Optional[str] = None  # For personalization

class RAGHit(BaseModel):
    title: str
    text: str
    source: Optional[str] = None
    url: Optional[str] = None
    tags: Optional[List[str]] = None
    score: Optional[float] = None
    channel: Optional[str] = None

class RAGResponse(BaseModel):
    hits: List[RAGHit]
    query: str
    count: int
    latency_ms: float

@app.post("/api/rag/query")
async def rag_query(req: RAGQuery):
    """Semantic search over 180+ AI coding transcripts"""
    start = datetime.now()

    with RAG_LATENCY.time():
        try:
            gql = {"query": f"""
                {{ Get {{ 
                    LearnedPattern(
                        limit: {req.k},
                        where: {{operator: Equal, path: ["pattern_type"], valueText: "video_transcript"}}
                    ) {{ 
                        title description pattern_data tags 
                    }} 
                }} }}
            """}

            headers = {"Content-Type": "application/json"}
            if WEAVIATE_TOKEN and WEAVIATE_TOKEN != "your-token-here":
                headers["X-Assistant-Token"] = WEAVIATE_TOKEN

            try:
                r = requests.post(f"{WEAVIATE_URL}/v1/graphql", json=gql, headers=headers, timeout=20)
                r.raise_for_status()
                patterns = r.json().get("data", {}).get("Get", {}).get("LearnedPattern", [])
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 401 and FALLBACK_MODE:
                    # Weaviate auth failed, return mock data
                    print(f"⚠️  Weaviate auth failed, using fallback mode: {e}")
                    patterns = []
                else:
                    raise e
            except Exception as e:
                if FALLBACK_MODE:
                    print(f"⚠️  Weaviate connection failed, using fallback mode: {e}")
                    patterns = []
                else:
                    raise e

            # Score and filter by query
            hits = []
            query_lower = req.query.lower()

            # If no patterns from Weaviate and in fallback mode, provide mock data
            if not patterns and FALLBACK_MODE:
                mock_patterns = [
                    {
                        "title": f"Mock result for '{req.query}'",
                        "description": f"This is a mock response for the query: {req.query}",
                        "pattern_data": json.dumps({"type": "mock", "content": f"Mock content for {req.query}"}),
                        "tags": ["mock", "fallback"]
                    }
                ]
                patterns = mock_patterns

            for p in patterns:
                try:
                    pd = json.loads(p.get("pattern_data", "{}"))

                    # Simple relevance scoring
                    score = 0.0
                    title = p.get("title", "")
                    desc = p.get("description", "")

                    if query_lower in title.lower():
                        score += 3.0
                    if query_lower in desc.lower():
                        score += 2.0
                    for tag in p.get("tags", []):
                        if tag.lower() in query_lower:
                            score += 1.0

                    if score > 0 or req.k >= len(patterns):  # Include if matches or requesting all
                        hits.append(RAGHit(
                            title=title,
                            text=desc,
                            source="youtube",
                            url=pd.get("video_url"),
                            tags=p.get("tags"),
                            score=score,
                            channel=pd.get("channel")
                        ))
                except:
                    continue

            # Get user preferences for personalization
            user_preferences = None
            if req.user_id:
                user_preferences = get_user_preferences(req.user_id)
                RAG_PERSONALIZATION_REQUESTS.inc()
                RAG_PERSONALIZATION_ENABLED_GAUGE.set(1)
            else:
                RAG_PERSONALIZATION_ENABLED_GAUGE.set(0)

            # RAG Reranking Integration with bandit-enhanced routing
            use_reranker = should_use_reranker(req.query)

            # Get bandit-enhanced routing decision
            bandit_decision = route_with_bandit_enhancement(req.query, None)  # intent=None for now
            use_reranker = bandit_decision.use_ce  # Override with bandit decision

            # Track bandit routing metrics
            RAG_BANDIT_DECISIONS.labels(
                arm_used=bandit_decision.bandit_arm or "unknown",
                exploration_used=str(bandit_decision.exploration_used).lower()
            ).inc()

            # Update bandit metrics
            from ce_bandit_router import ce_bandit_router
            bandit_stats = ce_bandit_router.get_bandit_stats()
            RAG_BANDIT_EXPLORATION_RATE.set(bandit_stats.get('exploration_rate_recent', 0.0))

            # Update arm win rates
            for arm_name, arm_data in bandit_stats.get('arm_performance', {}).items():
                RAG_BANDIT_ARM_WIN_RATES.labels(arm_name=arm_name).set(arm_data.get('local_win_rate', 0.0))

            # Update federation metrics
            federation_stats = bandit_stats.get('federation_stats', {})
            RAG_FEDERATION_ENABLED.set(1 if federation_stats.get('federation_enabled') else 0)

            # Legacy neural routing metrics (for comparison)
            confidence_range = f"{int(bandit_decision.confidence * 10) * 10}-{int(bandit_decision.confidence * 10) * 10 + 9}%"
            RAG_ROUTER_DECISIONS.labels(
                decision_type="ce" if bandit_decision.use_ce else "cosine",
                confidence_range=confidence_range
            ).inc()
            RAG_ROUTER_NEURAL_USED.inc()

            if use_reranker and hits:
                import uuid

                import numpy as np

                # Convert hits to candidate format for reranking
                candidates = []
                for i, hit in enumerate(hits):
                    # Create mock embeddings for cosine similarity (in production, use real embeddings)
                    mock_emb = np.random.rand(384)  # Mock embedding dimension
                    mock_emb = mock_emb / np.linalg.norm(mock_emb)  # Normalize

                    candidates.append({
                        "doc_id": f"hit_{i}",
                        "text": hit.text,
                        "emb": mock_emb,
                        "orig": hit.score or 0.0,
                        "title": hit.title,
                        "source": hit.source,
                        "url": hit.url,
                        "tags": hit.tags
                    })

                # Apply personalization to RAG selection
                candidates = personalize_rag_selection(candidates, user_preferences)

                # Generate query embedding (mock for now)
                query_emb = np.random.rand(384)
                query_emb = query_emb / np.linalg.norm(query_emb)

                # Apply reranking with precision routing
                reranked_candidates = rerank(query_emb, candidates, query_text=req.query, intent=None)

                # Convert back to RAGHit format
                final_hits = []
                for candidate in reranked_candidates:
                    if candidate.get("used", False):
                        final_hits.append(RAGHit(
                            title=candidate["title"],
                            text=candidate["text"],
                            source=candidate["source"],
                            url=candidate["url"],
                            tags=candidate["tags"],
                            score=candidate.get("rerank", candidate.get("orig", 0)),
                            channel=None  # Not available in mock data
                        ))

                # Log retrieval data for optimization learning
                interaction_id = str(uuid.uuid4())  # Generate interaction ID
                log_retrieval(interaction_id, req.query, candidates)

                # Update reranker metrics
                RAG_RERANK_ENABLED_GAUGE.set(1)
                RAG_CANARY_PERCENTAGE_GAUGE.set(RAG_CANARY_PERCENTAGE)
                RAG_DOCS_USED.observe(len(final_hits))
                from rag.rerank import load_dynamic_tau
                RAG_THRESHOLD.set(load_dynamic_tau())

                # Track cross-encoder usage
                ce_used = any(hit.get("reranker_type") == "crossencoder" for hit in reranked_candidates)
                if ce_used:
                    RAG_CE_REQUESTS.labels(intent="unknown").inc()  # TODO: Pass actual intent when available
                    RAG_CE_ENABLED_GAUGE.set(1)
                else:
                    RAG_CE_ENABLED_GAUGE.set(0)

            else:
                # Apply personalization even without reranking
                if user_preferences:
                    # Convert hits to candidates for personalization
                    candidates = [{"text": hit.text, "orig": hit.score or 0.0} for hit in hits]
                    personalized_candidates = personalize_rag_selection(candidates, user_preferences)
                    # Sort by personalized score + original score
                    hits_with_personalization = list(zip(hits, personalized_candidates))
                    hits_with_personalization.sort(
                        key=lambda x: (x[1].get("rerank", x[1]["orig"]), x[0].score or 0),
                        reverse=True
                    )
                    hits = [hit for hit, _ in hits_with_personalization]

                # Original behavior when reranking disabled
                final_hits = hits[:req.k]

                # Update metrics
                RAG_RERANK_ENABLED_GAUGE.set(0)
                RAG_CANARY_PERCENTAGE_GAUGE.set(RAG_CANARY_PERCENTAGE)

            latency = (datetime.now() - start).total_seconds() * 1000

            # Record metrics
            RAG_REQUESTS.labels(status='success').inc()
            RAG_HITS.observe(len(final_hits))

            return RAGResponse(
                hits=final_hits,
                query=req.query,
                count=len(final_hits),
                latency_ms=round(latency, 2)
            )
        except Exception as e:
            RAG_REQUESTS.labels(status='error').inc()
            raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/health")
async def health():
    """Health check"""
    try:
        r = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": "{ Aggregate { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"video_transcript\"}) { meta { count } } } }"},
            timeout=10
        )
        count = r.json()["data"]["Aggregate"]["LearnedPattern"][0]["meta"]["count"]
        return {"status": "healthy", "transcripts": count, "weaviate": WEAVIATE_URL}
    except:
        return {"status": "degraded", "weaviate": WEAVIATE_URL}

@app.get("/api/rag/stats")
async def stats():
    """Get knowledge base statistics"""
    try:
        r = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": "{ Get { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"video_transcript\"}, limit: 200) { title tags pattern_data } } }"},
            timeout=20
        )

        patterns = r.json()["data"]["Get"]["LearnedPattern"]
        channels = {}
        topics = {}

        for p in patterns:
            try:
                pd = json.loads(p.get("pattern_data", "{}"))
                ch = pd.get("channel", "Unknown")
                channels[ch] = channels.get(ch, 0) + 1
            except:
                pass
            for tag in p.get("tags", []):
                topics[tag] = topics.get(tag, 0) + 1

        return {
            "total": len(patterns),
            "channels": channels,
            "top_topics": dict(sorted(topics.items(), key=lambda x: x[1], reverse=True)[:15])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/ce-health")
async def ce_health():
    """Get cross-encoder model health status"""
    try:
        from rag.rerank import ce_manager
        health = ce_manager.health_check()

        # Update metrics
        RAG_CE_MODEL_LOADED.set(1 if health.get("model_loaded") else 0)
        RAG_CE_MODEL_CACHE_SIZE.set(health.get("cache_size", 0))

        return {
            "status": "healthy" if health.get("inference_working") else "degraded",
            "model_loaded": health.get("model_loaded", False),
            "model_name": health.get("model_name", "unknown"),
            "cache_size": health.get("cache_size", 0),
            "cache_max": health.get("cache_max", 0),
            "inference_working": health.get("inference_working", False),
            "fallback_mode": health.get("fallback_mode", False),
            "test_inference_score": health.get("test_inference_score"),
            "error": health.get("inference_error")
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/rag/bandit-health")
async def bandit_health():
    """Get bandit routing system health status"""
    try:
        from ce_bandit_router import ce_bandit_router
        stats = ce_bandit_router.get_bandit_stats()

        return {
            "status": "healthy",
            "total_decisions": stats.get("total_decisions", 0),
            "exploration_rate": stats.get("exploration_rate_recent", 0.0),
            "best_arm": stats.get("best_arm", "unknown"),
            "arms_performance": stats.get("arm_performance", {}),
            "avg_improvement": stats.get("avg_improvement", 0.0),
            "history_size": stats.get("history_size", 0),
            "federation_enabled": stats.get("federation_enabled", False),
            "federation_stats": stats.get("federation_stats", {})
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/rag/federation-health")
async def federation_health():
    """Get federation learning system health status"""
    try:
        from federated_bandit_coordinator import federation_coordinator
        stats = federation_coordinator.get_federation_stats()

        return {
            "status": "healthy" if stats.get("federation_enabled") else "disabled",
            "federation_enabled": stats.get("federation_enabled", False),
            "deployment_id": stats.get("deployment_id", "unknown"),
            "total_contributions": stats.get("total_contributions", 0),
            "total_updates": stats.get("total_knowledge_updates", 0),
            "recent_contributions": stats.get("recent_contributions", 0),
            "federated_arms": stats.get("federated_arms", 0),
            "hours_since_sync": stats.get("hours_since_sync", 0),
            "privacy_epsilon": stats.get("privacy_epsilon", 0.0),
            "deployment_reputation": stats.get("deployment_reputation", 1.0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/api/rag/governance-health")
async def governance_health():
    """Get constitutional governance system health status"""
    try:
        from constitutional_governance import constitutional_validator
        stats = constitutional_validator.get_governance_stats()

        return {
            "status": "healthy",
            "total_validations": stats.get("total_validations", 0),
            "compliance_rate": stats.get("compliance_rate", 1.0),
            "most_common_violations": stats.get("most_common_violations", []),
            "rules_active": stats.get("rules_active", 0),
            "validation_history_size": stats.get("validation_history_size", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

if __name__ == "__main__":
    print("🚀 Starting RAG Service on port 8015")
    print(f"📊 Weaviate: {WEAVIATE_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8015, log_level="info")

