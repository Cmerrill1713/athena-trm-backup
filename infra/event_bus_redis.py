#!/usr/bin/env python3
"""
Redis-backed Event Bus
Durable pub/sub for production multi-process governance orchestration.
"""

import json
import os
import threading
import logging
from typing import Callable, Dict, Any

import redis

logger = logging.getLogger(__name__)

# Global Redis connection
_redis_client = None


def _get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        _redis_client = redis.Redis.from_url(redis_url, decode_responses=True)
        logger.info(f"[event_bus_redis] Connected to Redis: {redis_url}")
    return _redis_client


def publish(topic: str, message: Dict[str, Any]) -> None:
    """
    Publish a message to Redis pub/sub channel.
    
    Args:
        topic: Event topic (Redis channel name)
        message: Event payload dict
    """
    try:
        r = _get_redis()
        payload = json.dumps(message)
        r.publish(topic, payload)
        logger.info(f"[event_bus_redis] Published to topic: {topic}")
    except Exception as e:
        logger.error(f"[event_bus_redis] Publish error on {topic}: {e}", exc_info=True)


def subscribe(topic: str, handler: Callable[[Dict[str, Any]], None]) -> None:
    """
    Subscribe a handler to a Redis pub/sub channel.
    Runs in a background daemon thread.
    
    Args:
        topic: Event topic (Redis channel name)
        handler: Callable that receives message dict
    """
    def _listen_loop():
        try:
            r = _get_redis()
            pubsub = r.pubsub()
            pubsub.subscribe(topic)
            logger.info(f"[event_bus_redis] Subscribed to topic: {topic}")
            
            for message in pubsub.listen():
                if message["type"] == "message":
                    try:
                        payload = json.loads(message["data"])
                        handler(payload)
                    except json.JSONDecodeError as e:
                        logger.error(f"[event_bus_redis] JSON decode error: {e}")
                    except Exception as e:
                        logger.error(f"[event_bus_redis] Handler error on {topic}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"[event_bus_redis] Subscription error on {topic}: {e}", exc_info=True)
    
    thread = threading.Thread(target=_listen_loop, daemon=True, name=f"redis-sub-{topic}")
    thread.start()


def get_subscriber_count(topic: str) -> int:
    """
    Get count of active subscribers for a Redis channel.
    Note: Returns number of connections, not handler count.
    """
    try:
        r = _get_redis()
        channels = r.pubsub_numsub(topic)
        return channels[0][1] if channels else 0
    except Exception as e:
        logger.error(f"[event_bus_redis] Error getting subscriber count: {e}")
        return 0

