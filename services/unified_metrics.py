#!/usr/bin/env python3
"""
Unified Metrics Service - One scoreboard for AGI + RAG + TRM

Collects and aggregates metrics from:
- AGI Core (agent performance, workflows)
- RAG Gateway (retrieval quality, latency)
- TRM Service (reasoning cycles, accuracy)
- Router (routing decisions, cost optimization)

Provides unified dashboard and quality gates for CI/CD.
"""

import os
import json
import time
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict, field
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import Response
from prometheus_client import (
    Counter, Histogram, Gauge, Summary,
    generate_latest, CONTENT_TYPE_LATEST, CollectorRegistry
)
import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Unified Metrics Service",
    description="Aggregated metrics for AGI + RAG + TRM",
    version="1.0.0"
)

# Configuration
AGI_METRICS_URL = os.getenv("AGI_METRICS_URL", "http://localhost:8091/metrics")
RAG_METRICS_URL = os.getenv("RAG_METRICS_URL", "http://localhost:8088/metrics")
TRM_METRICS_URL = os.getenv("TRM_METRICS_URL", "http://localhost:8089/metrics")
ROUTER_METRICS_URL = os.getenv("ROUTER_METRICS_URL", "http://localhost:9113/metrics")
ADAPTER_METRICS_URL = os.getenv("ADAPTER_METRICS_URL", "http://localhost:3000/metrics")

# Custom registry for aggregated metrics
registry = CollectorRegistry()

# ============================================================================
# UNIFIED METRICS
# ============================================================================

# System-wide metrics
unified_requests_total = Counter(
    "unified_requests_total",
    "Total requests across all systems",
    ["system", "route"],
    registry=registry
)

unified_latency_seconds = Histogram(
    "unified_latency_seconds",
    "End-to-end latency across all systems",
    ["system", "route"],
    buckets=[0.05, 0.1, 0.2, 0.5, 1.0, 2.0, 5.0, 10.0],
    registry=registry
)

unified_errors_total = Counter(
    "unified_errors_total",
    "Total errors across all systems",
    ["system", "error_type"],
    registry=registry
)

# Quality metrics
unified_rag_hit_rate = Gauge(
    "unified_rag_hit_rate",
    "Current RAG hit@5 rate",
    registry=registry
)

unified_rag_support_rate = Gauge(
    "unified_rag_support_rate",
    "Current RAG support@3 rate",
    registry=registry
)

unified_agi_utility_score = Gauge(
    "unified_agi_utility_score",
    "Current AGI utility score",
    registry=registry
)

unified_trm_reasoning_quality = Gauge(
    "unified_trm_reasoning_quality",
    "TRM reasoning quality score",
    registry=registry
)

# Cost & efficiency
unified_cost_per_request = Summary(
    "unified_cost_per_request",
    "Cost per request (tokens + compute)",
    ["route"],
    registry=registry
)

unified_token_usage_total = Counter(
    "unified_token_usage_total",
    "Total tokens consumed",
    ["system"],
    registry=registry
)

# Route mix
unified_route_decisions = Counter(
    "unified_route_decisions_total",
    "Routing decisions made",
    ["route", "decision"],
    registry=registry
)


@dataclass
class UnifiedMetricsSnapshot:
    """
    Single snapshot of all system metrics.
    
    Useful for CI/CD gates and dashboards.
    """
    timestamp: float
    
    # AGI Core
    agi_requests: int = 0
    agi_utility_score: float = 0.0
    agi_success_rate: float = 0.0
    agi_avg_latency_ms: float = 0.0
    
    # RAG Gateway
    rag_requests: int = 0
    rag_hit_at_5: float = 0.0
    rag_support_at_3: float = 0.0
    rag_avg_latency_ms: float = 0.0
    rag_p95_latency_ms: float = 0.0
    
    # TRM Service
    trm_requests: int = 0
    trm_avg_cycles: float = 0.0
    trm_reasoning_quality: float = 0.0
    trm_avg_latency_ms: float = 0.0
    
    # Router
    router_requests: int = 0
    router_rag_pct: float = 0.0
    router_llm_pct: float = 0.0
    router_hybrid_pct: float = 0.0
    router_trm_pct: float = 0.0
    
    # Adapter
    adapter_requests: int = 0
    adapter_stream_rate: float = 0.0
    adapter_errors: int = 0
    
    # System-wide
    total_requests: int = 0
    total_errors: int = 0
    avg_cost_per_request: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def meets_quality_gates(self, gates: Dict[str, float]) -> Tuple[bool, List[str]]:
        """
        Check if snapshot meets quality gates.
        
        Args:
            gates: Dict of metric_name -> minimum_value
        
        Returns:
            (passes, failures) tuple
        """
        failures = []
        
        for metric, min_value in gates.items():
            actual_value = getattr(self, metric, None)
            if actual_value is None:
                failures.append(f"{metric}: not available")
            elif actual_value < min_value:
                failures.append(f"{metric}: {actual_value:.3f} < {min_value:.3f}")
        
        return len(failures) == 0, failures


