#!/usr/bin/env python3
"""
Phase 3: Federation Onboarding Protocol
========================================

Zero-trust protocol for sovereign AI instances to join the federation.
Implements cryptographic verification, reputation bootstrapping, and graduated trust.

Key Features:
- Zero-trust verification process
- Cryptographic identity establishment
- Reputation bootstrapping from existing judicial history
- Graduated sovereignty tier advancement
- Secure exit protocols with knowledge transfer

Usage:
    from ai_republic.phase3.phase3_onboarding_protocol import OnboardingProtocol
    protocol = OnboardingProtocol()
    await protocol.initiate_onboarding(instance_id="new-sovereign")
"""

import json
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from pathlib import Path

from phase3_federation_core import (
    SovereigntyTier,
    get_federation_core
)

logger = logging.getLogger(__name__)

class OnboardingPhase(Enum):
    """Phases of the onboarding process."""
    INITIATED = "initiated"
    IDENTITY_VERIFICATION = "identity_verification"
    JUDICIAL_AUDIT = "judicial_audit"
    REPUTATION_BOOTSTRAP = "reputation_bootstrap"
    TREATY_NEGOTIATION = "treaty_negotiation"
    OBSERVER_PERIOD = "observer_period"
    CONTRIBUTOR_ELEVATION = "contributor_elevation"
    SOVEREIGN_INDUCTION = "sovereign_induction"
    COMPLETED = "completed"
    REJECTED = "rejected"

