import torch
import torch.nn as nn
import torch.optim as optim
from typing import List, Tuple, Dict, Optional
import numpy as np
from collections import defaultdict

class MetaLearner:
    """
    MAML-style meta-learner for rapid task adaptation.

    This implementation supports both classification and regression tasks
    through a flexible model architecture and loss function selection.
    """

    def __init__(self,
                 model: nn.Module,
                 inner_lr: float = 0.01,
                 outer_lr: float = 0.001,
                 num_inner_steps: int = 5,
                 task_batch_size: int = 4,
                 loss_fn: Optional[nn.Module] = None):
        """
        Initialize the MetaLearner.

        Args:
            model: Base model to be meta-learned
            inner_lr: Learning rate for inner loop (fast adaptation)
            outer_lr: Learning rate for outer loop (meta-update)
            num_inner_steps: Number of inner loop updates per task
            task_batch_size: Number of tasks to process in parallel
            loss_fn: Loss function to use (defaults to appropriate for model output)
        """
        self.model = model
        self.inner_lr = inner_lr
        self.outer_lr = outer_lr
        self.num_inner_steps = num_inner_steps
        self.task_batch_size = task_batch_size
        self.loss_fn = loss_fn or self._get_default_loss()

        # Store meta-parameters for gradient updates
        self.meta_params = list(model.parameters())

        # Metrics tracking
        self.metrics = defaultdict(list)

    def _get_default_loss(self) -> nn.Module:
        """Return appropriate loss function based on model output."""
        # Simple heuristic: check if model has final linear layer with 1 output
        # This is a simplified approach - in practice, you'd want to inspect the model structure
        return nn.CrossEntropyLoss() if hasattr(self.model, 'num_classes') else nn.MSELoss()

    def _inner_update(self,
                     model: nn.Module,
                     support_data: Tuple[torch.Tensor, torch.Tensor],
                     adaptation_steps: int) -> nn.Module:
        """
        Perform inner loop adaptation on a single task.

        Args:
            model: Current model state
            support_data: (features, targets) for adaptation
            adaptation_steps: Number of gradient steps

        Returns:
            Adapted model
        """
        model.train()
        inner_optimizer = optim.SGD(model.parameters(), lr=self.inner_lr)

        # Clone model to avoid modifying original during inner loop
        adapted_model = type(model)()
        adapted_model.load_state_dict(model.state_dict())

        for _ in range(adaptation_steps):
            features, targets = support_data
            inner_optimizer.zero_grad()

            # Forward pass
            outputs = adapted_model(features)
            loss = self.loss_fn(outputs, targets)

            # Backward pass
            loss.backward()
            inner_optimizer.step()

        return adapted_model

    def meta_train_step(self,
                       tasks: List[Tuple[torch.Tensor, torch.Tensor]],
                       verbose: bool = False) -> Dict[str, float]:
        """
        Perform one meta-training step across multiple tasks.

        Args:
            tasks: List of (features, targets) tuples for each task
            verbose: Whether to print training progress

        Returns:
            Dictionary of training metrics
        """
        if len(tasks) < self.task_batch_size:
            raise ValueError(f"Not enough tasks for batch size {self.task_batch_size}")

        # Sample tasks for this batch
        batch_indices = np.random.choice(len(tasks), self.task_batch_size, replace=False)
        batch_tasks = [tasks[i] for i in batch_indices]

        # Initialize meta-gradients
        meta_gradients = [torch.zeros_like(param) for param in self.meta_params]

        # Process each task in batch
        for features, targets in batch_tasks:
            # Inner loop adaptation
            adapted_model = self._inner_update(self.model, (features, targets), self.num_inner_steps)

            # Compute validation loss on adapted model
            adapted_model.eval()
            with torch.no_grad():
                val_features, val_targets = features, targets  # Using same data for simplicity
                val_outputs = adapted_model(val_features)
                val_loss = self.loss_fn(val_outputs, val_targets)

            # Compute gradients with respect to meta-parameters
            val_gradients = torch.autograd.grad(val_loss, adapted_model.parameters(),
                                              retain_graph=True, create_graph=True)

            # Accumulate meta-gradients
            for i, grad in enumerate(val_gradients):
                meta_gradients[i] += grad

        # Update meta-parameters
        for param, grad in zip(self.meta_params, meta_gradients):
            param.data -= self.outer_lr * grad / self.task_batch_size

        # Track metrics
        metrics = {
            'meta_loss': float(torch.tensor([g.sum() for g in meta_gradients]).mean()),
        }

        self.metrics['meta_loss'].append(metrics['meta_loss'])

        if verbose:
            print(f"Meta-loss: {metrics['meta_loss']:.4f}")

        return metrics

    def adapt_and_evaluate(self,
                          support_data: Tuple[torch.Tensor, torch.Tensor],
                          query_data: Tuple[torch.Tensor, torch.Tensor],
                          num_adaptation_steps: int = 5) -> Dict[str, float]:
        """
        Adapt model to new task and evaluate performance.

        Args:
            support_data: (features, targets) for adaptation
            query_data: (features, targets) for evaluation
            num_adaptation_steps: Number of adaptation steps

        Returns:
            Dictionary of evaluation metrics
        """
        # Adapt to new task
        adapted_model = self._inner_update(self.model, support_data, num_adaptation_steps)

        # Evaluate on query data
        adapted_model.eval()
        with torch.no_grad():
            features, targets = query_data
            outputs = adapted_model(features)
            loss = self.loss_fn(outputs, targets)

        return {
            'loss': float(loss),
            'accuracy': float((outputs.argmax(1) == targets).float().mean()) if outputs.shape[1] > 1 else 0.0
        }

# Example usage:
if __name__ == "__main__":
    # Simple example with synthetic data
    class SimpleModel(nn.Module):
        def __init__(self, input_size=10, hidden_size=20, output_size=2):
            super().__init__()
            self.fc1 = nn.Linear(input_size, hidden_size)
            self.fc2 = nn.Linear(hidden_size, output_size)
            self.relu = nn.ReLU()

        def forward(self, x):
            x = self.relu(self.fc1(x))
            x = self.fc2(x)
            return x

    # Create meta-learner
    model = SimpleModel()
    meta_learner = MetaLearner(model, inner_lr=0.01, outer_lr=0.001, num_inner_steps=3)

    # Generate synthetic tasks
    tasks = []
    for _ in range(10):
        features = torch.randn(20, 10)
        targets = torch.randint(0, 2, (20,))
        tasks.append((features, targets))

    # Meta-training
    for epoch in range(5):
        metrics = meta_learner.meta_train_step(tasks, verbose=True)

    # Test adaptation
    support_features = torch.randn(5, 10)
    support_targets = torch.randint(0, 2, (5,))
    query_features = torch.randn(10, 10)
    query_targets = torch.randint(0, 2, (10,))

    results = meta_learner.adapt_and_evaluate(
        (support_features, support_targets),
        (query_features, query_targets),
        num_adaptation_steps=3
    )

    print(f"Test results: {results}")
