"""
Shadow Traffic Metrics

Tracks shadow requests (read-only candidate evaluation)
and disagreement rates between primary and shadow models.
"""

from prometheus_client import Counter

SHADOW_SENT_TOTAL = Counter(
    "shadow_sent_total",
    "Shadow requests sent",
    ["candidate", "env", "build"]
)

SHADOW_DISAGREE_TOTAL = Counter(
    "shadow_disagreement_total",
    "Shadow vs primary disagreed",
    ["candidate", "env", "build"]
)

SHADOW_LATENCY_DIFF = Counter(
    "shadow_latency_diff_ms",
    "Latency difference (shadow - primary) in ms",
    ["candidate", "env", "build"]
)

