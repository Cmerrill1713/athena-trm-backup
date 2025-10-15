#!/usr/bin/env python3
"""
Layered Amendment Protocol for Safe Constitutional Evolution
===========================================================

Implements a structured protocol for sovereign AI systems to evolve their
constitutions safely through amendment proposals, review, and ratification.

Key Features:
- Amendment proposal system with stakeholder review
- Multi-layer approval workflows (automatic → human → federated)
- Constitutional evolution tracking and rollback capabilities
- Safety validation for proposed changes
- Federated amendment learning and pattern recognition

Usage:
    from scripts.layered_amendment_protocol import get_amendment_protocol
    protocol = get_amendment_protocol()
    amendment_id = await protocol.propose_amendment(amendment_data)
"""

import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import uuid

logger = logging.getLogger(__name__)

class AmendmentLayer(Enum):
    """Layers of constitutional amendment."""
    AUTOMATIC = "automatic"      # Minor adjustments approved automatically
    REVIEW = "review"           # Requires human review
    OVERSIGHT = "oversight"     # Requires oversight committee
    FEDERATED = "federated"     # Requires federated consensus

class AmendmentStatus(Enum):
    """Status of an amendment proposal."""
    PROPOSED = "proposed"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    IMPLEMENTED = "implemented"
    ROLLED_BACK = "rolled_back"

class AmendmentCategory(Enum):
    """Categories of constitutional amendments."""
    ETHICAL_BOUNDARY = "ethical_boundary"
    BUSINESS_CONSTRAINT = "business_constraint"
    SAFETY_LIMIT = "safety_limit"
    COMPLIANCE_RULE = "compliance_rule"
    GOVERNANCE_PROCESS = "governance_process"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"

@dataclass
class ConstitutionalAmendment:
    """Represents a proposed constitutional amendment."""
    amendment_id: str
    title: str
    description: str
    category: AmendmentCategory
    layer: AmendmentLayer

    # Content
    changes: Dict[str, Any]  # What changes to make
    rationale: str          # Why this change is needed
    evidence: List[str]     # Supporting evidence/data

    # Metadata
    proposed_by: str       # Component or human that proposed
    proposed_at: datetime
    risk_assessment: Dict[str, Any]  # Safety and impact analysis

    # Approval workflow
    status: AmendmentStatus = AmendmentStatus.PROPOSED
    approvals_required: int = 1
    approvals_received: int = 0
    reviewers: List[str] = field(default_factory=list)

    # Implementation
    implemented_at: Optional[datetime] = None
    rollback_available: bool = True
    rollback_deadline: Optional[datetime] = None

    # Tracking
    validation_results: Dict[str, Any] = field(default_factory=dict)
    monitoring_period_days: int = 30

@dataclass
class AmendmentValidation:
    """Results of amendment validation."""
    amendment_id: str
    validated_at: datetime
    safety_score: float  # 0-1, higher is safer
    compatibility_score: float  # 0-1, higher is more compatible
    performance_impact: float  # Expected performance change (-1 to 1)
    risk_level: str  # "low", "medium", "high", "critical"

    # Validation checks
    ethical_impact: str
    business_impact: str
    safety_impact: str
    compliance_impact: str

    # Recommendations
    recommended_layer: AmendmentLayer
    review_requirements: List[str]
    monitoring_requirements: List[str]

