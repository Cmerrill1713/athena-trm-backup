"""
Auto-Rollback System
Automatically rollback deployments if quality degrades
"""
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AutoRollbackEngine:
    def __init__(self, 
                 error_threshold: float = 0.05,
                 latency_threshold_ms: float = 5000,
                 sample_size: int = 100):
        self.error_threshold = error_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.sample_size = sample_size
        self.enabled = True
        logger.info(f"✅ AutoRollback initialized (threshold: {error_threshold:.1%}, latency: {latency_threshold_ms}ms)")
    
    async def evaluate_deployment(self, 
                                   canary_metrics: Dict[str, Any],
                                   production_metrics: Dict[str, Any]) -> str:
        """
        Evaluate if canary should be promoted or rolled back
        
        Returns: "PROMOTE", "ROLLBACK", or "HOLD"
        """
        if not self.enabled:
            return "HOLD"
        
        # Calculate error rates
        canary_error_rate = canary_metrics.get("errors", 0) / max(canary_metrics.get("requests", 1), 1)
        prod_error_rate = production_metrics.get("errors", 0) / max(production_metrics.get("requests", 1), 1)
        
        # Check if canary is significantly worse
        if canary_error_rate > self.error_threshold:
            logger.warning(f"🔴 Auto-Rollback: Canary error rate {canary_error_rate:.2%} > threshold {self.error_threshold:.2%}")
            return "ROLLBACK"
        
        if canary_error_rate > prod_error_rate * 2:
            logger.warning(f"🔴 Auto-Rollback: Canary errors 2x production ({canary_error_rate:.2%} vs {prod_error_rate:.2%})")
            return "ROLLBACK"
        
        # Check latency
        canary_p95 = canary_metrics.get("latency_p95_ms", 0)
        if canary_p95 > self.latency_threshold_ms:
            logger.warning(f"🔴 Auto-Rollback: Canary latency {canary_p95}ms > threshold {self.latency_threshold_ms}ms")
            return "ROLLBACK"
        
        # Check sample size
        if canary_metrics.get("requests", 0) < self.sample_size:
            return "HOLD"  # Need more data
        
        # If canary is performing well, promote
        if canary_error_rate <= prod_error_rate and canary_p95 < self.latency_threshold_ms:
            logger.info(f"✅ Auto-Promote: Canary performing well (errors: {canary_error_rate:.2%}, latency: {canary_p95}ms)")
            return "PROMOTE"
        
        return "HOLD"

