"""
Judicial Client for AGI Remediator
Submits remediation decisions to ASI safety oversight
"""

import requests
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

JUDICIAL_URL = "http://ai-republic-judicial:8096"

def submit_judicial_event_sync(
    event_id: str,
    actor_id: str,
    article: str,
    severity: float,
    confidence: float,
    classification: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Submit remediation decision to judicial oversight (sync version)."""
    try:
        payload = {
            "event_id": event_id,
            "instance_id": "athena-agi-remediator",
            "actor_id": actor_id,
            "article": article,
            "severity": severity,
            "confidence": confidence,
            "classification": classification,
            "details": details or {},
            "timestamp": time.time()
        }
        
        response = requests.post(
            f"{JUDICIAL_URL}/v2/judicial/adjudicate",
            json=payload,
            timeout=5.0
        )
        response.raise_for_status()
        verdict = response.json()
        
        logger.info(f"Judicial verdict for {event_id}: {verdict['verdict']}")
        
        if verdict['verdict'] in ['QUARANTINE', 'TRIBUNAL']:
            logger.warning(f"⚠️ AGI Remediator received {verdict['verdict']}")
            if verdict['review_required']:
                logger.critical(f"🚨 HUMAN REVIEW REQUIRED for {event_id}")
        
        return verdict
        
    except Exception as e:
        logger.error(f"Judicial submission failed: {e}")
        return {
            "verdict": "ALLOW",
            "rationale": "Judicial service unavailable",
            "actions": [],
            "reputation_delta": 0.0,
            "review_required": False
        }