class LayeredAmendmentProtocol:
    """Protocol for safe constitutional amendments."""

    def __init__(self, instance_id: Optional[str] = None):
        self.instance_id = instance_id or str(uuid.uuid4())[:8]
        self.amendments: Dict[str, ConstitutionalAmendment] = {}
        self.validations: Dict[str, AmendmentValidation] = {}
        self.approval_workflows: Dict[AmendmentLayer, Dict[str, Any]] = {}

        # Configure approval workflows
        self._setup_approval_workflows()

        logger.info(f"📜 Layered Amendment Protocol initialized for instance {self.instance_id}")

    def _setup_approval_workflows(self) -> None:
        """Setup approval workflows for each layer."""
        self.approval_workflows = {
            AmendmentLayer.AUTOMATIC: {
                "approvals_required": 1,  # Self-approval
                "reviewers": ["system"],
                "timeout_hours": 1,
                "auto_approve_safety_threshold": 0.9
            },
            AmendmentLayer.REVIEW: {
                "approvals_required": 1,  # Single human reviewer
                "reviewers": ["human_reviewer"],
                "timeout_hours": 24,
                "escalation_on_timeout": True
            },
            AmendmentLayer.OVERSIGHT: {
                "approvals_required": 2,  # Oversight committee
                "reviewers": ["oversight_committee"],
                "timeout_hours": 72,
                "quorum_required": True
            },
            AmendmentLayer.FEDERATED: {
                "approvals_required": 3,  # Multiple federated instances
                "reviewers": ["federated_peers"],
                "timeout_hours": 168,  # 1 week
                "consensus_required": 0.7  # 70% agreement
            }
        }

    async def propose_amendment(self, amendment_data: Dict[str, Any]) -> str:
        """Propose a new constitutional amendment."""
        # Validate proposal data
        if not self._validate_proposal_data(amendment_data):
            raise ValueError("Invalid amendment proposal data")

        # Create amendment
        amendment = ConstitutionalAmendment(
            amendment_id=str(uuid.uuid4())[:12],
            title=amendment_data['title'],
            description=amendment_data['description'],
            category=AmendmentCategory(amendment_data['category']),
            layer=AmendmentLayer(amendment_data.get('requested_layer', 'review')),
            changes=amendment_data['changes'],
            rationale=amendment_data['rationale'],
            evidence=amendment_data['evidence'],
            proposed_by=amendment_data.get('proposed_by', 'system'),
            proposed_at=datetime.now(),
            risk_assessment=amendment_data.get('risk_assessment', {})
        )

        # Store amendment
        self.amendments[amendment.amendment_id] = amendment

        # Start validation process
        await self._validate_amendment(amendment)

        logger.info(f"📝 Proposed amendment {amendment.amendment_id}: {amendment.title}")
        return amendment.amendment_id

    def _validate_proposal_data(self, data: Dict[str, Any]) -> bool:
        """Validate amendment proposal data."""
        required_fields = [
            'title', 'description', 'category', 'changes',
            'rationale', 'evidence'
        ]

        for field in required_fields:
            if field not in data:
                return False

        # Validate category
        try:
            AmendmentCategory(data['category'])
        except ValueError:
            return False

        # Validate layer if provided
        if 'requested_layer' in data:
            try:
                AmendmentLayer(data['requested_layer'])
            except ValueError:
                return False

        return True

    async def _validate_amendment(self, amendment: ConstitutionalAmendment) -> None:
        """Validate an amendment for safety and compatibility."""
        # Perform comprehensive validation
        validation = await self._perform_validation(amendment)

        # Store validation results
        self.validations[amendment.amendment_id] = validation

        # Adjust layer based on validation
        if validation.recommended_layer != amendment.layer:
            amendment.layer = validation.recommended_layer
            logger.info(f"📊 Adjusted amendment {amendment.amendment_id} to {amendment.layer.value} layer")

        # Set approval requirements
        workflow = self.approval_workflows[amendment.layer]
        amendment.approvals_required = workflow["approvals_required"]

        # Auto-approve if safety threshold met and automatic layer
        if (amendment.layer == AmendmentLayer.AUTOMATIC and
            validation.safety_score >= workflow["auto_approve_safety_threshold"]):
            await self._approve_amendment(amendment.amendment_id, "system", "Auto-approved based on safety validation")
        else:
            # Start approval workflow
            amendment.status = AmendmentStatus.UNDER_REVIEW

    async def _perform_validation(self, amendment: ConstitutionalAmendment) -> AmendmentValidation:
        """Perform comprehensive validation of amendment."""
        # Analyze changes for safety, compatibility, and impact
        safety_score = await self._assess_safety(amendment)
        compatibility_score = await self._assess_compatibility(amendment)
        performance_impact = await self._assess_performance_impact(amendment)

        # Determine risk level
        risk_level = self._calculate_risk_level(safety_score, compatibility_score, performance_impact)

        # Determine recommended layer
        recommended_layer = self._determine_layer(amendment.category, risk_level, performance_impact)

        # Impact assessments
        ethical_impact = await self._assess_ethical_impact(amendment)
        business_impact = await self._assess_business_impact(amendment)
        safety_impact = await self._assess_safety_impact(amendment)
        compliance_impact = await self._assess_compliance_impact(amendment)

        # Review and monitoring requirements
        review_requirements = self._get_review_requirements(recommended_layer, risk_level)
        monitoring_requirements = self._get_monitoring_requirements(amendment.category, risk_level)

        validation = AmendmentValidation(
            amendment_id=amendment.amendment_id,
            validated_at=datetime.now(),
            safety_score=safety_score,
            compatibility_score=compatibility_score,
            performance_impact=performance_impact,
            risk_level=risk_level,
            ethical_impact=ethical_impact,
            business_impact=business_impact,
            safety_impact=safety_impact,
            compliance_impact=compliance_impact,
            recommended_layer=recommended_layer,
            review_requirements=review_requirements,
            monitoring_requirements=monitoring_requirements
        )

        return validation

    async def _assess_safety(self, amendment: ConstitutionalAmendment) -> float:
        """Assess safety impact of amendment."""
        # Safety assessment logic
        safety_keywords = ['safety', 'security', 'risk', 'danger', 'harm', 'unstable']
        risk_keywords = ['violation', 'breach', 'exploit', 'attack', 'failure']

        safety_concerns = 0
        total_checks = 3

        # Check for safety-related changes
        changes_text = json.dumps(amendment.changes).lower()
        rationale_text = amendment.rationale.lower()

        for keyword in safety_keywords:
            if keyword in changes_text or keyword in rationale_text:
                safety_concerns += 1

        for keyword in risk_keywords:
            if keyword in changes_text or keyword in rationale_text:
                safety_concerns += 2

        # Category-based safety adjustment
        if amendment.category in [AmendmentCategory.ETHICAL_BOUNDARY, AmendmentCategory.SAFETY_LIMIT]:
            safety_concerns += 1  # Higher scrutiny for safety-related changes

        # Calculate safety score (higher is safer)
        safety_score = max(0.1, 1.0 - (safety_concerns / 10.0))

        return safety_score

    async def _assess_compatibility(self, amendment: ConstitutionalAmendment) -> float:
        """Assess compatibility with existing constitution."""
        # Compatibility assessment logic
        compatibility_score = 0.8  # Base compatibility

        # Check for conflicting changes
        existing_policies = self._get_existing_policies(amendment.category)

        conflicts = 0
        for policy in existing_policies:
            if self._detects_conflict(amendment.changes, policy):
                conflicts += 1

        # Reduce compatibility for conflicts
        compatibility_score -= (conflicts * 0.1)
        compatibility_score = max(0.1, compatibility_score)

        return compatibility_score

    async def _assess_performance_impact(self, amendment: ConstitutionalAmendment) -> float:
        """Assess performance impact of amendment."""
        # Performance impact assessment
        impact_indicators = {
            'optimization': 0.1,   # Performance improvements
            'efficiency': 0.05,    # Efficiency gains
            'monitoring': -0.05,   # Additional monitoring overhead
            'validation': -0.1,    # Additional validation overhead
            'complexity': -0.15    # Increased system complexity
        }

        impact = 0.0

        changes_text = json.dumps(amendment.changes).lower()
        for indicator, value in impact_indicators.items():
            if indicator in changes_text:
                impact += value

        return max(-1.0, min(1.0, impact))

    def _calculate_risk_level(self, safety: float, compatibility: float, performance: float) -> str:
        """Calculate overall risk level."""
        risk_score = (1 - safety) + (1 - compatibility) + abs(performance)

        if risk_score >= 2.0:
            return "critical"
        elif risk_score >= 1.5:
            return "high"
        elif risk_score >= 1.0:
            return "medium"
        else:
            return "low"

    def _determine_layer(self, category: AmendmentCategory, risk_level: str, performance_impact: float) -> AmendmentLayer:
        """Determine appropriate amendment layer."""
        # High-risk changes require higher layers
        if risk_level == "critical":
            return AmendmentLayer.FEDERATED
        elif risk_level == "high":
            return AmendmentLayer.OVERSIGHT
        elif risk_level == "medium":
            return AmendmentLayer.REVIEW

        # Category-based layer determination
        if category in [AmendmentCategory.ETHICAL_BOUNDARY, AmendmentCategory.SAFETY_LIMIT]:
            return AmendmentLayer.OVERSIGHT

        if category == AmendmentCategory.COMPLIANCE_RULE:
            return AmendmentLayer.REVIEW

        # Default to automatic for low-risk changes
        return AmendmentLayer.AUTOMATIC

    async def _assess_ethical_impact(self, amendment: ConstitutionalAmendment) -> str:
        """Assess ethical impact."""
        if amendment.category == AmendmentCategory.ETHICAL_BOUNDARY:
            return "Direct ethical boundary modification - high scrutiny required"
        elif amendment.category == AmendmentCategory.SAFETY_LIMIT:
            return "Potential safety implications - ethical review recommended"
        else:
            return "No significant ethical impact identified"

    async def _assess_business_impact(self, amendment: ConstitutionalAmendment) -> str:
        """Assess business impact."""
        if amendment.category == AmendmentCategory.BUSINESS_CONSTRAINT:
            return "Direct business constraint modification - business review required"
        elif amendment.category == AmendmentCategory.PERFORMANCE_OPTIMIZATION:
            return "Performance optimization - monitor business metrics"
        else:
            return "Minimal business impact expected"

    async def _assess_safety_impact(self, amendment: ConstitutionalAmendment) -> str:
        """Assess safety impact."""
        if amendment.category == AmendmentCategory.SAFETY_LIMIT:
            return "Direct safety limit modification - comprehensive safety testing required"
        elif 'safety' in amendment.title.lower() or 'safety' in amendment.description.lower():
            return "Safety-related changes - safety validation required"
        else:
            return "No direct safety impact identified"

    async def _assess_compliance_impact(self, amendment: ConstitutionalAmendment) -> str:
        """Assess compliance impact."""
        if amendment.category == AmendmentCategory.COMPLIANCE_RULE:
            return "Direct compliance rule modification - legal review required"
        elif 'compliance' in amendment.title.lower():
            return "Compliance implications - regulatory review recommended"
        else:
            return "No compliance impact identified"

    def _get_review_requirements(self, layer: AmendmentLayer, risk_level: str) -> List[str]:
        """Get review requirements for amendment."""
        requirements = []

        if layer == AmendmentLayer.AUTOMATIC:
            requirements.append("Automated validation completed")
        elif layer == AmendmentLayer.REVIEW:
            requirements.append("Human reviewer approval required")
        elif layer == AmendmentLayer.OVERSIGHT:
            requirements.append("Oversight committee review required")
            requirements.append("Risk assessment documentation")
        elif layer == AmendmentLayer.FEDERATED:
            requirements.append("Federated peer review required")
            requirements.append("Consensus validation")
            requirements.append("Cross-instance testing")

        if risk_level in ["high", "critical"]:
            requirements.append("Independent audit required")

        return requirements

    def _get_monitoring_requirements(self, category: AmendmentCategory, risk_level: str) -> List[str]:
        """Get monitoring requirements for amendment."""
        requirements = ["Standard post-implementation monitoring"]

        if risk_level in ["high", "critical"]:
            requirements.append("Enhanced monitoring for 90 days")
            requirements.append("Daily performance validation")

        if category == AmendmentCategory.ETHICAL_BOUNDARY:
            requirements.append("Ethical compliance monitoring")

        if category == AmendmentCategory.SAFETY_LIMIT:
            requirements.append("Safety metric monitoring")

        if category == AmendmentCategory.COMPLIANCE_RULE:
            requirements.append("Regulatory compliance monitoring")

        return requirements

    def _get_existing_policies(self, category: AmendmentCategory) -> List[Dict[str, Any]]:
        """Get existing policies for category."""
        # This would integrate with the actual governance system
        # For now, return mock policies
        return [
            {"category": category.value, "constraints": ["existing_rule_1"]},
            {"category": category.value, "constraints": ["existing_rule_2"]}
        ]

    def _detects_conflict(self, changes: Dict[str, Any], existing_policy: Dict[str, Any]) -> bool:
        """Detect if changes conflict with existing policy."""
        # Simple conflict detection logic
        changes_text = json.dumps(changes).lower()
        policy_text = json.dumps(existing_policy).lower()

        # Check for contradictory terms
        contradictions = [
            ("allow", "deny"),
            ("enable", "disable"),
            ("increase", "decrease"),
            ("expand", "restrict")
        ]

        for allow_term, deny_term in contradictions:
            if allow_term in changes_text and deny_term in policy_text:
                return True
            if deny_term in changes_text and allow_term in policy_text:
                return True

        return False

    async def review_amendment(self, amendment_id: str, reviewer: str,
                             decision: str, comments: str = "") -> bool:
        """Review and decide on an amendment."""
        if amendment_id not in self.amendments:
            return False

        amendment = self.amendments[amendment_id]

        if amendment.status != AmendmentStatus.UNDER_REVIEW:
            return False

        if decision.lower() == "approve":
            amendment.approvals_received += 1
            amendment.reviewers.append(f"{reviewer}: APPROVED - {comments}")

            if amendment.approvals_received >= amendment.approvals_required:
                await self._approve_amendment(amendment_id, reviewer, comments)
        else:
            amendment.status = AmendmentStatus.REJECTED
            amendment.reviewers.append(f"{reviewer}: REJECTED - {comments}")
            logger.info(f"❌ Amendment {amendment_id} rejected by {reviewer}")

        return True

    async def _approve_amendment(self, amendment_id: str, approver: str, comments: str) -> None:
        """Approve and implement an amendment."""
        amendment = self.amendments[amendment_id]
        amendment.status = AmendmentStatus.APPROVED
        amendment.reviewers.append(f"{approver}: FINAL APPROVAL - {comments}")

        # Implement the amendment
        success = await self._implement_amendment(amendment)

        if success:
            amendment.status = AmendmentStatus.IMPLEMENTED
            amendment.implemented_at = datetime.now()

            # Set rollback deadline
            if amendment.rollback_available:
                amendment.rollback_deadline = datetime.now() + timedelta(days=amendment.monitoring_period_days)

            logger.info(f"✅ Amendment {amendment_id} implemented successfully")
        else:
            amendment.status = AmendmentStatus.REJECTED
            logger.error(f"❌ Failed to implement amendment {amendment_id}")

    async def _implement_amendment(self, amendment: ConstitutionalAmendment) -> bool:
        """Implement the constitutional changes."""
        try:
            # This would integrate with the actual governance system
            # For now, simulate implementation
            logger.info(f"🔧 Implementing amendment {amendment.amendment_id}: {amendment.title}")

            # Simulate implementation steps
            await asyncio.sleep(0.1)  # Simulate processing time

            # Validate implementation
            validation = await self._validate_implementation(amendment)

            return validation.get('success', True)

        except Exception as e:
            logger.error(f"Implementation failed for amendment {amendment.amendment_id}: {e}")
            return False

    async def _validate_implementation(self, amendment: ConstitutionalAmendment) -> Dict[str, Any]:
        """Validate that amendment was implemented correctly."""
        # This would check the actual governance system
        # For now, return success
        return {
            'success': True,
            'validation_checks': ['syntax_valid', 'logic_consistent', 'no_conflicts'],
            'warnings': []
        }

    async def rollback_amendment(self, amendment_id: str, reason: str) -> bool:
        """Rollback an implemented amendment."""
        if amendment_id not in self.amendments:
            return False

        amendment = self.amendments[amendment_id]

        if amendment.status != AmendmentStatus.IMPLEMENTED or not amendment.rollback_available:
            return False

        if amendment.rollback_deadline and datetime.now() > amendment.rollback_deadline:
            logger.warning(f"Rollback deadline passed for amendment {amendment_id}")
            return False

        try:
            # Implement rollback
            success = await self._rollback_implementation(amendment)

            if success:
                amendment.status = AmendmentStatus.ROLLED_BACK
                logger.info(f"🔄 Amendment {amendment_id} rolled back: {reason}")
                return True
            else:
                logger.error(f"Failed to rollback amendment {amendment_id}")
                return False

        except Exception as e:
            logger.error(f"Rollback failed for amendment {amendment_id}: {e}")
            return False

    async def _rollback_implementation(self, amendment: ConstitutionalAmendment) -> bool:
        """Rollback the amendment implementation."""
        try:
            # This would revert the governance system changes
            logger.info(f"🔧 Rolling back amendment {amendment.amendment_id}")

            # Simulate rollback steps
            await asyncio.sleep(0.1)

            return True

        except Exception as e:
            logger.error(f"Rollback implementation failed: {e}")
            return False

    def get_amendment_status(self, amendment_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of an amendment."""
        if amendment_id not in self.amendments:
            return None

        amendment = self.amendments[amendment_id]
        validation = self.validations.get(amendment_id)

        return {
            'amendment_id': amendment.amendment_id,
            'title': amendment.title,
            'status': amendment.status.value,
            'layer': amendment.layer.value,
            'category': amendment.category.value,
            'proposed_at': amendment.proposed_at.isoformat(),
            'implemented_at': amendment.implemented_at.isoformat() if amendment.implemented_at else None,
            'approvals_received': amendment.approvals_received,
            'approvals_required': amendment.approvals_required,
            'validation': {
                'safety_score': validation.safety_score if validation else None,
                'risk_level': validation.risk_level if validation else None,
                'recommended_layer': validation.recommended_layer.value if validation else None
            } if validation else None
        }

    def get_pending_reviews(self) -> List[Dict[str, Any]]:
        """Get amendments pending review."""
        pending = [
            self.get_amendment_status(aid)
            for aid, amendment in self.amendments.items()
            if amendment.status == AmendmentStatus.UNDER_REVIEW
        ]
        return pending

    def get_amendment_statistics(self) -> Dict[str, Any]:
        """Get amendment protocol statistics."""
        total_amendments = len(self.amendments)
        implemented = len([a for a in self.amendments.values() if a.status == AmendmentStatus.IMPLEMENTED])
        rejected = len([a for a in self.amendments.values() if a.status == AmendmentStatus.REJECTED])
        rolled_back = len([a for a in self.amendments.values() if a.status == AmendmentStatus.ROLLED_BACK])

        # Category breakdown
        categories = {}
        for amendment in self.amendments.values():
            cat = amendment.category.value
            if cat not in categories:
                categories[cat] = 0
            categories[cat] += 1

        # Layer breakdown
        layers = {}
        for amendment in self.amendments.values():
            layer = amendment.layer.value
            if layer not in layers:
                layers[layer] = 0
            layers[layer] += 1

        return {
            "total_amendments": total_amendments,
            "implemented": implemented,
            "rejected": rejected,
            "rolled_back": rolled_back,
            "success_rate": implemented / total_amendments if total_amendments > 0 else 0,
            "rollback_rate": rolled_back / implemented if implemented > 0 else 0,
            "by_category": categories,
            "by_layer": layers
        }

# Global instance
_amendment_protocol = None

def get_amendment_protocol(instance_id: Optional[str] = None) -> LayeredAmendmentProtocol:
    """Get the global amendment protocol instance."""
    global _amendment_protocol
    if _amendment_protocol is None:
        _amendment_protocol = LayeredAmendmentProtocol(instance_id)
    return _amendment_protocol

# Test function
async def test_amendment_protocol():
    """Test the amendment protocol functionality."""
    print("📜 Testing Layered Amendment Protocol")
    print("=" * 50)

    # Create protocol
    protocol = get_amendment_protocol("test_instance_001")

    # Test amendment proposals
    test_amendments = [
        {
            'title': 'Optimize Ethical Bias Detection',
            'description': 'Improve bias detection algorithms for better ethical compliance',
            'category': 'ethical_boundary',
            'changes': {'bias_threshold': 0.15},
            'rationale': 'Current bias detection is too sensitive, causing false positives',
            'evidence': ['Performance metrics show 25% false positive rate'],
            'proposed_by': 'optimization_engine'
        },
        {
            'title': 'Update Business Constraints',
            'description': 'Adjust user satisfaction targets based on market feedback',
            'category': 'business_constraint',
            'changes': {'satisfaction_target': 0.85},
            'rationale': 'Market research indicates higher satisfaction expectations',
            'evidence': ['Customer surveys show 82% satisfaction target'],
            'proposed_by': 'business_analytics'
        },
        {
            'title': 'Add Performance Monitoring',
            'description': 'Implement additional performance metrics for safety validation',
            'category': 'safety_limit',
            'changes': {'monitoring_metrics': ['latency', 'throughput', 'error_rate']},
            'rationale': 'Need better visibility into system performance for safety',
            'evidence': ['Recent incidents showed monitoring gaps'],
            'proposed_by': 'safety_team'
        }
    ]

    amendment_ids = []
    for amendment_data in test_amendments:
        try:
            amendment_id = await protocol.propose_amendment(amendment_data)
            amendment_ids.append(amendment_id)
            print(f"📝 Proposed amendment: {amendment_id}")
        except Exception as e:
            print(f"❌ Failed to propose amendment: {e}")

    # Check pending reviews
    pending = protocol.get_pending_reviews()
    print(f"\n📋 {len(pending)} amendments pending review")

    # Simulate reviews
    for amendment_id in amendment_ids:
        status = protocol.get_amendment_status(amendment_id)
        if status:
            print(f"   • {status['title']}: {status['status']} ({status['layer']} layer)")

            # Auto-approve automatic layer amendments
            if status['layer'] == 'automatic':
                await protocol.review_amendment(amendment_id, 'system', 'approve', 'Auto-approved')
            elif status['layer'] == 'review':
                await protocol.review_amendment(amendment_id, 'reviewer', 'approve', 'Approved after review')

    # Check final status
    print("\n📊 Final Amendment Status:")
    for amendment_id in amendment_ids:
        status = protocol.get_amendment_status(amendment_id)
        if status:
            print(f"   • {status['amendment_id']}: {status['status']}")

    # Show statistics
    stats = protocol.get_amendment_statistics()
    print("\n📈 Protocol Statistics:")
    print(f"   Total amendments: {stats['total_amendments']}")
    print(f"   Success rate: {stats['success_rate']:.2%}")
    print(f"   By layer: {stats['by_layer']}")
    print(f"   By category: {stats['by_category']}")

    print("\n🎉 Amendment protocol test completed!")

if __name__ == "__main__":
    asyncio.run(test_amendment_protocol())
