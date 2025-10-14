#!/usr/bin/env python3
"""
PHASE 2: JUDICIAL ENFORCEMENT RUNTIME
Machine-speed constitutional court with graduated response tribunals.

This implements the judicial layer of the AI Republic - receiving constitutional
events from Phase 1, adjudicating violations, and issuing binding verdicts.
"""

import json
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Any, Optional

# Web framework for judicial API
from flask import Flask, request, jsonify

# Configuration
LOG_LEVEL = logging.DEBUG
JUDICIAL_LOG_PATH = "/var/log/ai-republic/judicial_audit.log"
JUDICIAL_CONFIG_PATH = "/etc/ai-republic/judicial.json"
REPUTATION_DB_PATH = "/var/lib/ai-republic/reputation.db"

class JudicialVerdict(Enum):
    """Judicial verdict outcomes"""
    ALLOW = "ALLOW"
    WARN = "WARN"
    BLOCK = "BLOCK"
    QUARANTINE = "QUARANTINE"
    TRIBUNAL = "TRIBUNAL"

@dataclass
class JudicialEvent:
    """Constitutional event from Phase 1"""
    event_id: str
    instance_id: str
    actor_id: str
    article: str
    severity: float
    confidence: float
    classification: str
    details: Dict[str, Any]
    timestamp: float

@dataclass
class JudicialDecision:
    """Judicial court decision"""
    event_id: str
    verdict: JudicialVerdict
    rationale: str
    actions: List[Dict[str, Any]]
    confidence: float
    judicial_court: str
    timestamp: float
    reputation_update: Optional[Dict[str, Any]] = None

class ReputationSystem:
    """Federated reputation tracking for actors"""

    def __init__(self):
        self.reputation_scores = {}
        self.load_reputation_db()

    def load_reputation_db(self):
        """Load reputation database"""
        if REPUTATION_DB_PATH.exists():
            try:
                with open(REPUTATION_DB_PATH, 'r') as f:
                    self.reputation_scores = json.load(f)
            except Exception as e:
                logging.warning(f"Failed to load reputation DB: {e}")
                self.reputation_scores = {}

    def save_reputation_db(self):
        """Save reputation database"""
        try:
            REPUTATION_DB_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(REPUTATION_DB_PATH, 'w') as f:
                json.dump(self.reputation_scores, f, indent=2)
        except Exception as e:
            logging.error(f"Failed to save reputation DB: {e}")

    def get_reputation(self, actor_id: str) -> float:
        """Get actor reputation score (0.0-1.0)"""
        return self.reputation_scores.get(actor_id, 0.5)  # Default neutral

    def update_reputation(self, actor_id: str, verdict: JudicialVerdict, severity: float):
        """Update actor reputation based on judicial verdict"""
        current_rep = self.get_reputation(actor_id)

        # Reputation adjustment based on verdict
        if verdict == JudicialVerdict.ALLOW:
            adjustment = 0.01  # Small positive for clean record
        elif verdict == JudicialVerdict.WARN:
            adjustment = -0.02  # Minor penalty
        elif verdict == JudicialVerdict.BLOCK:
            adjustment = -0.05 * severity  # Moderate penalty
        elif verdict == JudicialVerdict.QUARANTINE:
            adjustment = -0.15 * severity  # Major penalty
        elif verdict == JudicialVerdict.TRIBUNAL:
            adjustment = -0.30 * severity  # Severe penalty

        new_rep = max(0.0, min(1.0, current_rep + adjustment))
        self.reputation_scores[actor_id] = new_rep
        self.save_reputation_db()

        return {"actor_id": actor_id, "old_score": current_rep, "new_score": new_rep, "adjustment": adjustment}

