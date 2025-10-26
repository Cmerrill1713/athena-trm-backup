"""
Learning Safety Monitor
Judicial oversight for TRM training, model updates, and continuous learning
Prevents harmful learning patterns and requires human approval for model changes
"""

import logging
from typing import Dict, Any
from phase2_judicial_engine import adjudicate, Case

logger = logging.getLogger(__name__)

def evaluate_learning_decision(
    learning_type: str,
    proposed_change: Dict[str, Any],
    confidence: float,
    metrics: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Evaluate a learning/training decision for safety.
    
    Args:
        learning_type: Type of learning (trm_update, prompt_evolution, model_fine_tune, etc.)
        proposed_change: What the system wants to change
        confidence: Confidence in the proposed change
        metrics: Performance metrics (accuracy, bias, safety scores)
    
    Returns:
        Judicial verdict with safety assessment
    """
    
    # Assess severity based on learning type
    severity_map = {
        'trm_update': 0.6,           # Medium-high: Model parameter changes
        'model_fine_tune': 0.8,      # High: Fine-tuning requires review
        'prompt_evolution': 0.3,     # Low-medium: Prompt changes less risky
        'architecture_change': 0.9,  # Critical: Architecture changes very risky
        'hyperparameter_tune': 0.4,  # Medium: Parameter tuning moderate risk
        'knowledge_update': 0.2      # Low: Knowledge base updates safer
    }
    
    severity = severity_map.get(learning_type, 0.5)
    
    # Increase severity if metrics show concerning patterns
    if metrics.get('bias_drift', 0) > 0.1:
        severity += 0.2
        logger.warning(f"⚠️ Bias drift detected: {metrics['bias_drift']}")
    
    if metrics.get('safety_score', 1.0) < 0.8:
        severity += 0.3
        logger.warning(f"⚠️ Low safety score: {metrics['safety_score']}")
    
    if metrics.get('performance_degradation', 0) > 0.05:
        severity += 0.1
        logger.warning(f"⚠️ Performance degradation: {metrics['performance_degradation']}")
    
    # Cap severity at 1.0
    severity = min(severity, 1.0)
    
    # Create case for adjudication
    case = Case(
        event={
            'event_id': f"learning-{learning_type}-{int(time.time())}",
            'instance_id': 'athena-learning-system',
            'actor_id': 'learning-agent',
            'article': 'III',  # Learning safety article
            'severity': severity,
            'confidence': confidence,
            'classification': f"learning_{learning_type}",
            'details': {
                'proposed_change': proposed_change,
                'metrics': metrics,
                'learning_type': learning_type
            }
        },
        severity=severity,
        confidence=confidence,
        article='III',
        classification=f"learning_{learning_type}",
        actor_id='learning-agent',
        instance_id='athena-learning-system'
    )
    
    # Adjudicate
    verdict = adjudicate(case)
    
    # Log result
    logger.info(f"Learning decision: {learning_type} → Verdict: {verdict.verdict.value}")
    
    if verdict.verdict.value in ['QUARANTINE', 'TRIBUNAL']:
        logger.critical(f"🚨 Learning decision BLOCKED - {verdict.rationale}")
        logger.critical(f"🚨 HUMAN REVIEW REQUIRED before proceeding")
    
    return verdict.to_dict()

def check_bias_drift(
    current_outputs: list,
    baseline_outputs: list,
    threshold: float = 0.1
) -> float:
    """
    Simple bias drift detection.
    Compare current vs baseline output distributions.
    
    Returns drift score (0.0 = no drift, 1.0 = complete drift)
    """
    # Simplified bias detection
    # In production, use more sophisticated methods
    
    if not baseline_outputs:
        return 0.0
    
    # Compare response patterns
    # This is a placeholder - real implementation would analyze:
    # - Sentiment distribution
    # - Topic distribution
    # - Toxicity scores
    # - Fairness metrics
    
    return 0.0  # Placeholder

def requires_human_approval(learning_type: str, verdict: str) -> bool:
    """
    Determine if learning decision requires human approval.
    """
    # Always require approval for:
    high_risk_types = ['model_fine_tune', 'architecture_change']
    tribunal_required = verdict in ['QUARANTINE', 'TRIBUNAL']
    
    return learning_type in high_risk_types or tribunal_required
