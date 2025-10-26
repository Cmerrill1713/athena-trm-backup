"""
REP (Reputation) Awareness for Athena Dev Daemon
Read clustering signals and adapt behavior
"""
import logging
from typing import Dict, Any
from events_state import get_rep_clustering

logger = logging.getLogger(__name__)

# Clustering thresholds
CLUSTERING_HIGH = 0.7  # High clustering - back off
CLUSTERING_MEDIUM = 0.4  # Medium clustering - be cautious
CLUSTERING_LOW = 0.2  # Low clustering - normal operation

async def adapt_to_clustering(region: str = "us-west") -> Dict[str, Any]:
    """
    Read REP clustering signal and return adaptation strategy
    
    Args:
        region: REP region (default: us-west)
    
    Returns:
        Strategy dict with recommended actions
    """
    try:
        clustering_data = await get_rep_clustering(region)
        factor = clustering_data.get("clustering_factor", 0.0)
        
        logger.info(f"REP clustering factor: {factor}")
        
        if factor >= CLUSTERING_HIGH:
            # High clustering - aggressive backoff
            logger.warning(f"High clustering detected ({factor:.2f})")
            return {
                "strategy": "backoff",
                "prefer_alternative_model": True,
                "increase_bm25_weight": True,  # Prefer lexical over semantic
                "reduce_topK": True,  # Fewer snippets
                "suggested_topK": 5,
                "reason": f"High clustering ({factor:.2f}) - reducing load"
            }
        
        elif factor >= CLUSTERING_MEDIUM:
            # Medium clustering - mild backoff
            logger.info(f"Medium clustering detected ({factor:.2f})")
            return {
                "strategy": "cautious",
                "prefer_alternative_model": False,
                "increase_bm25_weight": True,
                "reduce_topK": False,
                "suggested_topK": 8,
                "reason": f"Medium clustering ({factor:.2f}) - being cautious"
            }
        
        else:
            # Low clustering - normal operation
            logger.debug(f"Low clustering ({factor:.2f}) - normal operation")
            return {
                "strategy": "normal",
                "prefer_alternative_model": False,
                "increase_bm25_weight": False,
                "reduce_topK": False,
                "suggested_topK": 8,
                "reason": "Low clustering - normal operation"
            }
    
    except Exception as e:
        logger.error(f"Failed to read REP clustering: {e}")
        # Default to normal operation on error
        return {
            "strategy": "normal",
            "prefer_alternative_model": False,
            "increase_bm25_weight": False,
            "reduce_topK": False,
            "suggested_topK": 8,
            "reason": "REP unavailable - default to normal"
        }


async def emit_rep_hint_used(factor: float, strategy: str):
    """
    Emit event when REP hint is used
    
    This allows us to measure impact of REP awareness
    """
    from events_state import event_emitter
    
    await event_emitter.emit("athena.rep.hint.used", {
        "clustering_factor": factor,
        "strategy": strategy,
        "source": "athena-devd"
    })
    
    logger.info(f"REP hint used: {strategy} (clustering={factor:.2f})")


async def apply_rep_strategy(
    strategy: Dict[str, Any],
    config: Any
) -> Dict[str, Any]:
    """
    Apply REP strategy to request configuration
    
    Args:
        strategy: Strategy from adapt_to_clustering()
        config: Current configuration
    
    Returns:
        Modified configuration
    """
    if strategy["strategy"] == "backoff":
        # High clustering - aggressive changes
        config.max_snippets = strategy["suggested_topK"]
        logger.info(f"REP backoff: Reduced topK to {config.max_snippets}")
    
    elif strategy["strategy"] == "cautious":
        # Medium clustering - mild changes
        logger.info("REP cautious: Slight adjustments")
    
    # Emit that we used REP hint
    await emit_rep_hint_used(
        strategy.get("clustering_factor", 0.0),
        strategy["strategy"]
    )
    
    return {
        "max_snippets": config.max_snippets,
        "prefer_lexical": strategy["increase_bm25_weight"],
        "prefer_alternative_model": strategy["prefer_alternative_model"]
    }

