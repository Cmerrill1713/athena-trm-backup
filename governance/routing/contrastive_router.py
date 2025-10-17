"""
Contrastive Domain Router - Advanced routing with embedding similarity.

Uses cosine similarity between query domain embeddings and model domain
embeddings to make intelligent routing decisions. Falls back to kNN or
weighted strategies when confidence is low.
"""

import logging
import numpy as np
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from governance.routing.basic_router import (
    BasicRouter,
    RoutingRequest,
    RoutingChoice,
    ModelProfile
)
from governance.observability.routing_metrics import routing_metrics

logger = logging.getLogger(__name__)


class EmbeddingCache:
    """
    LRU cache for domain embeddings.
    
    Caches embeddings to avoid recomputing for frequently seen domains.
    """
    
    def __init__(self, maxsize: int = 10000):
        """
        Initialize cache.
        
        Args:
            maxsize: Maximum number of entries to cache
        """
        self.cache: Dict[str, np.ndarray] = {}
        self.maxsize = maxsize
        self.access_order: List[str] = []
    
    def get(self, key: str) -> Optional[np.ndarray]:
        """Get embedding from cache."""
        if key in self.cache:
            # Update access order (move to end = most recent)
            self.access_order.remove(key)
            self.access_order.append(key)
            routing_metrics.record_cache_hit(key)
            return self.cache[key]
        
        routing_metrics.record_cache_miss(key)
        return None
    
    def put(self, key: str, value: np.ndarray):
        """Put embedding in cache."""
        if key in self.cache:
            # Update existing entry
            self.access_order.remove(key)
        elif len(self.cache) >= self.maxsize:
            # Evict least recently used
            lru_key = self.access_order.pop(0)
            del self.cache[lru_key]
        
        self.cache[key] = value
        self.access_order.append(key)
    
    def clear(self):
        """Clear the cache."""
        self.cache.clear()
        self.access_order.clear()


