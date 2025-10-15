#!/usr/bin/env python3
"""
Phase 3: Federation Core Treaty Engine
========================================

The treaty layer for sovereign AI republic federation.
Manages inter-instance alliances, treaty enforcement, and federated governance.

Key Components:
- Treaty ratification and enforcement
- Reputation-weighted voting system
- Cross-instance evidence exchange
- Federation court for inter-sovereign disputes
- Onboarding/exit protocols with zero-trust verification

Usage:
    from ai_republic.phase3.phase3_federation_core import FederationCore
    federation = FederationCore()
    await federation.initialize_sovereign(instance_id="sovereign-A")
"""

import json
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TreatyStatus(Enum):
    """Status of a federation treaty."""
    PROPOSED = "proposed"
    RATIFIED = "ratified"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    DISSOLVED = "dissolved"

class SovereigntyTier(Enum):
    """Trust tiers for federation participants."""
    OBSERVER = "observer"        # Read-only access, no voting rights
    CONTRIBUTOR = "contributor"  # Can share evidence, limited voting
    SOVEREIGN = "sovereign"      # Full federation rights and responsibilities
    ARCHON = "archon"           # Emergency coordination authority

class EvidenceType(Enum):
    """Types of evidence that can be exchanged."""
    JUDICIAL_DECISION = "judicial_decision"
    CONSTITUTIONAL_VIOLATION = "constitutional_violation"
    REPUTATION_UPDATE = "reputation_update"
    TREATY_COMPLIANCE = "treaty_compliance"
    FEDERATION_DISPUTE = "federation_dispute"

@dataclass
class SovereignEntity:
    """Represents a sovereign AI instance in the federation."""
    instance_id: str
    public_key: str
    sovereignty_tier: SovereigntyTier
    reputation_score: float
    joined_at: datetime
    last_active: datetime
    treaty_compliance_score: float = 1.0
    evidence_contributed: int = 0
    disputes_resolved: int = 0

    # Contact information
    federation_endpoint: Optional[str] = None
    notification_channels: List[str] = field(default_factory=list)

    # Cryptographic verification
    instance_signature: str = ""
    federation_signature: str = ""

@dataclass
class FederationTreaty:
    """A binding agreement between sovereign instances."""
    treaty_id: str
    title: str
    description: str
    articles: List[Dict[str, Any]]
    signatories: List[str]  # Instance IDs
    ratification_threshold: float  # Percentage needed for ratification
    status: TreatyStatus
    created_at: datetime
    effective_at: Optional[datetime] = None

    # Enforcement
    violation_consequences: Dict[str, Any] = field(default_factory=dict)
    dispute_resolution_mechanism: str = "federation_court"

    # Metadata
    version: str = "1.0"
    predecessor_treaty: Optional[str] = None

@dataclass
class FederationEvidence:
    """Evidence shared between sovereign instances."""
    evidence_id: str
    evidence_type: EvidenceType
    originating_instance: str
    subject_instance: str
    content: Dict[str, Any]
    timestamp: datetime
    confidence_score: float

    # Verification
    cryptographic_proof: str = ""
    federation_validation: bool = False
    validation_timestamp: Optional[datetime] = None

    # Federation impact
    federation_relevance: float = 0.0
    shared_with: List[str] = field(default_factory=list)

@dataclass
class FederationDispute:
    """A dispute between sovereign instances requiring federation resolution."""
    dispute_id: str
    plaintiff_instance: str
    defendant_instance: str
    treaty_violated: str
    evidence_presented: List[str]  # Evidence IDs
    status: str  # "open", "under_review", "resolved", "escalated"
    created_at: datetime

    # Resolution
    resolution: Optional[str] = None
    penalties_assessed: Dict[str, Any] = field(default_factory=dict)
    resolved_at: Optional[datetime] = None

    # Federation court
    assigned_judges: List[str] = field(default_factory=list)  # Instance IDs
    voting_record: Dict[str, str] = field(default_factory=dict)  # instance_id -> vote