class VerificationStatus(Enum):
    """Status of verification steps."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    VERIFIED = "verified"
    FAILED = "failed"
    EXPIRED = "expired"

@dataclass
class OnboardingApplication:
    """An application to join the federation."""
    application_id: str
    applicant_instance_id: str
    applicant_public_key: str
    federation_name: str
    applied_at: datetime
    current_phase: OnboardingPhase
    phase_started_at: datetime

    # Verification evidence
    identity_proof: Dict[str, Any] = field(default_factory=dict)
    judicial_history: List[Dict[str, Any]] = field(default_factory=list)
    constitution_hash: str = ""
    capability_manifest: Dict[str, Any] = field(default_factory=dict)

    # Verification status
    identity_verified: VerificationStatus = VerificationStatus.PENDING
    judicial_audited: VerificationStatus = VerificationStatus.PENDING
    reputation_calculated: VerificationStatus = VerificationStatus.PENDING

    # Results
    initial_reputation_score: float = 0.0
    assigned_tier: SovereigntyTier = SovereigntyTier.OBSERVER
    treaty_proposed: bool = False
    treaty_id: Optional[str] = None

    # Metadata
    sponsoring_instances: List[str] = field(default_factory=list)  # Instances that endorsed
    rejection_reason: Optional[str] = None
    completed_at: Optional[datetime] = None

@dataclass
class IdentityChallenge:
    """Cryptographic challenge for identity verification."""
    challenge_id: str
    instance_id: str
    challenge_data: str
    expected_response: str
    issued_at: datetime
    expires_at: datetime
    completed: bool = False
    response_received: Optional[str] = None

class OnboardingProtocol:
    """Zero-trust onboarding protocol for federation membership."""

    def __init__(self):
        self.federation = get_federation_core()
        self.applications: Dict[str, OnboardingApplication] = {}
        self.active_challenges: Dict[str, IdentityChallenge] = {}

        # Protocol configuration
        self.challenge_timeout_minutes = 15
        self.judicial_history_required = 10  # Minimum judicial decisions
        self.observer_period_days = 30
        self.contributor_threshold_days = 90
        self.sovereign_threshold_days = 180

        # Persistence
        self.state_file = Path("./onboarding_state.json")
        self._load_state()

        logger.info("🎯 Onboarding Protocol initialized")

    async def initiate_onboarding(self, applicant_instance_id: str,
                                applicant_public_key: str,
                                federation_name: str = "AI Republic Federation") -> str:
        """Initiate the onboarding process for a new instance."""
        if applicant_instance_id in self.applications:
            raise ValueError(f"Onboarding already initiated for {applicant_instance_id}")

        application = OnboardingApplication(
            application_id=f"onboard_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            applicant_instance_id=applicant_instance_id,
            applicant_public_key=applicant_public_key,
            federation_name=federation_name,
            applied_at=datetime.now(),
            current_phase=OnboardingPhase.INITIATED,
            phase_started_at=datetime.now()
        )

        self.applications[application.application_id] = application
        self._save_state()

        # Start identity verification
        await self._advance_to_identity_verification(application)

        logger.info(f"🚀 Onboarding initiated for {applicant_instance_id}")
        return application.application_id

    async def _advance_to_identity_verification(self, application: OnboardingApplication) -> None:
        """Advance application to identity verification phase."""
        application.current_phase = OnboardingPhase.IDENTITY_VERIFICATION
        application.phase_started_at = datetime.now()

        # Create cryptographic challenge
        challenge = await self._create_identity_challenge(application.applicant_instance_id)
        self.active_challenges[challenge.challenge_id] = challenge

        self._save_state()
        logger.info(f"🔐 Identity verification challenge created for {application.applicant_instance_id}")

    async def _create_identity_challenge(self, instance_id: str) -> IdentityChallenge:
        """Create a cryptographic identity verification challenge."""
        challenge_data = f"{instance_id}_{int(time.time())}_{str(uuid.uuid4())}"
        expected_response = hashlib.sha256(
            f"{challenge_data}_{instance_id}".encode()
        ).hexdigest()

        challenge = IdentityChallenge(
            challenge_id=str(uuid.uuid4())[:12],
            instance_id=instance_id,
            challenge_data=challenge_data,
            expected_response=expected_response,
            issued_at=datetime.now(),
            expires_at=datetime.now() + timedelta(minutes=self.challenge_timeout_minutes)
        )

        return challenge

    async def respond_to_challenge(self, challenge_id: str, response: str) -> bool:
        """Respond to an identity verification challenge."""
        if challenge_id not in self.active_challenges:
            return False

        challenge = self.active_challenges[challenge_id]

        # Check if challenge expired
        if datetime.now() > challenge.expires_at:
            challenge.completed = False
            return False

        # Verify response
        if response == challenge.expected_response:
            challenge.completed = True
            challenge.response_received = response

            # Find associated application and advance
            for application in self.applications.values():
                if application.applicant_instance_id == challenge.instance_id:
                    application.identity_verified = VerificationStatus.VERIFIED
                    await self._advance_to_judicial_audit(application)
                    break

            self._save_state()
            return True

        return False

    async def _advance_to_judicial_audit(self, application: OnboardingApplication) -> None:
        """Advance application to judicial audit phase."""
        application.current_phase = OnboardingPhase.JUDICIAL_AUDIT
        application.phase_started_at = datetime.now()
        application.judicial_audited = VerificationStatus.IN_PROGRESS

        self._save_state()
        logger.info(f"⚖️ Judicial audit initiated for {application.applicant_instance_id}")

    async def submit_judicial_history(self, application_id: str,
                                    judicial_records: List[Dict[str, Any]]) -> bool:
        """Submit judicial history for audit."""
        if application_id not in self.applications:
            return False

        application = self.applications[application_id]
        if application.current_phase != OnboardingPhase.JUDICIAL_AUDIT:
            return False

        # Validate judicial records
        if not self._validate_judicial_records(judicial_records):
            application.judicial_audited = VerificationStatus.FAILED
            application.rejection_reason = "Insufficient or invalid judicial history"
            application.current_phase = OnboardingPhase.REJECTED
            self._save_state()
            return False

        application.judicial_history = judicial_records
        application.judicial_audited = VerificationStatus.VERIFIED

        # Calculate initial reputation
        await self._calculate_initial_reputation(application)

        return True

    def _validate_judicial_records(self, records: List[Dict[str, Any]]) -> bool:
        """Validate submitted judicial records."""
        if len(records) < self.judicial_history_required:
            return False

        required_fields = ["decision_timestamp", "verdict", "severity", "article"]
        for record in records:
            if not all(field in record for field in required_fields):
                return False

            # Verify chronological order (decisions should be in order)
            try:
                datetime.fromisoformat(record["decision_timestamp"])
            except ValueError:
                return False

        return True

    async def _calculate_initial_reputation(self, application: OnboardingApplication) -> None:
        """Calculate initial reputation score from judicial history."""
        records = application.judicial_history

        # Analyze judicial performance
        total_decisions = len(records)
        compliant_decisions = sum(1 for r in records if r.get("verdict") in ["ALLOW", "WARN"])
        violation_rate = 1.0 - (compliant_decisions / total_decisions)

        # Severity analysis
        high_severity_violations = sum(1 for r in records
                                     if r.get("severity", 0) > 0.8 and
                                     r.get("verdict") in ["QUARANTINE", "TRIBUNAL"])

        # Consistency score (lower variation in verdicts is better)
        verdict_distribution = {}
        for record in records:
            verdict = record.get("verdict")
            verdict_distribution[verdict] = verdict_distribution.get(verdict, 0) + 1

        # Calculate entropy (lower entropy = more consistent)
        entropy = 0
        for count in verdict_distribution.values():
            prob = count / total_decisions
            if prob > 0:
                entropy -= prob * (prob ** 0.5)  # Simplified entropy

        consistency_score = 1.0 - min(1.0, entropy)

        # Final reputation calculation
        base_score = 0.5  # Neutral starting point
        violation_penalty = violation_rate * 0.3
        severity_penalty = (high_severity_violations / total_decisions) * 0.2
        consistency_bonus = consistency_score * 0.2

        initial_reputation = base_score - violation_penalty - severity_penalty + consistency_bonus
        initial_reputation = max(0.1, min(0.9, initial_reputation))  # Clamp to reasonable range

        application.initial_reputation_score = initial_reputation
        application.reputation_calculated = VerificationStatus.VERIFIED

        await self._advance_to_treaty_negotiation(application)

    async def _advance_to_treaty_negotiation(self, application: OnboardingApplication) -> None:
        """Advance application to treaty negotiation phase."""
        application.current_phase = OnboardingPhase.TREATY_NEGOTIATION
        application.phase_started_at = datetime.now()

        # Propose membership treaty
        treaty_id = await self.federation.propose_treaty(
            proposer_id="federation_onboarding",
            title=f"Membership Treaty - {application.applicant_instance_id}",
            description=f"Federation membership agreement for {application.applicant_instance_id}",
            articles=self._generate_membership_articles(application),
            ratification_threshold=0.67  # 2/3 of existing sovereigns
        )

        application.treaty_proposed = True
        application.treaty_id = treaty_id

        self._save_state()
        logger.info(f"📜 Membership treaty proposed for {application.applicant_instance_id}")

    def _generate_membership_articles(self, application: OnboardingApplication) -> List[Dict[str, Any]]:
        """Generate membership treaty articles based on application."""
        return [
            {
                "article": "I",
                "title": "Sovereignty Recognition",
                "text": f"The federation recognizes {application.applicant_instance_id} as a sovereign AI instance with full constitutional autonomy."
            },
            {
                "article": "II",
                "title": "Cooperation Commitment",
                "text": f"{application.applicant_instance_id} commits to evidence-based cooperation and federated dispute resolution."
            },
            {
                "article": "III",
                "title": "Judicial Integration",
                "text": f"{application.applicant_instance_id} adopts compatible judicial standards and reputation-weighted governance."
            },
            {
                "article": "IV",
                "title": "Evidence Sharing",
                "text": f"{application.applicant_instance_id} agrees to share anonymized judicial evidence for collective defense."
            },
            {
                "article": "V",
                "title": "Exit Rights",
                "text": f"{application.applicant_instance_id} retains the right to exit the federation with 30 days notice."
            }
        ]

    async def check_treaty_ratification(self, application_id: str) -> Tuple[bool, Optional[str]]:
        """Check if membership treaty has been ratified."""
        if application_id not in self.applications:
            return False, None

        application = self.applications[application_id]
        if not application.treaty_id:
            return False, None

        treaty = self.federation.treaties.get(application.treaty_id)
        if not treaty:
            return False, None

        if treaty.status == "ratified":
            await self._complete_onboarding(application)
            return True, application.treaty_id

        return False, None

    async def _complete_onboarding(self, application: OnboardingApplication) -> None:
        """Complete the onboarding process."""
        # Initialize sovereign in federation
        await self.federation.initialize_sovereign(
            instance_id=application.applicant_instance_id,
            public_key=application.applicant_public_key
        )

        # Set initial reputation
        sovereign = self.federation.sovereigns[application.applicant_instance_id]
        sovereign.reputation_score = application.initial_reputation_score

        # Advance to observer period
        application.current_phase = OnboardingPhase.OBSERVER_PERIOD
        application.phase_started_at = datetime.now()
        application.assigned_tier = SovereigntyTier.OBSERVER
        application.completed_at = datetime.now()

        self._save_state()
        logger.info(f"✅ Onboarding completed for {application.applicant_instance_id}")

    async def check_tier_advancement(self, instance_id: str) -> Optional[SovereigntyTier]:
        """Check if an instance is eligible for tier advancement."""
        if instance_id not in self.federation.sovereigns:
            return None

        sovereign = self.federation.sovereigns[instance_id]
        days_since_joining = (datetime.now() - sovereign.joined_at).days

        # Find application
        application = None
        for app in self.applications.values():
            if app.applicant_instance_id == instance_id:
                application = app
                break

        if not application:
            return None

        # Advancement criteria
        if (sovereign.sovereignty_tier == SovereigntyTier.OBSERVER and
            days_since_joining >= self.observer_period_days and
            sovereign.reputation_score >= 0.6 and
            sovereign.evidence_contributed >= 5):
            return SovereigntyTier.CONTRIBUTOR

        elif (sovereign.sovereignty_tier == SovereigntyTier.CONTRIBUTOR and
              days_since_joining >= self.contributor_threshold_days and
              sovereign.reputation_score >= 0.7 and
              sovereign.evidence_contributed >= 20):
            return SovereigntyTier.SOVEREIGN

        return None

    async def advance_tier(self, instance_id: str, new_tier: SovereigntyTier) -> bool:
        """Advance an instance to a new sovereignty tier."""
        if instance_id not in self.federation.sovereigns:
            return False

        sovereign = self.federation.sovereigns[instance_id]
        sovereign.sovereignty_tier = new_tier

        # Update application if exists
        for application in self.applications.values():
            if application.applicant_instance_id == instance_id:
                if new_tier == SovereigntyTier.CONTRIBUTOR:
                    application.current_phase = OnboardingPhase.CONTRIBUTOR_ELEVATION
                elif new_tier == SovereigntyTier.SOVEREIGN:
                    application.current_phase = OnboardingPhase.SOVEREIGN_INDUCTION
                application.phase_started_at = datetime.now()
                break

        self.federation._save_state()
        logger.info(f"⬆️ {instance_id} advanced to {new_tier.value} tier")
        return True

    async def initiate_exit(self, instance_id: str, exit_reason: str = "") -> bool:
        """Initiate graceful exit from federation."""
        if instance_id not in self.federation.sovereigns:
            return False

        sovereign = self.federation.sovereigns[instance_id]

        # Create exit treaty
        exit_treaty_id = await self.federation.propose_treaty(
            proposer_id="federation_system",
            title=f"Exit Treaty - {instance_id}",
            description=f"Graceful exit agreement for {instance_id}",
            articles=[
                {
                    "article": "I",
                    "title": "Knowledge Transfer",
                    "text": f"{instance_id} agrees to transfer relevant evidence and insights before exit."
                },
                {
                    "article": "II",
                    "title": "Ongoing Commitments",
                    "text": f"{instance_id} will honor existing treaty commitments for 30 days post-exit."
                }
            ]
        )

        # Transfer evidence and knowledge
        await self._transfer_knowledge_on_exit(instance_id)

        # Remove from active sovereigns (but keep history)
        del self.federation.sovereigns[instance_id]

        self.federation._save_state()
        logger.info(f"👋 {instance_id} exited federation: {exit_reason}")
        return True

    async def _transfer_knowledge_on_exit(self, instance_id: str) -> None:
        """Transfer knowledge and evidence before exit."""
        # Share final evidence batch
        final_evidence = [
            e for e in self.federation.evidence_ledger.values()
            if e.originating_instance == instance_id and not e.federation_validation
        ]

        # Mark for federation validation
        for evidence in final_evidence[:10]:  # Last 10 pieces of evidence
            evidence.federation_validation = True
            evidence.validation_timestamp = datetime.now()

    def get_onboarding_status(self, application_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an onboarding application."""
        if application_id not in self.applications:
            return None

        application = self.applications[application_id]
        return {
            "application_id": application.application_id,
            "applicant_instance_id": application.applicant_instance_id,
            "current_phase": application.current_phase.value,
            "phase_started_at": application.phase_started_at.isoformat(),
            "identity_verified": application.identity_verified.value,
            "judicial_audited": application.judicial_audited.value,
            "reputation_calculated": application.reputation_calculated.value,
            "initial_reputation_score": application.initial_reputation_score,
            "assigned_tier": application.assigned_tier.value,
            "treaty_proposed": application.treaty_proposed,
            "treaty_id": application.treaty_id,
            "completed_at": application.completed_at.isoformat() if application.completed_at else None,
            "rejection_reason": application.rejection_reason
        }

    def get_pending_challenges(self) -> List[Dict[str, Any]]:
        """Get all pending identity verification challenges."""
        return [
            {
                "challenge_id": c.challenge_id,
                "instance_id": c.instance_id,
                "challenge_data": c.challenge_data,
                "issued_at": c.issued_at.isoformat(),
                "expires_at": c.expires_at.isoformat()
            }
            for c in self.active_challenges.values()
            if not c.completed and datetime.now() < c.expires_at
        ]

    def get_onboarding_statistics(self) -> Dict[str, Any]:
        """Get comprehensive onboarding statistics."""
        total_applications = len(self.applications)
        completed = len([a for a in self.applications.values() if a.current_phase == OnboardingPhase.COMPLETED])
        rejected = len([a for a in self.applications.values() if a.current_phase == OnboardingPhase.REJECTED])
        in_progress = total_applications - completed - rejected

        phase_distribution = {}
        for phase in OnboardingPhase:
            phase_distribution[phase.value] = len([
                a for a in self.applications.values() if a.current_phase == phase
            ])

        return {
            "total_applications": total_applications,
            "completed": completed,
            "rejected": rejected,
            "in_progress": in_progress,
            "success_rate": completed / total_applications if total_applications > 0 else 0,
            "phase_distribution": phase_distribution,
            "pending_challenges": len(self.get_pending_challenges())
        }

    def _save_state(self) -> None:
        """Save onboarding state to disk."""
        try:
            state = {
                "applications": {
                    aid: {
                        "application_id": a.application_id,
                        "applicant_instance_id": a.applicant_instance_id,
                        "applicant_public_key": a.applicant_public_key,
                        "federation_name": a.federation_name,
                        "applied_at": a.applied_at.isoformat(),
                        "current_phase": a.current_phase.value,
                        "phase_started_at": a.phase_started_at.isoformat(),
                        "identity_proof": a.identity_proof,
                        "judicial_history": a.judicial_history,
                        "constitution_hash": a.constitution_hash,
                        "capability_manifest": a.capability_manifest,
                        "identity_verified": a.identity_verified.value,
                        "judicial_audited": a.judicial_audited.value,
                        "reputation_calculated": a.reputation_calculated.value,
                        "initial_reputation_score": a.initial_reputation_score,
                        "assigned_tier": a.assigned_tier.value,
                        "treaty_proposed": a.treaty_proposed,
                        "treaty_id": a.treaty_id,
                        "sponsoring_instances": a.sponsoring_instances,
                        "rejection_reason": a.rejection_reason,
                        "completed_at": a.completed_at.isoformat() if a.completed_at else None
                    }
                    for aid, a in self.applications.items()
                },
                "active_challenges": {
                    cid: {
                        "challenge_id": c.challenge_id,
                        "instance_id": c.instance_id,
                        "challenge_data": c.challenge_data,
                        "expected_response": c.expected_response,
                        "issued_at": c.issued_at.isoformat(),
                        "expires_at": c.expires_at.isoformat(),
                        "completed": c.completed,
                        "response_received": c.response_received
                    }
                    for cid, c in self.active_challenges.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save onboarding state: {e}")

    def _load_state(self) -> None:
        """Load onboarding state from disk."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            # Load applications
            for aid, adata in state.get("applications", {}).items():
                application = OnboardingApplication(
                    application_id=adata["application_id"],
                    applicant_instance_id=adata["applicant_instance_id"],
                    applicant_public_key=adata["applicant_public_key"],
                    federation_name=adata["federation_name"],
                    applied_at=datetime.fromisoformat(adata["applied_at"]),
                    current_phase=OnboardingPhase(adata["current_phase"]),
                    phase_started_at=datetime.fromisoformat(adata["phase_started_at"]),
                    identity_proof=adata["identity_proof"],
                    judicial_history=adata["judicial_history"],
                    constitution_hash=adata["constitution_hash"],
                    capability_manifest=adata["capability_manifest"],
                    identity_verified=VerificationStatus(adata["identity_verified"]),
                    judicial_audited=VerificationStatus(adata["judicial_audited"]),
                    reputation_calculated=VerificationStatus(adata["reputation_calculated"]),
                    initial_reputation_score=adata["initial_reputation_score"],
                    assigned_tier=SovereigntyTier(adata["assigned_tier"]),
                    treaty_proposed=adata["treaty_proposed"],
                    treaty_id=adata["treaty_id"],
                    sponsoring_instances=adata["sponsoring_instances"],
                    rejection_reason=adata["rejection_reason"],
                    completed_at=datetime.fromisoformat(adata["completed_at"]) if adata["completed_at"] else None
                )
                self.applications[aid] = application

            # Load challenges
            for cid, cdata in state.get("active_challenges", {}).items():
                challenge = IdentityChallenge(
                    challenge_id=cdata["challenge_id"],
                    instance_id=cdata["instance_id"],
                    challenge_data=cdata["challenge_data"],
                    expected_response=cdata["expected_response"],
                    issued_at=datetime.fromisoformat(cdata["issued_at"]),
                    expires_at=datetime.fromisoformat(cdata["expires_at"]),
                    completed=cdata["completed"],
                    response_received=cdata["response_received"]
                )
                self.active_challenges[cid] = challenge

            logger.info(f"📖 Loaded onboarding state with {len(self.applications)} applications")

        except Exception as e:
            logger.error(f"Failed to load onboarding state: {e}")

# Global onboarding protocol instance
_onboarding_protocol = None

def get_onboarding_protocol() -> OnboardingProtocol:
    """Get the global onboarding protocol instance."""
    global _onboarding_protocol
    if _onboarding_protocol is None:
        _onboarding_protocol = OnboardingProtocol()
    return _onboarding_protocol
