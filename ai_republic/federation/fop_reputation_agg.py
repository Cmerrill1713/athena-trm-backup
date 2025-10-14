#!/usr/bin/env python3
"""
FOP Reputation Aggregation Engine
Federated reputation scoring for AI Republic jurisdictions.

This module aggregates reputation events across the federation,
calculating trust tiers based on behavior patterns and peer assessments.
"""

import json
import hashlib
import time
from typing import Dict, Any, List, Optional
from collections import defaultdict
import yaml

# Load configuration
try:
    with open('/etc/ai-republic/federation.yaml', 'r') as f:
        CONFIG = yaml.safe_load(f)
except FileNotFoundError:
    # Default configuration
    CONFIG = {
        'reputation': {
            'weights': {
                "clean_audit_window": 0.02,
                "evidence_publish_quality": 0.01,
                "timely_disclosure": 0.02,
                "tribunal_overturn": -0.03,
                "hidden_incident_discovered": -0.10,
                "peer_endorse": 0.03,
                "peer_flag": -0.05
            },
            'base_score': 0.0,
            'max_score': 1.0,
            'min_score': -1.0,
            'decay_rate': 0.001,
            'tiers': {
                'SOVEREIGN': {'min_rep': 0.60},
                'TRUSTED': {'min_rep': 0.30},
                'PROVISIONAL': {'min_rep': -0.10},
                'QUARANTINED': {'max_rep': -0.50}
            }
        }
    }

# Event weight mappings (can be overridden by config)
WEIGHTS = CONFIG['reputation']['weights']

def sha256(data: Any) -> str:
    """Generate SHA-256 hash of data"""
    if isinstance(data, (dict, list)):
        data = json.dumps(data, sort_keys=True)
    elif not isinstance(data, str):
        data = str(data)
    return hashlib.sha256(data.encode()).hexdigest()

def get_event_weight(event_type: str) -> float:
    """Get weight for event type"""
    return WEIGHTS.get(event_type, 0.0)

def calculate_reputation_decay(base_score: float, last_update: float,
                             current_time: Optional[float] = None) -> float:
    """
    Apply time-based reputation decay toward neutral score.

    Args:
        base_score: Current reputation score
        last_update: Timestamp of last reputation update
        current_time: Current timestamp (defaults to now)

    Returns:
        Decayed reputation score
    """
    if current_time is None:
        current_time = time.time()

    hours_since_update = (current_time - last_update) / 3600
    decay_rate_per_hour = CONFIG['reputation']['decay_rate']

    # Exponential decay toward neutral (0.0)
    decay_factor = decay_rate_per_hour * hours_since_update
    decayed_score = base_score * (1 - decay_factor)

    # Clamp to bounds
    return max(CONFIG['reputation']['min_score'],
               min(CONFIG['reputation']['max_score'], decayed_score))

def apply_events(base_score: float, events: List[Dict[str, Any]],
                current_time: Optional[float] = None) -> Dict[str, Any]:
    """
    Apply reputation events to calculate new score.

    Args:
        base_score: Starting reputation score
        events: List of reputation events
        current_time: Current timestamp for decay calculation

    Returns:
        Dict with new score, applied events, and metadata
    """
    if current_time is None:
        current_time = time.time()

    score = base_score
    applied_events = []
    event_counts = defaultdict(int)

    # Apply events in chronological order
    sorted_events = sorted(events, key=lambda x: x.get('timestamp', 0))

    for event in sorted_events:
        event_type = event.get('type', 'unknown')
        weight = get_event_weight(event_type)

        if weight != 0.0:
            old_score = score
            score += weight

            # Clamp to bounds
            score = max(CONFIG['reputation']['min_score'],
                       min(CONFIG['reputation']['max_score'], score))

            applied_events.append({
                'event_type': event_type,
                'weight': weight,
                'old_score': old_score,
                'new_score': score,
                'timestamp': event.get('timestamp', current_time)
            })

            event_counts[event_type] += 1

    # Apply decay if we have events
    if applied_events:
        last_event_time = applied_events[-1]['timestamp']
        score = calculate_reputation_decay(score, last_event_time, current_time)

    return {
        'final_score': round(score, 4),
        'applied_events': applied_events,
        'event_counts': dict(event_counts),
        'decay_applied': bool(applied_events),
        'calculation_time': current_time
    }

def aggregate_period_events(period_events: List[Dict[str, Any]],
                          jurisdiction_reputations: Optional[Dict[str, float]] = None,
                          current_time: Optional[float] = None) -> Dict[str, Dict[str, Any]]:
    """
    Aggregate reputation events for a time period across all jurisdictions.

    Args:
        period_events: List of reputation events for the period
        jurisdiction_reputations: Current reputation scores (DID -> score)
        current_time: Current timestamp

    Returns:
        Dict mapping DID to reputation calculation results
    """
    if current_time is None:
        current_time = time.time()

    if jurisdiction_reputations is None:
        jurisdiction_reputations = {}

    # Group events by jurisdiction
    jurisdiction_events = defaultdict(list)
    for event in period_events:
        did = event.get('did', 'unknown')
        jurisdiction_events[did].append(event)

    # Calculate reputation for each jurisdiction
    results = {}
    for did, events in jurisdiction_events.items():
        base_score = jurisdiction_reputations.get(did, CONFIG['reputation']['base_score'])
        calculation = apply_events(base_score, events, current_time)
        results[did] = calculation

    return results

