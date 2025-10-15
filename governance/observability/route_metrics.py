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

