"""
A/B Testing Framework for Athena Router

Features:
- Traffic splitting between routing strategies
- Statistical significance tracking
- Cost-quality optimization
- Automatic winner declaration
"""

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from enum import Enum

from governance.routing.basic_router import BasicRouter, RoutingRequest, RoutingChoice
from governance.routing.contrastive_router import ContrastiveRouter

logger = logging.getLogger(__name__)


class ABTestStatus(Enum):
    """A/B test status."""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"


class ABTestStrategy(Enum):
    """Available A/B test strategies."""
    BASIC_VS_CONTRASTIVE = "basic_vs_contrastive"
    COST_VS_QUALITY = "cost_vs_quality"
    LATENCY_VS_ACCURACY = "latency_vs_accuracy"


@dataclass
class ABTestMetrics:
    """Metrics for A/B test variants."""
    requests: int = 0
    successful_requests: int = 0
    total_latency_ms: float = 0.0
    total_confidence: float = 0.0
    total_cost: float = 0.0
    error_count: int = 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / max(self.requests, 1)

    @property
    def avg_confidence(self) -> float:
        return self.total_confidence / max(self.requests, 1)

    @property
    def avg_cost(self) -> float:
        return self.total_cost / max(self.requests, 1)

    @property
    def success_rate(self) -> float:
        return self.successful_requests / max(self.requests, 1)

    def record_request(self, choice: RoutingChoice, success: bool = True):
        """Record a routing request."""
        self.requests += 1
        self.total_latency_ms += choice.latency_ms
        self.total_confidence += choice.confidence
        self.total_cost += choice.metadata.get("cost", 0.0)

        if success:
            self.successful_requests += 1
        else:
            self.error_count += 1


@dataclass
class ABTestVariant:
    """A/B test variant configuration."""
    name: str
    router: BasicRouter
    traffic_percentage: float
    metrics: ABTestMetrics = field(default_factory=ABTestMetrics)


@dataclass
class ABTest:
    """A/B test configuration and state."""
    test_id: str
    strategy: ABTestStrategy
    status: ABTestStatus = ABTestStatus.ACTIVE
    variants: List[ABTestVariant] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    min_samples: int = 1000
    significance_threshold: float = 0.95

    def get_variant(self, request: RoutingRequest) -> ABTestVariant:
        """Get variant for request using consistent hashing."""
        if not self.variants:
            raise ValueError("No variants configured")

        # Simple traffic splitting based on request hash
        request_hash = hash(request.query + request.domain) % 100
        cumulative_percentage = 0.0

        for variant in self.variants:
            cumulative_percentage += variant.traffic_percentage
            if request_hash / 100.0 <= cumulative_percentage:
                return variant

        # Fallback to first variant
        return self.variants[0]

    def record_result(self, variant: ABTestVariant, choice: RoutingChoice, success: bool = True):
        """Record test result."""
        variant.metrics.record_request(choice, success)

    def should_complete(self) -> bool:
        """Check if test should be completed."""
        if self.status != ABTestStatus.ACTIVE:
            return False

        # Check minimum sample size
        total_samples = sum(v.metrics.requests for v in self.variants)
        if total_samples < self.min_samples:
            return False

        # Check statistical significance (simplified)
        if len(self.variants) >= 2:
            # Compare success rates
            success_rates = [v.metrics.success_rate for v in self.variants]
            max_rate = max(success_rates)
            min_rate = min(success_rates)

            # If one variant is significantly better
            if max_rate - min_rate > 0.05:  # 5% difference threshold
                return True

        return False

    def get_winner(self) -> Optional[ABTestVariant]:
        """Get the winning variant."""
        if not self.variants:
            return None

        # Simple winner selection based on success rate
        return max(self.variants, key=lambda v: v.metrics.success_rate)


class ABTestManager:
    """Manages A/B tests for the routing system."""

    def __init__(self):
        self.tests: Dict[str, ABTest] = {}
        self.logger = logging.getLogger(__name__)

    def create_test(self, test_id: str, strategy: ABTestStrategy,
                   basic_router: BasicRouter, contrastive_router: Optional[ContrastiveRouter] = None) -> ABTest:
        """Create a new A/B test."""

        if strategy == ABTestStrategy.BASIC_VS_CONTRASTIVE:
            if not contrastive_router:
                raise ValueError("Contrastive router required for BASIC_VS_CONTRASTIVE test")

            test = ABTest(
                test_id=test_id,
                strategy=strategy,
                variants=[
                    ABTestVariant("basic", basic_router, 0.5),
                    ABTestVariant("contrastive", contrastive_router, 0.5)
                ]
            )

        elif strategy == ABTestStrategy.COST_VS_QUALITY:
            # Create variants with different cost/quality tradeoffs
            test = ABTest(
                test_id=test_id,
                strategy=strategy,
                variants=[
                    ABTestVariant("cost_optimized", basic_router, 0.5),
                    ABTestVariant("quality_optimized", basic_router, 0.5)  # Could be different router
                ]
            )

        else:
            raise ValueError(f"Unsupported strategy: {strategy}")

        self.tests[test_id] = test
        self.logger.info(f"Created A/B test {test_id} with strategy {strategy.value}")
        return test

    def route_request(self, test_id: str, request: RoutingRequest) -> RoutingChoice:
        """Route request through A/B test."""
        test = self.tests.get(test_id)
        if not test or test.status != ABTestStatus.ACTIVE:
            raise ValueError(f"A/B test {test_id} not active")

        variant = test.get_variant(request)
        choice = variant.router.route(request)
        test.record_result(variant, choice)

        self.logger.debug(f"A/B test {test_id}: routed to {variant.name} -> {choice.model}")

        return choice

    def complete_test(self, test_id: str) -> Optional[ABTestVariant]:
        """Complete an A/B test and return winner."""
        test = self.tests.get(test_id)
        if not test:
            return None

        winner = test.get_winner()
        test.status = ABTestStatus.COMPLETED

        self.logger.info(f"Completed A/B test {test_id}. Winner: {winner.name if winner else 'None'}")

        return winner

    def get_test_status(self, test_id: str) -> Optional[Dict]:
        """Get A/B test status."""
        test = self.tests.get(test_id)
        if not test:
            return None

        return {
            "test_id": test.test_id,
            "strategy": test.strategy.value,
            "status": test.status.value,
            "variants": [
                {
                    "name": v.name,
                    "traffic_percentage": v.traffic_percentage,
                    "requests": v.metrics.requests,
                    "success_rate": v.metrics.success_rate,
                    "avg_latency_ms": v.metrics.avg_latency_ms,
                    "avg_confidence": v.metrics.avg_confidence,
                    "avg_cost": v.metrics.avg_cost
                }
                for v in test.variants
            ],
            "should_complete": test.should_complete()
        }


# Global A/B test manager
ab_test_manager = ABTestManager()

