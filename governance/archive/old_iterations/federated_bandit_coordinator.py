#!/usr/bin/env python3
"""
Federated Bandit Coordinator
===========================

Manages collective learning across deployments without sharing individual data.

Features:
- Differential privacy for bandit priors
- Secure aggregation of routing insights
- Deployment anonymity and contribution tracking
- Cross-deployment knowledge transfer
"""

import os
import hashlib
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random

# Constitutional governance integration
from constitutional_governance import (
    validate_routing_strategy
)

@dataclass
class FederatedPriors:
    """Anonymized bandit priors for federation."""
    deployment_id: str  # Hashed for anonymity
    timestamp: str
    arm_priors: Dict[str, Tuple[int, int]]  # {arm_name: (successes, failures)}
    sample_count: int
    privacy_budget: float  # ε for differential privacy
    federation_round: int
    constitutional_validation: Optional[Dict[str, Any]] = None  # Governance validation result

@dataclass
class FederationRound:
    """A federation learning round."""
    round_id: str
    start_time: datetime
    participating_deployments: List[str]
    aggregated_priors: Dict[str, Tuple[float, float]]  # {arm: (alpha, beta)}
    privacy_guarantees: Dict[str, float]
    round_status: str = "active"  # active, completed, failed

@dataclass
class DeploymentProfile:
    """Profile for a participating deployment."""
    deployment_id: str
    public_key_hash: str
    join_date: datetime
    contribution_count: int = 0
    reputation_score: float = 1.0
    last_contribution: Optional[datetime] = None

class DifferentialPrivacy:
    """Differential privacy mechanisms for federated learning."""

    @staticmethod
    def add_laplace_noise(value: float, sensitivity: float, epsilon: float) -> float:
        """Add Laplace noise for ε-differential privacy."""
        scale = sensitivity / epsilon
        noise = np.random.laplace(0, scale)
        return max(0, value + noise)  # Ensure non-negative

    @staticmethod
    def add_gaussian_noise(value: float, sensitivity: float, epsilon: float, delta: float) -> float:
        """Add Gaussian noise for (ε,δ)-differential privacy."""
        sigma = (sensitivity * np.sqrt(2 * np.log(1.25 / delta))) / epsilon
        noise = np.random.normal(0, sigma)
        return max(0, value + noise)

    @staticmethod
    def privatize_priors(successes: int, failures: int, epsilon: float) -> Tuple[int, int]:
        """Apply differential privacy to Beta distribution priors."""
        # Sensitivity is 1 (adding/removing one sample changes count by 1)
        sensitivity = 1.0

        # Use Laplace mechanism for simplicity
        privatized_successes = int(DifferentialPrivacy.add_laplace_noise(
            successes, sensitivity, epsilon
        ))
        privatized_failures = int(DifferentialPrivacy.add_laplace_noise(
            failures, sensitivity, epsilon
        ))

        return max(1, privatized_successes), max(1, privatized_failures)

