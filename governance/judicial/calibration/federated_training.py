"""
Federated Neural Training
========================

Enables privacy-preserving collaborative learning across NeuroForge deployments.
Multiple instances share model improvements without exchanging training data.

Features:
- FedAvg algorithm with differential privacy
- Secure model aggregation
- Deployment registry and opt-in controls
- Model versioning and lineage tracking
- Automatic federated rounds
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import torch

from .adaptive_federated_scheduling import AdaptiveFederatedScheduler
from .neural_context_encoder import NeuralContextEncoder

logger = logging.getLogger(__name__)

@dataclass
class FederatedConfig:
    """Configuration for federated learning."""
    coordinator_url: str = "https://federation.neuroforge.ai"
    deployment_id: str = "default"
    round_interval_hours: int = 24  # How often to run federated rounds
    min_participants: int = 3       # Minimum deployments needed for a round
    max_participants: int = 10      # Maximum deployments per round
    privacy_epsilon: float = 1.0    # Differential privacy parameter
    privacy_delta: float = 1e-5     # Differential privacy parameter
    model_version_ttl_days: int = 30  # How long to keep old model versions
    enable_federation: bool = True

@dataclass
class ModelUpdate:
    """A model update from a deployment."""
    deployment_id: str
    model_version: str
    parameters: Dict[str, torch.Tensor]
    num_examples: int
    training_loss: float
    validation_accuracy: float
    timestamp: datetime
    differential_privacy_noise: Optional[Dict[str, torch.Tensor]] = None

@dataclass
class FederatedRound:
    """A federated learning round."""
    round_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    participants: List[str] = field(default_factory=list)
    updates_received: List[ModelUpdate] = field(default_factory=list)
    aggregated_model: Optional[Dict[str, torch.Tensor]] = None
    global_model_version: str = ""
    status: str = "active"  # active, completed, failed

class DifferentialPrivacy:
    """Differential privacy utilities for federated learning."""

    @staticmethod
    def add_gaussian_noise(tensor: torch.Tensor, sensitivity: float,
                          epsilon: float, delta: float) -> torch.Tensor:
        """
        Add Gaussian noise for differential privacy.

        σ = (sensitivity * √(2 ln(1.25/δ))) / ε
        """
        sigma = (sensitivity * np.sqrt(2 * np.log(1.25 / delta))) / epsilon

        # Generate Gaussian noise with calculated sigma
        noise = torch.normal(0, sigma, tensor.shape, dtype=tensor.dtype, device=tensor.device)

        return tensor + noise

    @staticmethod
    def clip_gradients(gradients: Dict[str, torch.Tensor], max_norm: float) -> Dict[str, torch.Tensor]:
        """Clip gradients to bound sensitivity for differential privacy."""
        total_norm = 0
        for grad in gradients.values():
            param_norm = grad.data.norm(2)
            total_norm += param_norm.item() ** 2
        total_norm = total_norm ** (1. / 2)

        clip_coef = max_norm / (total_norm + 1e-6)
        if clip_coef < 1:
            for name in gradients:
                gradients[name].mul_(clip_coef)

        return gradients

class FedAvgAggregator:
    """Federated Averaging (FedAvg) algorithm implementation."""

    def __init__(self, privacy_epsilon: float = 1.0, privacy_delta: float = 1e-5):
        self.privacy_epsilon = privacy_epsilon
        self.privacy_delta = privacy_delta

    def aggregate_updates(self, updates: List[ModelUpdate]) -> Dict[str, torch.Tensor]:
        """
        Aggregate model updates using FedAvg algorithm.

        FedAvg: Average the model parameters weighted by number of examples.
        """
        if not updates:
            raise ValueError("No updates to aggregate")

        # Calculate total examples across all updates
        total_examples = sum(update.num_examples for update in updates)

        if total_examples == 0:
            raise ValueError("No training examples in updates")

        # Initialize aggregated parameters with zeros
        param_names = updates[0].parameters.keys()
        aggregated_params = {}

        for param_name in param_names:
            # Weighted average of parameters
            weighted_sum = torch.zeros_like(updates[0].parameters[param_name])

            for update in updates:
                weight = update.num_examples / total_examples
                weighted_sum += weight * update.parameters[param_name]

                # Add differential privacy noise if available
                if update.differential_privacy_noise and param_name in update.differential_privacy_noise:
                    weighted_sum += update.differential_privacy_noise[param_name]

            aggregated_params[param_name] = weighted_sum

        return aggregated_params

class DeploymentRegistry:
    """Registry of federated learning participants."""

    def __init__(self, config: FederatedConfig):
        self.config = config
        self.deployments: Dict[str, Dict] = {}
        self._load_registry()

    def register_deployment(self, deployment_id: str, metadata: Dict) -> bool:
        """Register a deployment for federated learning."""
        if deployment_id in self.deployments:
            logger.warning(f"Deployment {deployment_id} already registered")
            return False

        self.deployments[deployment_id] = {
            'metadata': metadata,
            'registered_at': datetime.now(),
            'last_seen': datetime.now(),
            'participation_count': 0,
            'opt_in': metadata.get('opt_in', True)
        }

        self._save_registry()
        logger.info(f"Registered deployment: {deployment_id}")
        return True

    def update_deployment_status(self, deployment_id: str):
        """Update last seen timestamp for a deployment."""
        if deployment_id in self.deployments:
            self.deployments[deployment_id]['last_seen'] = datetime.now()
            self._save_registry()

    def get_active_deployments(self) -> List[str]:
        """Get list of active deployments that have opted in."""
        cutoff = datetime.now() - timedelta(hours=2)  # Consider active if seen in last 2 hours
        active = []

        for dep_id, info in self.deployments.items():
            if (info['opt_in'] and
                info['last_seen'] > cutoff and
                dep_id != self.config.deployment_id):  # Exclude self
                active.append(dep_id)

        return active

    def opt_out_deployment(self, deployment_id: str):
        """Opt a deployment out of federated learning."""
        if deployment_id in self.deployments:
            self.deployments[deployment_id]['opt_in'] = False
            self._save_registry()
            logger.info(f"Deployment {deployment_id} opted out of federation")

    def _load_registry(self):
        """Load deployment registry from disk."""
        try:
            registry_path = Path("data/federated_registry.json")
            if registry_path.exists():
                with open(registry_path, 'r') as f:
                    data = json.load(f)
                    # Convert ISO strings back to datetime
                    for dep_id, info in data.items():
                        info['registered_at'] = datetime.fromisoformat(info['registered_at'])
                        info['last_seen'] = datetime.fromisoformat(info['last_seen'])
                    self.deployments = data
        except Exception as e:
            logger.warning(f"Failed to load federated registry: {e}")
            self.deployments = {}

    def _save_registry(self):
        """Save deployment registry to disk."""
        try:
            registry_path = Path("data")
            registry_path.mkdir(exist_ok=True)

            # Convert datetime to ISO strings for JSON serialization
            serializable = {}
            for dep_id, info in self.deployments.items():
                serializable[dep_id] = info.copy()
                serializable[dep_id]['registered_at'] = info['registered_at'].isoformat()
                serializable[dep_id]['last_seen'] = info['last_seen'].isoformat()

            with open(registry_path / "federated_registry.json", 'w') as f:
                json.dump(serializable, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save federated registry: {e}")

class FederatedCoordinator:
    """
    Coordinates federated learning across deployments.

    Manages the federated learning lifecycle:
    - Round initialization and participant selection
    - Model update collection and aggregation
    - Global model distribution
    - Privacy and security enforcement
    """

    def __init__(self, config: FederatedConfig):
        self.config = config
        self.registry = DeploymentRegistry(config)
        self.aggregator = FedAvgAggregator(config.privacy_epsilon, config.privacy_delta)
        self.differential_privacy = DifferentialPrivacy()

        # Adaptive scheduling
        self.adaptive_scheduler = AdaptiveFederatedScheduler(config)

        # Active rounds
        self.active_rounds: Dict[str, FederatedRound] = {}
        self.completed_rounds: List[FederatedRound] = []

        # Model versioning
        self.model_versions: Dict[str, Dict] = {}

        self._load_state()

    def initialize_round(self) -> Optional[str]:
        """Initialize a new federated learning round."""
        if not self.config.enable_federation:
            return None

        # Check if enough time has passed since last round
        if self.completed_rounds:
            last_round = max(self.completed_rounds, key=lambda r: r.end_time or datetime.min)
            if last_round.end_time:
                time_since_last = datetime.now() - last_round.end_time
                if time_since_last < timedelta(hours=self.config.round_interval_hours):
                    return None  # Too soon for new round

        # Get active participants
        participants = self.registry.get_active_deployments()
        if len(participants) < self.config.min_participants:
            logger.info(f"Not enough participants for federated round: {len(participants)} < {self.config.min_participants}")
            return None

        # Limit participants if too many
        if len(participants) > self.config.max_participants:
            participants = participants[:self.config.max_participants]

        # Create new round
        round_id = f"round_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        round_obj = FederatedRound(
            round_id=round_id,
            start_time=datetime.now(),
            participants=participants + [self.config.deployment_id]  # Include self
        )

        self.active_rounds[round_id] = round_obj
        logger.info(f"Initialized federated round {round_id} with {len(participants)} participants")

        return round_id

    def submit_model_update(self, round_id: str, update: ModelUpdate) -> bool:
        """Submit a model update for a federated round."""
        if round_id not in self.active_rounds:
            logger.warning(f"Round {round_id} not found or not active")
            return False

        round_obj = self.active_rounds[round_id]

        # Validate submission
        if update.deployment_id not in round_obj.participants:
            logger.warning(f"Deployment {update.deployment_id} not in round {round_id} participants")
            return False

        # Check for duplicate submission
        existing = [u for u in round_obj.updates_received if u.deployment_id == update.deployment_id]
        if existing:
            logger.warning(f"Deployment {update.deployment_id} already submitted to round {round_id}")
            return False

        # Add differential privacy noise if configured
        if self.config.privacy_epsilon > 0:
            update.differential_privacy_noise = {}
            for param_name, param_tensor in update.parameters.items():
                # Estimate sensitivity (simplified - in practice this needs careful calculation)
                sensitivity = param_tensor.norm(2).item() * 0.01  # Rough estimate
                noisy_tensor = self.differential_privacy.add_gaussian_noise(
                    param_tensor, sensitivity,
                    self.config.privacy_epsilon, self.config.privacy_delta
                )
                update.differential_privacy_noise[param_name] = noisy_tensor - param_tensor

        round_obj.updates_received.append(update)
        logger.info(f"Received model update from {update.deployment_id} for round {round_id}")

        # Check if round is complete
        if len(round_obj.updates_received) >= len(round_obj.participants):
            self._complete_round(round_id)

        return True

    def _complete_round(self, round_id: str):
        """Complete a federated round and aggregate updates."""
        round_obj = self.active_rounds[round_id]

        try:
            # Aggregate model updates
            aggregated_params = self.aggregator.aggregate_updates(round_obj.updates_received)

            # Create new global model version
            global_version = f"fed_{round_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            # Store aggregated model
            round_obj.aggregated_model = aggregated_params
            round_obj.global_model_version = global_version
            round_obj.end_time = datetime.now()
            round_obj.status = "completed"

            # Update model versions
            self.model_versions[global_version] = {
                'round_id': round_id,
                'participants': round_obj.participants,
                'num_updates': len(round_obj.updates_received),
                'total_examples': sum(u.num_examples for u in round_obj.updates_received),
                'created_at': datetime.now().isoformat(),
                'parameters': {k: v.tolist() for k, v in aggregated_params.items()}  # For storage
            }

            # Move to completed rounds
            self.completed_rounds.append(round_obj)
            del self.active_rounds[round_id]

            self._save_state()

            logger.info(f"Completed federated round {round_id} with {len(round_obj.updates_received)} updates")

        except Exception as e:
            logger.error(f"Failed to complete round {round_id}: {e}")
            round_obj.status = "failed"
            round_obj.end_time = datetime.now()

    def get_global_model(self, version: Optional[str] = None) -> Optional[Dict[str, torch.Tensor]]:
        """Get the latest global model or specific version."""
        if version and version in self.model_versions:
            # Convert back from lists to tensors
            params_data = self.model_versions[version]['parameters']
            return {k: torch.tensor(v) for k, v in params_data.items()}

        # Return latest completed round's model
        if self.completed_rounds:
            latest_round = max(self.completed_rounds, key=lambda r: r.end_time)
            return latest_round.aggregated_model

        return None

    def get_round_status(self, round_id: str) -> Optional[Dict]:
        """Get status of a federated round."""
        if round_id in self.active_rounds:
            round_obj = self.active_rounds[round_id]
        elif any(r.round_id == round_id for r in self.completed_rounds):
            round_obj = next(r for r in self.completed_rounds if r.round_id == round_id)
        else:
            return None

        return {
            'round_id': round_obj.round_id,
            'status': round_obj.status,
            'participants': round_obj.participants,
            'updates_received': len(round_obj.updates_received),
            'start_time': round_obj.start_time.isoformat(),
            'end_time': round_obj.end_time.isoformat() if round_obj.end_time else None
        }

    def evaluate_round_participation(self, round_info: Dict) -> Tuple[bool, str, Any]:
        """
        Evaluate whether this deployment should participate in a round.

        Uses adaptive scheduling to make economically optimal decisions.
        """
        return self.adaptive_scheduler.evaluate_round_participation(round_info)

    def record_round_participation_outcome(self,
                                         round_id: str,
                                         participated: bool,
                                         actual_improvement: float,
                                         privacy_cost: float):
        """Record outcome of round participation for learning."""
        self.adaptive_scheduler.record_round_outcome(
            round_id, participated, actual_improvement, privacy_cost
        )

    def get_adaptive_scheduling_stats(self) -> Dict:
        """Get adaptive scheduling statistics."""
        return self.adaptive_scheduler.get_scheduler_stats()

    def run_autonomous_round_evaluation(self) -> List[Dict]:
        """
        Run autonomous evaluation of available rounds.

        Returns decisions for each available round.
        """
        return self.adaptive_scheduler.run_autonomous_scheduling()

    def _load_state(self):
        """Load coordinator state from disk."""
        try:
            state_path = Path("data/federated_coordinator.json")
            if state_path.exists():
                with open(state_path, 'r') as f:
                    data = json.load(f)

                # Restore completed rounds
                self.completed_rounds = []
                for round_data in data.get('completed_rounds', []):
                    round_obj = FederatedRound(
                        round_id=round_data['round_id'],
                        start_time=datetime.fromisoformat(round_data['start_time']),
                        end_time=datetime.fromisoformat(round_data['end_time']) if round_data.get('end_time') else None,
                        participants=round_data['participants'],
                        status=round_data['status']
                    )
                    # Restore aggregated model if available
                    if 'aggregated_model' in round_data:
                        round_obj.aggregated_model = {
                            k: torch.tensor(v) for k, v in round_data['aggregated_model'].items()
                        }
                    round_obj.global_model_version = round_data.get('global_model_version', '')
                    self.completed_rounds.append(round_obj)

                # Restore model versions
                self.model_versions = data.get('model_versions', {})

        except Exception as e:
            logger.warning(f"Failed to load federated coordinator state: {e}")

    def _save_state(self):
        """Save coordinator state to disk."""
        try:
            state_path = Path("data")
            state_path.mkdir(exist_ok=True)

            # Serialize completed rounds
            completed_data = []
            for round_obj in self.completed_rounds[-10:]:  # Keep last 10
                round_data = {
                    'round_id': round_obj.round_id,
                    'start_time': round_obj.start_time.isoformat(),
                    'end_time': round_obj.end_time.isoformat() if round_obj.end_time else None,
                    'participants': round_obj.participants,
                    'status': round_obj.status,
                    'global_model_version': round_obj.global_model_version
                }
                if round_obj.aggregated_model:
                    round_data['aggregated_model'] = {
                        k: v.tolist() for k, v in round_obj.aggregated_model.items()
                    }
                completed_data.append(round_data)

            state = {
                'completed_rounds': completed_data,
                'model_versions': self.model_versions
            }

            with open(state_path / "federated_coordinator.json", 'w') as f:
                json.dump(state, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save federated coordinator state: {e}")

class FederatedClient:
    """
    Client for participating in federated learning.

    Handles:
    - Local model training
    - Model update submission
    - Global model retrieval
    - Privacy-preserving updates
    """

    def __init__(self, config: FederatedConfig, context_encoder: NeuralContextEncoder):
        self.config = config
        self.context_encoder = context_encoder
        self.coordinator = FederatedCoordinator(config)
        self.differential_privacy = DifferentialPrivacy()

    def prepare_model_update(self, training_metrics: Dict) -> ModelUpdate:
        """Prepare a model update for federated learning."""
        # Get current model parameters
        parameters = {}
        for name, param in self.context_encoder.named_parameters():
            if param.requires_grad:
                parameters[name] = param.data.clone()

        # Apply differential privacy if configured
        dp_noise = None
        if self.config.privacy_epsilon > 0:
            dp_noise = {}
            for name, param in parameters.items():
                sensitivity = param.norm(2).item() * 0.01  # Simplified sensitivity
                noisy_param = self.differential_privacy.add_gaussian_noise(
                    param, sensitivity,
                    self.config.privacy_epsilon, self.config.privacy_delta
                )
                dp_noise[name] = noisy_param - param

        return ModelUpdate(
            deployment_id=self.config.deployment_id,
            model_version=f"local_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            parameters=parameters,
            num_examples=training_metrics.get('num_examples', 0),
            training_loss=training_metrics.get('final_loss', 0.0),
            validation_accuracy=training_metrics.get('final_accuracy', 0.0),
            timestamp=datetime.now(),
            differential_privacy_noise=dp_noise
        )

    def submit_update_to_coordinator(self, update: ModelUpdate, round_id: str) -> bool:
        """Submit model update to federated coordinator."""
        return self.coordinator.submit_model_update(round_id, update)

    def get_global_model(self, version: Optional[str] = None) -> Optional[Dict[str, torch.Tensor]]:
        """Retrieve the latest global model from coordinator."""
        return self.coordinator.get_global_model(version)

    def update_local_model(self, global_parameters: Dict[str, torch.Tensor]):
        """Update local model with global parameters."""
        try:
            # Load global parameters into local model
            state_dict = self.context_encoder.state_dict()
            for name, global_param in global_parameters.items():
                if name in state_dict:
                    state_dict[name].copy_(global_param)

            self.context_encoder.load_state_dict(state_dict)
            logger.info("Updated local model with global federated parameters")

        except Exception as e:
            logger.error(f"Failed to update local model with global parameters: {e}")

    def participate_in_round(self, round_id: str, training_metrics: Dict) -> bool:
        """Participate in a federated learning round."""
        try:
            # Prepare model update
            update = self.prepare_model_update(training_metrics)

            # Submit to coordinator
            success = self.submit_update_to_coordinator(update, round_id)

            if success:
                logger.info(f"Successfully participated in federated round {round_id}")
            else:
                logger.warning(f"Failed to participate in federated round {round_id}")

            return success

        except Exception as e:
            logger.error(f"Error participating in federated round {round_id}: {e}")
            return False

# Global instances
_federated_coordinator = None
_federated_client = None

def get_federated_coordinator(config: Optional[FederatedConfig] = None) -> FederatedCoordinator:
    """Get or create global federated coordinator instance."""
    global _federated_coordinator
    if _federated_coordinator is None:
        if config is None:
            config = FederatedConfig()
        _federated_coordinator = FederatedCoordinator(config)
    return _federated_coordinator

def get_federated_client(config: Optional[FederatedConfig] = None,
                        context_encoder: Optional[NeuralContextEncoder] = None) -> FederatedClient:
    """Get or create global federated client instance."""
    global _federated_client
    if _federated_client is None:
        if config is None:
            config = FederatedConfig()
        if context_encoder is None:
            raise ValueError("Context encoder must be provided for federated client")
        _federated_client = FederatedClient(config, context_encoder)
    return _federated_client
