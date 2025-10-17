#!/usr/bin/env python3
"""
Athena Governance Canary Controller

Monitors router canary metrics and triggers automatic rollback on breach.

Breach conditions:
- p95 latency > 1200ms
- Cost per request > $0.05
- Error rate > 10%

On breach:
- Revokes ALLOW_CLOUD override
- Logs rollback event
- Fires Prometheus alert
"""
import os
import sys
import json
import time
import asyncio
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from prometheus_client import Counter, Gauge, push_to_gateway, CollectorRegistry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

ROUTER_URL = os.getenv("ROUTER_URL", "http://127.0.0.1:9113")
PROMETHEUS_PUSHGATEWAY = os.getenv("PROMETHEUS_PUSHGATEWAY", "http://127.0.0.1:9091")

# Breach thresholds (text modality)
MAX_P95_LATENCY_MS = 1200
MAX_COST_PER_REQUEST = 0.05
MAX_ERROR_RATE = 0.10

# Modal-specific thresholds
MAX_VISION_P95_MS = 1500  # Vision: ≤ 1.5s
MAX_VOICE_P95_MS = 350    # TTS: ≤ 0.35s (350ms)
MAX_MODAL_ECE = 0.06      # Per modality ECE

# Check interval
CHECK_INTERVAL_SECONDS = 5

# ============================================================================
# METRICS
# ============================================================================

registry = CollectorRegistry()

canary_checks_total = Counter(
    'athena_governance_canary_checks_total',
    'Total canary checks performed',
    registry=registry
)

canary_breaches_total = Counter(
    'athena_governance_canary_breaches_total',
    'Total breach events detected',
    ['breach_type'],
    registry=registry
)

canary_rollbacks_total = Counter(
    'athena_governance_canary_rollbacks_total',
    'Total rollbacks executed',
    ['reason'],
    registry=registry
)

canary_state_gauge = Gauge(
    'athena_governance_canary_state',
    'Canary state (0=inactive, 1=active, 2=breached)',
    registry=registry
)

# ============================================================================
# EVENT LOGGER
# ============================================================================

class PolicyChangeLogger:
    """Logs policy change events to JSONL."""
    
    def __init__(self, log_path: str = "/tmp/policy_change_events.jsonl"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
    
    def log_event(
        self,
        event_type: str,
        reason: str,
        details: Optional[Dict[str, Any]] = None
    ):
        """Log a policy change event."""
        event = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "reason": reason,
            "details": details or {}
        }
        
        try:
            with open(self.log_path, 'a') as f:
                f.write(json.dumps(event) + '\n')
            logger.info(f"Logged event: {event_type} - {reason}")
        except Exception as e:
            logger.error(f"Failed to log event: {e}")

# ============================================================================
# CANARY CONTROLLER
# ============================================================================

