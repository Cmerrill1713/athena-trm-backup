"""
Canary Router - Progressive model rollout with circuit breaker protection

Enables safe A/B testing of new models:
- Route X% of traffic to canary model
- Monitor success rate and latency
- Automatic rollback if canary degrades
- Circuit breaker prevents cascading failures

Environment variables:
- CANARY_ENABLED: true/false
- CANARY_MODEL: Model to test (e.g., "fastvlm-1.5b")
- CANARY_PERCENT: % of traffic (0-100)
- CANARY_REQUIRE_HEALTH: Skip canary if circuit open (default: true)
"""

import os
import random
from typing import Any, Dict, Optional, Tuple
from .circuit_breaker import get_circuit_breaker

# Configuration from environment
CANARY_ENABLED = os.environ.get("CANARY_ENABLED", "false").lower() == "true"
CANARY_MODEL = os.environ.get("CANARY_MODEL", "")
CANARY_PERCENT = int(os.environ.get("CANARY_PERCENT", 0))
CANARY_REQUIRE_HEALTH = os.environ.get("CANARY_REQUIRE_HEALTH", "true").lower() == "true"

# Get circuit breaker instance
CB = get_circuit_breaker()


def model_healthy(model: str) -> bool:
    """
    Check if model is healthy (circuit not open)

    Args:
        model: Model name

    Returns:
        True if model is healthy
    """
    return not CB.is_open(model)


def pick_model(
    base_policy: Dict[str, Any],
    intent: Optional[str] = None
) -> Tuple[str, Dict[str, Any], str]:
    """
    Select model with canary sampling and circuit breaker protection

    Args:
        base_policy: Baseline routing policy
        intent: Optional request intent/type

    Returns:
        (model_name, policy, bucket)
        bucket is one of: "control", "canary", "fallback"
    """
    control_model = base_policy.get("selected_model", "mlx:qwen")
    chosen_model = control_model
    bucket = "control"

    # Circuit breaker: If control is open, use fallback
    if CB.is_open(control_model):
        # Choose a safe fallback
        fallback_model = "mlx:qwen" if control_model != "mlx:qwen" else "ollama:llama3.1"

        if model_healthy(fallback_model):
            chosen_model = fallback_model
            bucket = "fallback"
            print(f"⚠️  Circuit open for {control_model}, using {fallback_model}")
        else:
            # No healthy fallback, use control anyway (last resort)
            print(f"⚠️  No healthy fallback for {control_model}, using anyway")

    # Canary sampling (only if enabled, configured, and healthy)
    if (CANARY_ENABLED and
        CANARY_MODEL and
        CANARY_PERCENT > 0 and
        not CB.is_open(CANARY_MODEL)):

        # Skip canary if it requires health check and fails
        if CANARY_REQUIRE_HEALTH and not model_healthy(CANARY_MODEL):
            pass  # Use control
        else:
            # Random sampling
            roll = random.randint(1, 100)
            if roll <= CANARY_PERCENT:
                chosen_model = CANARY_MODEL
                bucket = "canary"

    # Build final policy with bucket tag
    policy = {
        **base_policy,
        "selected_model": chosen_model,
        "bucket": bucket
    }

    return chosen_model, policy, bucket


def record_outcome(
    model: str,
    success: bool,
    latency_ms: int
):
    """
    Record request outcome to circuit breaker

    Args:
        model: Model name
        success: Whether request succeeded
        latency_ms: Request latency in milliseconds
    """
    CB.record(model, success, latency_ms)


def get_breaker_stats(model: str) -> Optional[Dict]:
    """
    Get circuit breaker stats for a model

    Args:
        model: Model name

    Returns:
        Stats dict or None
    """
    return CB.get_stats(model)


def reset_breaker(model: str):
    """
    Manually reset circuit for a model

    Args:
        model: Model name
    """
    CB.reset(model)


def get_canary_config() -> Dict[str, Any]:
    """
    Get current canary configuration

    Returns:
        Config dict
    """
    return {
        "enabled": CANARY_ENABLED,
        "model": CANARY_MODEL,
        "percent": CANARY_PERCENT,
        "require_health": CANARY_REQUIRE_HEALTH,
        "circuit_breaker": {
            "window": CB.window,
            "fail_rate_threshold": CB.fail_rate,
            "p95_threshold_ms": CB.p95_ms,
            "open_seconds": CB.open_seconds
        }
    }
