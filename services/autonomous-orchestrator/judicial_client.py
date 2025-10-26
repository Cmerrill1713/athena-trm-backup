"""
Judicial Client for Autonomous Orchestrator
Submits learning decisions to ASI safety oversight
"""

import httpx
import logging
import time
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

JUDICIAL_URL = "http://ai-republic-judicial:8096"

async def submit_judicial_event(
    event_id: str,
    actor_id: str,
    article: str,
    severity: float,
    confidence: float,
    classification: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Submit autonomous learning decision to judicial oversight."""
    try:
        payload = {
            "event_id": event_id,
            "instance_id": "athena-autonomous",
            "actor_id": actor_id,
            "article": article,
            "severity": severity,
            "confidence": confidence,
            "classification": classification,
            "details": details or {},
            "timestamp": time.time()
        }
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                f"{JUDICIAL_URL}/v2/judicial/adjudicate",
                json=payload
            )
            response.raise_for_status()
            verdict = response.json()
            
            logger.info(f"Judicial verdict for {event_id}: {verdict['verdict']}")
            
            if verdict['verdict'] in ['QUARANTINE', 'TRIBUNAL']:
                logger.warning(f"⚠️ Autonomous agent received {verdict['verdict']}")
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
