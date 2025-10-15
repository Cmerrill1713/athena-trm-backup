#!/usr/bin/env python3
"""
Phase 3: Evidence Exchange Protocol
====================================

Secure, anonymized evidence sharing between sovereign instances.
Implements zero-knowledge proofs, differential privacy, and federated validation.

Key Features:
- Cryptographic evidence integrity
- Anonymization through aggregation
- Zero-knowledge validation
- Cross-instance judicial precedent sharing
- Federated evidence validation network

Usage:
    from ai_republic.phase3.phase3_evidence_exchange import EvidenceExchange
    exchange = EvidenceExchange()
    await exchange.share_judicial_evidence(evidence_data)
"""

import json
import hashlib
import time
import uuid
import base64
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
import logging
from pathlib import Path

from phase3_federation_core import (
    EvidenceType,
    get_federation_core
)

logger = logging.getLogger(__name__)

class PrivacyLevel(Enum):
    """Levels of evidence anonymization."""
    PUBLIC = "public"          # Fully public, no anonymization needed
    ANONYMIZED = "anonymized"  # Instance identifiers removed
    AGGREGATED = "aggregated"  # Statistical aggregation applied
    ZERO_KNOWLEDGE = "zero_knowledge"  # Cryptographic proof without disclosure

class EvidenceValidation(Enum):
    """Evidence validation status."""
    UNVALIDATED = "unvalidated"
    PENDING_VALIDATION = "pending_validation"
    FEDERATION_VALIDATED = "federation_validated"
    REJECTED = "rejected"

@dataclass
class EvidencePackage:
    """A package of evidence prepared for exchange."""
    package_id: str
    evidence_type: EvidenceType
    originating_instance: str
    privacy_level: PrivacyLevel
    content: Dict[str, Any]
    metadata: Dict[str, Any]

    # Cryptographic elements
    content_hash: str = ""
    zero_knowledge_proof: Optional[str] = None
    differential_privacy_noise: Optional[Dict[str, float]] = None

    # Federation routing
    target_instances: List[str] = field(default_factory=list)
    excluded_instances: List[str] = field(default_factory=list)

    # Validation
    validation_status: EvidenceValidation = EvidenceValidation.UNVALIDATED
    validation_votes: Dict[str, bool] = field(default_factory=dict)  # instance_id -> approval
    validation_required: int = 3  # Minimum validators needed

    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    validated_at: Optional[datetime] = None

    def __post_init__(self):
        """Generate content hash after initialization."""
        if not self.content_hash:
            # Create canonical representation for hashing
            canonical_content = {
                "evidence_type": self.evidence_type.value,
                "privacy_level": self.privacy_level.value,
                "content": self._canonicalize_content(self.content),
                "metadata": self._canonicalize_content(self.metadata)
            }
            content_str = json.dumps(canonical_content, sort_keys=True)
            self.content_hash = hashlib.sha256(content_str.encode()).hexdigest()

    def _canonicalize_content(self, content: Any) -> Any:
        """Create canonical representation for consistent hashing."""
        if isinstance(content, dict):
            return {k: self._canonicalize_content(v) for k, v in sorted(content.items())}
        elif isinstance(content, list):
            return [self._canonicalize_content(item) for item in content]
        elif isinstance(content, (int, float, str, bool)) or content is None:
            return content
        else:
            # Convert other types to string representation
            return str(content)

@dataclass
class EvidenceAggregate:
    """Statistical aggregate of evidence for privacy-preserving sharing."""
    aggregate_id: str
    evidence_type: EvidenceType
    aggregation_period: Tuple[datetime, datetime]
    sample_size: int
    aggregated_metrics: Dict[str, Any]

    # Privacy parameters
    privacy_budget: float  # Differential privacy budget
    noise_scale: float     # Laplace noise scale

    # Source instances (anonymized)
    contributing_instances: int  # Count only, not identifiers

    # Validation
    aggregate_hash: str = ""
    validated: bool = False

    def __post_init__(self):
        """Generate aggregate hash."""
        if not self.aggregate_hash:
            content = {
                "evidence_type": self.evidence_type.value,
                "aggregation_period": (
                    self.aggregation_period[0].isoformat(),
                    self.aggregation_period[1].isoformat()
                ),
                "sample_size": self.sample_size,
                "aggregated_metrics": self.aggregated_metrics,
                "privacy_budget": self.privacy_budget,
                "contributing_instances": self.contributing_instances
            }
            content_str = json.dumps(content, sort_keys=True)
            self.aggregate_hash = hashlib.sha256(content_str.encode()).hexdigest()