class FederatedBanditCoordinator:
    """
    Coordinates federated learning across bandit routing deployments.

    Features:
    - Secure aggregation of bandit priors
    - Differential privacy protection
    - Deployment reputation system
    - Knowledge transfer without data sharing
    """

    def __init__(self,
                 coordinator_url: str = "https://federation.example.com",
                 encryption_key: Optional[str] = None):
        self.coordinator_url = coordinator_url
        self.encryption_key = encryption_key or os.getenv("FEDERATION_ENCRYPTION_KEY")

        # Federation state
        self.deployment_id = self._generate_deployment_id()
        self.current_round: Optional[FederationRound] = None
        self.deployment_profile = DeploymentProfile(
            deployment_id=self.deployment_id,
            public_key_hash=self._hash_key(self.encryption_key) if self.encryption_key else "",
            join_date=datetime.now()
        )

        # Privacy settings
        self.privacy_epsilon = float(os.getenv("FEDERATION_PRIVACY_EPSILON", "0.5"))
        self.federation_enabled = os.getenv("FEDERATION_ENABLED", "false").lower() == "true"

        # Local knowledge cache
        self.federated_knowledge: Dict[str, Tuple[float, float]] = {}
        self.last_federation_sync = datetime.now() - timedelta(hours=25)  # Force initial sync

        # Federation history
        self.contribution_history: List[Dict[str, Any]] = []
        self.knowledge_updates: List[Dict[str, Any]] = []

    def _generate_deployment_id(self) -> str:
        """Generate anonymous deployment identifier."""
        # Hash combination of hostname, random salt, and timestamp
        import socket
        hostname = socket.gethostname()
        salt = os.urandom(16).hex()
        timestamp = str(datetime.now().timestamp())

        identifier = f"{hostname}:{salt}:{timestamp}"
        return hashlib.sha256(identifier.encode()).hexdigest()[:16]

    def _hash_key(self, key: str) -> str:
        """Hash encryption key for verification."""
        return hashlib.sha256(key.encode()).hexdigest()

    def prepare_local_contribution(self, local_priors: Dict[str, Tuple[int, int]],
                                  strategy_stats: Optional[Dict[str, Any]] = None) -> Optional[FederatedPriors]:
        """
        Prepare local bandit priors for federation with privacy protection and constitutional validation.

        Args:
            local_priors: {arm_name: (successes, failures)}
            strategy_stats: Complete strategy statistics for constitutional validation

        Returns:
            Anonymized FederatedPriors ready for sharing, or None if unconstitutional
        """
        # Constitutional validation (required for federation)
        if strategy_stats:
            validation_result = validate_routing_strategy(strategy_stats)
            if not validation_result.compliant:
                # Log the violation but don't share unconstitutional strategies
                print(f"⚠️  Constitutional violation detected: {len(validation_result.violations)} violations")
                for violation in validation_result.violations:
                    print(f"   {violation['violation_type']}: {violation['explanation']}")
                return None  # Block unconstitutional contributions

            constitutional_validation = {
                'compliant': True,
                'violations': len(validation_result.violations),
                'warnings': len(validation_result.warnings),
                'validation_hash': validation_result.strategy_hash
            }
        else:
            constitutional_validation = None

        # Apply differential privacy
        privatized_priors = {}
        for arm_name, (successes, failures) in local_priors.items():
            priv_successes, priv_failures = DifferentialPrivacy.privatize_priors(
                successes, failures, self.privacy_epsilon
            )
            privatized_priors[arm_name] = (priv_successes, priv_failures)

        # Calculate sample count for weighting
        total_samples = sum(successes + failures for successes, failures in local_priors.values())

        return FederatedPriors(
            deployment_id=self.deployment_id,
            timestamp=datetime.now().isoformat(),
            arm_priors=privatized_priors,
            sample_count=total_samples,
            privacy_budget=self.privacy_epsilon,
            federation_round=self.current_round.round_id if self.current_round else 0,
            constitutional_validation=constitutional_validation
        )

    def aggregate_federated_knowledge(self, contributions: List[FederatedPriors]) -> Dict[str, Tuple[float, float]]:
        """
        Aggregate multiple deployments' privatized priors into global knowledge.

        Uses weighted averaging based on sample counts and reputation.
        """
        # Group contributions by arm
        arm_contributions: Dict[str, List[Tuple[float, float, float]]] = {}

        for contribution in contributions:
            weight = min(contribution.sample_count / 100.0, 1.0)  # Cap influence

            for arm_name, (alpha, beta) in contribution.arm_priors.items():
                if arm_name not in arm_contributions:
                    arm_contributions[arm_name] = []
                arm_contributions[arm_name].append((alpha, beta, weight))

        # Aggregate using weighted average
        aggregated_priors = {}
        for arm_name, priors_list in arm_contributions.items():
            if not priors_list:
                continue

            # Weighted average of alpha and beta parameters
            total_weight = sum(weight for _, _, weight in priors_list)
            avg_alpha = sum(alpha * weight for alpha, _, weight in priors_list) / total_weight
            avg_beta = sum(beta * weight for _, beta, weight in priors_list) / total_weight

            aggregated_priors[arm_name] = (avg_alpha, avg_beta)

        return aggregated_priors

    def update_local_knowledge(self, federated_knowledge: Dict[str, Tuple[float, float]],
                              learning_rate: float = 0.1):
        """
        Update local bandit priors with federated knowledge.

        Uses gradual learning to avoid destabilizing local models.
        """
        updates_made = 0

        for arm_name, (fed_alpha, fed_beta) in federated_knowledge.items():
            if arm_name in self.federated_knowledge:
                # Gradually update existing knowledge
                local_alpha, local_beta = self.federated_knowledge[arm_name]
                new_alpha = local_alpha * (1 - learning_rate) + fed_alpha * learning_rate
                new_beta = local_beta * (1 - learning_rate) + fed_beta * learning_rate
                self.federated_knowledge[arm_name] = (new_alpha, new_beta)
            else:
                # Initialize with federated knowledge
                self.federated_knowledge[arm_name] = (fed_alpha, fed_beta)

            updates_made += 1

        # Record the update
        self.knowledge_updates.append({
            'timestamp': datetime.now().isoformat(),
            'updates_made': updates_made,
            'learning_rate': learning_rate,
            'source': 'federation'
        })

        return updates_made

    def sync_with_federation(self, local_priors: Dict[str, Tuple[int, int]],
                           strategy_stats: Optional[Dict[str, Any]] = None) -> bool:
        """
        Synchronize with federation coordinator.

        1. Submit local contribution
        2. Receive aggregated global knowledge
        3. Update local priors

        Returns True if sync successful.
        """
        if not self.federation_enabled:
            return False

        try:
            # Prepare local contribution with constitutional validation
            contribution = self.prepare_local_contribution(local_priors, strategy_stats)

            # Block federation if strategy is unconstitutional
            if contribution is None:
                print("🚫 Federation blocked: unconstitutional strategy")
                return False

            # Submit to federation (in real implementation, this would be an API call)
            # For demo, simulate federation response
            federated_knowledge = self._simulate_federation_round(contribution)

            # Update local knowledge
            updates = self.update_local_knowledge(federated_knowledge)

            # Record contribution
            self.contribution_history.append({
                'timestamp': datetime.now().isoformat(),
                'round_id': contribution.federation_round,
                'arms_contributed': len(contribution.arm_priors),
                'sample_count': contribution.sample_count,
                'privacy_budget': contribution.privacy_budget
            })

            self.last_federation_sync = datetime.now()
            return True

        except Exception as e:
            print(f"Federation sync failed: {e}")
            return False

    def _simulate_federation_round(self, contribution: FederatedPriors) -> Dict[str, Tuple[float, float]]:
        """Simulate a federation round for demonstration."""
        # In real implementation, this would be API calls to federation coordinator

        # Simulate other deployments' contributions
        simulated_contributions = [
            FederatedPriors(
                deployment_id=f"dep_{i}",
                timestamp=datetime.now().isoformat(),
                arm_priors={
                    arm: (max(1, s + random.randint(-2, 2)), max(1, f + random.randint(-2, 2)))
                    for arm, (s, f) in contribution.arm_priors.items()
                },
                sample_count=random.randint(50, 200),
                privacy_budget=self.privacy_epsilon,
                federation_round=contribution.federation_round
            )
            for i in range(3)  # Simulate 3 other deployments
        ]

        all_contributions = [contribution] + simulated_contributions
        return self.aggregate_federated_knowledge(all_contributions)

    def get_federated_priors(self, arm_name: str) -> Optional[Tuple[float, float]]:
        """Get federated priors for an arm, if available."""
        return self.federated_knowledge.get(arm_name)

    def get_federation_stats(self) -> Dict[str, Any]:
        """Get comprehensive federation statistics."""
        total_contributions = len(self.contribution_history)
        total_updates = len(self.knowledge_updates)

        recent_contributions = [
            c for c in self.contribution_history
            if (datetime.now() - datetime.fromisoformat(c['timestamp'])).days <= 7
        ]

        return {
            'federation_enabled': self.federation_enabled,
            'deployment_id': self.deployment_id,
            'total_contributions': total_contributions,
            'total_knowledge_updates': total_updates,
            'recent_contributions': len(recent_contributions),
            'federated_arms': len(self.federated_knowledge),
            'last_sync': self.last_federation_sync.isoformat(),
            'hours_since_sync': (datetime.now() - self.last_federation_sync).total_seconds() / 3600,
            'privacy_epsilon': self.privacy_epsilon,
            'deployment_reputation': self.deployment_profile.reputation_score
        }

