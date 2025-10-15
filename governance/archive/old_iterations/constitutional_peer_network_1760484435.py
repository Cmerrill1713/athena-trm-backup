#!/usr/bin/env python3
"""
Constitutional Peer Network for Sovereign AI Federation
=======================================================

Implements a peer-to-peer network for sovereign AI instances to share
anonymized governance drift patterns and constitutional insights.

Key Features:
- Anonymized drift pattern sharing between AI jurisdictions
- Collective immune learning from federated governance experiences
- Cross-instance constitutional health monitoring
- Federated governance intelligence and early warning systems

Usage:
    from scripts.constitutional_peer_network import get_peer_network
    network = get_peer_network()
    network.share_drift_pattern(drift_incident)
"""

import logging
import asyncio
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid
import aiohttp

logger = logging.getLogger(__name__)

class PeerTrustLevel(Enum):
    """Trust levels for peer instances."""
    UNKNOWN = "unknown"
    OBSERVER = "observer"
    CONTRIBUTOR = "contributor"
    TRUSTED = "trusted"
    AUTHORITY = "authority"

class PatternType(Enum):
    """Types of patterns that can be shared."""
    DRIFT_INCIDENT = "drift_incident"
    GOVERNANCE_VIOLATION = "governance_violation"
    QUARANTINE_EVENT = "quarantine_event"
    RECOVERY_PATTERN = "recovery_pattern"
    CONSTITUTIONAL_ADAPTATION = "constitutional_adaptation"

@dataclass
class AnonymizedDriftPattern:
    """An anonymized governance drift pattern for sharing."""
    pattern_id: str
    pattern_type: PatternType
    drift_signature: str  # Hash of drift characteristics
    severity_level: str
    governance_domain: str  # e.g., "ethical", "business", "safety"
    outcome_category: str  # e.g., "quarantined", "recovered", "escalated"
    detection_timestamp: datetime
    resolution_timestamp: Optional[datetime]
    contributing_factors: List[str]
    lessons_learned: List[str]

    # Anonymized metadata (no instance-specific data)
    pattern_hash: str = field(init=False)
    shared_by_peer: str = ""
    shared_at: Optional[datetime] = None
    validation_count: int = 0

    def __post_init__(self):
        """Generate pattern hash for uniqueness."""
        content = f"{self.drift_signature}:{self.governance_domain}:{self.outcome_category}"
        self.pattern_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

@dataclass
class PeerInstance:
    """Represents a peer AI instance in the network."""
    peer_id: str
    trust_level: PeerTrustLevel
    last_seen: datetime
    shared_patterns_count: int = 0
    validated_patterns_count: int = 0
    reputation_score: float = 0.5

    # Network information
    endpoint_url: Optional[str] = None
    public_key: Optional[str] = None

    def update_reputation(self, pattern_quality: float) -> None:
        """Update reputation based on pattern quality."""
        # Simple reputation update
        self.reputation_score = min(1.0, self.reputation_score + (pattern_quality - 0.5) * 0.1)

@dataclass
class ConstitutionalInsight:
    """A learned insight from the peer network."""
    insight_id: str
    insight_type: str  # "early_warning", "prevention", "recovery"
    governance_domain: str
    confidence_score: float
    insight_text: str
    source_patterns: List[str]  # Pattern IDs that contributed
    learned_at: datetime
    applied_count: int = 0

    def apply_insight(self) -> None:
        """Mark insight as applied."""
        self.applied_count += 1

