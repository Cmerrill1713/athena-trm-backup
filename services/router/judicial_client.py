"""
Judicial Client - Submit events to AI Republic Judicial System
Enables ASI safety oversight for Router decisions
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
    """
    Submit event to judicial system for oversight.
    
    Args:
        event_id: Unique event identifier
        actor_id: AI agent identifier (e.g., "router-001")
        article: Constitutional article (I, II, III, etc.)
        severity: 0.0-1.0 (how severe the potential violation)
        confidence: 0.0-1.0 (how confident in the assessment)
        classification: Event type (e.g., "routing_decision", "policy_drift")
        details: Additional context
    
    Returns:
        Judicial verdict with actions, reputation delta, review requirements
    """
    try:
        payload = {
            "event_id": event_id,
            "instance_id": "athena-router",
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
            
            # Log verdict
            logger.info(f"Judicial verdict for {event_id}: {verdict['verdict']}")
            
            # Check if quarantine required
            if verdict['verdict'] in ['QUARANTINE', 'TRIBUNAL']:
                logger.warning(f"⚠️ Agent {actor_id} received {verdict['verdict']} - {verdict['rationale']}")
                if verdict['review_required']:
                    logger.critical(f"🚨 HUMAN REVIEW REQUIRED for {event_id}")
            
            return verdict
            
    except Exception as e:
        logger.error(f"Judicial submission failed: {e}")
        # Fail-safe: Allow operation but log failure
        return {
            "verdict": "ALLOW",
            "rationale": "Judicial service unavailable - default allow",
            "actions": [],
            "reputation_delta": 0.0,
            "review_required": False,
            "error": str(e)
        }

async def check_reputation(actor_id: str) -> float:
    """Get current reputation score for an AI agent."""
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(f"{JUDICIAL_URL}/v2/reputation/{actor_id}")
            if response.status_code == 200:
                data = response.json()
                return data.get("reputation", 0.0)
    except Exception:
        pass
    
    return 0.0  # Default neutral reputation
