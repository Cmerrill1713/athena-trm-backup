"""
Basic router implementation for Athena.

Provides simple round-robin and weighted routing strategies
as a foundation for more sophisticated contrastive routing.
"""

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from governance.observability.routing_metrics import routing_metrics

logger = logging.getLogger(__name__)


@dataclass
class RoutingRequest:
    """A request to route to a model."""
    query: str
    domain: str = "general"
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class RoutingChoice:
    """The router's choice of model."""
    model: str
    confidence: float
    domain: str
    latency_ms: float = 0.0
    metadata: Dict[str, any] = field(default_factory=dict)


@dataclass
class ModelProfile:
    """Model profile loaded from JSON."""
    model_id: str
    domain: str
    domain_embedding: List[float]
    quality_score: float
    cost: float
    latency_p50_ms: float
    latency_p95_ms: float
    is_approximate: bool
    confidence: float
    metadata: Dict[str, any]
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModelProfile':
        """Load from dictionary."""
        return cls(
            model_id=data['model_id'],
            domain=data['domain'],
            domain_embedding=data['domain_embedding'],
            quality_score=data['quality_score'],
            cost=data['cost'],
            latency_p50_ms=data.get('latency_p50_ms', 1000),
            latency_p95_ms=data.get('latency_p95_ms', 2000),
            is_approximate=data['is_approximate'],
            confidence=data['confidence'],
            metadata=data.get('metadata', {})
        )


class BasicRouter:
    """
    Basic router implementation with fallback support.
    
    Implements simple routing strategies:
    - Domain-based routing (match request domain to model domain)
    - Weighted routing (based on quality score)
    - Round-robin fallback
    """
    
    def __init__(
        self,
        profiles_path: Path,
        fallback_threshold: float = 0.7
    ):
        """
        Initialize router.
        
        Args:
            profiles_path: Path to model_profiles.json
            fallback_threshold: Confidence threshold for fallback
        """
        self.profiles_path = profiles_path
        self.fallback_threshold = fallback_threshold
        self.models: List[ModelProfile] = []
        self.round_robin_index = 0
        
        self._load_profiles()
    
    def _load_profiles(self):
        """Load model profiles from JSON."""
        try:
            logger.info(f"Loading model profiles from {self.profiles_path}")
            
            with open(self.profiles_path) as f:
                data = json.load(f)
            
            self.models = [
                ModelProfile.from_dict(m)
                for m in data.get('models', [])
            ]
            
            logger.info(f"Loaded {len(self.models)} model profiles")
            
            for model in self.models:
                status = 'approximate' if model.is_approximate else 'success'
                routing_metrics.record_profile_load(status)
        
        except Exception as e:
            logger.error(f"Failed to load model profiles: {e}")
            routing_metrics.record_profile_load('error')
            raise
    
    def route(self, request: RoutingRequest) -> RoutingChoice:
        """
        Route a request to a model.
        
        Args:
            request: Routing request
        
        Returns:
            Routing choice with selected model
        """
        start_time = time.time()
        
        try:
            # Strategy 1: Domain matching
            domain_match = self._find_domain_match(request)
            if domain_match and domain_match.confidence >= self.fallback_threshold:
                choice = domain_match
            else:
                # Strategy 2: Weighted quality fallback
                logger.info(
                    f"Domain match confidence ({domain_match.confidence if domain_match else 0:.2f}) "
                    f"< threshold ({self.fallback_threshold}), using fallback"
                )
                
                if domain_match:
                    routing_metrics.record_fallback(
                        reason='low_confidence',
                        from_model=domain_match.model,
                        to_model='fallback_weighted'
                    )
                
                choice = self._weighted_fallback(request)
            
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
                f"Routed request to {choice.model} "
                f"(domain: {choice.domain}, confidence: {choice.confidence:.2f}, "
                f"latency: {latency_ms:.1f}ms)"
            )
            
            return choice
        
        except Exception as e:
            logger.error(f"Routing error: {e}", exc_info=True)
            
            latency_ms = (time.time() - start_time) * 1000
            routing_metrics.record_request(
                model='error',
                domain=request.domain,
                status='error',
                latency_ms=latency_ms
            )
            
            # Emergency fallback: round-robin
            return self._round_robin_fallback(request)
    
    def _find_domain_match(self, request: RoutingRequest) -> Optional[RoutingChoice]:
        """Find best domain match."""
        # Filter models by domain
        matches = [
            m for m in self.models
            if m.domain == request.domain
        ]
        
        if not matches:
            logger.debug(f"No domain match for {request.domain}")
            return None
        
        # Select best by quality score
        best = max(matches, key=lambda m: m.quality_score)
        
        # Confidence = quality score for domain matches
        # (will be replaced with embedding similarity in contrastive router)
        confidence = best.quality_score
        
        return RoutingChoice(
            model=best.model_id,
            confidence=confidence,
            domain=best.domain,
            metadata={
                'strategy': 'domain_match',
                'quality_score': best.quality_score,
                'cost': best.cost
            }
        )
    
    def _weighted_fallback(self, request: RoutingRequest) -> RoutingChoice:
        """Weighted fallback based on quality/cost ratio."""
        if not self.models:
            raise RuntimeError("No models available for fallback")
        
        # Simple heuristic: quality / cost
        best = max(self.models, key=lambda m: m.quality_score / (m.cost + 0.001))
        
        return RoutingChoice(
            model=best.model_id,
            confidence=0.5,  # Fallback has lower confidence
            domain=best.domain,
            metadata={
                'strategy': 'weighted_fallback',
                'quality_score': best.quality_score,
                'cost': best.cost
            }
        )
    
    def _round_robin_fallback(self, request: RoutingRequest) -> RoutingChoice:
        """Emergency round-robin fallback."""
        if not self.models:
            raise RuntimeError("No models available for emergency fallback")
        
        model = self.models[self.round_robin_index % len(self.models)]
        self.round_robin_index += 1
        
        routing_metrics.record_fallback(
            reason='emergency',
            from_model='unknown',
            to_model=model.model_id
        )
        
        return RoutingChoice(
            model=model.model_id,
            confidence=0.3,  # Emergency fallback has lowest confidence
            domain=model.domain,
            metadata={
                'strategy': 'round_robin_emergency',
                'quality_score': model.quality_score,
                'cost': model.cost
            }
        )

