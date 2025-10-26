"""
Event Bus & State Store Integration for Athena Dev Daemon
NATS for events, etcd for state
"""
import json
import logging
import os
from typing import Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

# Configuration
NATS_URL = os.getenv("NATS_URL", "nats://athena-nats:4222")
ETCD_URL = os.getenv("ETCD_URL", "http://athena-etcd:2379")

# Event subjects
SUBJECT_CTX_REQUESTED = "athena.dev.ctx.requested"
SUBJECT_CTX_SERVED = "athena.dev.ctx.served"
SUBJECT_ROUTING_DECISION = "athena.routing.decision.proposed"


class EventEmitter:
    """
    Emit events to NATS for system-wide coordination
    """
    
    def __init__(self):
        self.nats_client = None
        # TODO: Initialize NATS client
        # from nats.aio.client import Client as NATS
        # self.nats_client = NATS()
    
    async def connect(self):
        """Connect to NATS"""
        try:
            # TODO: Uncomment when nats-py is added to requirements
            # await self.nats_client.connect(NATS_URL)
            logger.info(f"Connected to NATS at {NATS_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to NATS: {e}")
    
    async def emit(self, subject: str, data: Dict[str, Any]):
        """
        Emit event to NATS
        
        Args:
            subject: NATS subject (e.g., "athena.dev.ctx.requested")
            data: Event payload
        """
        try:
            payload = {
                "timestamp": datetime.utcnow().isoformat(),
                "source": "athena-devd",
                **data
            }
            
            # TODO: Uncomment when NATS is wired
            # await self.nats_client.publish(subject, json.dumps(payload).encode())
            
            # For now, log it
            logger.info(f"Event emitted: {subject}")
            logger.debug(f"Event payload: {json.dumps(payload, indent=2)}")
            
        except Exception as e:
            logger.error(f"Failed to emit event to {subject}: {e}")


class StateStore:
    """
    Write state to etcd for global visibility
    """
    
    def __init__(self):
        self.etcd_client = None
        # TODO: Initialize etcd client
        # import etcd3
        # self.etcd_client = etcd3.client(host='athena-etcd', port=2379)
    
    async def connect(self):
        """Connect to etcd"""
        try:
            # TODO: Uncomment when etcd3 is added to requirements
            # self.etcd_client = etcd3.client(host=ETCD_URL.split('://')[1].split(':')[0], port=2379)
            logger.info(f"Connected to etcd at {ETCD_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to etcd: {e}")
    
    async def write_user_activity(self, user_id: str, activity: Dict[str, Any]):
        """
        Write user's dev activity to etcd
        
        Key: /athena/devd/active/{user}
        Value: {last_files, last_intent, last_latency_ms, last_snippets_count}
        """
        try:
            key = f"/athena/devd/active/{user_id}"
            value = json.dumps({
                "timestamp": datetime.utcnow().isoformat(),
                "last_files": activity.get("files", [])[-10:],  # Last 10 files
                "last_intent": activity.get("intent", "unknown"),
                "last_latency_ms": activity.get("latency_ms", 0),
                "last_snippets_count": activity.get("snippets_count", 0),
                "total_requests": activity.get("total_requests", 0)
            })
            
            # TODO: Uncomment when etcd is wired
            # self.etcd_client.put(key, value)
            
            # For now, log it
            logger.info(f"State written to etcd: {key}")
            logger.debug(f"State value: {value}")
            
        except Exception as e:
            logger.error(f"Failed to write state to etcd: {e}")
    
    async def read_rep_clustering(self, region: str = "us-west") -> Dict[str, Any]:
        """
        Read REP clustering signal from etcd
        
        Key: /athena/rep/regions/{region}/summary/clustering
        Returns: {clustering_factor, recommended_action, timestamp}
        """
        try:
            key = f"/athena/rep/regions/{region}/summary/clustering"
            
            # TODO: Uncomment when etcd is wired
            # value, metadata = self.etcd_client.get(key)
            # if value:
            #     return json.loads(value.decode('utf-8'))
            
            # For now, return mock data
            logger.info(f"Read REP clustering from etcd: {key}")
            return {
                "clustering_factor": 0.3,  # Low clustering
                "recommended_action": "normal",
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to read REP clustering: {e}")
            return {"clustering_factor": 0.0, "recommended_action": "normal"}


# Global instances
event_emitter = EventEmitter()
state_store = StateStore()


async def initialize_event_state():
    """Initialize NATS and etcd connections"""
    await event_emitter.connect()
    await state_store.connect()


# Convenience functions
async def emit_ctx_requested(ctx: Dict[str, Any], decision: Dict[str, Any], trace_id: str):
    """Emit context requested event"""
    await event_emitter.emit(SUBJECT_CTX_REQUESTED, {
        "trace_id": trace_id,
        "context": ctx,
        "decision": decision
    })


async def emit_ctx_served(trace_id: str, snippets_count: int, latency_ms: float):
    """Emit context served event"""
    await event_emitter.emit(SUBJECT_CTX_SERVED, {
        "trace_id": trace_id,
        "snippets_count": snippets_count,
        "latency_ms": latency_ms
    })


async def update_user_state(user_id: str, activity: Dict[str, Any]):
    """Update user activity in etcd"""
    await state_store.write_user_activity(user_id, activity)


async def get_rep_clustering(region: str = "us-west") -> Dict[str, Any]:
    """Get REP clustering signal"""
    return await state_store.read_rep_clustering(region)

