# RAG Reranker Optimization Layer
# Automatically tunes retrieval quality using judge feedback

import os
from typing import Any, Dict, List, Optional

import numpy as np

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

class CrossEncoderManager:
    """Manages cross-encoder model loading and inference."""

    def __init__(self):
        self.model = None
        self.model_name = os.getenv('CROSS_ENCODER_MODEL', 'cross-encoder/ms-marco-MiniLM-L-6-v2')
        self.max_length = int(os.getenv('CROSS_ENCODER_MAX_LENGTH', '512'))
        self.cache_size = int(os.getenv('CROSS_ENCODER_CACHE_SIZE', '1000'))

        # Simple LRU cache for predictions
        self.cache = {}
        self.cache_order = []

        self._load_model()

    def _load_model(self):
        """Load the cross-encoder model."""
        try:
            from sentence_transformers import CrossEncoder
            print(f"Loading cross-encoder model: {self.model_name}")
            self.model = CrossEncoder(self.model_name, max_length=self.max_length)
            print("✅ Cross-encoder model loaded successfully")
        except ImportError:
            print("⚠️  sentence-transformers not available, using fallback similarity")
            self.model = None
        except Exception as e:
            print(f"❌ Failed to load cross-encoder model: {e}")
            self.model = None

    def predict(self, query: str, doc_text: str) -> float:
        """Get cross-encoder similarity score."""
        if self.model is None:
            # Fallback to improved mock similarity
            return self._fallback_similarity(query, doc_text)

        # Create cache key
        cache_key = f"{hash(query)}:{hash(doc_text)}"

        # Check cache
        if cache_key in self.cache:
            # Track cache hit
            self._track_metric('cache_hit')
            return self.cache[cache_key]

        # Track cache miss
        self._track_metric('cache_miss')

        try:
            import time
            start_time = time.time()

            # Get prediction
            score = self.model.predict([query, doc_text])[0]

            # Track inference time
            inference_time = time.time() - start_time
            self._track_metric('inference_time', inference_time)

            # Ensure score is in 0-1 range (some models return logits)
            if score < 0:
                score = 1 / (1 + abs(score))  # Sigmoid for negative scores
            elif score > 1:
                score = min(score / 10, 1.0)  # Normalize large positive scores

            # Cache result
            self._cache_result(cache_key, score)

            return float(score)

        except Exception as e:
            print(f"CE prediction failed, using fallback: {e}")
            self._track_metric('inference_error')
            return self._fallback_similarity(query, doc_text)

    def _fallback_similarity(self, query: str, doc_text: str) -> float:
        """Improved fallback similarity when model unavailable."""
        query_words = set(query.lower().split())
        doc_words = set(doc_text.lower().split())

        # Jaccard similarity
        intersection = len(query_words & doc_words)
        union = len(query_words | doc_words)

        if union == 0:
            return 0.1  # Small baseline score

        jaccard = intersection / union

        # Boost for exact matches and semantic indicators
        boost = 1.0
        query_lower = query.lower()
        doc_lower = doc_text.lower()

        # Exact phrase matches
        if query_lower in doc_lower:
            boost *= 1.5

        # Question-answer alignment indicators
        if any(word in doc_lower for word in ['because', 'therefore', 'thus', 'so', 'due to']):
            boost *= 1.2

        # Technical content indicators
        if any(word in doc_lower for word in ['implement', 'configure', 'setup', 'create', 'build']):
            boost *= 1.1

        return min(jaccard * boost, 0.95)  # Cap at 0.95

    def _cache_result(self, key: str, value: float):
        """Cache a prediction result with LRU eviction."""
        if key in self.cache:
            # Move to end (most recently used)
            self.cache_order.remove(key)
        else:
            # Check cache size limit
            if len(self.cache) >= self.cache_size:
                # Remove least recently used
                oldest_key = self.cache_order.pop(0)
                del self.cache[oldest_key]

        self.cache[key] = value
        self.cache_order.append(key)

    def _track_metric(self, metric_type: str, value: float = None):
        """Track CE model metrics."""
        try:
            # Import here to avoid circular imports
            from prometheus_client import Counter, Gauge, Histogram

            if metric_type == 'cache_hit':
                # Would need to define these globally in the service
                pass  # Metrics tracked in service layer
            elif metric_type == 'cache_miss':
                pass  # Metrics tracked in service layer
            elif metric_type == 'inference_time' and value is not None:
                pass  # Metrics tracked in service layer
            elif metric_type == 'inference_error':
                pass  # Metrics tracked in service layer
        except ImportError:
            pass  # Prometheus not available

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return {
            "cache_size": len(self.cache),
            "cache_max": self.cache_size,
            "model_loaded": self.model is not None,
            "model_name": self.model_name
        }

    def health_check(self) -> dict:
        """Comprehensive health check for CE model."""
        stats = self.get_cache_stats()

        # Test inference if model loaded
        if stats["model_loaded"]:
            try:
                test_score = self.predict("test query", "test document")
                stats["inference_working"] = isinstance(test_score, float) and 0 <= test_score <= 1
                stats["test_inference_score"] = test_score
            except Exception as e:
                stats["inference_working"] = False
                stats["inference_error"] = str(e)
        else:
            stats["inference_working"] = False
            stats["fallback_mode"] = True

        return stats

# Global cross-encoder manager
ce_manager = CrossEncoderManager()

def _cross_encoder_similarity(query: str, doc_text: str) -> float:
    """Get cross-encoder similarity score."""
    return ce_manager.predict(query, doc_text)

def should_use_cross_encoder(query: str, intent: Optional[str] = None) -> bool:
    """
    Determine if query should use cross-encoder reranking using neural routing.

    Uses neural context analysis for intelligent routing decisions.
    Falls back to heuristic rules if neural analysis unavailable.
    """
    if not RAG_RERANKER_CE_ENABLED:
        return False

    try:
        # Try neural routing first
        from ce_neural_router import route_to_ce
        decision = route_to_ce(query, intent)
        return decision.use_ce

    except ImportError:
        # Fallback to heuristic rules
        return _heuristic_ce_routing(query, intent)

def _heuristic_ce_routing(query: str, intent: Optional[str] = None) -> bool:
    """Fallback heuristic routing when neural router unavailable."""
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