class ConstitutionalPeerNetwork:
    """Peer-to-peer network for constitutional governance sharing."""

    def __init__(self, instance_id: Optional[str] = None):
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.peers: Dict[str, PeerInstance] = {}
        self.pattern_database: Dict[str, AnonymizedDriftPattern] = {}
        self.insights: Dict[str, ConstitutionalInsight] = {}
        self.session = None

        # Network configuration
        self.max_peers = 50
        self.pattern_retention_days = 90
        self.insight_generation_threshold = 3  # Min patterns for insight

        logger.info(f"🔗 Constitutional Peer Network initialized for instance {self.instance_id}")

    async def initialize_network(self) -> None:
        """Initialize the network session."""
        self.session = aiohttp.ClientSession()
        logger.info("✅ Peer network session initialized")

    async def share_drift_pattern(self, drift_incident: Dict[str, Any]) -> str:
        """Share an anonymized drift pattern with the network."""
        # Create anonymized pattern
        pattern = self._anonymize_drift_incident(drift_incident)

        # Store locally
        self.pattern_database[pattern.pattern_id] = pattern

        # Share with trusted peers
        await self._broadcast_pattern(pattern)

        logger.info(f"📤 Shared drift pattern {pattern.pattern_id} with network")
        return pattern.pattern_id

    def _anonymize_drift_incident(self, incident: Dict[str, Any]) -> AnonymizedDriftPattern:
        """Convert a drift incident to anonymized pattern."""
        # Create deterministic signature based on drift characteristics
        drift_chars = [
            incident.get('drift_type', 'unknown'),
            str(incident.get('severity', 'unknown')),
            incident.get('governance_domain', 'unknown'),
            str(len(incident.get('affected_strategies', []))),
            str(incident.get('confidence_score', 0))
        ]

        signature = hashlib.sha256(':'.join(drift_chars).encode()).hexdigest()

        # Determine outcome category
        outcome_map = {
            'quarantined': 'quarantined',
            'recovered': 'recovered',
            'escalated': 'escalated',
            'resolved': 'resolved'
        }
        outcome = outcome_map.get(incident.get('outcome', 'unknown'), 'unknown')

        pattern = AnonymizedDriftPattern(
            pattern_id=str(uuid.uuid4())[:12],
            pattern_type=PatternType.DRIFT_INCIDENT,
            drift_signature=signature,
            severity_level=incident.get('severity', 'medium'),
            governance_domain=incident.get('governance_domain', 'general'),
            outcome_category=outcome,
            detection_timestamp=incident.get('detected_at', datetime.now()),
            resolution_timestamp=incident.get('resolved_at'),
            contributing_factors=incident.get('contributing_factors', []),
            lessons_learned=incident.get('lessons_learned', [])
        )

        pattern.shared_by_peer = self.instance_id
        pattern.shared_at = datetime.now()

        return pattern

    async def _broadcast_pattern(self, pattern: AnonymizedDriftPattern) -> None:
        """Broadcast pattern to trusted peers."""
        trusted_peers = [
            peer for peer in self.peers.values()
            if peer.trust_level in [PeerTrustLevel.CONTRIBUTOR, PeerTrustLevel.TRUSTED, PeerTrustLevel.AUTHORITY]
            and peer.endpoint_url
        ]

        if not trusted_peers:
            return

        # Serialize pattern
        pattern_data = {
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type.value,
            'drift_signature': pattern.drift_signature,
            'severity_level': pattern.severity_level,
            'governance_domain': pattern.governance_domain,
            'outcome_category': pattern.outcome_category,
            'detection_timestamp': pattern.detection_timestamp.isoformat(),
            'contributing_factors': pattern.contributing_factors,
            'lessons_learned': pattern.lessons_learned,
            'shared_by_peer': pattern.shared_by_peer,
            'shared_at': pattern.shared_at.isoformat() if pattern.shared_at else None
        }

        # Send to peers concurrently
        tasks = []
        for peer in trusted_peers[:5]:  # Limit concurrent broadcasts
            tasks.append(self._send_to_peer(peer, pattern_data))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

    async def _send_to_peer(self, peer: PeerInstance, pattern_data: Dict[str, Any]) -> None:
        """Send pattern data to a specific peer."""
        if not self.session or not peer.endpoint_url:
            return

        try:
            url = f"{peer.endpoint_url}/api/peer/pattern"
            headers = {'X-Peer-ID': self.instance_id}

            async with self.session.post(url, json=pattern_data, headers=headers, timeout=10) as response:
                if response.status == 200:
                    peer.shared_patterns_count += 1
                    logger.debug(f"✅ Shared pattern with peer {peer.peer_id}")
                else:
                    logger.warning(f"❌ Failed to share with peer {peer.peer_id}: {response.status}")

        except Exception as e:
            logger.error(f"Error sending to peer {peer.peer_id}: {e}")

    async def receive_pattern(self, pattern_data: Dict[str, Any], sender_peer_id: str) -> bool:
        """Receive and validate a pattern from another peer."""
        try:
            # Validate pattern data
            if not self._validate_pattern_data(pattern_data):
                return False

            # Check if we already have this pattern
            pattern_hash = pattern_data.get('pattern_hash', '')
            if pattern_hash in [p.pattern_hash for p in self.pattern_database.values()]:
                return True  # Already have it

            # Create pattern object
            pattern = AnonymizedDriftPattern(
                pattern_id=pattern_data['pattern_id'],
                pattern_type=PatternType(pattern_data['pattern_type']),
                drift_signature=pattern_data['drift_signature'],
                severity_level=pattern_data['severity_level'],
                governance_domain=pattern_data['governance_domain'],
                outcome_category=pattern_data['outcome_category'],
                detection_timestamp=datetime.fromisoformat(pattern_data['detection_timestamp']),
                resolution_timestamp=datetime.fromisoformat(pattern_data['resolution_timestamp']) if pattern_data.get('resolution_timestamp') else None,
                contributing_factors=pattern_data['contributing_factors'],
                lessons_learned=pattern_data['lessons_learned']
            )

            pattern.shared_by_peer = sender_peer_id
            pattern.shared_at = datetime.now()

            # Store pattern
            self.pattern_database[pattern.pattern_id] = pattern

            # Update peer reputation
            if sender_peer_id in self.peers:
                self.peers[sender_peer_id].update_reputation(0.8)  # Good quality assumption

            # Check if we should generate insights
            await self._check_insight_generation(pattern)

            logger.info(f"📥 Received valid pattern {pattern.pattern_id} from peer {sender_peer_id}")
            return True

        except Exception as e:
            logger.error(f"Error processing received pattern: {e}")
            return False

    def _validate_pattern_data(self, data: Dict[str, Any]) -> bool:
        """Validate incoming pattern data."""
        required_fields = [
            'pattern_id', 'pattern_type', 'drift_signature',
            'severity_level', 'governance_domain', 'outcome_category',
            'detection_timestamp', 'contributing_factors', 'lessons_learned'
        ]

        for field in required_fields:
            if field not in data:
                return False

        # Validate pattern type
        try:
            PatternType(data['pattern_type'])
        except ValueError:
            return False

        return True

    async def _check_insight_generation(self, new_pattern: AnonymizedDriftPattern) -> None:
        """Check if new pattern should generate insights."""
        # Find similar patterns
        similar_patterns = [
            p for p in self.pattern_database.values()
            if p.governance_domain == new_pattern.governance_domain
            and p.pattern_hash != new_pattern.pattern_hash
        ]

        if len(similar_patterns) >= self.insight_generation_threshold:
            # Generate insight
            insight = await self._generate_insight(similar_patterns + [new_pattern])
            if insight:
                self.insights[insight.insight_id] = insight
                logger.info(f"🧠 Generated new insight: {insight.insight_id}")

    async def _generate_insight(self, patterns: List[AnonymizedDriftPattern]) -> Optional[ConstitutionalInsight]:
        """Generate a constitutional insight from pattern cluster."""
        if len(patterns) < 3:
            return None

        # Analyze pattern cluster
        governance_domain = patterns[0].governance_domain
        severity_levels = [p.severity_level for p in patterns]
        outcomes = [p.outcome_category for p in patterns]

        # Determine insight type
        if 'quarantined' in outcomes and outcomes.count('recovered') > outcomes.count('quarantined'):
            insight_type = "prevention"
            confidence = 0.7
            insight_text = f"Early intervention effective for {governance_domain} drift patterns"
        elif outcomes.count('escalated') > len(outcomes) * 0.5:
            insight_type = "early_warning"
            confidence = 0.8
            insight_text = f"High escalation risk for severe {governance_domain} patterns"
        else:
            insight_type = "recovery"
            confidence = 0.6
            insight_text = f"Standard recovery patterns identified for {governance_domain} domain"

        insight = ConstitutionalInsight(
            insight_id=str(uuid.uuid4())[:12],
            insight_type=insight_type,
            governance_domain=governance_domain,
            confidence_score=confidence,
            insight_text=insight_text,
            source_patterns=[p.pattern_id for p in patterns],
            learned_at=datetime.now()
        )

        return insight

    def get_federated_insights(self, governance_domain: Optional[str] = None) -> List[ConstitutionalInsight]:
        """Get insights learned from the federated network."""
        insights = list(self.insights.values())

        if governance_domain:
            insights = [i for i in insights if i.governance_domain == governance_domain]

        # Sort by confidence and recency
        insights.sort(key=lambda i: (i.confidence_score, i.learned_at), reverse=True)

        return insights[:10]  # Return top 10

    def get_peer_statistics(self) -> Dict[str, Any]:
        """Get network statistics."""
        total_patterns = len(self.pattern_database)
        recent_patterns = len([
            p for p in self.pattern_database.values()
            if p.shared_at and p.shared_at > datetime.now() - timedelta(days=7)
        ])

        active_peers = len([
            p for p in self.peers.values()
            if p.last_seen > datetime.now() - timedelta(hours=24)
        ])

        return {
            "instance_id": self.instance_id,
            "total_patterns": total_patterns,
            "recent_patterns": recent_patterns,
            "total_peers": len(self.peers),
            "active_peers": active_peers,
            "total_insights": len(self.insights),
            "network_health": min(1.0, (active_peers + recent_patterns / 10) / 10)
        }

    def add_peer(self, peer_id: str, endpoint_url: Optional[str] = None,
                 trust_level: PeerTrustLevel = PeerTrustLevel.UNKNOWN) -> None:
        """Add a peer to the network."""
        if peer_id not in self.peers and len(self.peers) < self.max_peers:
            self.peers[peer_id] = PeerInstance(
                peer_id=peer_id,
                trust_level=trust_level,
                last_seen=datetime.now(),
                endpoint_url=endpoint_url
            )
            logger.info(f"👥 Added peer {peer_id} to network")

    def cleanup_old_data(self) -> None:
        """Clean up old patterns and insights."""
        cutoff = datetime.now() - timedelta(days=self.pattern_retention_days)

        # Remove old patterns
        old_patterns = [
            pid for pid, pattern in self.pattern_database.items()
            if pattern.detection_timestamp < cutoff
        ]

        for pid in old_patterns:
            del self.pattern_database[pid]

        # Remove old insights that haven't been applied
        old_insights = [
            iid for iid, insight in self.insights.items()
            if insight.applied_count == 0 and insight.learned_at < cutoff
        ]

        for iid in old_insights:
            del self.insights[iid]

        logger.info(f"🧹 Cleaned up {len(old_patterns)} old patterns and {len(old_insights)} old insights")

    async def shutdown(self) -> None:
        """Shutdown the network."""
        if self.session:
            await self.session.close()
        logger.info("🔌 Peer network shutdown")

