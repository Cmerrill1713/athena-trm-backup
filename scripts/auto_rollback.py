#!/usr/bin/env python3
"""
Auto-Rollback Guard - Statistical canary evaluation

Checks if canary is statistically significantly worse than control.
Only triggers rollback if BOTH magnitude AND significance thresholds met.

Prevents false rollbacks due to random variance.

Usage:
    PROM_URL=http://localhost:9090 \
    CONTROL_MODEL=fastvlm-1.5b \
    CANARY_MODEL=fastvlm-0.5b \
    python3 scripts/auto_rollback.py
"""

import os
import sys
import requests
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.routing.canary_statistics import should_rollback_canary


# Configuration
PROM_URL = os.environ.get("PROM_URL", "http://localhost:9090")
CONTROL_MODEL = os.environ.get("CONTROL_MODEL", "fastvlm-1.5b")
CANARY_MODEL = os.environ.get("CANARY_MODEL", "fastvlm-0.5b")
MIN_DELTA = float(os.environ.get("MIN_DELTA", "0.05"))  # 5%
CONFIDENCE = float(os.environ.get("CONFIDENCE", "0.95"))  # 95%


def query_prometheus(query: str) -> dict:
    """Query Prometheus"""
    response = requests.get(
        f"{PROM_URL}/api/v1/query",
        params={"query": query},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def get_bucket_stats(bucket: str, time_window: str = "15m") -> tuple[int, int]:
    """
    Get successes and trials for a bucket
    
    Returns:
        (successes, trials)
    """
    # Success count
    success_query = f'sum(increase(routing_success_total{{bucket="{bucket}"}}[{time_window}]))'
    success_data = query_prometheus(success_query)
    successes = 0
    if success_data["data"]["result"]:
        successes = int(float(success_data["data"]["result"][0]["value"][1]))
    
    # Total count
    total_query = f'sum(increase(routing_decisions_total{{bucket="{bucket}"}}[{time_window}]))'
    total_data = query_prometheus(total_query)
    trials = 0
    if total_data["data"]["result"]:
        trials = int(float(total_data["data"]["result"][0]["value"][1]))
    
    return (successes, trials)


def record_rollback_metric(from_model: str, to_model: str, reason: str):
    """Record rollback to Prometheus metrics"""
    try:
        import sys
        sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
        from src.metrics.route_metrics import record_promotion
        
        record_promotion(
            action="rollback",
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            task="routing"
        )
        print("📊 Rollback metric recorded to Prometheus")
    except Exception as e:
        print(f"⚠️  Metric recording failed (non-fatal): {e}")

def main():
    """Main entry point"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Auto-Rollback Guard (Statistical Eval)                ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    print(f"Control model:  {CONTROL_MODEL}")
    print(f"Canary model:   {CANARY_MODEL}")
    print(f"Min delta:      {MIN_DELTA:.0%}")
    print(f"Confidence:     {CONFIDENCE:.0%}")
    print(f"Prometheus:     {PROM_URL}\n")
    
    # Fetch metrics from Prometheus
    print("📊 Fetching metrics from Prometheus...")
    
    try:
        canary_successes, canary_trials = get_bucket_stats("canary", "15m")
        control_successes, control_trials = get_bucket_stats("control", "15m")
        
        print(f"   Control: {control_successes}/{control_trials} = {control_successes/max(1,control_trials):.1%}")
        print(f"   Canary:  {canary_successes}/{canary_trials} = {canary_successes/max(1,canary_trials):.1%}\n")
        
    except Exception as e:
        print(f"❌ Failed to fetch metrics: {e}")
        sys.exit(1)
    
    # Evaluate
    print("🔍 Statistical evaluation...")
    should_rollback, reason = should_rollback_canary(
        canary_successes=canary_successes,
        canary_trials=canary_trials,
        control_successes=control_successes,
        control_trials=control_trials,
        min_delta=MIN_DELTA,
        confidence=CONFIDENCE
    )
    
    print(reason)
    print()
    
    # Decision
    if should_rollback:
        # Log structured rollback event
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent))
            from scripts.lib.promotion_log import write_rollback, record_rollback_metric
            
            canary_model = os.environ.get("CANARY_MODEL", "unknown")
            control_model = os.environ.get("CONTROL_MODEL", "unknown")
            
            write_rollback(
                from_model=canary_model,
                to_model=control_model,
                reason="canary_regression_stat_sig",
                notes=f"Canary {canary_successes}/{canary_trials} vs Control {control_successes}/{control_trials}"
            )
            
            # Prometheus counter
            record_rollback_metric(canary_model, control_model, "canary_regression_stat_sig")
        except Exception as e:
            print(f"⚠️  Failed to log rollback (non-fatal): {e}")
        
        print("🚨 AUTO-ROLLBACK TRIGGERED")
        print("   Run: make canary-rollback && source /tmp/canary.env")
        sys.exit(1)  # Exit with error to trigger automation
    else:
        print("✅ Canary is performing acceptably")
        print("   Continue monitoring")
        sys.exit(0)


if __name__ == "__main__":
    main()
