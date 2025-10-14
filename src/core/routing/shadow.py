"""
Shadow Mode - Safe read-only candidate evaluation

Mirrors a % of traffic to candidate models without impacting users.
Measures disagreement and performance differences.
"""

import threading
import os
import sys
from pathlib import Path

# Import metrics
try:
    github_root = Path(__file__).parent.parent.parent.parent
    sys.path.insert(0, str(github_root))
    from src.metrics.shadow_metrics import SHADOW_SENT_TOTAL, SHADOW_DISAGREE_TOTAL
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

CANDIDATE = os.getenv("SHADOW_CANDIDATE")  # e.g. "mlx/chat@canary" or "fastvlm@canary"
ENABLE = os.getenv("SHADOW_ENABLE", "0") == "1"
ENV = os.getenv("ENV", "local")
BUILD = os.getenv("BUILD_SHA", "dev")

def send_shadow(primary_output: str, prompt: str, meta: dict, call_model_fn):
    """
    Send shadow request to candidate model (async, non-blocking)
    
    Args:
        primary_output: Output from primary model
        prompt: Original user prompt
        meta: Request metadata
        call_model_fn: Function to call model (signature: fn(model, prompt, meta, timeout))
    """
    if not ENABLE or not CANDIDATE:
        return
    
    def _run():
        try:
            if METRICS_AVAILABLE:
                SHADOW_SENT_TOTAL.labels(CANDIDATE, ENV, BUILD).inc()
            
            # Call candidate model with timeout
            cand_output = call_model_fn(CANDIDATE, prompt, meta, timeout=3.0)
            
            # Naive disagreement heuristic (can be improved)
            if cand_output is None:
                disagree = True
            else:
                len_diff = abs(len(cand_output) - len(primary_output))
                threshold = max(80, 0.3 * len(primary_output))
                disagree = len_diff > threshold
            
            if disagree and METRICS_AVAILABLE:
                SHADOW_DISAGREE_TOTAL.labels(CANDIDATE, ENV, BUILD).inc()
                print(f"📊 Shadow disagreement: {CANDIDATE} vs primary")
            
        except Exception as e:
            # Shadow failures don't impact primary
            if METRICS_AVAILABLE:
                SHADOW_DISAGREE_TOTAL.labels(CANDIDATE, ENV, BUILD).inc()
            print(f"⚠️  Shadow call failed: {e}")
    
    # Run in background thread (non-blocking)
    threading.Thread(target=_run, daemon=True).start()