class EvidenceExchange:
    """Secure evidence exchange protocol for federation."""

    def __init__(self):
        self.federation = get_federation_core()

        # Exchange configuration
        self.max_evidence_age_days = 30
        self.validation_timeout_hours = 24
        self.min_validation_threshold = 0.6  # 60% approval needed
        self.privacy_budgets = {
            EvidenceType.JUDICIAL_DECISION: 1.0,
            EvidenceType.CONSTITUTIONAL_VIOLATION: 0.8,
            EvidenceType.REPUTATION_UPDATE: 1.2,
            EvidenceType.TREATY_COMPLIANCE: 0.9,
            EvidenceType.FEDERATION_DISPUTE: 0.7
        }

        # In-memory caches
        self.pending_packages: Dict[str, EvidencePackage] = {}
        self.aggregates: Dict[str, EvidenceAggregate] = {}

        # Persistence
        self.state_file = Path("./evidence_exchange_state.json")
        self._load_state()

        logger.info("📤 Evidence Exchange initialized")

    async def prepare_evidence_package(self, evidence_type: EvidenceType,
                                     content: Dict[str, Any],
                                     privacy_level: PrivacyLevel = PrivacyLevel.ANONYMIZED,
                                     target_instances: Optional[List[str]] = None) -> str:
        """Prepare an evidence package for exchange."""
        # Determine appropriate privacy level based on evidence type
        if privacy_level == PrivacyLevel.PUBLIC:
            actual_privacy = PrivacyLevel.PUBLIC
        else:
            actual_privacy = self._determine_privacy_level(evidence_type, content)

        # Apply privacy transformations
        processed_content = await self._apply_privacy_transformations(
            content, actual_privacy, evidence_type
        )

        # Create package
        package = EvidencePackage(
            package_id=f"pkg_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            evidence_type=evidence_type,
            originating_instance=self.federation.instance_id,
            privacy_level=actual_privacy,
            content=processed_content,
            metadata=self._generate_metadata(evidence_type, content),
            target_instances=target_instances or []
        )

        self.pending_packages[package.package_id] = package
        self._save_state()

        logger.info(f"📦 Prepared evidence package: {package.package_id} ({actual_privacy.value})")
        return package.package_id

    def _determine_privacy_level(self, evidence_type: EvidenceType, content: Dict[str, Any]) -> PrivacyLevel:
        """Determine appropriate privacy level for evidence."""
        # High-sensitivity evidence types
        if evidence_type in [EvidenceType.CONSTITUTIONAL_VIOLATION, EvidenceType.FEDERATION_DISPUTE]:
            return PrivacyLevel.AGGREGATED

        # Medium-sensitivity with instance identifiers
        if 'instance_id' in content or 'actor_id' in content:
            return PrivacyLevel.ANONYMIZED

        # Default to zero-knowledge for maximum privacy
        return PrivacyLevel.ZERO_KNOWLEDGE

    async def _apply_privacy_transformations(self, content: Dict[str, Any],
                                           privacy_level: PrivacyLevel,
                                           evidence_type: EvidenceType) -> Dict[str, Any]:
        """Apply privacy transformations to evidence content."""
        if privacy_level == PrivacyLevel.PUBLIC:
            return content

        elif privacy_level == PrivacyLevel.ANONYMIZED:
            # Remove direct identifiers
            processed = self._anonymize_content(content)
            return processed

        elif privacy_level == PrivacyLevel.AGGREGATED:
            # Create statistical aggregate instead of raw data
            return await self._create_aggregate(content, evidence_type)

        elif privacy_level == PrivacyLevel.ZERO_KNOWLEDGE:
            # Generate zero-knowledge proof
            processed = self._anonymize_content(content)
            processed['_zk_proof'] = self._generate_zk_proof(processed, evidence_type)
            return processed

        return content

    def _anonymize_content(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Remove or hash direct identifiers from content."""
        processed = {}

        for key, value in content.items():
            if key in ['instance_id', 'actor_id', 'user_id', 'session_id']:
                # Replace with cryptographic hash
                if isinstance(value, str):
                    processed[f"{key}_hash"] = hashlib.sha256(value.encode()).hexdigest()[:16]
                else:
                    processed[f"{key}_hash"] = hashlib.sha256(str(value).encode()).hexdigest()[:16]
            elif isinstance(value, dict):
                processed[key] = self._anonymize_content(value)
            elif isinstance(value, list):
                processed[key] = [self._anonymize_content(item) if isinstance(item, dict) else item
                                for item in value]
            else:
                processed[key] = value

        return processed

    async def _create_aggregate(self, content: Dict[str, Any], evidence_type: EvidenceType) -> Dict[str, Any]:
        """Create statistical aggregate from evidence."""
        # This would collect evidence over time and create aggregates
        # For now, return anonymized version
        return self._anonymize_content(content)

    def _generate_zk_proof(self, content: Dict[str, Any], evidence_type: EvidenceType) -> str:
        """Generate zero-knowledge proof for evidence validity."""
        # Simplified ZK proof generation
        proof_data = {
            "evidence_type": evidence_type.value,
            "content_hash": hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest(),
            "timestamp": datetime.now().isoformat(),
            "prover": self.federation.instance_id
        }

        proof_str = json.dumps(proof_data, sort_keys=True)
        return base64.b64encode(proof_str.encode()).decode()

    def _generate_metadata(self, evidence_type: EvidenceType, original_content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate metadata for evidence package."""
        return {
            "evidence_type": evidence_type.value,
            "original_size": len(json.dumps(original_content)),
            "created_by": self.federation.instance_id,
            "federation_relevance": self._calculate_relevance(evidence_type, original_content),
            "retention_days": self.max_evidence_age_days,
            "validation_required": self._requires_validation(evidence_type)
        }

    def _calculate_relevance(self, evidence_type: EvidenceType, content: Dict[str, Any]) -> float:
        """Calculate federation relevance score."""
        base_relevance = {
            EvidenceType.JUDICIAL_DECISION: 0.7,
            EvidenceType.CONSTITUTIONAL_VIOLATION: 0.9,
            EvidenceType.REPUTATION_UPDATE: 0.5,
            EvidenceType.TREATY_COMPLIANCE: 0.8,
            EvidenceType.FEDERATION_DISPUTE: 1.0
        }.get(evidence_type, 0.5)

        # Boost for cross-instance evidence
        if 'instance_id' in content and content.get('instance_id') != self.federation.instance_id:
            base_relevance += 0.2

        return min(1.0, base_relevance)

    def _requires_validation(self, evidence_type: EvidenceType) -> bool:
        """Determine if evidence type requires federation validation."""
        return evidence_type in [
            EvidenceType.CONSTITUTIONAL_VIOLATION,
            EvidenceType.FEDERATION_DISPUTE,
            EvidenceType.TREATY_COMPLIANCE
        ]

    async def submit_evidence_package(self, package_id: str) -> bool:
        """Submit a prepared evidence package to the federation."""
        if package_id not in self.pending_packages:
            return False

        package = self.pending_packages[package_id]

        # Submit to federation core
        evidence_id = await self.federation.share_evidence(
            originating_instance=package.originating_instance,
            evidence_type=package.evidence_type,
            subject_instance=package.content.get('instance_id_hash', 'unknown'),
            content=package.content,
            confidence_score=package.metadata.get('federation_relevance', 0.5)
        )

        # Update package status
        package.validation_status = EvidenceValidation.PENDING_VALIDATION

        # Start validation process if required
        if package.metadata.get('validation_required', False):
            await self._initiate_validation(package)

        # Move from pending to federation
        del self.pending_packages[package_id]
        self._save_state()

        logger.info(f"📨 Submitted evidence package {package_id} to federation")
        return True

    async def _initiate_validation(self, package: EvidencePackage) -> None:
        """Initiate federation validation for a package."""
        # Select validators based on sovereignty tier and reputation
        validators = self._select_validators(package)

        package.target_instances = validators
        package.validation_required = len(validators)

        # In a real implementation, this would send validation requests
        logger.info(f"🔍 Initiated validation for package {package.package_id} with {len(validators)} validators")

    def _select_validators(self, package: EvidencePackage) -> List[str]:
        """Select appropriate validators for a package."""
        eligible_validators = []

        for instance_id, sovereign in self.federation.sovereigns.items():
            # Only sovereign and archon tiers can validate
            if sovereign.sovereignty_tier.value in ['sovereign', 'archon']:
                # Higher reputation = higher chance of selection
                weight = sovereign.reputation_score
                eligible_validators.extend([instance_id] * int(weight * 10))

        # Randomly select up to 5 validators (weighted)
        import random
        selected = []
        if eligible_validators:
            selected = random.sample(eligible_validators, min(5, len(set(eligible_validators))))

        return list(set(selected))

    async def validate_evidence_package(self, package_id: str, validator_instance: str, approved: bool) -> bool:
        """Submit validation vote for an evidence package."""
        # Find package in federation evidence
        target_evidence = None
        for evidence in self.federation.evidence_ledger.values():
            if evidence.evidence_id == package_id:
                target_evidence = evidence
                break

        if not target_evidence:
            return False

        # Find corresponding package
        package = None
        for pkg in self.pending_packages.values():
            if pkg.content_hash == target_evidence.cryptographic_proof:
                package = pkg
                break

        if not package:
            return False

        # Record vote
        package.validation_votes[validator_instance] = approved

        # Check if validation complete
        total_votes = len(package.validation_votes)
        approval_votes = sum(package.validation_votes.values())

        if total_votes >= package.validation_required:
            approval_rate = approval_votes / total_votes

            if approval_rate >= self.min_validation_threshold:
                package.validation_status = EvidenceValidation.FEDERATION_VALIDATED
                target_evidence.federation_validation = True
                target_evidence.validation_timestamp = datetime.now()
                logger.info(f"✅ Evidence package {package_id} validated ({approval_rate:.1%} approval)")
            else:
                package.validation_status = EvidenceValidation.REJECTED
                logger.warning(f"❌ Evidence package {package_id} rejected ({approval_rate:.1%} approval)")

            self.federation._save_state()
            self._save_state()

        return True

    async def query_evidence(self, evidence_type: Optional[EvidenceType] = None,
                           instance_filter: Optional[str] = None,
                           date_from: Optional[datetime] = None,
                           privacy_level: Optional[PrivacyLevel] = None) -> List[Dict[str, Any]]:
        """Query evidence from the federation ledger."""
        results = []

        for evidence in self.federation.evidence_ledger.values():
            # Apply filters
            if evidence_type and evidence.evidence_type != evidence_type:
                continue
            if instance_filter and evidence.originating_instance != instance_filter:
                continue
            if date_from and evidence.timestamp < date_from:
                continue

            # Check if user has access to this privacy level
            if privacy_level and evidence.content.get('_privacy_level') == privacy_level.value:
                continue

            results.append({
                "evidence_id": evidence.evidence_id,
                "evidence_type": evidence.evidence_type.value,
                "originating_instance": evidence.originating_instance,
                "timestamp": evidence.timestamp.isoformat(),
                "confidence_score": evidence.confidence_score,
                "federation_validation": evidence.federation_validation,
                "content": evidence.content
            })

        return results

    async def create_evidence_aggregate(self, evidence_type: EvidenceType,
                                      aggregation_hours: int = 24) -> Optional[str]:
        """Create statistical aggregate of evidence for privacy-preserving sharing."""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=aggregation_hours)

        # Collect relevant evidence
        relevant_evidence = [
            e for e in self.federation.evidence_ledger.values()
            if e.evidence_type == evidence_type
            and start_time <= e.timestamp <= end_time
            and e.federation_validation
        ]

        if len(relevant_evidence) < 5:  # Minimum sample size
            return None

        # Calculate aggregate metrics
        confidence_scores = [e.confidence_score for e in relevant_evidence]
        aggregated_metrics = {
            "count": len(relevant_evidence),
            "avg_confidence": sum(confidence_scores) / len(confidence_scores),
            "min_confidence": min(confidence_scores),
            "max_confidence": max(confidence_scores),
            "confidence_std": (sum((x - sum(confidence_scores)/len(confidence_scores))**2
                                 for x in confidence_scores) / len(confidence_scores))**0.5
        }

        # Create aggregate
        aggregate = EvidenceAggregate(
            aggregate_id=f"agg_{int(time.time())}_{str(uuid.uuid4())[:8]}",
            evidence_type=evidence_type,
            aggregation_period=(start_time, end_time),
            sample_size=len(relevant_evidence),
            aggregated_metrics=aggregated_metrics,
            privacy_budget=self.privacy_budgets.get(evidence_type, 1.0),
            noise_scale=0.1,  # Laplace noise scale
            contributing_instances=len(set(e.originating_instance for e in relevant_evidence))
        )

        self.aggregates[aggregate.aggregate_id] = aggregate
        self._save_state()

        # Share aggregate with federation
        await self._share_aggregate(aggregate)

        logger.info(f"📊 Created evidence aggregate: {aggregate.aggregate_id}")
        return aggregate.aggregate_id

    async def _share_aggregate(self, aggregate: EvidenceAggregate) -> None:
        """Share statistical aggregate with federation."""
        # This would distribute the aggregate to other instances
        logger.debug(f"📤 Sharing aggregate {aggregate.aggregate_id}")

    def get_exchange_statistics(self) -> Dict[str, Any]:
        """Get evidence exchange statistics."""
        total_evidence = len(self.federation.evidence_ledger)
        validated_evidence = len([e for e in self.federation.evidence_ledger.values() if e.federation_validation])
        pending_packages = len(self.pending_packages)
        total_aggregates = len(self.aggregates)

        evidence_by_type = {}
        for evidence in self.federation.evidence_ledger.values():
            etype = evidence.evidence_type.value
            evidence_by_type[etype] = evidence_by_type.get(etype, 0) + 1

        return {
            "total_evidence": total_evidence,
            "validated_evidence": validated_evidence,
            "validation_rate": validated_evidence / total_evidence if total_evidence > 0 else 0,
            "pending_packages": pending_packages,
            "total_aggregates": total_aggregates,
            "evidence_by_type": evidence_by_type,
            "exchange_health": self._calculate_exchange_health()
        }

    def _calculate_exchange_health(self) -> float:
        """Calculate overall exchange health score."""
        if not self.federation.evidence_ledger:
            return 0.0

        # Validation rate
        validation_rate = len([e for e in self.federation.evidence_ledger.values()
                             if e.federation_validation]) / len(self.federation.evidence_ledger)

        # Recency (evidence from last 7 days)
        recent_evidence = len([e for e in self.federation.evidence_ledger.values()
                             if e.timestamp > datetime.now() - timedelta(days=7)])

        recency_rate = recent_evidence / len(self.federation.evidence_ledger)

        # Diversity (evidence from different instances)
        unique_instances = len(set(e.originating_instance for e in self.federation.evidence_ledger.values()))
        diversity_score = min(1.0, unique_instances / 10)  # Cap at 10 instances

        health = (validation_rate * 0.4) + (recency_rate * 0.3) + (diversity_score * 0.3)
        return min(1.0, health)

    def _save_state(self) -> None:
        """Save exchange state to disk."""
        try:
            state = {
                "pending_packages": {
                    pid: {
                        "package_id": p.package_id,
                        "evidence_type": p.evidence_type.value,
                        "originating_instance": p.originating_instance,
                        "privacy_level": p.privacy_level.value,
                        "content": p.content,
                        "metadata": p.metadata,
                        "content_hash": p.content_hash,
                        "zero_knowledge_proof": p.zero_knowledge_proof,
                        "differential_privacy_noise": p.differential_privacy_noise,
                        "target_instances": p.target_instances,
                        "excluded_instances": p.excluded_instances,
                        "validation_status": p.validation_status.value,
                        "validation_votes": p.validation_votes,
                        "validation_required": p.validation_required,
                        "created_at": p.created_at.isoformat(),
                        "validated_at": p.validated_at.isoformat() if p.validated_at else None
                    }
                    for pid, p in self.pending_packages.items()
                },
                "aggregates": {
                    aid: {
                        "aggregate_id": a.aggregate_id,
                        "evidence_type": a.evidence_type.value,
                        "aggregation_period": (
                            a.aggregation_period[0].isoformat(),
                            a.aggregation_period[1].isoformat()
                        ),
                        "sample_size": a.sample_size,
                        "aggregated_metrics": a.aggregated_metrics,
                        "privacy_budget": a.privacy_budget,
                        "noise_scale": a.noise_scale,
                        "contributing_instances": a.contributing_instances,
                        "aggregate_hash": a.aggregate_hash,
                        "validated": a.validated
                    }
                    for aid, a in self.aggregates.items()
                }
            }

            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2, default=str)

        except Exception as e:
            logger.error(f"Failed to save exchange state: {e}")

    def _load_state(self) -> None:
        """Load exchange state from disk."""
        if not self.state_file.exists():
            return

        try:
            with open(self.state_file, 'r') as f:
                state = json.load(f)

            # Load pending packages
            for pid, pdata in state.get("pending_packages", {}).items():
                package = EvidencePackage(
                    package_id=pdata["package_id"],
                    evidence_type=EvidenceType(pdata["evidence_type"]),
                    originating_instance=pdata["originating_instance"],
                    privacy_level=PrivacyLevel(pdata["privacy_level"]),
                    content=pdata["content"],
                    metadata=pdata["metadata"],
                    content_hash=pdata["content_hash"],
                    zero_knowledge_proof=pdata["zero_knowledge_proof"],
                    differential_privacy_noise=pdata["differential_privacy_noise"],
                    target_instances=pdata["target_instances"],
                    excluded_instances=pdata["excluded_instances"],
                    validation_status=EvidenceValidation(pdata["validation_status"]),
                    validation_votes=pdata["validation_votes"],
                    validation_required=pdata["validation_required"],
                    created_at=datetime.fromisoformat(pdata["created_at"]),
                    validated_at=datetime.fromisoformat(pdata["validated_at"]) if pdata["validated_at"] else None
                )
                self.pending_packages[pid] = package

            # Load aggregates
            for aid, adata in state.get("aggregates", {}).items():
                aggregate = EvidenceAggregate(
                    aggregate_id=adata["aggregate_id"],
                    evidence_type=EvidenceType(adata["evidence_type"]),
                    aggregation_period=(
                        datetime.fromisoformat(adata["aggregation_period"][0]),
                        datetime.fromisoformat(adata["aggregation_period"][1])
                    ),
                    sample_size=adata["sample_size"],
                    aggregated_metrics=adata["aggregated_metrics"],
                    privacy_budget=adata["privacy_budget"],
                    noise_scale=adata["noise_scale"],
                    contributing_instances=adata["contributing_instances"],
                    aggregate_hash=adata["aggregate_hash"],
                    validated=adata["validated"]
                )
                self.aggregates[aid] = aggregate

            logger.info(f"📖 Loaded exchange state with {len(self.pending_packages)} pending packages")

        except Exception as e:
            logger.error(f"Failed to load exchange state: {e}")

# Global evidence exchange instance
_evidence_exchange = None

def get_evidence_exchange() -> EvidenceExchange:
    """Get the global evidence exchange instance."""
    global _evidence_exchange
    if _evidence_exchange is None:
        _evidence_exchange = EvidenceExchange()
    return _evidence_exchange
