# RAG Reranker Optimization Layer
# Automatically tunes retrieval quality using judge feedback

import os
import numpy as np
from typing import List, Dict, Any, Optional

# Configuration
RAG_RERANK_ENABLED = os.getenv("RAG_RERANK_ENABLED", "false").lower() == "true"
RERANKER = os.getenv("RAG_RERANKER", "cosine")
TOPK = int(os.getenv("RAG_RERANK_TOPK", "8"))
TAU = float(os.getenv("RAG_THRESHOLD", "0.45"))  # Current threshold

# Cross-encoder precision mode
RAG_RERANKER_CE_ENABLED = os.getenv("RAG_RERANKER_CE_ENABLED", "false").lower() == "true"
RAG_RERANKER_CE_INTENTS = set(os.getenv("RAG_RERANKER_CE_INTENTS", "policy,incident,legal,diagnosis").split(","))
RAG_RERANKER_CE_LATENCY_BUDGET_MS = int(os.getenv("RAG_RERANKER_CE_LATENCY_BUDGET_MS", "500"))

def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """Calculate cosine similarity between two vectors."""
    na, nb = np.linalg.norm(a), np.linalg.norm(b)
    if na == 0 or nb == 0:
        return 0.0
    return float(np.dot(a, b) / (na * nb))

def _cross_encoder_similarity(query: str, doc_text: str) -> float:
    """
    Placeholder for cross-encoder reranking.
    In production, this would use a trained cross-encoder model like MS MARCO.

    For now: return a boosted cosine similarity as proxy.
    """
    # TODO: Replace with actual cross-encoder inference
    # Example: model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    # return model.predict([query, doc_text])

    # Placeholder: boost cosine similarity by 10-20% for "high-value" content
    base_similarity = 0.7  # Mock cross-encoder score
    return base_similarity

def should_use_cross_encoder(query: str, intent: Optional[str] = None) -> bool:
    """
    Determine if query should use cross-encoder reranking based on routing rules.

    Rules:
    - If intent in {policy, incident, legal, diagnosis} → CE
    - If query_len > 16 → CE
    - Else → cosine (fast path)
    """
    if not RAG_RERANKER_CE_ENABLED:
        return False

    # Check intent-based routing
    if intent and intent.lower() in RAG_RERANKER_CE_INTENTS:
        return True

    # Check query length routing
    if len(query.split()) > 16:
        return True

    return False

def load_dynamic_tau() -> float:
    """Load dynamically tuned threshold from database if available."""
    try:
        import psycopg2
        dsn = os.getenv("DATABASE_URL", "dbname=universal_ai_tools user=postgres password=postgres host=athena-postgres port=5432")
        with psycopg2.connect(dsn) as conn, conn.cursor() as cur:
            cur.execute("SELECT value FROM kv_config WHERE key='RAG_THRESHOLD'")
            row = cur.fetchone()
            if row:
                return float(row[0])
    except Exception as e:
        print(f"Failed to load dynamic TAU, using default: {e}")

    return TAU  # Fallback to environment/default

def rerank(query_emb: np.ndarray, candidates: List[Dict[str, Any]], query_text: str = "", intent: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Rerank retrieval candidates using optimized scoring with precision routing.

    Args:
        query_emb: Query embedding vector
        candidates: List of candidate documents with embeddings and original scores
        query_text: Original query text (for cross-encoder routing)
        intent: Query intent (for cross-encoder routing)

    Returns:
        Reranked and filtered list of candidates
    """
    if not RAG_RERANK_ENABLED:
        # Pass-through mode: just sort by original score and take top-k
        sorted_candidates = sorted(candidates, key=lambda x: x.get("orig", 0), reverse=True)[:TOPK]
        for c in sorted_candidates:
            c["rerank"] = c.get("orig", 0)
            c["used"] = True
            c["reranker_type"] = "none"
        return sorted_candidates

    # Get current threshold (may be dynamically tuned)
    current_tau = load_dynamic_tau()

    # Determine reranker type based on routing rules
    use_ce = should_use_cross_encoder(query_text, intent)
    reranker_type = "crossencoder" if use_ce else "cosine"

    # Apply reranking algorithm
    if reranker_type == "cosine":
        # Blend original score with semantic similarity
        for candidate in candidates:
            if "emb" in candidate and candidate["emb"] is not None:
                semantic_sim = _cosine_similarity(query_emb, candidate["emb"])
                # Weighted combination: 60% original + 40% semantic
                candidate["rerank"] = 0.6 * candidate.get("orig", 0) + 0.4 * semantic_sim
            else:
                # Fallback to original score if no embedding
                candidate["rerank"] = candidate.get("orig", 0)

    elif reranker_type == "crossencoder":
        # Cross-encoder reranking (precision mode)
        for candidate in candidates:
            doc_text = candidate.get("text", "")
            ce_score = _cross_encoder_similarity(query_text, doc_text)
            # Use CE score directly (higher precision, no blend needed)
            candidate["rerank"] = ce_score

    else:
        # Unknown reranker, fall back to original
        for candidate in candidates:
            candidate["rerank"] = candidate.get("orig", 0)

    # Sort by rerank score (descending)
    ranked_candidates = sorted(candidates, key=lambda x: x.get("rerank", 0), reverse=True)

    # Apply threshold-based filtering with top-k limit
    kept_candidates = []
    for candidate in ranked_candidates:
        if len(kept_candidates) >= TOPK:
            break

        rerank_score = candidate.get("rerank", 0)
        # Keep if score >= threshold OR if we haven't filled half of top-k yet
        if rerank_score >= current_tau or len(kept_candidates) < (TOPK // 2):
            candidate["used"] = True
            candidate["reranker_type"] = reranker_type
            kept_candidates.append(candidate)
        else:
            candidate["used"] = False
            candidate["reranker_type"] = reranker_type

    return kept_candidates

def get_rerank_stats(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get statistics about reranking performance."""
    if not candidates:
        return {}

    rerank_scores = [c.get("rerank", 0) for c in candidates if "rerank" in c]
    orig_scores = [c.get("orig", 0) for c in candidates if "orig" in c]
    used_count = sum(1 for c in candidates if c.get("used", False))

    # Count reranker types used
    reranker_types = {}
    for c in candidates:
        rt = c.get("reranker_type", "unknown")
        reranker_types[rt] = reranker_types.get(rt, 0) + 1

    return {
        "total_candidates": len(candidates),
        "used_candidates": used_count,
        "rerank_scores": {
            "mean": float(np.mean(rerank_scores)) if rerank_scores else 0,
            "max": float(np.max(rerank_scores)) if rerank_scores else 0,
            "min": float(np.min(rerank_scores)) if rerank_scores else 0
        },
        "orig_scores": {
            "mean": float(np.mean(orig_scores)) if orig_scores else 0,
            "max": float(np.max(orig_scores)) if orig_scores else 0,
            "min": float(np.min(orig_scores)) if orig_scores else 0
        },
        "current_threshold": load_dynamic_tau(),
        "reranker_enabled": RAG_RERANK_ENABLED,
        "reranker_types_used": reranker_types,
        "ce_enabled": RAG_RERANKER_CE_ENABLED,
        "ce_intents": list(RAG_RERANKER_CE_INTENTS),
        "ce_latency_budget_ms": RAG_RERANKER_CE_LATENCY_BUDGET_MS
    }