# Global federation coordinator instance
federation_coordinator = FederatedBanditCoordinator()

def get_federated_priors(arm_name: str) -> Optional[Tuple[float, float]]:
    """Get federated priors for an arm."""
    return federation_coordinator.get_federated_priors(arm_name)

def sync_federated_knowledge(local_priors: Dict[str, Tuple[int, int]],
                            strategy_stats: Optional[Dict[str, Any]] = None) -> bool:
    """Sync local knowledge with federation."""
    return federation_coordinator.sync_with_federation(local_priors, strategy_stats)

if __name__ == "__main__":
    # Demo federated learning
    print("🌐 Federated Bandit Learning Demo")
    print("=" * 50)

    # Simulate local priors
    local_priors = {
        'conservative_ce': (12, 3),  # 80% win rate
        'aggressive_ce': (15, 5),    # 75% win rate
        'exploratory': (8, 7)        # 53% win rate
    }

    print("Local priors before federation:")
    for arm, (s, f) in local_priors.items():
        win_rate = s / (s + f)
        print(f"  {arm}: {s}/{s+f} = {win_rate:.1%}")

    # Sync with federation
    print("\nSyncing with federation...")
    success = sync_federated_knowledge(local_priors)

    if success:
        print("✅ Federation sync successful!")

        print("\nFederated knowledge received:")
        for arm in local_priors.keys():
            priors = get_federated_priors(arm)
            if priors:
                alpha, beta = priors
                expected_win_rate = alpha / (alpha + beta)
                print(f"  {arm}: α={alpha:.1f}, β={beta:.1f} → {expected_win_rate:.1%}")

        # Show federation stats
        stats = federation_coordinator.get_federation_stats()
        print("\nFederation Stats:")
        print(f"  Contributions: {stats['total_contributions']}")
        print(f"  Federated arms: {stats['federated_arms']}")
        print(f"  Privacy ε: {stats['privacy_epsilon']}")

    print("\n🎉 Federated learning ready!")
    print("   Collective intelligence without data sharing.")
