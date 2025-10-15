#!/usr/bin/env python3
"""
Quick script to add inline /metrics endpoint to running API
Injects prometheus metrics without external file dependencies
"""

code_to_inject = '''
# Quick inline metrics endpoint (added by monitoring setup)
from prometheus_client import Counter, Histogram, make_asgi_app

ROUTING_DECISIONS = Counter("routing_decisions_total", "Total routing decisions", ["model"])
ROUTING_SUCCESS = Counter("routing_success_total", "Successful routing decisions")
ROUTING_LATENCY = Histogram("routing_latency_ms", "Routing latency (ms)",
                            buckets=[50,100,200,400,800,1200,1600,2000,3000])

metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
print("✅ Inline Prometheus /metrics endpoint mounted")
'''

print("This approach requires rebuilding the image.")
print("For production: rebuild the image with the new code")
print("For now: let's verify the code changes work locally")