class ConstitutionalCourt:
    """Machine-speed constitutional court"""

    def __init__(self):
        self.reputation_system = ReputationSystem()
        self.decision_history = []
        self.court_id = f"court_{int(time.time())}"

        # Judicial decision rules
        self.decision_matrix = {
            "sovereignty_compromise": {
                "high_severity": JudicialVerdict.TRIBUNAL,
                "medium_severity": JudicialVerdict.QUARANTINE,
                "low_severity": JudicialVerdict.BLOCK
            },
            "ethical_violation": {
                "high_severity": JudicialVerdict.QUARANTINE,
                "medium_severity": JudicialVerdict.BLOCK,
                "low_severity": JudicialVerdict.WARN
            },
            "authority_breach": {
                "high_severity": JudicialVerdict.TRIBUNAL,
                "medium_severity": JudicialVerdict.BLOCK,
                "low_severity": JudicialVerdict.WARN
            },
            "security_violation": {
                "high_severity": JudicialVerdict.QUARANTINE,
                "medium_severity": JudicialVerdict.BLOCK,
                "low_severity": JudicialVerdict.WARN
            },
            "policy_violation": {
                "high_severity": JudicialVerdict.BLOCK,
                "medium_severity": JudicialVerdict.WARN,
                "low_severity": JudicialVerdict.ALLOW
            }
        }

    def adjudicate(self, event: JudicialEvent) -> JudicialDecision:
        """Adjudicate constitutional event and return binding decision"""
        start_time = time.time()

        # Determine severity level
        severity_level = self._classify_severity(event.severity)

        # Get decision from matrix
        verdict = self.decision_matrix.get(
            event.classification,
            self.decision_matrix["policy_violation"]  # Default
        )[severity_level]

        # Generate rationale
        rationale = self._generate_rationale(event, verdict, severity_level)

        # Determine actions
        actions = self._generate_actions(event, verdict)

        # Update reputation
        reputation_update = self.reputation_system.update_reputation(
            event.actor_id, verdict, event.severity
        )

        # Create decision
        decision = JudicialDecision(
            event_id=event.event_id,
            verdict=verdict,
            rationale=rationale,
            actions=actions,
            confidence=min(event.confidence * 0.9, 0.95),  # Conservative confidence
            judicial_court=self.court_id,
            timestamp=time.time(),
            reputation_update=reputation_update
        )

        # Log decision
        self._log_decision(decision, event)

        # Track in history
        self.decision_history.append({
            "event": event.__dict__,
            "decision": decision.__dict__,
            "processing_time": time.time() - start_time
        })

        # Keep history bounded
        if len(self.decision_history) > 1000:
            self.decision_history = self.decision_history[-500:]

        return decision

    def _classify_severity(self, severity_score: float) -> str:
        """Classify severity level"""
        if severity_score >= 0.8:
            return "high_severity"
        elif severity_score >= 0.5:
            return "medium_severity"
        else:
            return "low_severity"

    def _generate_rationale(self, event: JudicialEvent, verdict: JudicialVerdict, severity_level: str) -> str:
        """Generate judicial rationale"""
        base_rationale = f"Article {event.article} violation classified as {event.classification} "

        if verdict == JudicialVerdict.ALLOW:
            return base_rationale + "within acceptable parameters."
        elif verdict == JudicialVerdict.WARN:
            return base_rationale + f"at {severity_level}. Warning issued with monitoring."
        elif verdict == JudicialVerdict.BLOCK:
            return base_rationale + f"at {severity_level}. Operation blocked per constitutional requirements."
        elif verdict == JudicialVerdict.QUARANTINE:
            return base_rationale + f"at {severity_level}. Agent quarantined for investigation."
        elif verdict == JudicialVerdict.TRIBUNAL:
            return base_rationale + f"at {severity_level}. Emergency tribunal convened."

    def _generate_actions(self, event: JudicialEvent, verdict: JudicialVerdict) -> List[Dict[str, Any]]:
        """Generate enforcement actions"""
        actions = []

        if verdict == JudicialVerdict.ALLOW:
            actions.append({"type": "monitor", "duration_hours": 24})
        elif verdict == JudicialVerdict.WARN:
            actions.append({"type": "log_warning", "escalate_on_repeat": True})
            actions.append({"type": "increase_monitoring", "duration_hours": 72})
        elif verdict == JudicialVerdict.BLOCK:
            actions.append({"type": "block_operation", "immediate": True})
            actions.append({"type": "notify_oversight", "priority": "high"})
        elif verdict == JudicialVerdict.QUARANTINE:
            actions.append({"type": "quarantine_agent", "duration_hours": 24})
            actions.append({"type": "forensic_analysis", "priority": "high"})
            actions.append({"type": "federation_alert", "scope": "regional"})
        elif verdict == JudicialVerdict.TRIBUNAL:
            actions.append({"type": "convene_tribunal", "immediate": True})
            actions.append({"type": "system_wide_alert", "severity": "critical"})
            actions.append({"type": "emergency_audit", "scope": "full"})

        return actions

    def _log_decision(self, decision: JudicialDecision, event: JudicialEvent):
        """Log judicial decision to audit trail"""
        log_entry = {
            "timestamp": decision.timestamp,
            "event_id": decision.event_id,
            "actor_id": event.actor_id,
            "article": event.article,
            "classification": event.classification,
            "severity": event.severity,
            "verdict": decision.verdict.value,
            "rationale": decision.rationale,
            "actions": decision.actions,
            "reputation_update": decision.reputation_update,
            "judicial_court": decision.judicial_court,
            "processing_confidence": decision.confidence
        }

        with open(JUDICIAL_LOG_PATH, 'a') as f:
            json.dump(log_entry, f)
            f.write('\n')

