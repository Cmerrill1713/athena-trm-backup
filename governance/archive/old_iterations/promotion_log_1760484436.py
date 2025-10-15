#!/usr/bin/env python3
"""
Promotion Log - Structured logging for model promotions and rollbacks

Emits JSON lines to logs/promotions.log for lineage tracking.
"""

import json
import os
import time
from pathlib import Path
from typing import Optional

LOG_PATH = Path("logs/promotions.log")
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    """Current timestamp in ISO format"""
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_promotion(
    from_model: str,
    to_model: str,
    reason: str,
    improvement: Optional[float] = None,
    p_value: Optional[float] = None,
    canary_window_hours: Optional[float] = None,
    canary_success: Optional[float] = None,
    control_success: Optional[float] = None,
    sample_canary: Optional[int] = None,
    sample_control: Optional[int] = None,
    task: Optional[str] = None,
    trm_version: Optional[str] = None,
    notes: Optional[str] = None
):
    """
    Log a promotion event
    
    Args:
        from_model: Model being replaced
        to_model: New model being promoted
        reason: Reason for promotion (e.g., "canary_win_stat_sig", "nightly_trm")
        improvement: Success rate improvement (0.061 = 6.1%)
        p_value: Statistical p-value (if applicable)
        canary_window_hours: How long canary was monitored
        canary_success: Canary success rate (0.0-1.0)
        control_success: Control success rate (0.0-1.0)
        sample_canary: Canary sample size
        sample_control: Control sample size
        task: Task type (vision, ocr, chart, etc.)
        trm_version: TRM model version (if promoted via learning)
        notes: Additional notes
    """
    rec = {
        "ts": _ts(),
        "event": "PROMOTION",
        "from": from_model,
        "to": to_model,
        "reason": reason,
        "improvement": improvement,
        "p_value": p_value,
        "window_hours": canary_window_hours,
        "canary_success": canary_success,
        "control_success": control_success,
        "sample_canary": sample_canary,
        "sample_control": sample_control,
        "task": task,
        "trm_version": trm_version,
        "notes": notes,
    }
    
    # Filter out None values
    rec_filtered = {k: v for k, v in rec.items() if v is not None}
    
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(rec_filtered) + "\n")
    
    print(f"📝 Logged promotion: {from_model} → {to_model}")


def write_rollback(
    from_model: str,
    to_model: str,
    reason: str,
    notes: Optional[str] = None
):
    """
    Log a rollback event
    
    Args:
        from_model: Model being rolled back (canary)
        to_model: Model being restored (control)
        reason: Reason for rollback
        notes: Additional notes
    """
    rec = {
        "ts": _ts(),
        "event": "ROLLBACK",
        "from": from_model,
        "to": to_model,
        "reason": reason,
        "notes": notes
    }
    
    rec_filtered = {k: v for k, v in rec.items() if v is not None}
    
    with LOG_PATH.open("a") as f:
        f.write(json.dumps(rec_filtered) + "\n")
    
    print(f"📝 Logged rollback: {from_model} → {to_model}")


# Expose Prometheus counter for promotions
try:
    from prometheus_client import Counter
    
    PROMOTIONS_TOTAL = Counter(
        'model_promotions_total',
        'Total model promotions',
        ['from_model', 'to_model', 'reason', 'env', 'build']
    )
    
    ROLLBACKS_TOTAL = Counter(
        'model_rollbacks_total',
        'Total model rollbacks',
        ['from_model', 'to_model', 'reason', 'env', 'build']
    )
    
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False


def record_promotion_metric(
    from_model: str,
    to_model: str,
    reason: str
):
    """Record promotion to Prometheus"""
    if METRICS_AVAILABLE:
        env = os.environ.get("ENV", "local")
        build = os.environ.get("BUILD_SHA", "dev")
        
        PROMOTIONS_TOTAL.labels(
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            env=env,
            build=build
        ).inc()


def record_rollback_metric(
    from_model: str,
    to_model: str,
    reason: str
):
    """Record rollback to Prometheus"""
    if METRICS_AVAILABLE:
        env = os.environ.get("ENV", "local")
        build = os.environ.get("BUILD_SHA", "dev")
        
        ROLLBACKS_TOTAL.labels(
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            env=env,
            build=build
        ).inc()

