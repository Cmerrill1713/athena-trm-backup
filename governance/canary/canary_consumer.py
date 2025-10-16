#!/usr/bin/env python3
"""
Canary Decision Consumer
Listens to canary window results and executes promote/rollback actions.
Integrates with auto-remediation system.
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

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

# State tracking
STATE_DIR = Path("state/canary")
STATE_DIR.mkdir(parents=True, exist_ok=True)


class CanaryActionExecutor:
    """
    Executes canary deployment actions (promote/rollback/hold).
    """
    
    def __init__(self):
        self.state_file = STATE_DIR / "canary_state.json"
        self.action_log = STATE_DIR / "canary_actions.jsonl"
        
    def load_state(self) -> Dict[str, Any]:
        """Load current canary state."""
        if self.state_file.exists():
            with open(self.state_file, 'r') as f:
                return json.load(f)
        return {
            "current_model": "baseline",
            "canary_model": None,
            "last_action": None,
            "last_action_time": None
        }
    
    def save_state(self, state: Dict[str, Any]) -> None:
        """Save canary state."""
        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def log_action(self, action: str, details: Dict[str, Any]) -> None:
        """Append action to audit log."""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "action": action,
            **details
        }
        with open(self.action_log, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def do_promote(self, decision_msg: Dict[str, Any]) -> None:
        """
        Execute canary promotion.
        
        In production, this would:
        - Update routing configuration
        - Swap traffic weights (100% → new model)
        - Archive old model
        - Notify ChatOps
        """
        logger.info("=== EXECUTING PROMOTE ===")
        
        state = self.load_state()
        old_model = state.get("current_model", "unknown")
        new_model = state.get("canary_model", "canary")
        
        logger.info(f"Promoting: {new_model} (was canary)")
        logger.info(f"Deprecating: {old_model} (was control)")
        
        # Update state
        state["current_model"] = new_model
        state["canary_model"] = None
        state["last_action"] = "PROMOTE"
        state["last_action_time"] = datetime.now().isoformat()
        state["promotion_details"] = {
            "ece_post": decision_msg.get("ece_post"),
            "samples": decision_msg.get("samples"),
            "source": decision_msg.get("source"),
            "plan_id": decision_msg.get("plan_id")
        }
        self.save_state(state)
        
        # Log action
        self.log_action("PROMOTE", {
            "from_model": old_model,
            "to_model": new_model,
            "ece_post": decision_msg.get("ece_post"),
            "samples": decision_msg.get("samples"),
            "task_id": decision_msg.get("task_id")
        })
        
        # Publish promotion event
        publish("release.promoted", {
            "topic": "release.promoted",
            "from_model": old_model,
            "to_model": new_model,
            "timestamp": datetime.now().isoformat(),
            "ece_post": decision_msg.get("ece_post")
        })
        
        logger.info(f"✓ Promotion complete: {new_model} is now live")
    
    def do_rollback(self, decision_msg: Dict[str, Any]) -> None:
        """
        Execute canary rollback.
        
        In production, this would:
        - Revert routing to 100% control
        - Disable canary model
        - Preserve artifacts for analysis
        - Alert operators
        """
        logger.warning("=== EXECUTING ROLLBACK ===")
        
        state = self.load_state()
        current_model = state.get("current_model", "baseline")
        canary_model = state.get("canary_model", "canary")
        
        logger.warning(f"Rolling back: {canary_model} (failed canary)")
        logger.info(f"Keeping: {current_model} (current control)")
        
        # Update state
        state["canary_model"] = None
        state["last_action"] = "ROLLBACK"
        state["last_action_time"] = datetime.now().isoformat()
        state["rollback_details"] = {
            "ece_post": decision_msg.get("ece_post"),
            "samples": decision_msg.get("samples"),
            "source": decision_msg.get("source"),
            "plan_id": decision_msg.get("plan_id")
        }
        self.save_state(state)
        
        # Log action
        self.log_action("ROLLBACK", {
            "failed_model": canary_model,
            "kept_model": current_model,
            "ece_post": decision_msg.get("ece_post"),
            "samples": decision_msg.get("samples"),
            "task_id": decision_msg.get("task_id")
        })
        
        # Publish rollback event
        publish("release.rolled_back", {
            "topic": "release.rolled_back",
            "failed_model": canary_model,
            "kept_model": current_model,
            "timestamp": datetime.now().isoformat(),
            "ece_post": decision_msg.get("ece_post")
        })
        
        logger.warning(f"✓ Rollback complete: {current_model} remains live")
    
    def do_hold(self, decision_msg: Dict[str, Any]) -> None:
        """
        Hold canary deployment (inconclusive).
        
        Continue monitoring without action.
        """
        logger.info("=== HOLDING CANARY ===")
        logger.info("Inconclusive results - continue monitoring")
        
        self.log_action("HOLD", {
            "ece_post": decision_msg.get("ece_post"),
            "samples": decision_msg.get("samples"),
            "task_id": decision_msg.get("task_id")
        })


class CanaryConsumerService:
    """
    Main canary consumer service.
    Subscribes to window_result events and executes actions.
    """
    
    def __init__(self):
        self.executor = CanaryActionExecutor()
        
    def handle_window_result(self, msg: Dict[str, Any]) -> None:
        """
        Handle canary window result event.
        
        Args:
            msg: Event message with decision (PROMOTE/ROLLBACK/HOLD)
        """
        decision = msg.get("decision", "UNKNOWN")
        source = msg.get("source", "unknown")
        task_id = msg.get("task_id", "unknown")
        
        logger.info(f"[CanaryConsumer] Window result from {source}: {decision} (task={task_id})")
        
        try:
            if decision == "PROMOTE":
                self.executor.do_promote(msg)
            elif decision == "ROLLBACK":
                self.executor.do_rollback(msg)
            elif decision == "HOLD":
                self.executor.do_hold(msg)
            else:
                logger.warning(f"Unknown decision: {decision}")
                
        except Exception as e:
            logger.error(f"[CanaryConsumer] Error executing action: {e}", exc_info=True)


def main():
    """Main entry point."""
    logger.info("=== Canary Decision Consumer Starting ===")
    logger.info(f"Event Bus: {os.getenv('EVENT_BUS', 'local')}")
    
    # Initialize service
    consumer = CanaryConsumerService()
    
    # Subscribe to window results
    subscribe("release.canary.window_result", consumer.handle_window_result)
    logger.info("Subscribed to release.canary.window_result")
    
    # Keep service running
    logger.info("Canary consumer ready, waiting for events...")
    
    # In production, this would run as part of a larger service
    # For now, just keep the thread alive
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")


if __name__ == "__main__":
    main()

