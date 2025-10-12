"""
Feature Builder for Routing Decisions
=====================================
Extracts routing-relevant features from records
"""

from datetime import datetime, timezone
from typing import Dict, Any


def mins_since(iso_ts: str) -> int:
    """
    Calculate minutes since ISO timestamp

    Args:
        iso_ts: ISO format timestamp string

    Returns:
        Minutes since timestamp
    """
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        now = datetime.now(tz=dt.tzinfo or timezone.utc)
        return int((now - dt).total_seconds() // 60)
    except Exception:
        return 0


def build_features(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build routing features from record

    Args:
        record: Input record dictionary

    Returns:
        Feature dictionary for routing decisions
    """
    return {
        "channel": record.get("channel", "email"),
        "vendor_tier": record.get("vendor_tier", "C"),
        "age_mins": mins_since(record.get("created_at", "")),
        "sla_mins_left": record.get("sla_mins_left", 0),
        "attachments": len(record.get("files", [])),
        "priority": record.get("priority", "normal"),
        "complexity": record.get("complexity_estimate", 0.5),
    }


def extract_urgency(features: Dict[str, Any]) -> str:
    """
    Determine urgency level from features

    Returns:
        "critical", "high", "normal", or "low"
    """
    sla = features.get("sla_mins_left", 999)

    if sla < 15:
        return "critical"
    elif sla < 60:
        return "high"
    elif sla < 240:
        return "normal"
    else:
        return "low"


def should_use_fast_path(features: Dict[str, Any]) -> bool:
    """Determine if fast path should be used"""
    urgency = extract_urgency(features)
    return urgency in ("critical", "high")