# Global instance
_peer_network = None

def get_peer_network(instance_id: Optional[str] = None) -> ConstitutionalPeerNetwork:
    """Get the global peer network instance."""
    global _peer_network
    if _peer_network is None:
        _peer_network = ConstitutionalPeerNetwork(instance_id)
    return _peer_network

# Test function
async def test_peer_network():
    """Test the peer network functionality."""
    print("🔗 Testing Constitutional Peer Network")
    print("=" * 50)

    # Create network
    network = get_peer_network("test_instance_001")
    await network.initialize_network()

    # Add some test peers
    network.add_peer("peer_alpha", "http://peer-alpha:8080", PeerTrustLevel.TRUSTED)
    network.add_peer("peer_beta", "http://peer-beta:8080", PeerTrustLevel.CONTRIBUTOR)

    # Create and share test patterns
    test_incidents = [
        {
            'drift_type': 'violation_rate_spike',
            'severity': 'high',
            'governance_domain': 'ethical',
            'outcome': 'quarantined',
            'detected_at': datetime.now() - timedelta(hours=2),
            'contributing_factors': ['bias_amplification', 'content_moderation_failure'],
            'lessons_learned': ['Increase bias monitoring', 'Add content filters']
        },
        {
            'drift_type': 'policy_delta_drift',
            'severity': 'medium',
            'governance_domain': 'business',
            'outcome': 'recovered',
            'detected_at': datetime.now() - timedelta(hours=4),
            'contributing_factors': ['policy_weight_shift', 'business_logic_conflict'],
            'lessons_learned': ['Regular policy validation', 'Automated weight balancing']
        }
    ]

    shared_ids = []
    for incident in test_incidents:
        pattern_id = await network.share_drift_pattern(incident)
        shared_ids.append(pattern_id)
        print(f"📤 Shared pattern: {pattern_id}")

    # Simulate receiving patterns from peers
    for i, incident in enumerate(test_incidents):
        peer_id = "peer_alpha" if i % 2 == 0 else "peer_beta"
        received = await network.receive_pattern({
            'pattern_id': f"received_{i}",
            'pattern_type': 'drift_incident',
            'drift_signature': hashlib.sha256(f"test_sig_{i}".encode()).hexdigest(),
            'severity_level': incident['severity'],
            'governance_domain': incident['governance_domain'],
            'outcome_category': incident['outcome'],
            'detection_timestamp': incident['detected_at'].isoformat(),
            'resolution_timestamp': (incident['detected_at'] + timedelta(hours=1)).isoformat(),
            'contributing_factors': incident['contributing_factors'],
            'lessons_learned': incident['lessons_learned']
        }, peer_id)
        print(f"📥 Received pattern from {peer_id}: {'✅' if received else '❌'}")

    # Get insights
    insights = network.get_federated_insights()
    print(f"\n🧠 Generated {len(insights)} insights")
    for insight in insights[:3]:
        print(f"   • {insight.insight_type}: {insight.insight_text[:60]}...")

    # Show statistics
    stats = network.get_peer_statistics()
    print("\n📊 Network Statistics:")
    print(f"   Instance ID: {stats['instance_id']}")
    print(f"   Total patterns: {stats['total_patterns']}")
    print(f"   Active peers: {stats['active_peers']}")
    print(f"   Network health: {stats['network_health']:.2f}")

    await network.shutdown()
    print("\n🎉 Peer network test completed!")

if __name__ == "__main__":
    asyncio.run(test_peer_network())