class ContrastiveRouter(BasicRouter):
    """
    Contrastive domain router using embedding similarity.
    
    Extends BasicRouter with:
    - Cosine similarity scoring between query and model embeddings
    - Margin-based fallback (confidence = margin between best and second-best)
    - Embedding cache for performance
    - kNN fallback for cold start
    """
    
    def __init__(
        self,
        profiles_path: Path,
        fallback_threshold: float = 0.7,
        fallback_margin: float = 0.1,
        cache_size: int = 10000,
        w_domain: float = 0.5,
        w_quality: float = 0.3,
        w_cost: float = 0.2
    ):
        """
        Initialize contrastive router.
        
        Args:
            profiles_path: Path to model_profiles.json
            fallback_threshold: Confidence threshold for fallback
            fallback_margin: Margin threshold (best - second_best)
            cache_size: Embedding cache size
            w_domain: Weight for domain similarity
            w_quality: Weight for quality score
            w_cost: Weight for cost (negative)
        """
        super().__init__(profiles_path, fallback_threshold)
        
        self.fallback_margin = fallback_margin
        self.w_domain = w_domain
        self.w_quality = w_quality
        self.w_cost = w_cost
        
        # Embedding cache
        self.embedding_cache = EmbeddingCache(maxsize=cache_size)
        
        # Pre-compute model embeddings as numpy arrays
        self._prepare_model_embeddings()
        
        logger.info(
            f"ContrastiveRouter initialized: "
            f"fallback_threshold={fallback_threshold}, "
            f"fallback_margin={fallback_margin}, "
            f"weights=({w_domain}, {w_quality}, {w_cost})"
        )
    
    def _prepare_model_embeddings(self):
        """Pre-compute model embeddings as numpy arrays for efficiency."""
        for model in self.models:
            if model.domain_embedding:
                # Convert to numpy array and normalize
                emb = np.array(model.domain_embedding, dtype=np.float32)
                model.domain_embedding_np = emb / (np.linalg.norm(emb) + 1e-8)
            else:
                logger.warning(f"Model {model.model_id} has no domain embedding")
                model.domain_embedding_np = None
    
    def _get_query_embedding(self, domain: str) -> Optional[np.ndarray]:
        """
        Get query domain embedding.
        
        For now, uses the embedding of the best-matching model domain.
        In production, this would call a sentence-transformer model.
        
        Args:
            domain: Query domain
        
        Returns:
            Normalized embedding vector or None
        """
        # Check cache first
        cached = self.embedding_cache.get(domain)
        if cached is not None:
            return cached
        
        # Find model with matching domain
        for model in self.models:
            if model.domain == domain and model.domain_embedding_np is not None:
                # Use model's domain embedding as proxy
                self.embedding_cache.put(domain, model.domain_embedding_np)
                return model.domain_embedding_np
        
        logger.debug(f"No embedding found for domain: {domain}")
        return None
    
    def _cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """
        Compute cosine similarity between two vectors.
        
        Args:
            a: First vector (normalized)
            b: Second vector (normalized)
        
        Returns:
            Cosine similarity in [0, 1]
        """
        # Since vectors are pre-normalized, dot product = cosine similarity
        similarity = np.dot(a, b)
        # Clamp to [0, 1] (should already be in [-1, 1])
        return float(max(0.0, min(1.0, similarity)))
    
    def _compute_scores(
        self,
        query_embedding: np.ndarray,
        request: RoutingRequest
    ) -> List[Tuple[ModelProfile, float, float]]:
        """
        Compute scores for all models.
        
        Args:
            query_embedding: Query domain embedding
            request: Routing request
        
        Returns:
            List of (model, score, similarity) tuples, sorted by score descending
        """
        scores = []
        
        for model in self.models:
            if model.domain_embedding_np is None:
                continue
            
            # Compute cosine similarity
            similarity = self._cosine_similarity(
                query_embedding,
                model.domain_embedding_np
            )
            
            # Compute weighted score
            # Higher quality and similarity = better
            # Higher cost = worse
            score = (
                similarity * self.w_domain
                + model.quality_score * self.w_quality
                - model.cost * self.w_cost
            )
            
            scores.append((model, score, similarity))
        
        # Sort by score descending
        scores.sort(key=lambda x: x[1], reverse=True)
        
        return scores
    
    def route(self, request: RoutingRequest) -> RoutingChoice:
        """
        Route request using contrastive domain embeddings.
        
        Args:
            request: Routing request
        
        Returns:
            Routing choice with confidence
        """
        start_time = time.time()
        
        try:
            # Get query embedding
            query_emb = self._get_query_embedding(request.domain)
            
            if query_emb is None:
                # No embedding available, fall back to basic router
                logger.info(
                    f"No embedding for domain '{request.domain}', "
                    f"using basic routing"
                )
                return super().route(request)
            
            # Compute scores for all models
            scores = self._compute_scores(query_emb, request)
            
            if not scores:
                logger.warning("No models with embeddings available")
                return super().route(request)
            
            # Get best and second-best
            best_model, best_score, best_similarity = scores[0]
            second_score = scores[1][1] if len(scores) > 1 else 0.0
            
            # Compute margin and confidence
            margin = best_score - second_score
            confidence = best_similarity  # Use similarity as confidence
            
            # Check margin threshold
            if margin < self.fallback_margin:
                logger.info(
                    f"Low margin ({margin:.3f} < {self.fallback_margin}), "
                    f"using kNN fallback"
                )
                
                routing_metrics.record_fallback(
                    reason='low_margin',
                    from_model=best_model.model_id,
                    to_model='knn_fallback'
                )
                
                # kNN fallback: use top-k similar models
                choice = self._knn_fallback(scores, request)
            
            elif confidence < self.fallback_threshold:
                logger.info(
                    f"Low confidence ({confidence:.3f} < {self.fallback_threshold}), "
                    f"using weighted fallback"
                )
                
                routing_metrics.record_fallback(
                    reason='low_confidence',
                    from_model=best_model.model_id,
                    to_model='weighted_fallback'
                )
                
                choice = self._weighted_fallback(request)
            
            else:
                # Use best model
                choice = RoutingChoice(
                    model=best_model.model_id,
                    confidence=confidence,
                    domain=best_model.domain,
                    metadata={
                        'strategy': 'contrastive',
                        'similarity': best_similarity,
                        'score': best_score,
                        'margin': margin,
                        'quality_score': best_model.quality_score,
                        'cost': best_model.cost
                    }
                )
            
            # Record metrics
            latency_ms = (time.time() - start_time) * 1000
            choice.latency_ms = latency_ms
            
            routing_metrics.record_request(
                model=choice.model,
                domain=choice.domain,
                status='success',
                latency_ms=latency_ms,
                confidence=choice.confidence
            )
            
            logger.info(
                f"Routed to {choice.model} "
                f"(confidence: {choice.confidence:.3f}, "
                f"margin: {margin:.3f}, "
                f"latency: {latency_ms:.1f}ms)"
            )
            
            return choice
        
        except Exception as e:
            logger.error(f"Contrastive routing error: {e}", exc_info=True)
            
            # Fall back to basic router
            routing_metrics.record_agent_error(
                agent='contrastive_router',
                error_type=type(e).__name__
            )
            
            return super().route(request)
    
    def _knn_fallback(
        self,
        scores: List[Tuple[ModelProfile, float, float]],
        request: RoutingRequest,
        k: int = 3
    ) -> RoutingChoice:
        """
        kNN fallback: ensemble of top-k similar models.
        
        For now, just returns the best of top-k by quality/cost ratio.
        In production, this could do weighted voting or ensemble.
        
        Args:
            scores: Sorted list of (model, score, similarity)
            request: Routing request
            k: Number of neighbors to consider
        
        Returns:
            Routing choice
        """
        # Take top-k
        top_k = scores[:k]
        
        # Select best by quality/cost ratio among top-k
        best = max(top_k, key=lambda x: x[0].quality_score / (x[0].cost + 0.001))
        model, score, similarity = best
        
        return RoutingChoice(
            model=model.model_id,
            confidence=0.6,  # kNN fallback has medium confidence
            domain=model.domain,
            metadata={
                'strategy': 'knn_fallback',
                'k': k,
                'similarity': similarity,
                'score': score,
                'quality_score': model.quality_score,
                'cost': model.cost
            }
        )

