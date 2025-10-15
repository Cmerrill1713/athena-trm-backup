from prometheus_client import Counter, Histogram

# Labels: model, env (local|staging|prod), build (git sha or tag)
ROUTING_DECISIONS = Counter(
    "routing_decisions_total", 
    "Total routing decisions", 
    ["model", "env", "build"]
)

ROUTING_SUCCESS = Counter(
    "routing_success_total", 
    "Successful routing decisions",
    ["env", "build"]
)

ROUTING_LATENCY = Histogram(
    "routing_latency_ms", 
    "Routing latency (ms)",
    ["env", "build"],
    buckets=[50, 100, 200, 400, 800, 1200, 1600, 2000, 3000]
)

TRM_PROMOTIONS = Counter(
    "trm_promotions_total", 
    "TRM promotions",
    ["env", "build"]
)

TRM_ACC_DELTA = Counter(
    "trm_accuracy_delta", 
    "Accuracy delta vs baseline", 
    ["delta_type", "env", "build"]
)

# Promotions and rollbacks (detailed tracking)
PROMOTIONS_TOTAL = Counter(
    "promotions_total",
    "Count of model promotions and rollbacks",
    ["action", "from_model", "to_model", "reason", "task", "env", "build"]
)

def record_promotion(action: str, from_model: str, to_model: str, reason: str, task: str = None):
    """
    Record a promotion or rollback event
    
    Args:
        action: "promotion" or "rollback"
        from_model: Model being replaced
        to_model: Model being promoted to
        reason: Why (e.g., "canary_win_stat_sig_48h", "regression")
        task: Optional task type (e.g., "vision", "chat")
    """
    import os
    env = os.getenv("ENV", "local")
    build = os.getenv("BUILD_SHA", "dev")
    
    PROMOTIONS_TOTAL.labels(
        action=action,
        from_model=from_model or "unknown",
        to_model=to_model or "unknown",
        reason=reason or "unspecified",
        task=task or "unknown",
        env=env,
        build=build
    ).inc()

