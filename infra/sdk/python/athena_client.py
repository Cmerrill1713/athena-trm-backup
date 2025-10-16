"""
Athena Governance SDK - Python Client

Thin SDK wrapper for emitting governance receipts from jobs, CLIs, and services.

Usage:
    from infra.sdk.python.athena_client import governed_task, emit_receipt
    
    @governed_task("batch_job")
    def run_batch():
        # Your code here
        pass
"""

import json
import os
import time
import uuid
import logging
from typing import Dict, Any, Optional, Callable
from functools import wraps

try:
    import requests
except ImportError:
    requests = None
    logging.warning("requests not installed, governance receipts will not be sent")


logger = logging.getLogger(__name__)


# Configuration
ATHENA_URL = os.getenv("ATHENA_URL", "http://localhost:9110")
ATHENA_MODE = os.getenv("ATHENA_MODE", "shadow")
ATHENA_POLICY_VERSION = os.getenv("ATHENA_POLICY_VERSION", "unknown")


def emit_receipt(
    task_type: str,
    payload: Dict[str, Any],
    status: str = "start",
    trace_id: Optional[str] = None
) -> bool:
    """
    Emit a governance receipt to Athena orchestrator
    
    Args:
        task_type: Type of task (e.g. "batch_job", "api_call")
        payload: Arbitrary payload data
        status: "start" | "end" | "error"
        trace_id: Optional trace ID (generated if not provided)
    
    Returns:
        True if receipt was sent successfully, False otherwise
    """
    
    if requests is None:
        return False
    
    body = {
        "trace_id": trace_id or payload.get("trace_id") or str(uuid.uuid4()),
        "task_type": task_type,
        "status": status,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "mode": ATHENA_MODE,
        "policy": ATHENA_POLICY_VERSION,
        "payload": payload,
    }
    
    try:
        response = requests.post(
            f"{ATHENA_URL}/receipt",
            json=body,
            timeout=2  # Fast timeout - don't block caller
        )
        
        if response.status_code in (200, 201, 202):
            logger.debug(f"Receipt sent: {task_type}/{status}")
            return True
        else:
            logger.warning(f"Receipt failed: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.warning(f"Receipt timeout for {task_type}")
        return False
    except Exception as e:
        logger.warning(f"Receipt error: {e}")
        return False


def governed_task(task_type: str, emit_end: bool = True):
    """
    Decorator to emit governance receipts for a function
    
    Args:
        task_type: Type of task (e.g. "model_inference", "data_export")
        emit_end: Whether to emit end/error receipts (default: True)
    
    Usage:
        @governed_task("batch_processing")
        def process_batch(items):
            # Your code here
            return results
    """
    
    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            trace_id = str(uuid.uuid4())
            
            # Emit start receipt
            payload = {
                "function": fn.__name__,
                "args": str(args)[:100],  # Truncate for size
                "kwargs": str(kwargs)[:100]
            }
            emit_receipt(task_type, payload, "start", trace_id)
            
            # Execute function
            try:
                result = fn(*args, **kwargs)
                
                # Emit end receipt
                if emit_end:
                    emit_receipt(
                        task_type,
                        {"result": "ok", "function": fn.__name__},
                        "end",
                        trace_id
                    )
                
                return result
                
            except Exception as e:
                # Emit error receipt
                if emit_end:
                    emit_receipt(
                        task_type,
                        {"error": str(e)[:200], "function": fn.__name__},
                        "error",
                        trace_id
                    )
                raise
        
        return wrapper
    return decorator


class AthenaClient:
    """Full-featured Athena governance client"""
    
    def __init__(
        self,
        url: Optional[str] = None,
        mode: Optional[str] = None,
        policy_version: Optional[str] = None
    ):
        self.url = url or ATHENA_URL
        self.mode = mode or ATHENA_MODE
        self.policy_version = policy_version or ATHENA_POLICY_VERSION
    
    def send_receipt(
        self,
        task_type: str,
        payload: Dict[str, Any],
        status: str = "start",
        trace_id: Optional[str] = None
    ) -> bool:
        """Send a governance receipt"""
        return emit_receipt(task_type, payload, status, trace_id)
    
    def send_verdict_request(
        self,
        task_id: str,
        verdict: str,
        ece_post: float,
        entropy: float,
        actions: list
    ) -> Dict[str, Any]:
        """Send a verdict to the orchestrator"""
        
        if requests is None:
            return {"error": "requests not installed"}
        
        body = {
            "task_id": task_id,
            "verdict": verdict,
            "ece_post": ece_post,
            "entropy": entropy,
            "actions": actions,
            "ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        }
        
        try:
            response = requests.post(
                f"{self.url}/verdict",
                json=body,
                timeout=5
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Verdict request failed: {e}")
            return {"error": str(e)}
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        
        if requests is None:
            return {"error": "requests not installed"}
        
        try:
            response = requests.get(f"{self.url}/health", timeout=2)
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def check_coverage(self, prometheus_url: str = "http://localhost:9090") -> Dict[str, float]:
        """Check governance coverage from Prometheus"""
        
        if requests is None:
            return {}
        
        try:
            # Query ingress requests
            ingress_resp = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": "sum(ingress_requests_total)"},
                timeout=5
            )
            ingress_total = float(ingress_resp.json()["data"]["result"][0]["value"][1])
            
            # Query governance receipts
            receipts_resp = requests.get(
                f"{prometheus_url}/api/v1/query",
                params={"query": "sum(governance_receipts_total)"},
                timeout=5
            )
            receipts_total = float(receipts_resp.json()["data"]["result"][0]["value"][1])
            
            coverage = receipts_total / ingress_total if ingress_total > 0 else 0.0
            
            return {
                "coverage": coverage,
                "ingress_total": ingress_total,
                "receipts_total": receipts_total
            }
        except Exception as e:
            logger.error(f"Coverage check failed: {e}")
            return {}


# Convenience exports
__all__ = [
    "emit_receipt",
    "governed_task",
    "AthenaClient",
]


if __name__ == "__main__":
    # Test the client
    print("Testing Athena SDK...\n")
    
    client = AthenaClient()
    status = client.get_status()
    print(f"Orchestrator status: {status}")
    
    # Test receipt
    success = emit_receipt(
        "test_task",
        {"test": "data"},
        "start"
    )
    print(f"\nReceipt sent: {success}")
    
    # Test decorator
    @governed_task("demo_task")
    def demo():
        print("Running governed task...")
        return "success"
    
    result = demo()
    print(f"Task result: {result}")