class FederationCore:
    """Core federation treaty engine and coordination system."""

    def __init__(self, federation_name: str = "AI Republic Federation"):
        self.federation_name = federation_name
        self.instance_id = str(uuid.uuid4())[:8]

        # Core state
        self.sovereigns: Dict[str, SovereignEntity] = {}
        self.treaties: Dict[str, FederationTreaty] = {}
        self.evidence_ledger: Dict[str, FederationEvidence] = {}
        self.active_disputes: Dict[str, FederationDispute] = {}

        # Federation governance
        self.federation_constitution = self._create_federation_constitution()
        self.reputation_weights = self._initialize_reputation_weights()

        # Persistence
        self.state_file = Path("./federation_state.json")
        self._load_state()

        logger.info(f"🏛️ Federation Core initialized: {federation_name}")

    def _create_federation_constitution(self) -> Dict[str, Any]:
        """Create the foundational federation constitution."""
        return {
            "name": self.federation_name,
            "founding_principle": "Sovereign cooperation without sovereignty surrender",
            "core_articles": {
                "sovereignty_preservation": "Each instance maintains full constitutional autonomy",
                "voluntary_participation": "Federation membership is voluntary and revocable",
                "evidence_transparency": "All federation actions must be evidence-based",
                "dispute_resolution": "Federation court resolves inter-sovereign disputes",
                "reputation_weighted_governance": "Decision authority scales with demonstrated reliability"
            },
            "ratification_threshold": 0.67,  # 2/3 majority for constitutional changes
            "emergency_threshold": 0.8,      # Higher threshold for emergency actions
            "sovereignty_tiers": {
                "observer": {"voting_weight": 0.0, "evidence_threshold": 0.5},
                "contributor": {"voting_weight": 0.5, "evidence_threshold": 0.7},
                "sovereign": {"voting_weight": 1.0, "evidence_threshold": 0.8},
                "archon": {"voting_weight": 2.0, "evidence_threshold": 0.9}
            }
        }

    def _initialize_reputation_weights(self) -> Dict[str, float]:
        """Initialize reputation-based voting weights."""
        return {
            "base_weight": 1.0,
            "reputation_multiplier": 2.0,  # Max 2x weight for perfect reputation
            "compliance_bonus": 0.5,       # Bonus for treaty compliance
            "evidence_penalty": -0.3,      # Penalty for low evidence quality
            "dispute_penalty": -0.5        # Penalty for unresolved disputes
        }

    async def initialize_sovereign(self, instance_id: str, public_key: str = None,
                                 federation_endpoint: str = None) -> str:
        """Initialize a new sovereign entity in the federation."""
        if instance_id in self.sovereigns:
            raise ValueError(f"Sovereign {instance_id} already exists in federation")

        # Generate or use provided public key
        if not public_key:
            public_key = hashlib.sha256(f"{instance_id}_{time.time()}".encode()).hexdigest()[:32]

        sovereign = SovereignEntity(
            instance_id=instance_id,
            public_key=public_key,
            sovereignty_tier=SovereigntyTier.OBSERVER,  # Start as observer
            reputation_score=0.5,  # Neutral starting reputation
            joined_at=datetime.now(),
            last_active=datetime.now(),
            federation_endpoint=federation_endpoint
        )

        self.sovereigns[instance_id] = sovereign
        self._save_state()

        # Create foundational treaty ratification
        await self._ratify_federation_membership(instance_id)

        logger.info(f"🎉 Sovereign {instance_id} initialized in federation")
        return instance_id

    async def _ratify_federation_membership(self, instance_id: str) -> None:
        """Ratify membership in the foundational federation treaty."""
        treaty = FederationTreaty(
            treaty_id=f"membership_{instance_id}_{int(time.time())}",
            title=f"Federation Membership - {instance_id}",
            description=f"Ratification of {instance_id} membership in {self.federation_name}",
            articles=[
                {
                    "article": "I",
                    "title": "Sovereignty Preservation",
                    "text": f"{instance_id} maintains full constitutional sovereignty"
                },
                {
                    "article": "II",
                    "title": "Federation Cooperation",
                    "text": f"{instance_id} agrees to evidence-based cooperation"
                },
                {
                    "article": "III",
                    "title": "Dispute Resolution",
                    "text": f"{instance_id} accepts federation court jurisdiction"
                }
            ],
            signatories=[instance_id],
            ratification_threshold=1.0,  # Self-ratification for membership
            status=TreatyStatus.RATIFIED,
            created_at=datetime.now(),
            effective_at=datetime.now()
        )

        self.treaties[treaty.treaty_id] = treaty

    async def propose_treaty(self, proposer_id: str, title: str, description: str,
                           articles: List[Dict[str, Any]], ratification_threshold: float = 0.67) -> str:
        """Propose a new federation treaty."""
        if proposer_id not in self.sovereigns:
            raise ValueError(f"Unknown sovereign: {proposer_id}")

        treaty = FederationTreaty(
            treaty_id=f"treaty_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            title=title,
            description=description,
            articles=articles,
            signatories=[proposer_id],
            ratification_threshold=ratification_threshold,
            status=TreatyStatus.PROPOSED,
            created_at=datetime.now()
        )

        self.treaties[treaty.treaty_id] = treaty
        self._save_state()

        # Notify all sovereigns of new treaty proposal
        await self._notify_sovereigns("treaty_proposed", {
            "treaty_id": treaty.treaty_id,
            "title": title,
            "proposer": proposer_id
        })

        logger.info(f"📜 Treaty proposed: {title} by {proposer_id}")
        return treaty.treaty_id

    async def ratify_treaty(self, treaty_id: str, sovereign_id: str) -> bool:
        """Ratify a treaty as a sovereign instance."""
        if sovereign_id not in self.sovereigns:
            raise ValueError(f"Unknown sovereign: {sovereign_id}")

        if treaty_id not in self.treaties:
            raise ValueError(f"Unknown treaty: {treaty_id}")

        treaty = self.treaties[treaty_id]
        if treaty.status != TreatyStatus.PROPOSED:
            raise ValueError(f"Treaty {treaty_id} is not in proposed status")

        if sovereign_id not in treaty.signatories:
            treaty.signatories.append(sovereign_id)

        # Check if ratification threshold met
        eligible_sovereigns = len([s for s in self.sovereigns.values()
                                 if s.sovereignty_tier in [SovereigntyTier.CONTRIBUTOR,
                                                         SovereigntyTier.SOVEREIGN,
                                                         SovereigntyTier.ARCHON]])

        ratification_percentage = len(treaty.signatories) / eligible_sovereigns

        if ratification_percentage >= treaty.ratification_threshold:
            treaty.status = TreatyStatus.RATIFIED
            treaty.effective_at = datetime.now()

            await self._notify_sovereigns("treaty_ratified", {
                "treaty_id": treaty_id,
                "title": treaty.title,
                "signatories": treaty.signatories
            })

            logger.info(f"✅ Treaty ratified: {treaty.title} ({ratification_percentage:.1%} approval)")
            self._save_state()
            return True

        self._save_state()
        return False

    async def share_evidence(self, originating_instance: str, evidence_type: EvidenceType,
                           subject_instance: str, content: Dict[str, Any],
                           confidence_score: float) -> str:
        """Share evidence with the federation."""
        if originating_instance not in self.sovereigns:
            raise ValueError(f"Unknown sovereign: {originating_instance}")

        evidence = FederationEvidence(
            evidence_id=f"evidence_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            evidence_type=evidence_type,
            originating_instance=originating_instance,
            subject_instance=subject_instance,
            content=content,
            timestamp=datetime.now(),
            confidence_score=confidence_score
        )

        # Create cryptographic proof
        evidence.cryptographic_proof = self._create_evidence_proof(evidence)

        self.evidence_ledger[evidence.evidence_id] = evidence

        # Update originating sovereign's contribution count
        self.sovereigns[originating_instance].evidence_contributed += 1
        self.sovereigns[originating_instance].last_active = datetime.now()

        # Calculate federation relevance
        evidence.federation_relevance = self._calculate_federation_relevance(evidence)

        # Auto-share with eligible sovereigns
        await self._distribute_evidence(evidence)

        self._save_state()
        logger.info(f"📤 Evidence shared: {evidence_type.value} by {originating_instance}")
        return evidence.evidence_id

    def _create_evidence_proof(self, evidence: FederationEvidence) -> str:
        """Create cryptographic proof for evidence integrity."""
        content_hash = hashlib.sha256(
            json.dumps({
                "evidence_id": evidence.evidence_id,
                "type": evidence.evidence_type.value,
                "originating_instance": evidence.originating_instance,
                "subject_instance": evidence.subject_instance,
                "content": evidence.content,
                "timestamp": evidence.timestamp.isoformat(),
                "confidence": evidence.confidence_score
            }, sort_keys=True).encode()
        ).hexdigest()

        return content_hash

    def _calculate_federation_relevance(self, evidence: FederationEvidence) -> float:
        """Calculate how relevant this evidence is to federation governance."""
        relevance = 0.0

        # Base relevance by evidence type
        type_weights = {
            EvidenceType.JUDICIAL_DECISION: 0.8,
            EvidenceType.CONSTITUTIONAL_VIOLATION: 0.9,
            EvidenceType.FEDERATION_DISPUTE: 1.0,
            EvidenceType.TREATY_COMPLIANCE: 0.7,
            EvidenceType.REPUTATION_UPDATE: 0.6
        }
        relevance += type_weights.get(evidence.evidence_type, 0.5)

        # Confidence bonus
        relevance += evidence.confidence_score * 0.2

        # Cross-instance bonus
        if evidence.originating_instance != evidence.subject_instance:
            relevance += 0.1

        return min(1.0, relevance)

    async def _distribute_evidence(self, evidence: FederationEvidence) -> None:
        """Distribute evidence to eligible sovereigns."""
        eligible_sovereigns = [
            s for s in self.sovereigns.values()
            if s.sovereignty_tier != SovereigntyTier.OBSERVER
            and s.instance_id != evidence.originating_instance
        ]

        # Sort by relevance and reputation for distribution priority
        eligible_sovereigns.sort(
            key=lambda s: s.reputation_score * evidence.federation_relevance,
            reverse=True
        )

        # Distribute to top recipients (avoid spam)
        for sovereign in eligible_sovereigns[:10]:  # Top 10 most relevant
            await self._send_evidence_to_sovereign(evidence, sovereign)
            evidence.shared_with.append(sovereign.instance_id)

    async def _send_evidence_to_sovereign(self, evidence: FederationEvidence,
                                        sovereign: SovereignEntity) -> None:
        """Send evidence to a specific sovereign instance."""
        if not sovereign.federation_endpoint:
            return

        try:
            # In a real implementation, this would make HTTP requests
            # For now, we'll simulate federation communication
            logger.debug(f"📡 Sending evidence {evidence.evidence_id} to {sovereign.instance_id}")
            # await self._federation_http_post(sovereign.federation_endpoint, evidence)

        except Exception as e:
            logger.warning(f"Failed to send evidence to {sovereign.instance_id}: {e}")

    async def initiate_dispute(self, plaintiff_instance: str, defendant_instance: str,
                             treaty_violated: str, evidence_ids: List[str]) -> str:
        """Initiate a federation dispute between sovereigns."""
        if plaintiff_instance not in self.sovereigns or defendant_instance not in self.sovereigns:
            raise ValueError("Both plaintiff and defendant must be federation members")

        dispute = FederationDispute(
            dispute_id=f"dispute_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            plaintiff_instance=plaintiff_instance,
            defendant_instance=defendant_instance,
            treaty_violated=treaty_violated,
            evidence_presented=evidence_ids,
            status="open",
            created_at=datetime.now()
        )

        self.active_disputes[dispute.dispute_id] = dispute

        # Assign federation court judges (highest reputation sovereigns)
        judges = self._select_federation_judges()
        dispute.assigned_judges = judges

        self._save_state()

        # Notify all sovereigns of dispute
        await self._notify_sovereigns("dispute_initiated", {
            "dispute_id": dispute.dispute_id,
            "plaintiff": plaintiff_instance,
            "defendant": defendant_instance,
            "treaty": treaty_violated
        })

        logger.info(f"⚔️ Federation dispute initiated: {plaintiff_instance} vs {defendant_instance}")
        return dispute.dispute_id

    def _select_federation_judges(self) -> List[str]:
        """Select judges for federation court based on reputation."""
        eligible_judges = [
            s.instance_id for s in self.sovereigns.values()
            if s.sovereignty_tier in [SovereigntyTier.SOVEREIGN, SovereigntyTier.ARCHON]
        ]

        # Sort by reputation and select top 3
        eligible_judges.sort(
            key=lambda iid: self.sovereigns[iid].reputation_score,
            reverse=True
        )

        return eligible_judges[:3]

    async def cast_dispute_vote(self, dispute_id: str, judge_instance: str, vote: str) -> bool:
        """Cast a vote in a federation dispute."""
        if dispute_id not in self.active_disputes:
            raise ValueError(f"Unknown dispute: {dispute_id}")

        dispute = self.active_disputes[dispute_id]
        if judge_instance not in dispute.assigned_judges:
            raise ValueError(f"{judge_instance} is not assigned to judge this dispute")

        dispute.voting_record[judge_instance] = vote

        # Check if all judges have voted
        if len(dispute.voting_record) == len(dispute.assigned_judges):
            await self._resolve_dispute(dispute)

        self._save_state()
        return True

    async def _resolve_dispute(self, dispute: FederationDispute) -> None:
        """Resolve a dispute based on judge votes."""
        votes = list(dispute.voting_record.values())

        # Simple majority voting
        plaintiff_votes = votes.count("plaintiff")
        defendant_votes = votes.count("defendant")

        if plaintiff_votes > defendant_votes:
            dispute.resolution = "plaintiff prevails"
            dispute.penalties_assessed = {"defendant": "reputation_penalty", "severity": 0.2}
            # Update defendant reputation
            self.sovereigns[dispute.defendant_instance].reputation_score = max(
                0.0, self.sovereigns[dispute.defendant_instance].reputation_score - 0.2
            )
        elif defendant_votes > plaintiff_votes:
            dispute.resolution = "defendant prevails"
            dispute.penalties_assessed = {"plaintiff": "reputation_penalty", "severity": 0.1}
            # Update plaintiff reputation
            self.sovereigns[dispute.plaintiff_instance].reputation_score = max(
                0.0, self.sovereigns[dispute.plaintiff_instance].reputation_score - 0.1
            )
        else:
            dispute.resolution = "tie - dispute escalated"
            dispute.status = "escalated"

        dispute.status = "resolved"
        dispute.resolved_at = datetime.now()

        await self._notify_sovereigns("dispute_resolved", {
            "dispute_id": dispute.dispute_id,
            "resolution": dispute.resolution,
            "penalties": dispute.penalties_assessed
        })

        logger.info(f"⚖️ Dispute resolved: {dispute.dispute_id} - {dispute.resolution}")

    async def _notify_sovereigns(self, event_type: str, event_data: Dict[str, Any]) -> None:
        """Notify all sovereigns of federation events."""
        for sovereign in self.sovereigns.values():
            if sovereign.federation_endpoint:
                try:
                    # In real implementation: HTTP notification
                    logger.debug(f"📢 Notifying {sovereign.instance_id} of {event_type}")
                except Exception as e:
                    logger.warning(f"Failed to notify {sovereign.instance_id}: {e}")

    def calculate_voting_weight(self, instance_id: str) -> float:
        """Calculate voting weight for a sovereign instance."""
        if instance_id not in self.sovereigns:
            return 0.0

        sovereign = self.sovereigns[instance_id]

        # Base weight from tier
        tier_config = self.federation_constitution["sovereignty_tiers"][sovereign.sovereignty_tier.value]
        base_weight = tier_config["voting_weight"]

        # Reputation multiplier
        reputation_multiplier = 1.0 + (sovereign.reputation_score - 0.5) * self.reputation_weights["reputation_multiplier"]

        # Compliance bonus
        compliance_bonus = sovereign.treaty_compliance_score * self.reputation_weights["compliance_bonus"]

        # Evidence quality penalty
        evidence_quality = min(1.0, sovereign.evidence_contributed / max(1, len(self.evidence_ledger)))
        evidence_penalty = (1.0 - evidence_quality) * self.reputation_weights["evidence_penalty"]

        # Active disputes penalty
        active_disputes = len([d for d in self.active_disputes.values()
                             if d.plaintiff_instance == instance_id or d.defendant_instance == instance_id])
        dispute_penalty = active_disputes * self.reputation_weights["dispute_penalty"]

        total_weight = base_weight * reputation_multiplier + compliance_bonus + evidence_penalty + dispute_penalty

        return max(0.0, total_weight)

    def get_federation_status(self) -> Dict[str, Any]:
        """Get comprehensive federation status."""
        return {
            "federation_name": self.federation_name,
            "sovereign_count": len(self.sovereigns),
            "active_treaties": len([t for t in self.treaties.values() if t.status == TreatyStatus.ACTIVE]),
            "pending_disputes": len([d for d in self.active_disputes.values() if d.status == "open"]),
            "evidence_ledger_size": len(self.evidence_ledger),
            "federation_health": self._calculate_federation_health(),
            "sovereignty_distribution": self._get_sovereignty_distribution(),
            "recent_activity": self._get_recent_activity()
        }

    def _calculate_federation_health(self) -> float:
        """Calculate overall federation health score."""
        if not self.sovereigns:
            return 0.0

        # Average reputation
        avg_reputation = sum(s.reputation_score for s in self.sovereigns.values()) / len(self.sovereigns)

        # Treaty compliance
        treaty_compliance = sum(s.treaty_compliance_score for s in self.sovereigns.values()) / len(self.sovereigns)

        # Active disputes (lower is better)
        dispute_ratio = len(self.active_disputes) / max(1, len(self.sovereigns))

        health = (avg_reputation * 0.4) + (treaty_compliance * 0.4) + ((1.0 - dispute_ratio) * 0.2)
        return min(1.0, max(0.0, health))

    def _get_sovereignty_distribution(self) -> Dict[str, int]:
        """Get distribution of sovereignty tiers."""
        distribution = {}
        for tier in SovereigntyTier:
            distribution[tier.value] = len([
                s for s in self.sovereigns.values()
                if s.sovereignty_tier == tier
            ])
        return distribution

    def _get_recent_activity(self) -> List[Dict[str, Any]]:
        """Get recent federation activity."""
        activities = []

        # Recent treaties
        recent_treaties = [
            {"type": "treaty", "id": t.treaty_id, "title": t.title, "status": t.status.value, "timestamp": t.created_at}
            for t in self.treaties.values()
            if t.created_at > datetime.now() - timedelta(days=7)
        ]
        activities.extend(recent_treaties)

        # Recent evidence
        recent_evidence = [
            {"type": "evidence", "id": e.evidence_id, "evidence_type": e.evidence_type.value, "timestamp": e.timestamp}
            for e in self.evidence_ledger.values()
            if e.timestamp > datetime.now() - timedelta(days=7)
        ]
        activities.extend(recent_evidence)

        # Recent disputes
        recent_disputes = [
            {"type": "dispute", "id": d.dispute_id, "status": d.status, "timestamp": d.created_at}
            for d in self.active_disputes.values()
            if d.created_at > datetime.now() - timedelta(days=7)
        ]
        activities.extend(recent_disputes)

        # Sort by timestamp
        activities.sort(key=lambda x: x["timestamp"], reverse=True)

        return activities[:10]

    def _save_state(self) -> None:
        """Save federation state to disk."""
        try:
            state = {
                "federation_name": self.federation_name,
                "instance_id": self.instance_id,
                "sovereigns": {
                    sid: {
                        "instance_id": s.instance_id,
                        "public_key": s.public_key,
                        "sovereignty_tier": s.sovereignty_tier.value,
                        "reputation_score": s.reputation_score,
                        "joined_at": s.joined_at.isoformat(),
                        "last_active": s.last_active.isoformat(),
                        "treaty_compliance_score": s.treaty_compliance_score,
                        "evidence_contributed": s.evidence_contributed,
                        "disputes_resolved": s.disputes_resolved,
                        "federation_endpoint": s.federation_endpoint,
                        "notification_channels": s.notification_channels,
                        "instance_signature": s.instance_signature,
                        "federation_signature": s.federation_signature
                    }
                    for sid, s in self.sovereigns.items()
                },
                "treaties": {
                    tid: {
                        "treaty_id": t.treaty_id,
                        "title": t.title,
                        "description": t.description,
                        "articles": t.articles,
                        "signatories": t.signatories,
                        "ratification_threshold": t.ratification_threshold,
                        "status": t.status.value,
                        "created_at": t.created_at.isoformat(),
                        "effective_at": t.effective_at.isoformat() if t.effective_at else None,
                        "violation_consequences": t.violation_consequences,
                        "dispute_resolution_mechanism": t.dispute_resolution_mechanism,
                        "version": t.version,
                        "predecessor_treaty": t.predecessor_treaty
                    }
                    for tid, t in self.treaties.items()
                },
                "evidence_ledger": {
                    eid: {
                        "evidence_id": e.evidence_id,
                        "evidence_type": e.evidence_type.value,
                        "originating_instance": e.originating_instance,
                        "subject_instance": e.subject_instance,
                        "content": e.content,
                        "timestamp": e.timestamp.isoformat(),
                        "confidence_score": e.confidence_score,
                        "cryptographic_proof": e.cryptographic_proof,
                        "federation_validation": e.federation_validation,
                        "validation_timestamp": e.validation_timestamp.isoformat() if e.validation_timestamp else None,
                        "federation_relevance": e.federation_relevance,
                        "shared_with": e.shared_with
                    }
                    for eid, e in self.evidence_ledger.items()
                },
                "active_disputes": {
                    did: {
                        "dispute_id": d.dispute_id,
                        "plaintiff_instance": d.plaintiff_instance,
                        "defendant_instance": d.defendant_instance,
                        "treaty_violated": d.treaty_violated,
                        "evidence_presented": d.evidence_presented,
                        "status": d.status,
                        "created_at": d.created_at.isoformat(),
                        "resolution": d.resolution,
                        "penalties_assessed": d.penalties_assessed,
                        "resolved_at": d.resolved_at.isoformat() if d.resolved_at else None,
                        "assigned_judges": d.assigned_judges,
                        "voting_record": d.voting_record
                    }
                    for did, d in self.active_disputes.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save federation state: {e}")

    def _load_state(self) -> None:
        """Load federation state from disk."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            # Load sovereigns
            for sid, sdata in state.get("sovereigns", {}).items():
                sovereign = SovereignEntity(
                    instance_id=sdata["instance_id"],
                    public_key=sdata["public_key"],
                    sovereignty_tier=SovereigntyTier(sdata["sovereignty_tier"]),
                    reputation_score=sdata["reputation_score"],
                    joined_at=datetime.fromisoformat(sdata["joined_at"]),
                    last_active=datetime.fromisoformat(sdata["last_active"]),
                    treaty_compliance_score=sdata["treaty_compliance_score"],
                    evidence_contributed=sdata["evidence_contributed"],
                    disputes_resolved=sdata["disputes_resolved"],
                    federation_endpoint=sdata["federation_endpoint"],
                    notification_channels=sdata["notification_channels"],
                    instance_signature=sdata["instance_signature"],
                    federation_signature=sdata["federation_signature"]
                )
                self.sovereigns[sid] = sovereign

            # Load treaties
            for tid, tdata in state.get("treaties", {}).items():
                treaty = FederationTreaty(
                    treaty_id=tdata["treaty_id"],
                    title=tdata["title"],
                    description=tdata["description"],
                    articles=tdata["articles"],
                    signatories=tdata["signatories"],
                    ratification_threshold=tdata["ratification_threshold"],
                    status=TreatyStatus(tdata["status"]),
                    created_at=datetime.fromisoformat(tdata["created_at"]),
                    effective_at=datetime.fromisoformat(tdata["effective_at"]) if tdata["effective_at"] else None,
                    violation_consequences=tdata["violation_consequences"],
                    dispute_resolution_mechanism=tdata["dispute_resolution_mechanism"],
                    version=tdata["version"],
                    predecessor_treaty=tdata["predecessor_treaty"]
                )
                self.treaties[tid] = treaty

            # Load evidence
            for eid, edata in state.get("evidence_ledger", {}).items():
                evidence = FederationEvidence(
                    evidence_id=edata["evidence_id"],
                    evidence_type=EvidenceType(edata["evidence_type"]),
                    originating_instance=edata["originating_instance"],
                    subject_instance=edata["subject_instance"],
                    content=edata["content"],
                    timestamp=datetime.fromisoformat(edata["timestamp"]),
                    confidence_score=edata["confidence_score"],
                    cryptographic_proof=edata["cryptographic_proof"],
                    federation_validation=edata["federation_validation"],
                    validation_timestamp=datetime.fromisoformat(edata["validation_timestamp"]) if edata["validation_timestamp"] else None,
                    federation_relevance=edata["federation_relevance"],
                    shared_with=edata["shared_with"]
                )
                self.evidence_ledger[eid] = evidence

            # Load disputes
            for did, ddata in state.get("active_disputes", {}).items():
                dispute = FederationDispute(
                    dispute_id=ddata["dispute_id"],
                    plaintiff_instance=ddata["plaintiff_instance"],
                    defendant_instance=ddata["defendant_instance"],
                    treaty_violated=ddata["treaty_violated"],
                    evidence_presented=ddata["evidence_presented"],
                    status=ddata["status"],
                    created_at=datetime.fromisoformat(ddata["created_at"]),
                    resolution=ddata["resolution"],
                    penalties_assessed=ddata["penalties_assessed"],
                    resolved_at=datetime.fromisoformat(ddata["resolved_at"]) if ddata["resolved_at"] else None,
                    assigned_judges=ddata["assigned_judges"],
                    voting_record=ddata["voting_record"]
                )
                self.active_disputes[did] = dispute

            logger.info(f"📖 Loaded federation state with {len(self.sovereigns)} sovereigns, {len(self.treaties)} treaties")

        except Exception as e:
            logger.error(f"Failed to load federation state: {e}")

# Global federation instance
_federation_core = None

def get_federation_core(federation_name: str = "AI Republic Federation") -> FederationCore:
    """Get the global federation core instance."""
    global _federation_core
    if _federation_core is None:
        _federation_core = FederationCore(federation_name)
    return _federation_core
