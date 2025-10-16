"""
Monitoring Bridge

Unified monitoring setup across AGI Core and Governance systems.
"""

from fastapi import FastAPI
from typing import Optional
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from common.ops import wire_tracing, attach_guardrails, add_health_endpoints

import logging
logger = logging.getLogger(__name__)


def setup_unified_monitoring(
    app: FastAPI,
    service_name: str,
    enable_tracing: bool = True,
    enable_guardrails: bool = True,
    enable_health: bool = True,
    rate_limit: str = "100/minute",
    max_body_mb: int = 5
) -> None:
    """
    Set up unified monitoring for any service
    
    Uses common/ops.py utilities to configure:
    - OpenTelemetry tracing
    - Rate limiting & guardrails
    - Health check endpoints
    
    Usage:
        from fastapi import FastAPI
        from agi_core.integrations import setup_unified_monitoring
        
        app = FastAPI(title="My Service")
        setup_unified_monitoring(app, "my-service")
    """
    logger.info(f"Setting up unified monitoring for {service_name}")
    
    if enable_tracing:
        wire_tracing(app, service_name)
        logger.info(f"✅ OpenTelemetry tracing enabled for {service_name}")
    
    if enable_guardrails:
        attach_guardrails(
            app,
            per_ip_rate=rate_limit,
            max_body_mb=max_body_mb
        )
        logger.info(f"✅ Guardrails enabled: rate={rate_limit}, max_body={max_body_mb}MB")
    
    if enable_health:
        add_health_endpoints(app)
        logger.info(f"✅ Health endpoints added: /live, /ready, /metrics")
    
    logger.info(f"🎉 Unified monitoring complete for {service_name}")

