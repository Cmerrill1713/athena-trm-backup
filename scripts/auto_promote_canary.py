#!/usr/bin/env python3
"""
Auto-Promote Canary - Statistically-driven promotion

Promotes canary to control if:
1. Canary statistically significantly BETTER than control
2. Condition sustained for MIN_DURATION (default: 48 hours)
3. Sample sizes sufficient (≥50 each)
4. No circuit breaker issues

Prevents premature promotions due to lucky streaks.

Usage:
    PROM_URL=http://localhost:9090 \
    CONTROL_MODEL=fastvlm-1.5b \
    CANARY_MODEL=fastvlm-0.5b \
    MIN_IMPROVEMENT=0.03 \
    MIN_DURATION_HOURS=48 \
    python3 scripts/auto_promote_canary.py
"""

import os
import sys
import requests
from pathlib import Path
from datetime import datetime

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.routing.canary_statistics import is_significantly_different


# Configuration
PROM_URL = os.environ.get("PROM_URL", "http://localhost:9090")
CONTROL_MODEL = os.environ.get("CONTROL_MODEL", "fastvlm-1.5b")
CANARY_MODEL = os.environ.get("CANARY_MODEL", "fastvlm-0.5b")
MIN_IMPROVEMENT = float(os.environ.get("MIN_IMPROVEMENT", "0.03"))  # 3%
MIN_DURATION_HOURS = int(os.environ.get("MIN_DURATION_HOURS", "48"))
MIN_SAMPLES = int(os.environ.get("MIN_SAMPLES", "50"))
CONFIDENCE = float(os.environ.get("CONFIDENCE", "0.95"))

# State file to track sustained improvement
STATE_FILE = "/tmp/fastvlm_canary_promotion_state.json"


def query_prometheus(query: str) -> dict:
    """Query Prometheus"""
    response = requests.get(
        f"{PROM_URL}/api/v1/query",
        params={"query": query},
        timeout=10
    )
    response.raise_for_status()
    return response.json()


