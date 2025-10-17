"""
Cost Optimization for Athena Router

Features:
- Cost-aware routing decisions
- Budget tracking and enforcement
- Cost-quality tradeoff optimization
- Usage analytics and reporting
"""

import logging
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import defaultdict

from governance.routing.basic_router import RoutingChoice, RoutingRequest
from governance.routing.contrastive_router import ContrastiveRouter

logger = logging.getLogger(__name__)


@dataclass
class CostMetrics:
    """Cost tracking metrics."""
    total_cost: float = 0.0
    request_count: int = 0
    cost_by_model: Dict[str, float] = field(default_factory=dict)
    cost_by_domain: Dict[str, float] = field(default_factory=dict)
    hourly_costs: Dict[int, float] = field(default_factory=dict)

    @property
    def avg_cost_per_request(self) -> float:
        return self.total_cost / max(self.request_count, 1)

    def record_cost(self, model: str, domain: str, cost: float):
        """Record a cost."""
        self.total_cost += cost
        self.request_count += 1

        self.cost_by_model[model] = self.cost_by_model.get(model, 0) + cost
        self.cost_by_domain[domain] = self.cost_by_domain.get(domain, 0) + cost

        # Hourly tracking
        hour = int(time.time() // 3600)
        self.hourly_costs[hour] = self.hourly_costs.get(hour, 0) + cost


@dataclass
class CostBudget:
    """Cost budget configuration."""
    daily_limit: float
    hourly_limit: float
    alert_threshold: float = 0.8  # Alert at 80% of budget

    def is_over_budget(self, metrics: CostMetrics) -> bool:
        """Check if over budget."""
        # Check hourly budget
        current_hour = int(time.time() // 3600)
        hourly_cost = metrics.hourly_costs.get(current_hour, 0)

        if hourly_cost >= self.hourly_limit:
            return True

        # Could add daily budget check here
        return False


class CostOptimizer:
    """Optimizes routing decisions for cost efficiency."""

    def __init__(self, budget: Optional[CostBudget] = None):
        self.budget = budget
        self.metrics = CostMetrics()
        self.cost_weights = {
            'cost': 0.7,      # 70% weight on cost
            'quality': 0.2,   # 20% weight on quality
            'latency': 0.1    # 10% weight on latency
        }

    def optimize_choice(self, router: ContrastiveRouter, request: RoutingRequest,
                       candidates: List[RoutingChoice]) -> RoutingChoice:
        """Optimize routing choice based on cost constraints."""

        if not candidates:
            # Fallback to normal routing
            return router.route(request)

        # Apply cost optimization
        scored_candidates = []
        for candidate in candidates:
            score = self._calculate_cost_score(candidate)
            scored_candidates.append((candidate, score))

        # Sort by score (lower is better for cost optimization)
        scored_candidates.sort(key=lambda x: x[1])

        best_choice = scored_candidates[0][0]

        # Record cost
        cost = best_choice.metadata.get('cost', 0.0)
        self.metrics.record_cost(best_choice.model, best_choice.domain, cost)

        # Check budget constraints
        if self.budget and self.budget.is_over_budget(self.metrics):
            logger.warning(f"Cost budget exceeded. Current: ${self.metrics.total_cost:.4f}")

        return best_choice

    def _calculate_cost_score(self, choice: RoutingChoice) -> float:
        """Calculate cost optimization score."""
        cost = choice.metadata.get('cost', 0.0)
        quality = choice.metadata.get('quality_score', 0.5)
        latency = choice.latency_ms

        # Normalize metrics
        normalized_cost = min(cost / 0.01, 1.0)  # Assume $0.01 max
        normalized_quality = quality  # Already 0-1
        normalized_latency = min(latency / 1000, 1.0)  # Assume 1000ms max

        # Calculate weighted score
        score = (
            self.cost_weights['cost'] * normalized_cost +
            self.cost_weights['quality'] * (1 - normalized_quality) +  # Lower quality = higher cost
            self.cost_weights['latency'] * normalized_latency
        )

        return score

    def get_cost_report(self) -> Dict:
        """Get cost analytics report."""
        return {
            'total_cost': self.metrics.total_cost,
            'request_count': self.metrics.request_count,
            'avg_cost_per_request': self.metrics.avg_cost_per_request,
            'cost_by_model': dict(self.metrics.cost_by_model),
            'cost_by_domain': dict(self.metrics.cost_by_domain),
            'top_cost_models': sorted(
                self.metrics.cost_by_model.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'budget_status': {
                'over_budget': self.budget.is_over_budget(self.metrics) if self.budget else False,
                'budget_configured': self.budget is not None
            }
        }

    def set_cost_weights(self, cost_weight: float, quality_weight: float, latency_weight: float):
        """Update cost optimization weights."""
        total = cost_weight + quality_weight + latency_weight
        self.cost_weights = {
            'cost': cost_weight / total,
            'quality': quality_weight / total,
            'latency': latency_weight / total
        }
        logger.info(f"Updated cost weights: {self.cost_weights}")


class UsageAnalytics:
    """Usage analytics and reporting."""

    def __init__(self):
        self.hourly_usage = defaultdict(int)
        self.model_usage = defaultdict(int)
        self.domain_usage = defaultdict(int)
        self.error_counts = defaultdict(int)

    def record_usage(self, model: str, domain: str, success: bool = True):
        """Record usage metrics."""
        hour = int(time.time() // 3600)

        self.hourly_usage[hour] += 1
        self.model_usage[model] += 1
        self.domain_usage[domain] += 1

        if not success:
            self.error_counts[model] += 1

    def get_usage_report(self) -> Dict:
        """Get usage analytics report."""
        total_requests = sum(self.hourly_usage.values())

        return {
            'total_requests': total_requests,
            'hourly_distribution': dict(self.hourly_usage),
            'model_distribution': dict(self.model_usage),
            'domain_distribution': dict(self.domain_usage),
            'error_rates': {
                model: self.error_counts[model] / max(self.model_usage[model], 1)
                for model in self.model_usage
            },
            'top_models': sorted(
                self.model_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5],
            'top_domains': sorted(
                self.domain_usage.items(),
                key=lambda x: x[1],
                reverse=True
            )[:3]
        }


# Global instances
cost_optimizer = CostOptimizer()
usage_analytics = UsageAnalytics()