class MetricsAggregator:
    """
    Aggregates metrics from all services.
    
    Polls each service's /metrics endpoint and combines into unified view.
    """
    
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=5.0)
    
    async def collect_snapshot(self) -> UnifiedMetricsSnapshot:
        """
        Collect current metrics snapshot from all services.
        
        Returns:
            UnifiedMetricsSnapshot with current state
        """
        snapshot = UnifiedMetricsSnapshot(timestamp=time.time())
        
        try:
            # Collect AGI Core metrics
            agi_data = await self._fetch_metrics(AGI_METRICS_URL)
            snapshot.agi_requests = self._extract_counter(agi_data, "agi_requests_total")
            snapshot.agi_utility_score = self._extract_gauge(agi_data, "agi_utility_score")
            snapshot.agi_success_rate = self._extract_gauge(agi_data, "agi_success_rate")
            snapshot.agi_avg_latency_ms = self._extract_histogram_mean(agi_data, "agi_latency_ms")
            
            # Collect RAG metrics
            rag_data = await self._fetch_metrics(RAG_METRICS_URL)
            snapshot.rag_requests = self._extract_counter(rag_data, "rag_queries_total")
            snapshot.rag_avg_latency_ms = self._extract_histogram_mean(rag_data, "rag_query_latency_ms")
            
            # Collect TRM metrics
            trm_data = await self._fetch_metrics(TRM_METRICS_URL)
            snapshot.trm_requests = self._extract_counter(trm_data, "trm_requests_total")
            snapshot.trm_avg_cycles = self._extract_gauge(trm_data, "trm_avg_cycles")
            
            # Collect Router metrics
            router_data = await self._fetch_metrics(ROUTER_METRICS_URL)
            snapshot.router_requests = self._extract_counter(router_data, "athena_router_requests_total")
            
            # Collect Adapter metrics
            adapter_data = await self._fetch_metrics(ADAPTER_METRICS_URL)
            snapshot.adapter_requests = self._extract_counter(adapter_data, "openai_compat_requests_total")
            snapshot.adapter_errors = self._extract_counter(adapter_data, "openai_compat_errors_total")
            
            # Calculate totals
            snapshot.total_requests = (
                snapshot.agi_requests +
                snapshot.rag_requests +
                snapshot.trm_requests +
                snapshot.router_requests +
                snapshot.adapter_requests
            )
            
            logger.info(f"Collected metrics snapshot: {snapshot.total_requests} total requests")
            
        except Exception as e:
            logger.error(f"Failed to collect metrics snapshot: {e}")
        
        return snapshot
    
    async def _fetch_metrics(self, url: str) -> Dict[str, Any]:
        """Fetch Prometheus metrics from endpoint"""
        try:
            response = await self.client.get(url)
            if response.status_code == 200:
                # Parse Prometheus text format (simplified)
                # In production, use prometheus_client.parser
                return self._parse_prometheus_text(response.text)
            return {}
        except Exception as e:
            logger.warning(f"Failed to fetch metrics from {url}: {e}")
            return {}
    
    def _parse_prometheus_text(self, text: str) -> Dict[str, Any]:
        """Simple Prometheus text format parser"""
        metrics = {}
        for line in text.split("\n"):
            if line.startswith("#") or not line.strip():
                continue
            
            # Parse metric line: metric_name{labels} value timestamp
            parts = line.split()
            if len(parts) >= 2:
                metric_name_labels = parts[0]
                value = float(parts[1])
                
                # Extract metric name (before {)
                if "{" in metric_name_labels:
                    metric_name = metric_name_labels.split("{")[0]
                else:
                    metric_name = metric_name_labels
                
                metrics[metric_name] = value
        
        return metrics
    
    def _extract_counter(self, data: Dict, name: str) -> int:
        """Extract counter value"""
        return int(data.get(name, 0))
    
    def _extract_gauge(self, data: Dict, name: str) -> float:
        """Extract gauge value"""
        return float(data.get(name, 0.0))
    
    def _extract_histogram_mean(self, data: Dict, name: str) -> float:
        """Extract histogram mean (sum/count)"""
        sum_val = data.get(f"{name}_sum", 0.0)
        count_val = data.get(f"{name}_count", 1.0)
        return sum_val / count_val if count_val > 0 else 0.0
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Global aggregator
aggregator = MetricsAggregator()


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
async def root():
    return {
        "service": "unified-metrics",
        "version": "1.0.0",
        "endpoints": ["/snapshot", "/metrics", "/health"]
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/snapshot")
async def get_snapshot():
    """Get current unified metrics snapshot"""
    snapshot = await aggregator.collect_snapshot()
    return snapshot.to_dict()

@app.get("/metrics")
def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(registry), media_type=CONTENT_TYPE_LATEST)

@app.post("/gates")
async def check_gates(gates: Dict[str, float]):
    """
    Check if current metrics meet quality gates.
    
    Example:
        POST /gates
        {
            "rag_hit_at_5": 0.97,
            "rag_support_at_3": 0.95,
            "agi_utility_score": 0.80,
            "agi_success_rate": 0.90
        }
    
    Returns:
        {
            "passed": true/false,
            "failures": ["metric: value < threshold", ...]
        }
    """
    snapshot = await aggregator.collect_snapshot()
    passed, failures = snapshot.meets_quality_gates(gates)
    
    return {
        "passed": passed,
        "failures": failures,
        "snapshot": snapshot.to_dict()
    }


# ============================================================================
# STARTUP / SHUTDOWN
# ============================================================================

@app.on_event("startup")
async def startup():
    logger.info("Unified Metrics Service starting...")
    logger.info(f"AGI Metrics: {AGI_METRICS_URL}")
    logger.info(f"RAG Metrics: {RAG_METRICS_URL}")
    logger.info(f"TRM Metrics: {TRM_METRICS_URL}")
    logger.info(f"Router Metrics: {ROUTER_METRICS_URL}")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down Unified Metrics Service...")
    await aggregator.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8092"))
    logger.info(f"Starting Unified Metrics Service on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