def get_bucket_stats(bucket: str, time_window: str = "48h") -> tuple[int, int]:
    """
    Get successes and trials for a bucket over time window
    
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


def check_circuit_breakers() -> tuple[bool, str]:
    """
    Check if any circuit breakers are open
    
    Returns:
        (all_healthy, message)
    """
    try:
        query = 'circuit_breaker_open'
        data = query_prometheus(query)
        
        if not data["data"]["result"]:
            return (True, "No circuit breakers")
        
        open_breakers = [
            r["metric"]["model"]
            for r in data["data"]["result"]
            if r["value"][1] == "1"
        ]
        
        if open_breakers:
            return (False, f"Circuit breakers OPEN: {', '.join(open_breakers)}")
        else:
            return (True, "All circuits closed")
    
    except Exception as e:
        return (False, f"Failed to check circuits: {e}")


def load_state() -> dict:
    """Load promotion state from file"""
    import json
    
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_state(state: dict):
    """Save promotion state to file"""
    import json
    
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def main():
    """Main entry point"""
    print("╔════════════════════════════════════════════════════════════════╗")
    print("║          Auto-Promote Canary (Statistical)                     ║")
    print("╚════════════════════════════════════════════════════════════════╝\n")
    
    print(f"Control model:   {CONTROL_MODEL}")
    print(f"Canary model:    {CANARY_MODEL}")
    print(f"Min improvement: {MIN_IMPROVEMENT:.0%}")
    print(f"Min duration:    {MIN_DURATION_HOURS} hours")
    print(f"Min samples:     {MIN_SAMPLES} each")
    print(f"Confidence:      {CONFIDENCE:.0%}\n")
    
    # Check circuit breakers first
    print("🔒 Checking circuit breakers...")
    circuits_healthy, circuit_msg = check_circuit_breakers()
    print(f"   {circuit_msg}")
    
    if not circuits_healthy:
        print("\n❌ Cannot promote with open circuit breakers")
        print("   Wait for circuits to close\n")
        sys.exit(1)
    
    # Fetch metrics from Prometheus
    print(f"\n📊 Fetching {MIN_DURATION_HOURS}h metrics from Prometheus...")
    
    try:
        window = f"{MIN_DURATION_HOURS}h"
        canary_successes, canary_trials = get_bucket_stats("canary", window)
        control_successes, control_trials = get_bucket_stats("control", window)
        
        canary_rate = canary_successes / max(1, canary_trials)
        control_rate = control_successes / max(1, control_trials)
        
        print(f"   Control: {control_successes}/{control_trials} = {control_rate:.1%}")
        print(f"   Canary:  {canary_successes}/{canary_trials} = {canary_rate:.1%}\n")
        
    except Exception as e:
        print(f"❌ Failed to fetch metrics: {e}\n")
        sys.exit(1)
    
    # Check sample sizes
    if canary_trials < MIN_SAMPLES or control_trials < MIN_SAMPLES:
        print("⏳ Insufficient sample size")
        print(f"   Need {MIN_SAMPLES}+ trials each, have: canary={canary_trials}, control={control_trials}")
        print("   Continue monitoring\n")
        sys.exit(0)
    
    # Statistical evaluation (reversed: check if canary is better)
    print("🔍 Statistical evaluation...")
    
    # Flip the comparison: we want canary > control
    is_control_worse, delta, explanation = is_significantly_different(
        control_successes, control_trials,
        canary_successes, canary_trials,
        min_delta=MIN_IMPROVEMENT,
        confidence=CONFIDENCE
    )
    
    # is_control_worse means canary is significantly BETTER
    canary_is_better = is_control_worse
    delta = -delta  # Flip sign (we compare canary - control)
    
    print(f"   {explanation}")
    print(f"   Delta: {delta:+.1%}\n")
    
    # Load state
    state = load_state()
    
    if canary_is_better:
        # Canary is statistically significantly better!
        print(f"✅ Canary is statistically better: {canary_rate:.1%} vs {control_rate:.1%}")
        print(f"   Delta: {delta:+.1%} (threshold: >{MIN_IMPROVEMENT:.1%})")
        print(f"   Confidence: {CONFIDENCE:.0%}\n")
        
        # Check if this is sustained
        if "canary_better_since" not in state:
            # First time seeing canary better
            state["canary_better_since"] = datetime.now().isoformat()
            state["canary_model"] = CANARY_MODEL
            state["control_model"] = CONTROL_MODEL
            save_state(state)
            
            print("📅 Started tracking improvement")
            print(f"   Will promote after {MIN_DURATION_HOURS} hours of sustained improvement\n")
            sys.exit(0)
        
        # Check duration
        better_since = datetime.fromisoformat(state["canary_better_since"])
        duration = datetime.now() - better_since
        duration_hours = duration.total_seconds() / 3600
        
        print(f"📅 Canary has been better for {duration_hours:.1f} hours")
        print(f"   Target: {MIN_DURATION_HOURS} hours\n")
        
        if duration_hours >= MIN_DURATION_HOURS:
            # PROMOTE!
            print("🎉 PROMOTION CRITERIA MET!")
            print(f"   Canary: {canary_rate:.1%}")
            print(f"   Control: {control_rate:.1%}")
            print(f"   Improvement: {delta:+.1%}")
            print(f"   Duration: {duration_hours:.1f} hours")
            print(f"   Confidence: {CONFIDENCE:.0%}\n")
            
            print("🚀 AUTO-PROMOTING CANARY")
            print(f"   {CANARY_MODEL} → new control")
            print(f"   {CONTROL_MODEL} → deprecated\n")
            
            print("   Run:")
            print(f"   1. Update routing config: CONTROL_MODEL={CANARY_MODEL}")
            print("   2. make canary-off && source /tmp/canary.env")
            print("   3. Verify: make learn-verify\n")
            
            # Log structured promotion event
            try:
                sys.path.insert(0, str(Path(__file__).parent.parent))
                from scripts.lib.promotion_log import write_promotion, record_promotion_metric
                
                write_promotion(
                    from_model=CONTROL_MODEL,
                    to_model=CANARY_MODEL,
                    reason="canary_win_stat_sig",
                    improvement=delta,
                    p_value=0.05,  # By definition (Wilson intervals)
                    canary_window_hours=duration_hours,
                    canary_success=canary_rate,
                    control_success=control_rate,
                    sample_canary=canary_trials,
                    sample_control=control_trials,
                    task="vision",
                    trm_version=os.environ.get("TRM_VERSION"),
                    notes=f"Promoted after {duration_hours:.1f}h sustained win"
                )
                
                # Prometheus counter
                record_promotion_metric(CONTROL_MODEL, CANARY_MODEL, "canary_win_stat_sig")
            except Exception as e:
                print(f"⚠️  Failed to log promotion (non-fatal): {e}")
            
            # Clear state
            state["promoted_at"] = datetime.now().isoformat()
            state["promoted_from"] = CONTROL_MODEL
            state["promoted_to"] = CANARY_MODEL
            state["improvement"] = delta
            del state["canary_better_since"]
            save_state(state)
            
            # Exit with special code to trigger automation
            sys.exit(42)  # 42 = promote
        else:
            remaining = MIN_DURATION_HOURS - duration_hours
            print(f"⏳ {remaining:.1f} hours remaining before auto-promotion")
            print("   Continue monitoring\n")
            sys.exit(0)
    
    else:
        # Canary is not better (or not significantly)
        if "canary_better_since" in state:
            # Was better before, reset
            print("⚠️  Canary no longer significantly better")
            print("   Resetting promotion timer\n")
            del state["canary_better_since"]
            save_state(state)
        else:
            print("ℹ️  Canary not significantly better than control")
            print("   Continue monitoring\n")
        
        sys.exit(0)


if __name__ == "__main__":
    main()