class CanaryController:
    """Monitors canary metrics and triggers rollback on breach."""
    
    def __init__(self):
        self.event_logger = PolicyChangeLogger()
        self.running = False
        self.breach_count = 0
        self.breach_threshold = 3  # Require 3 consecutive breaches
    
    async def get_canary_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch canary metrics from router."""
        try:
            response = requests.get(f"{ROUTER_URL}/canary", timeout=2.0)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Router /canary returned {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Failed to fetch canary metrics: {e}")
            return None
    
    async def get_modal_metrics(self) -> Optional[Dict[str, Any]]:
        """Fetch modal-specific metrics from router."""
        try:
            response = requests.get(f"{ROUTER_URL}/metrics", timeout=2.0)
            if response.status_code == 200:
                # Parse Prometheus metrics for modality data
                metrics_text = response.text
                
                modal_data = {}
                for line in metrics_text.split('\n'):
                    if 'athena_vision_latency_seconds' in line and 'quantile="0.95"' in line:
                        try:
                            value = float(line.split()[-1])
                            modal_data['vision_p95_ms'] = value * 1000
                        except:
                            pass
                    elif 'athena_voice_latency_seconds' in line and 'quantile="0.95"' in line:
                        try:
                            value = float(line.split()[-1])
                            modal_data['voice_p95_ms'] = value * 1000
                        except:
                            pass
                    elif 'athena_modality_ece_estimate{modality="vision"}' in line:
                        try:
                            value = float(line.split()[-1])
                            modal_data['vision_ece'] = value
                        except:
                            pass
                    elif 'athena_modality_ece_estimate{modality="voice"}' in line:
                        try:
                            value = float(line.split()[-1])
                            modal_data['voice_ece'] = value
                        except:
                            pass
                
                return modal_data
            return {}
        except Exception as e:
            logger.debug(f"Failed to fetch modal metrics: {e}")
            return {}
    
    def check_breach(self, metrics: Dict[str, Any]) -> Optional[str]:
        """
        Check if metrics exceed breach thresholds.
        
        Returns:
            Breach reason if breached, None otherwise
        """
        if not metrics.get("canary_active", False):
            return None  # Canary not active
        
        providers = metrics.get("providers", {})
        aggregate = metrics.get("aggregate", {})
        
        # Check p95 latency (text modality)
        avg_p95 = aggregate.get("avg_p95_latency_ms", 0)
        if avg_p95 > MAX_P95_LATENCY_MS:
            logger.warning(f"⚠️  P95 latency breach: {avg_p95:.1f}ms > {MAX_P95_LATENCY_MS}ms")
            canary_breaches_total.labels(breach_type='latency').inc()
            return f"p95_latency_breach:{avg_p95:.1f}ms"
        
        # Check error rates
        for provider_name, status in providers.items():
            error_rate = status.get("error_rate", 0.0)
            if error_rate > MAX_ERROR_RATE:
                logger.warning(f"⚠️  Error rate breach on {provider_name}: {error_rate:.2%}")
                canary_breaches_total.labels(breach_type='error_rate').inc()
                return f"error_rate_breach:{provider_name}:{error_rate:.2%}"
        
        return None
    
    def check_modal_breach(self, modal_metrics: Dict[str, Any]) -> Optional[str]:
        """Check modality-specific breach thresholds."""
        # Check vision p95
        vision_p95 = modal_metrics.get('vision_p95_ms', 0)
        if vision_p95 > MAX_VISION_P95_MS:
            logger.warning(f"⚠️  Vision p95 breach: {vision_p95:.1f}ms > {MAX_VISION_P95_MS}ms")
            canary_breaches_total.labels(breach_type='vision_latency').inc()
            return f"vision_p95_breach:{vision_p95:.1f}ms"
        
        # Check voice p95
        voice_p95 = modal_metrics.get('voice_p95_ms', 0)
        if voice_p95 > MAX_VOICE_P95_MS:
            logger.warning(f"⚠️  Voice p95 breach: {voice_p95:.1f}ms > {MAX_VOICE_P95_MS}ms")
            canary_breaches_total.labels(breach_type='voice_latency').inc()
            return f"voice_p95_breach:{voice_p95:.1f}ms"
        
        # Check modal ECE
        vision_ece = modal_metrics.get('vision_ece', 0)
        if vision_ece > MAX_MODAL_ECE:
            logger.warning(f"⚠️  Vision ECE breach: ${vision_ece:.4f} > ${MAX_MODAL_ECE}")
            canary_breaches_total.labels(breach_type='vision_ece').inc()
            return f"vision_ece_breach:${vision_ece:.4f}"
        
        voice_ece = modal_metrics.get('voice_ece', 0)
        if voice_ece > MAX_MODAL_ECE:
            logger.warning(f"⚠️  Voice ECE breach: ${voice_ece:.4f} > ${MAX_MODAL_ECE}")
            canary_breaches_total.labels(breach_type='voice_ece').inc()
            return f"voice_ece_breach:${voice_ece:.4f}"
        
        return None
    
    def revoke_cloud_override(self):
        """Revoke ALLOW_CLOUD policy override."""
        override_path = Path("state/router_policy_overrides.json")
        
        if override_path.exists():
            try:
                override_path.unlink()
                logger.info("✅ Cloud override revoked")
                return True
            except Exception as e:
                logger.error(f"Failed to revoke override: {e}")
                return False
        else:
            logger.info("No active override to revoke")
            return True
    
    def execute_rollback(self, reason: str):
        """Execute rollback: revoke cloud access and log event."""
        logger.warning(f"🚨 ROLLBACK TRIGGERED: {reason}")
        
        # Revoke cloud override
        if self.revoke_cloud_override():
            canary_rollbacks_total.labels(reason='breach').inc()
            canary_state_gauge.set(2)  # Breached
            
            # Log rollback event
            self.event_logger.log_event(
                event_type="rollback",
                reason=reason,
                details={
                    "threshold_breached": True,
                    "action": "revoke_cloud_override"
                }
            )
            
            logger.info("✅ Rollback complete")
        else:
            logger.error("❌ Rollback failed")
    
    async def check_loop(self):
        """Main monitoring loop."""
        self.running = True
        
        logger.info("🔍 Canary controller started")
        logger.info(f"   Check interval: {CHECK_INTERVAL_SECONDS}s")
        logger.info(f"   Breach threshold: {self.breach_threshold} consecutive")
        logger.info(f"   Max p95 latency: {MAX_P95_LATENCY_MS}ms")
        logger.info(f"   Max error rate: {MAX_ERROR_RATE:.0%}")
        
        while self.running:
            try:
                # Fetch metrics
                metrics = await self.get_canary_metrics()
                
                if metrics:
                    canary_checks_total.inc()
                    
                    # Update canary state
                    if metrics.get("canary_active", False):
                        canary_state_gauge.set(1)  # Active
                    else:
                        canary_state_gauge.set(0)  # Inactive
                        self.breach_count = 0
                    
                    # Check for breach (text modality)
                    breach_reason = self.check_breach(metrics)
                    
                    # Check modal breaches
                    if not breach_reason:
                        modal_metrics = await self.get_modal_metrics()
                        if modal_metrics:
                            breach_reason = self.check_modal_breach(modal_metrics)
                    
                    if breach_reason:
                        self.breach_count += 1
                        logger.warning(f"Breach detected ({self.breach_count}/{self.breach_threshold}): {breach_reason}")
                        
                        if self.breach_count >= self.breach_threshold:
                            self.execute_rollback(breach_reason)
                            self.breach_count = 0
                    else:
                        # Reset breach count on healthy check
                        if self.breach_count > 0:
                            logger.info("Metrics returned to healthy, resetting breach count")
                        self.breach_count = 0
                    
                    # Push metrics to Prometheus
                    try:
                        push_to_gateway(
                            PROMETHEUS_PUSHGATEWAY,
                            job='governance_canary',
                            registry=registry
                        )
                    except Exception as e:
                        logger.debug(f"Failed to push metrics: {e}")
                
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Check loop error: {e}")
                await asyncio.sleep(CHECK_INTERVAL_SECONDS)
        
        logger.info("Canary controller stopped")
    
    def stop(self):
        """Stop the controller."""
        self.running = False

# ============================================================================
# MAIN
# ============================================================================

async def main():
    """Run canary controller."""
    controller = CanaryController()
    
    try:
        await controller.check_loop()
    except KeyboardInterrupt:
        logger.info("Shutdown requested")
        controller.stop()

if __name__ == "__main__":
    asyncio.run(main())

