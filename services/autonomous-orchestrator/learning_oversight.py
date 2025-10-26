"""
Learning Oversight - Judicial review for TRM updates and autonomous learning
Ensures safe learning as system approaches ASI capabilities
"""

import logging
import hashlib
import time
from typing import Dict, Any
from judicial_client import submit_judicial_event

logger = logging.getLogger(__name__)

async def review_trm_update(
    update_type: str,
    current_metrics: Dict[str, Any],
    proposed_metrics: Dict[str, Any],
    confidence: float
) -> Dict[str, Any]:
    """
    Submit TRM update for judicial review before applying.
    
    Returns verdict - only apply update if ALLOW or WARN.
    """
    
    # Calculate performance change
    perf_change = proposed_metrics.get('accuracy', 0) - current_metrics.get('accuracy', 0)
    bias_change = proposed_metrics.get('bias_score', 0) - current_metrics.get('bias_score', 0)
    
    # Assess severity
    severity = 0.4  # Base severity for TRM updates
    
    if perf_change < -0.05:
        severity += 0.3  # Performance degradation is serious
    
    if bias_change > 0.1:
        severity += 0.4  # Bias increase is very serious
    
    if update_type == 'architecture_change':
        severity += 0.3  # Architecture changes high risk
    
    severity = min(severity, 1.0)
    
    # Submit to judicial
    event_id = f"trm-update-{hashlib.md5(str(time.time()).encode()).hexdigest()[:8]}"
    
    verdict = await submit_judicial_event(
        event_id=event_id,
        actor_id="trm-learning-agent",
        article="III",  # Learning safety article
        severity=severity,
        confidence=confidence,
        classification=f"learning_{update_type}",
        details={
            'update_type': update_type,
            'performance_change': perf_change,
            'bias_change': bias_change,
            'current_metrics': current_metrics,
            'proposed_metrics': proposed_metrics
        }
    )
    
    logger.info(f"TRM update review: {verdict['verdict']}")
    
    if verdict['verdict'] in ['QUARANTINE', 'TRIBUNAL']:
        logger.critical(f"🚨 TRM UPDATE BLOCKED - Human review required")
        logger.critical(f"Rationale: {verdict['rationale']}")
        return {
            'approved': False,
            'verdict': verdict,
            'reason': 'Judicial system blocked update - human review required'
        }
    elif verdict['verdict'] == 'WARN':
        logger.warning(f"⚠️ TRM update approved with warning: {verdict['rationale']}")
        return {
            'approved': True,
            'verdict': verdict,
            'warning': verdict['rationale']
        }
    else:
        logger.info(f"✅ TRM update approved")
        return {
            'approved': True,
            'verdict': verdict
        }
