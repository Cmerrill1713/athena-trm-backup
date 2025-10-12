"""
FastVLM Fallback Handler

Automatic fallback to backup vision models when FastVLM:
- Is unavailable
- Has high latency (p95 > threshold)
- Returns errors
- Is overloaded

Emits metrics for observability of fallback decisions.
"""

import os
import time
import logging
from typing import Optional, Dict, Any

try:
    from prometheus_client import Counter
    
    FALLBACK_DECISIONS = Counter(
        'fastvlm_fallback_total',
        'FastVLM fallback decisions',
        ['reason', 'backup_model', 'env', 'build']
    )
    
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)

ENV = os.environ.get("ENV", "dev")
BUILD_SHA = os.environ.get("BUILD_SHA", "local")

# Fallback thresholds
P95_LATENCY_THRESHOLD_MS = 3000  # Fallback if p95 > 3s
ERROR_RATE_THRESHOLD = 0.1       # Fallback if error rate > 10%
MAX_RETRIES = 2                  # Retry before fallback


class FastVLMFallbackHandler:
    """
    Handles automatic fallback from FastVLM to backup vision models
    
    Fallback reasons:
    - unavailable: Server health check failed
    - high_latency: p95 latency exceeded threshold
    - errors: Error rate too high
    - overload: Too many concurrent requests
    - timeout: Request timed out
    """
    
    def __init__(self, backup_models: Optional[list] = None):
        """
        Initialize fallback handler
        
        Args:
            backup_models: List of backup model names in priority order
                         Default: ["openai-gpt4-vision", "anthropic-claude-vision"]
        """
        self.backup_models = backup_models or [
            "openai-gpt4-vision",
            "anthropic-claude-vision"
        ]
        self.logger = logger.getChild("FallbackHandler")
        
        # Track recent performance
        self.recent_latencies = []
        self.recent_errors = 0
        self.recent_successes = 0
    
    def should_fallback(self, reason: str) -> bool:
        """
        Decide if we should fallback based on recent performance
        
        Args:
            reason: Reason for considering fallback
        
        Returns:
            True if should fallback
        """
        # Always fallback if unavailable
        if reason == "unavailable":
            return True
        
        # Check error rate
        total_requests = self.recent_errors + self.recent_successes
        if total_requests > 10:
            error_rate = self.recent_errors / total_requests
            if error_rate > ERROR_RATE_THRESHOLD:
                self.logger.warning(
                    f"High error rate: {error_rate:.1%}, enabling fallback"
                )
                return True
        
        # Check latency (p95)
        if len(self.recent_latencies) > 20:
            sorted_latencies = sorted(self.recent_latencies)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p95 = sorted_latencies[p95_idx]
            
            if p95 > P95_LATENCY_THRESHOLD_MS:
                self.logger.warning(
                    f"High p95 latency: {p95:.0f}ms, enabling fallback"
                )
                return True
        
        return False
    
    def record_success(self, latency_ms: float):
        """Record a successful request"""
        self.recent_successes += 1
        self.recent_latencies.append(latency_ms)
        
        # Keep only last 100 latencies
        if len(self.recent_latencies) > 100:
            self.recent_latencies = self.recent_latencies[-100:]
    
    def record_error(self):
        """Record a failed request"""
        self.recent_errors += 1
    
    def get_backup_model(self, preferred: Optional[str] = None) -> str:
        """
        Get backup model to use
        
        Args:
            preferred: Preferred backup model (if available)
        
        Returns:
            Backup model name
        """
        if preferred and preferred in self.backup_models:
            return preferred
        
        return self.backup_models[0] if self.backup_models else "openai-gpt4-vision"
    
    def call_with_fallback(
        self,
        primary_fn,
        backup_fn,
        *args,
        **kwargs
    ) -> tuple[Any, str]:
        """
        Call primary function with automatic fallback
        
        Args:
            primary_fn: Primary function to call (FastVLM)
            backup_fn: Backup function to call on fallback
            *args, **kwargs: Arguments to pass to functions
        
        Returns:
            (result, model_used)
        """
        # Try primary first
        for attempt in range(MAX_RETRIES):
            try:
                start = time.time()
                result = primary_fn(*args, **kwargs)
                latency_ms = (time.time() - start) * 1000
                
                self.record_success(latency_ms)
                return result, "fastvlm-1.5b"
            
            except Exception as e:
                self.record_error()
                self.logger.warning(
                    f"FastVLM attempt {attempt + 1}/{MAX_RETRIES} failed: {e}"
                )
                
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))  # Exponential backoff
                    continue
                
                # All retries exhausted, check if we should fallback
                reason = self._classify_error(e)
                
                if self.should_fallback(reason):
                    backup_model = self.get_backup_model()
                    
                    self.logger.info(
                        f"Falling back to {backup_model} (reason: {reason})"
                    )
                    
                    # Emit metric
                    if METRICS_AVAILABLE:
                        FALLBACK_DECISIONS.labels(
                            reason=reason,
                            backup_model=backup_model,
                            env=ENV,
                            build=BUILD_SHA
                        ).inc()
                    
                    # Call backup
                    try:
                        result = backup_fn(*args, **kwargs)
                        return result, backup_model
                    except Exception as backup_error:
                        self.logger.error(
                            f"Backup {backup_model} also failed: {backup_error}"
                        )
                        raise
                else:
                    # Don't fallback, propagate error
                    raise
        
        # Should never reach here
        raise RuntimeError("Fallback logic error")
    
    def _classify_error(self, error: Exception) -> str:
        """Classify error for metrics"""
        error_str = str(error).lower()
        
        if "timeout" in error_str:
            return "timeout"
        elif "connection" in error_str or "unavailable" in error_str:
            return "unavailable"
        elif "overload" in error_str or "too many" in error_str:
            return "overload"
        else:
            return "error"


# Singleton instance
_fallback_handler: Optional[FastVLMFallbackHandler] = None


def get_fallback_handler() -> FastVLMFallbackHandler:
    """Get or create singleton fallback handler"""
    global _fallback_handler
    
    if _fallback_handler is None:
        _fallback_handler = FastVLMFallbackHandler()
    
    return _fallback_handler

