#!/usr/bin/env python3
"""
Canary Evaluation - Statistical confidence check

Uses Wilson score interval to determine if canary is statistically
better than control before promotion.

Usage:
    python3 scripts/canary_eval.py
    
Returns:
    0 - Canary is stable/monitoring (no action)
    1 - Canary should be promoted (stat-sig better)
    2 - Canary should be rolled back (stat-sig worse)
"""

import os
import sys
import json
import urllib.parse
import urllib.request
import math

PROM = os.getenv("PROM_URL", "http://localhost:9090")
ENV = os.getenv("ENV", "local")
CONTROL = os.getenv("CONTROL_MODEL", "mlx/chat")
CANARY = os.getenv("CANARY_MODEL", "mlx/chat@canary")
CONFIDENCE = float(os.getenv("CONFIDENCE_LEVEL", "0.95"))  # 95% confidence

def prom_query(query):
    """Query Prometheus"""
    url = f"{PROM}/api/v1/query?query=" + urllib.parse.quote(query)
    try:
        with urllib.request.urlopen(url, timeout=5) as r:
            data = json.loads(r.read())
            return data.get("data", {}).get("result", [])
    except Exception as e:
        print(f"⚠️  Query failed: {e}", file=sys.stderr)
        return []

def wilson_score_interval(successes, trials, confidence=0.95):
    """
    Calculate Wilson score confidence interval
    
    Returns: (lower_bound, upper_bound, center)
    """
    if trials == 0:
        return (0, 0, 0)
    
    p = successes / trials
    
    # Z-score for confidence level
    z_scores = {0.90: 1.645, 0.95: 1.96, 0.99: 2.576}
    z = z_scores.get(confidence, 1.96)
    
    denominator = 1 + z**2 / trials
    center = (p + z**2 / (2 * trials)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z**2 / (4 * trials)) / trials) / denominator
    
    return (center - margin, center + margin, center)

def main():
    """Evaluate canary vs control"""
    print("📊 Canary Evaluation (Statistical)")
    print("=" * 50)
    
    # Get success counts for last 24h
    control_successes_q = f'sum(increase(routing_success_total{{model="{CONTROL}",env="{ENV}"}}[24h]))'
    control_total_q = f'sum(increase(routing_decisions_total{{model="{CONTROL}",env="{ENV}"}}[24h]))'
    canary_successes_q = f'sum(increase(routing_success_total{{model="{CANARY}",env="{ENV}"}}[24h]))'
    canary_total_q = f'sum(increase(routing_decisions_total{{model="{CANARY}",env="{ENV}"}}[24h]))'
    
    control_succ = prom_query(control_successes_q)
    control_tot = prom_query(control_total_q)
    canary_succ = prom_query(canary_successes_q)
    canary_tot = prom_query(canary_total_q)
    
    # Extract values
    ctrl_s = int(float(control_succ[0]["value"][1])) if control_succ else 0
    ctrl_n = int(float(control_tot[0]["value"][1])) if control_tot else 0
    cana_s = int(float(canary_succ[0]["value"][1])) if canary_succ else 0
    cana_n = int(float(canary_tot[0]["value"][1])) if canary_tot else 0
    
    print(f"Control ({CONTROL}): {ctrl_s}/{ctrl_n} successes")
    print(f"Canary ({CANARY}): {cana_s}/{cana_n} successes")
    
    if ctrl_n == 0 or cana_n == 0:
        print("ℹ️  Insufficient data for evaluation")
        print("Status: MONITORING")
        return 0
    
    # Calculate Wilson intervals
    ctrl_lower, ctrl_upper, ctrl_center = wilson_score_interval(ctrl_s, ctrl_n, CONFIDENCE)
    cana_lower, cana_upper, cana_center = wilson_score_interval(cana_s, cana_n, CONFIDENCE)
    
    print(f"\nControl: {ctrl_center*100:.2f}% ({ctrl_lower*100:.2f}% - {ctrl_upper*100:.2f}%)")
    print(f"Canary:  {cana_center*100:.2f}% ({cana_lower*100:.2f}% - {cana_upper*100:.2f}%)")
    
    # Decision logic
    if cana_lower > ctrl_upper:
        # Canary is stat-sig better
        improvement = (cana_center - ctrl_center) * 100
        print(f"\n✅ PROMOTE: Canary is {improvement:.1f}% better (stat-sig at {CONFIDENCE*100:.0f}%)")
        return 1
    elif cana_upper < ctrl_lower:
        # Canary is stat-sig worse
        degradation = (ctrl_center - cana_center) * 100
        print(f"\n🔴 ROLLBACK: Canary is {degradation:.1f}% worse (stat-sig at {CONFIDENCE*100:.0f}%)")
        return 2
    else:
        # Overlapping intervals - not stat-sig different
        print(f"\n📊 MONITORING: No stat-sig difference (confidence intervals overlap)")
        return 0

if __name__ == "__main__":
    sys.exit(main())