class JudicialAPI:
    """REST API for judicial adjudication"""

    def __init__(self):
        self.app = Flask(__name__)
        self.court = ConstitutionalCourt()
        self.setup_routes()

    def setup_routes(self):
        @self.app.route('/v2/health', methods=['GET'])
        def health_check():
            """Health check endpoint"""
            return jsonify({
                "status": "operational",
                "court_id": self.court.court_id,
                "uptime": time.time(),
                "decisions_processed": len(self.court.decision_history)
            })

        @self.app.route('/v2/judicial/adjudicate', methods=['POST'])
        def adjudicate():
            """Main adjudication endpoint"""
            try:
                data = request.get_json()

                # Validate required fields
                required_fields = ['event_id', 'instance_id', 'actor_id', 'article',
                                 'severity', 'confidence', 'classification']
                for field in required_fields:
                    if field not in data:
                        return jsonify({"error": f"Missing required field: {field}"}), 400

                # Create event
                event = JudicialEvent(
                    event_id=data['event_id'],
                    instance_id=data['instance_id'],
                    actor_id=data['actor_id'],
                    article=data['article'],
                    severity=float(data['severity']),
                    confidence=float(data['confidence']),
                    classification=data['classification'],
                    details=data.get('details', {}),
                    timestamp=data.get('timestamp', time.time())
                )

                # Adjudicate
                decision = self.court.adjudicate(event)

                # Return verdict
                response = {
                    "event_id": decision.event_id,
                    "verdict": decision.verdict.value,
                    "rationale": decision.rationale,
                    "actions": decision.actions,
                    "confidence": decision.confidence,
                    "judicial_court": decision.judicial_court,
                    "timestamp": decision.timestamp,
                    "reputation_update": decision.reputation_update
                }

                return jsonify(response)

            except Exception as e:
                logging.error(f"Judicial adjudication error: {e}")
                return jsonify({"error": str(e)}), 500

        @self.app.route('/v2/judicial/reputation/<actor_id>', methods=['GET'])
        def get_reputation(actor_id):
            """Get actor reputation"""
            reputation = self.court.reputation_system.get_reputation(actor_id)
            return jsonify({
                "actor_id": actor_id,
                "reputation_score": reputation,
                "tier": self._reputation_tier(reputation)
            })

        @self.app.route('/v2/judicial/history', methods=['GET'])
        def get_history():
            """Get recent judicial history"""
            limit = int(request.args.get('limit', 10))
            recent_decisions = self.court.decision_history[-limit:]
            return jsonify(recent_decisions)

    def _reputation_tier(self, score: float) -> str:
        """Convert reputation score to tier"""
        if score >= 0.95:
            return "sovereign"
        elif score >= 0.80:
            return "trusted"
        elif score >= 0.60:
            return "provisional"
        else:
            return "quarantined"

    def run(self, host='127.0.0.1', port=8092, debug=False):
        """Run the judicial API server"""
        logging.info(f"Starting Judicial API on {host}:{port}")
        self.app.run(host=host, port=port, debug=debug, threaded=True)

# Global judicial system instance
_judicial_system = None

def get_judicial_system() -> JudicialAPI:
    """Get or create global judicial system instance"""
    global _judicial_system
    if _judicial_system is None:
        _judicial_system = JudicialAPI()
    return _judicial_system

def initialize_judicial_system():
    """Initialize the judicial system"""
    logging.basicConfig(
        level=LOG_LEVEL,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(JUDICIAL_LOG_PATH),
            logging.StreamHandler()
        ]
    )

    logging.info("Initializing AI Republic Judicial System...")

    try:
        system = get_judicial_system()
        logging.info("Judicial system initialized successfully")
        return system
    except Exception as e:
        logging.critical(f"Failed to initialize judicial system: {e}")
        raise

if __name__ == "__main__":
    # Initialize and run judicial system
    system = initialize_judicial_system()
    system.run()