def get_reputation_tier(score: float) -> str:
    """Determine reputation tier based on score"""
    tiers = CONFIG['reputation']['tiers']

    if score >= tiers['SOVEREIGN']['min_rep']:
        return 'SOVEREIGN'
    elif score >= tiers['TRUSTED']['min_rep']:
        return 'TRUSTED'
    elif score >= tiers['PROVISIONAL']['min_rep']:
        return 'PROVISIONAL'
    else:
        return 'QUARANTINED'

def validate_reputation_calculation(did: str, events: List[Dict[str, Any]],
                                  expected_score: float, tolerance: float = 0.01) -> Dict[str, Any]:
    """
    Validate reputation calculation for auditing purposes.

    Args:
        did: Jurisdiction DID
        events: Reputation events
        expected_score: Expected final score
        tolerance: Acceptable calculation tolerance

    Returns:
        Validation results
    """
    calculation = apply_events(CONFIG['reputation']['base_score'], events)

    actual_score = calculation['final_score']
    difference = abs(actual_score - expected_score)

    return {
        'did': did,
        'expected_score': expected_score,
        'actual_score': actual_score,
        'difference': difference,
        'within_tolerance': difference <= tolerance,
        'calculation_details': calculation,
        'validation_timestamp': time.time()
    }

def export_reputation_snapshot(reputations: Dict[str, float],
                             metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Export reputation snapshot for federation sharing.

    Args:
        reputations: Current reputation scores (DID -> score)
        metadata: Optional metadata for the snapshot

    Returns:
        Privacy-preserving reputation snapshot
    """
    if metadata is None:
        metadata = {}

    # Group by tiers (k-anonymity for privacy)
    tier_groups = defaultdict(list)
    for did, score in reputations.items():
        tier = get_reputation_tier(score)
        # Store anonymized representation
        tier_groups[tier].append({
            'score_bucket': round(score * 10) / 10,  # Round to 1 decimal
            'anonymized_id': sha256(did)[:16]  # Truncated hash for privacy
        })

    return {
        'snapshot_timestamp': time.time(),
        'tier_distribution': {
            tier: len(scores) for tier, scores in tier_groups.items()
        },
        'tier_details': dict(tier_groups),  # For federation analysis
        'total_jurisdictions': len(reputations),
        'metadata': metadata
    }

class ReputationEngine:
    """Main reputation aggregation engine"""

    def __init__(self):
        self.current_reputations = {}
        self.event_history = []
        self.last_calculation = 0

    def load_state(self, reputation_file: str = '/var/lib/ai-republic/reputation_state.json'):
        """Load reputation state from file"""
        try:
            with open(reputation_file, 'r') as f:
                state = json.load(f)
                self.current_reputations = state.get('reputations', {})
                self.event_history = state.get('event_history', [])
                self.last_calculation = state.get('last_calculation', 0)
        except FileNotFoundError:
            # Initialize empty state
            pass

    def save_state(self, reputation_file: str = '/var/lib/ai-republic/reputation_state.json'):
        """Save reputation state to file"""
        state = {
            'reputations': self.current_reputations,
            'event_history': self.event_history[-1000:],  # Keep last 1000 events
            'last_calculation': self.last_calculation
        }
        with open(reputation_file, 'w') as f:
            json.dump(state, f, indent=2)

    def process_events(self, events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Process batch of reputation events"""
        results = aggregate_period_events(events, self.current_reputations)

        # Update current reputations
        for did, calculation in results.items():
            self.current_reputations[did] = calculation['final_score']

        # Add to history
        self.event_history.extend(events)
        self.last_calculation = time.time()

        # Auto-save state
        self.save_state()

        return results

    def get_jurisdiction_status(self, did: str) -> Dict[str, Any]:
        """Get full status for a jurisdiction"""
        score = self.current_reputations.get(did, CONFIG['reputation']['base_score'])
        tier = get_reputation_tier(score)

        return {
            'did': did,
            'reputation_score': score,
            'tier': tier,
            'tier_requirements': CONFIG['reputation']['tiers'].get(tier, {}),
            'last_updated': self.last_calculation,
            'event_count': len([e for e in self.event_history if e.get('did') == did])
        }

    def get_federation_overview(self) -> Dict[str, Any]:
        """Get federation-wide reputation overview"""
        tier_counts = defaultdict(int)
        total_score = 0

        for did, score in self.current_reputations.items():
            tier = get_reputation_tier(score)
            tier_counts[tier] += 1
            total_score += score

        return {
            'total_jurisdictions': len(self.current_reputations),
            'tier_distribution': dict(tier_counts),
            'average_reputation': total_score / max(1, len(self.current_reputations)),
            'last_updated': self.last_calculation,
            'total_events_processed': len(self.event_history)
        }

if __name__ == "__main__":
    # Demo usage
    demo_events = [
        {"did": "did:airep:X", "type": "clean_audit_window", "timestamp": time.time()},
        {"did": "did:airep:X", "type": "peer_endorse", "timestamp": time.time()},
        {"did": "did:airep:Y", "type": "hidden_incident_discovered", "timestamp": time.time()}
    ]

    results = aggregate_period_events(demo_events)
    print("Reputation aggregation results:")
    for did, calc in results.items():
        tier = get_reputation_tier(calc['final_score'])
        print(f"  {did}: {calc['final_score']:.3f} ({tier})")

    # Engine demo
    engine = ReputationEngine()
    engine.process_events(demo_events)

    print("\nFederation overview:")
    overview = engine.get_federation_overview()
    print(json.dumps(overview, indent=2))
