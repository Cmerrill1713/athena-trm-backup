#!/usr/bin/env python3
"""
AGI Core Auto-Remediator Service
Listens for remediation requests, generates plans using AGI Core,
validates via canary, and promotes/rolls back automatically.
"""

import os
import json
import logging
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from http.server import BaseHTTPRequestHandler, HTTPServer

# Event bus setup
if os.getenv("EVENT_BUS", "local") == "redis":
    from infra.event_bus_redis import subscribe, publish
else:
    from infra.event_bus import subscribe, publish

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Metrics
_metrics = {
    "remediations_requested": 0,
    "remediations_started": 0,
    "remediations_completed": 0,
    "remediations_promoted": 0,
    "remediations_rolled_back": 0,
    "remediations_failed": 0
}


class RemediationPlanner:
    """
    Generates remediation plans using AGI Core / governance bridge.
    Stub implementation - replace with real AGI Core integration.
    """
    
    def __init__(self):
        self.plan_counter = 0
        
    def generate_plan(self, verdict: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate remediation plan based on verdict.
        
        In production, this would:
        - Call GovernanceBridge to analyze failure
        - Use STOP optimizer to generate improvements
        - Synthesize code patches using foundation model
        
        Args:
            verdict: Verdict dict with failure info
            
        Returns:
            Remediation plan dict
        """
        self.plan_counter += 1
        plan_id = f"plan-{int(time.time())}-{self.plan_counter}"
        
        logger.info(f"[RemediationPlanner] Generating plan {plan_id}")
        
        # Extract failure context
        verdict_type = verdict.get('verdict', 'UNKNOWN')
        ece_estimate = verdict.get('ece_estimate', 0.0)
        benchmark_results = verdict.get('inputs', {}).get('benchmark_results', {})
        
        # Analyze failure type
        if verdict_type in ['REJECT', 'HARD_FAIL']:
            failure_reason = "Performance regression or constitutional violation"
        elif 'ROLLBACK' in verdict.get('actions', []):
            failure_reason = "Failed deployment requiring rollback"
        else:
            failure_reason = "Unknown failure"
        
        # Generate plan (stub)
        plan = {
            "plan_id": plan_id,
            "timestamp": datetime.now().isoformat(),
            "target": f"gen-{verdict.get('inputs', {}).get('generation', 'unknown')}",
            "failure_reason": failure_reason,
            "actions": [
                {
                    "type": "patch",
                    "target": "service://governance-orchestrator",
                    "description": "Tighten ECE gate threshold to reduce false positives",
                    "risk": "low",
                    "patch_content": "# ECE threshold tightened to 0.08\nECE_THRESHOLD = 0.08"
                },
                {
                    "type": "config_update",
                    "target": "dgm_config.yaml",
                    "description": "Add conservative mutation rate",
                    "risk": "low",
                    "config_changes": {"mutation_rate": 0.05}
                }
            ],
            "risk_level": "low",
            "confidence": 0.74,
            "estimated_success_rate": 0.82
        }
        
        logger.info(f"[RemediationPlanner] Generated plan with {len(plan['actions'])} actions")
        return plan


class CanaryValidator:
    """
    Runs canary validation for remediation plans.
    """
    
    def __init__(self):
        self.sandbox_dir = Path("sandbox")
        self.sandbox_dir.mkdir(exist_ok=True)
        
    def apply_to_sandbox(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply remediation plan to sandbox environment.
        
        Args:
            plan: Remediation plan
            
        Returns:
            Sandbox info dict
        """
        logger.info(f"[CanaryValidator] Applying plan {plan['plan_id']} to sandbox")
        
        # Write plan artifacts to sandbox
        plan_file = self.sandbox_dir / f"{plan['plan_id']}.json"
        with open(plan_file, 'w') as f:
            json.dump(plan, f, indent=2)
        
        # In production, this would:
        # - Apply patches to isolated environment
        # - Update config files
        # - Deploy to canary infrastructure
        
        return {
            "sandbox_path": str(self.sandbox_dir),
            "plan_file": str(plan_file),
            "status": "applied"
        }
    
    def run_canary(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run canary validation on remediation.
        
        Args:
            plan: Remediation plan
            
        Returns:
            Canary result dict with decision
        """
        logger.info(f"[CanaryValidator] Running canary for plan {plan['plan_id']}")
        
        # Simulate canary window
        time.sleep(1.0)
        
        # In production, this would:
        # - Call scripts/gov_canary_decider.py
        # - Monitor ECE/entropy on canary traffic
        # - Compare against baseline
        
        # Stub: 80% success rate
        import random
        success = random.random() < 0.80
        
        if success:
            decision = "PROMOTE"
            ece_post = 0.045
            samples = 250
        else:
            decision = "ROLLBACK"
            ece_post = 0.092
            samples = 150
        
        result = {
            "plan_id": plan["plan_id"],
            "decision": decision,
            "ece_post": ece_post,
            "samples": samples,
            "timestamp": datetime.now().isoformat()
        }
        
        logger.info(f"[CanaryValidator] Canary decision: {decision} (ECE={ece_post:.3f})")
        return result


class RemediatorService:
    """
    Main remediation service that orchestrates the full loop.
    """
    
    def __init__(self):
        self.planner = RemediationPlanner()
        self.validator = CanaryValidator()
        
    def handle_remediation_request(self, msg: Dict[str, Any]) -> None:
        """
        Handle remediation request event.
        
        Args:
            msg: Event message with verdict and failure info
        """
        task_id = msg.get("task_id", "unknown")
        logger.info(f"[Remediator] Handling remediation request for task {task_id}")
        
        _metrics["remediations_requested"] += 1
        
        try:
            # Publish start event
            publish("exec.remediation.started", {
                "topic": "exec.remediation.started",
                "task_id": task_id,
                "timestamp": datetime.now().isoformat()
            })
            _metrics["remediations_started"] += 1
            
            # Step 1: Generate remediation plan
            plan = self.planner.generate_plan(msg.get("inputs", {}))
            
            # Step 2: Apply to sandbox
            sandbox_info = self.validator.apply_to_sandbox(plan)
            
            # Step 3: Run canary validation
            canary_result = self.validator.run_canary(plan)
            
            # Step 4: Publish completion event
            decision = canary_result["decision"]
            publish("exec.remediation.completed", {
                "topic": "exec.remediation.completed",
                "task_id": task_id,
                "plan_id": plan["plan_id"],
                "decision": decision,
                "ece_post": canary_result["ece_post"],
                "samples": canary_result["samples"],
                "timestamp": datetime.now().isoformat()
            })
            _metrics["remediations_completed"] += 1
            
            # Step 5: Notify canary system of decision
            publish("release.canary.window_result", {
                "topic": "release.canary.window_result",
                "decision": decision,
                "source": "remediator",
                "task_id": task_id,
                "plan_id": plan["plan_id"],
                "samples": canary_result["samples"],
                "ece_post": canary_result["ece_post"],
                "timestamp": datetime.now().isoformat()
            })
            
            # Update metrics
            if decision == "PROMOTE":
                _metrics["remediations_promoted"] += 1
                logger.info(f"✓ Remediation {plan['plan_id']} PROMOTED")
            elif decision == "ROLLBACK":
                _metrics["remediations_rolled_back"] += 1
                logger.warning(f"✗ Remediation {plan['plan_id']} ROLLED BACK")
            
        except Exception as e:
            logger.error(f"[Remediator] Error handling remediation: {e}", exc_info=True)
            _metrics["remediations_failed"] += 1
            
            # Publish failure event
            publish("exec.remediation.failed", {
                "topic": "exec.remediation.failed",
                "task_id": task_id,
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })


class RemediatorHTTPHandler(BaseHTTPRequestHandler):
    """HTTP handler for health and metrics endpoints."""
    
    def log_message(self, format, *args):
        """Suppress default request logging."""
        pass
    
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"OK")
            
        elif self.path == "/metrics":
            # Prometheus metrics format
            metrics_text = []
            metrics_text.append("# HELP governance_remediations_requested_total Total remediation requests")
            metrics_text.append("# TYPE governance_remediations_requested_total counter")
            metrics_text.append(f"governance_remediations_requested_total {_metrics['remediations_requested']}")
            
            metrics_text.append("# HELP governance_remediations_started_total Total remediations started")
            metrics_text.append("# TYPE governance_remediations_started_total counter")
            metrics_text.append(f"governance_remediations_started_total {_metrics['remediations_started']}")
            
            metrics_text.append("# HELP governance_remediations_completed_total Total remediations completed")
            metrics_text.append("# TYPE governance_remediations_completed_total counter")
            metrics_text.append(f"governance_remediations_completed_total {_metrics['remediations_completed']}")
            
            metrics_text.append("# HELP governance_remediations_promoted_total Total remediations promoted")
            metrics_text.append("# TYPE governance_remediations_promoted_total counter")
            metrics_text.append(f"governance_remediations_promoted_total {_metrics['remediations_promoted']}")
            
            metrics_text.append("# HELP governance_remediations_rolled_back_total Total remediations rolled back")
            metrics_text.append("# TYPE governance_remediations_rolled_back_total counter")
            metrics_text.append(f"governance_remediations_rolled_back_total {_metrics['remediations_rolled_back']}")
            
            metrics_text.append("# HELP governance_remediations_failed_total Total remediation failures")
            metrics_text.append("# TYPE governance_remediations_failed_total counter")
            metrics_text.append(f"governance_remediations_failed_total {_metrics['remediations_failed']}")
            
            output = "\n".join(metrics_text) + "\n"
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            self.wfile.write(output.encode())
            
        else:
            self.send_response(404)
            self.end_headers()


def run_http_server(port: int = 9112):
    """Run HTTP server for health and metrics."""
    server = HTTPServer(("0.0.0.0", port), RemediatorHTTPHandler)
    logger.info(f"[Remediator] HTTP server listening on port {port}")
    server.serve_forever()


def main():
    """Main entry point."""
    logger.info("=== AGI Core Auto-Remediator Starting ===")
    logger.info(f"Event Bus: {os.getenv('EVENT_BUS', 'local')}")
    
    # Initialize service
    remediator = RemediatorService()
    
    # Subscribe to remediation requests
    subscribe("exec.remediation.requested", remediator.handle_remediation_request)
    logger.info("Subscribed to exec.remediation.requested")
    
    # Start HTTP server in main thread
    port = int(os.getenv("REMEDIATOR_PORT", "9112"))
    run_http_server(port)


if __name__ == "__main__":
    main()

