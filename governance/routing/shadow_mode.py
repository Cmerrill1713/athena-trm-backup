"""
Shadow Mode Router - A/B testing for routing strategies.

Runs two routers in parallel:
- Primary router (serves actual traffic)
- Shadow router (logs decisions for comparison)

Collects metrics on routing distribution, confidence, and agreement
to validate new routing strategies before full deployment.
"""

import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from governance.routing.basic_router import BasicRouter, RoutingRequest, RoutingChoice
from governance.observability.routing_metrics import routing_metrics

logger = logging.getLogger(__name__)


@dataclass
class ShadowComparison:
    """Comparison between primary and shadow routing decisions."""
    
    query: str
    domain: str
    timestamp: datetime
    
    # Primary router decision
    primary_model: str
    primary_confidence: float
    primary_latency_ms: float
    primary_metadata: Dict
    
    # Shadow router decision
    shadow_model: str
    shadow_confidence: float
    shadow_latency_ms: float
    shadow_metadata: Dict
    
    # Comparison
    agreement: bool  # True if both chose same model
    confidence_delta: float  # shadow - primary confidence
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for logging/storage."""
        return {
            'query': self.query,
            'domain': self.domain,
            'timestamp': self.timestamp.isoformat(),
            'primary': {
                'model': self.primary_model,
                'confidence': self.primary_confidence,
                'latency_ms': self.primary_latency_ms,
                'metadata': self.primary_metadata
            },
            'shadow': {
                'model': self.shadow_model,
                'confidence': self.shadow_confidence,
                'latency_ms': self.shadow_latency_ms,
                'metadata': self.shadow_metadata
            },
            'agreement': self.agreement,
            'confidence_delta': self.confidence_delta
        }


class ShadowModeRouter:
    """
    Shadow mode router for A/B testing.
    
    Runs primary and shadow routers in parallel, serving traffic from
    primary while collecting comparison metrics from shadow.
    """
    
    def __init__(
        self,
        primary_router: BasicRouter,
        shadow_router: BasicRouter,
        log_path: Optional[Path] = None,
        sample_rate: float = 1.0
    ):
        """
        Initialize shadow mode router.
        
        Args:
            primary_router: Primary router (serves traffic)
            shadow_router: Shadow router (logs for comparison)
            log_path: Path to log comparisons (JSON lines)
            sample_rate: Fraction of requests to shadow (0.0-1.0)
        """
        self.primary_router = primary_router
        self.shadow_router = shadow_router
        self.log_path = log_path or Path('state/shadow_mode_comparisons.jsonl')
        self.sample_rate = sample_rate
        
        # Ensure log directory exists
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.total_requests = 0
        self.shadow_requests = 0
        self.agreements = 0
        self.confidence_deltas: List[float] = []
        
        logger.info(
            f"ShadowModeRouter initialized: "
            f"log_path={log_path}, sample_rate={sample_rate}"
        )
    
    def route(self, request: RoutingRequest) -> RoutingChoice:
        """
        Route request using primary router, optionally shadow.
        
        Args:
            request: Routing request
        
        Returns:
            Primary router's choice (shadow logged separately)
        """
        self.total_requests += 1
        
        # Always route with primary
        primary_choice = self.primary_router.route(request)
        
        # Shadow with probability sample_rate
        import random
        if random.random() < self.sample_rate:
            self.shadow_requests += 1
            self._shadow_route(request, primary_choice)
        
        return primary_choice
    
    def _shadow_route(self, request: RoutingRequest, primary_choice: RoutingChoice):
        """
        Route with shadow router and log comparison.
        
        Args:
            request: Routing request
            primary_choice: Primary router's decision
        """
        try:
            # Route with shadow
            shadow_choice = self.shadow_router.route(request)
            
            # Compare
            agreement = (primary_choice.model == shadow_choice.model)
            confidence_delta = shadow_choice.confidence - primary_choice.confidence
            
            if agreement:
                self.agreements += 1
            
            self.confidence_deltas.append(confidence_delta)
            
            # Create comparison
            comparison = ShadowComparison(
                query=request.query,
                domain=request.domain,
                timestamp=datetime.now(),
                primary_model=primary_choice.model,
                primary_confidence=primary_choice.confidence,
                primary_latency_ms=primary_choice.latency_ms,
                primary_metadata=primary_choice.metadata,
                shadow_model=shadow_choice.model,
                shadow_confidence=shadow_choice.confidence,
                shadow_latency_ms=shadow_choice.latency_ms,
                shadow_metadata=shadow_choice.metadata,
                agreement=agreement,
                confidence_delta=confidence_delta
            )
            
            # Log comparison
            self._log_comparison(comparison)
            
            # Record metrics
            from prometheus_client import Counter, Histogram, Gauge
            
            # These would be defined in routing_metrics.py in production
            if not hasattr(self, '_shadow_metrics_initialized'):
                self._shadow_agreement = Counter(
                    'athena_shadow_agreement_total',
                    'Shadow mode router agreement',
                    ['primary_model', 'shadow_model']
                )
                self._shadow_confidence_delta = Histogram(
                    'athena_shadow_confidence_delta',
                    'Shadow mode confidence delta',
                    buckets=(-1.0, -0.5, -0.2, -0.1, 0.0, 0.1, 0.2, 0.5, 1.0)
                )
                self._shadow_metrics_initialized = True
            
            if agreement:
                self._shadow_agreement.labels(
                    primary_model=primary_choice.model,
                    shadow_model=shadow_choice.model
                ).inc()
            
            self._shadow_confidence_delta.observe(confidence_delta)
            
        except Exception as e:
            logger.error(f"Shadow routing error: {e}", exc_info=True)
            routing_metrics.record_agent_error(
                agent='shadow_router',
                error_type=type(e).__name__
            )
    
    def _log_comparison(self, comparison: ShadowComparison):
        """Log comparison to JSONL file."""
        try:
            import json
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(comparison.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to log comparison: {e}")
    
    def get_statistics(self) -> Dict:
        """
        Get shadow mode statistics.
        
        Returns:
            Dictionary with agreement rate, confidence deltas, etc.
        """
        if self.shadow_requests == 0:
            return {
                'total_requests': self.total_requests,
                'shadow_requests': 0,
                'agreement_rate': 0.0,
                'avg_confidence_delta': 0.0
            }
        
        import numpy as np
        
        agreement_rate = self.agreements / self.shadow_requests
        avg_confidence_delta = np.mean(self.confidence_deltas)
        
        return {
            'total_requests': self.total_requests,
            'shadow_requests': self.shadow_requests,
            'sample_rate': self.sample_rate,
            'agreement_rate': agreement_rate,
            'agreements': self.agreements,
            'disagreements': self.shadow_requests - self.agreements,
            'avg_confidence_delta': float(avg_confidence_delta),
            'confidence_delta_std': float(np.std(self.confidence_deltas)),
            'confidence_delta_min': float(np.min(self.confidence_deltas)),
            'confidence_delta_max': float(np.max(self.confidence_deltas))
        }
    
    def print_report(self):
        """Print shadow mode report."""
        stats = self.get_statistics()
        
        print("\n" + "="*60)
        print("SHADOW MODE ROUTING REPORT")
        print("="*60)
        print(f"Total Requests: {stats['total_requests']}")
        print(f"Shadow Requests: {stats['shadow_requests']} ({stats['sample_rate']*100:.1f}%)")
        print(f"\nAgreement Rate: {stats['agreement_rate']*100:.1f}%")
        print(f"  Agreements: {stats['agreements']}")
        print(f"  Disagreements: {stats['disagreements']}")
        print(f"\nConfidence Delta (Shadow - Primary):")
        print(f"  Mean: {stats['avg_confidence_delta']:+.3f}")
        print(f"  Std Dev: {stats['confidence_delta_std']:.3f}")
        print(f"  Range: [{stats['confidence_delta_min']:+.3f}, {stats['confidence_delta_max']:+.3f}]")
        print("="*60 + "\n")

