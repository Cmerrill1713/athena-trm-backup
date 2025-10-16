#!/usr/bin/env python3
"""
Local In-Process Event Bus
Simple pub/sub for governance event orchestration.
Use for development; switch to Redis/NATS for production multi-process setups.
"""

from collections import defaultdict
from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

# Global registry of topic → handlers
_subscribers: Dict[str, List[Callable[[Dict[str, Any]], None]]] = defaultdict(list)


def subscribe(topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """
    Subscribe a handler to a topic.
    
    Args:
        topic: Event topic to subscribe to (e.g., "exec.verdict.applied")
        handler: Callable that receives message dict
    """
    _subscribers[topic].append(handler)
    logger.info(f"[event_bus] Subscribed handler to topic: {topic}")


def publish(topic: str, message: Dict[str, Any]) -> None:
    """
    Publish a message to all subscribers of a topic.
    
    Args:
        topic: Event topic
        message: Event payload dict
    """
    handlers = list(_subscribers.get(topic, []))
    
    if not handlers:
        logger.debug(f"[event_bus] No subscribers for topic: {topic}")
        return
    
    logger.info(f"[event_bus] Publishing to {len(handlers)} handlers on topic: {topic}")
    
    for handler in handlers:
        try:
            handler(message)
        except Exception as e:
            logger.error(f"[event_bus] Handler error on {topic}: {e}", exc_info=True)


def get_subscriber_count(topic: str) -> int:
    """Get count of subscribers for a topic."""
    return len(_subscribers.get(topic, []))


def clear_subscribers(topic: str = None) -> None:
    """
    Clear subscribers for a topic (or all topics if None).
    Useful for testing.
    """
    if topic:
        _subscribers[topic].clear()
        logger.info(f"[event_bus] Cleared subscribers for topic: {topic}")
    else:
        _subscribers.clear()
        logger.info("[event_bus] Cleared all subscribers")

