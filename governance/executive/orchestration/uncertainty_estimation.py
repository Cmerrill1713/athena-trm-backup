import logging
from typing import List, Tuple, Union, Dict
import torch
import torch.nn as nn

logger = logging.getLogger(__name__)

class UncertaintyEstimator:
    """
    Bayesian Uncertainty Estimator using Monte Carlo Dropout.

    This class implements uncertainty estimation for neural networks using
    Monte Carlo dropout sampling. It provides both aleatoric and epistemic
    uncertainty estimates by running multiple forward passes with dropout
    enabled during inference.
    """

    def __init__(self, model: nn.Module, num_samples: int = 10):
        """
        Initialize the uncertainty estimator.

        Args:
            model: PyTorch model with dropout layers
            num_samples: Number of Monte Carlo samples to use for uncertainty estimation
        """
        self.model = model
        self.num_samples = num_samples
        self._is_training = False

        # Validate that model has dropout layers
        self._validate_model()

    def _validate_model(self) -> None:
        """Validate that the model contains dropout layers."""
        dropout_layers = []
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d)):
                dropout_layers.append(module)

        if not dropout_layers:
            logger.warning("Model has no dropout layers. Uncertainty estimation may not be meaningful.")

    def _set_dropout_training(self, training: bool) -> None:
        """Set dropout layers to training or evaluation mode."""
        for module in self.model.modules():
            if isinstance(module, (nn.Dropout, nn.Dropout2d, nn.Dropout3d)):
                module.train(training)

    def predict_with_uncertainty(self,
                               x: torch.Tensor,
                               return_variance: bool = True) -> Union[
                                   Tuple[torch.Tensor, torch.Tensor],
                                   torch.Tensor
                               ]:
        """
        Make predictions with uncertainty estimation.

        Args:
            x: Input tensor of shape (batch_size, ...)
            return_variance: Whether to return variance along with predictions

        Returns:
            If return_variance=True: (mean_predictions, variance_predictions)
            If return_variance=False: mean_predictions
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError("Input x must be a torch.Tensor")

        # Set model to training mode to enable dropout
        self._set_dropout_training(True)

        # Store original model state
        original_train_state = self.model.training

        try:
            # Run multiple forward passes
            predictions = []
            with torch.no_grad():
                for _ in range(self.num_samples):
                    # Forward pass with dropout enabled
                    pred = self.model(x)
                    predictions.append(pred)

            # Convert to tensor and compute statistics
            predictions = torch.stack(predictions, dim=0)

            # Mean prediction (expected value)
            mean_pred = torch.mean(predictions, dim=0)

            if return_variance:
                # Variance prediction (uncertainty measure)
                var_pred = torch.var(predictions, dim=0)
                return mean_pred, var_pred
            else:
                return mean_pred

        finally:
            # Restore original training state
            self._set_dropout_training(original_train_state)

    def get_uncertainty_score(self,
                            x: torch.Tensor,
                            uncertainty_type: str = 'variance') -> torch.Tensor:
        """
        Get uncertainty score for input data.

        Args:
            x: Input tensor of shape (batch_size, ...)
            uncertainty_type: Type of uncertainty ('variance', 'std', 'entropy')

        Returns:
            Uncertainty scores for each sample
        """
        if uncertainty_type == 'variance':
            _, variance = self.predict_with_uncertainty(x, return_variance=True)
            return variance
        elif uncertainty_type == 'std':
            _, variance = self.predict_with_uncertainty(x, return_variance=True)
            return torch.sqrt(variance)
        elif uncertainty_type == 'entropy':
            return self._compute_entropy(x)
        else:
            raise ValueError(f"Unknown uncertainty type: {uncertainty_type}")

    def _compute_entropy(self, x: torch.Tensor) -> torch.Tensor:
        """Compute entropy-based uncertainty."""
        # For classification, compute entropy of predictions
        # This requires the model to output probabilities
        predictions = []
        self._set_dropout_training(True)
        original_train_state = self.model.training

        try:
            with torch.no_grad():
                for _ in range(self.num_samples):
                    pred = self.model(x)
                    predictions.append(pred)

            predictions = torch.stack(predictions, dim=0)
            mean_pred = torch.mean(predictions, dim=0)

            # Compute entropy: -sum(p * log(p))
            # Add small epsilon to prevent log(0)
            epsilon = 1e-8
            entropy = -torch.sum(mean_pred * torch.log(mean_pred + epsilon), dim=-1)
            return entropy

        finally:
            self._set_dropout_training(original_train_state)

    def make_decision(self,
                     x: torch.Tensor,
                     confidence_threshold: float = 0.8,
                     human_threshold: float = 0.95) -> Dict[str, List[str]]:
        """
        Make decisions based on uncertainty scores.

        Args:
            x: Input tensor
            confidence_threshold: Threshold for confident execution
            human_threshold: Threshold for deferring to human

        Returns:
            Dictionary with decision categories
        """
        # Get uncertainty scores
        uncertainty = self.get_uncertainty_score(x, 'variance')

        # Classify based on uncertainty
        decisions = {
            'execute_confidently': [],
            'request_context': [],
            'defer_to_human': []
        }

        for i, score in enumerate(uncertainty):
            if score < confidence_threshold:
                decisions['execute_confidently'].append(str(i))
            elif score < human_threshold:
                decisions['request_context'].append(str(i))
            else:
                decisions['defer_to_human'].append(str(i))

        return decisions

class EnsembleUncertaintyEstimator:
    """
    Alternative implementation using model ensembles.

    This class provides uncertainty estimation using an ensemble of models
    instead of Monte Carlo dropout.
    """

    def __init__(self, models: List[nn.Module]):
        """
        Initialize ensemble uncertainty estimator.

        Args:
            models: List of trained models in the ensemble
        """
        self.models = models
        self.num_models = len(models)

        if self.num_models == 0:
            raise ValueError("At least one model must be provided for ensemble")

    def predict_with_uncertainty(self,
                               x: torch.Tensor,
                               return_variance: bool = True) -> Union[
                                   Tuple[torch.Tensor, torch.Tensor],
                                   torch.Tensor
                               ]:
        """
        Make predictions with uncertainty using ensemble.

        Args:
            x: Input tensor
            return_variance: Whether to return variance

        Returns:
            Mean predictions and variance (if requested)
        """
        if not isinstance(x, torch.Tensor):
            raise TypeError("Input x must be a torch.Tensor")

        predictions = []
        with torch.no_grad():
            for model in self.models:
                model.eval()  # Set to eval mode
                pred = model(x)
                predictions.append(pred)

        predictions = torch.stack(predictions, dim=0)

        mean_pred = torch.mean(predictions, dim=0)

        if return_variance:
            var_pred = torch.var(predictions, dim=0)
            return mean_pred, var_pred
        else:
            return mean_pred

# Example usage and testing
def example_usage():
    """Example of how to use the uncertainty estimator."""

    # Simple model with dropout for demonstration
    class SimpleModel(nn.Module):
        def __init__(self, input_size: int = 10, hidden_size: int = 20, output_size: int = 2):
            super().__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.dropout = nn.Dropout(0.5)
            self.fc2 = nn.Linear(hidden_size, output_size)

        def forward(self, x):
            x = self.fc1(x)
            x = self.dropout(x)
            x = torch.relu(x)
            x = self.fc2(x)
            return x

    # Create model and estimator
    model = SimpleModel()
    estimator = UncertaintyEstimator(model, num_samples=5)

    # Generate sample data
    x = torch.randn(32, 10)  # 32 samples, 10 features

    # Get predictions with uncertainty
    mean_pred, variance = estimator.predict_with_uncertainty(x, return_variance=True)
    print(f"Mean predictions shape: {mean_pred.shape}")
    print(f"Variance predictions shape: {variance.shape}")

    # Get uncertainty scores
    uncertainty = estimator.get_uncertainty_score(x, 'variance')
    print(f"Uncertainty scores shape: {uncertainty.shape}")

    # Make decisions
    decisions = estimator.make_decision(x, confidence_threshold=0.1, human_threshold=0.2)
    print(f"Decisions: {decisions}")

if __name__ == "__main__":
    example_usage()
