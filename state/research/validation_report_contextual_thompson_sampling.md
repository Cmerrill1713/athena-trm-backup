================================================================================
📋 CODE VALIDATION REPORT
================================================================================

✅ Completed: 4/5 validation checks
📊 Total tokens: 11193

================================================================================
🔍 SECURITY AUDITOR
================================================================================
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, List, Optional, Dict, Any
from collections import defaultdict
import random

class ContextualThompsonSampling:
    """
    Contextual Thompson Sampling for multi-armed bandits.

    This implementation extends standard Thompson Sampling by incorporating
    context information through a neural network that adjusts Beta distribution
    parameters based on observed contexts.
    """

    def __init__(self,
                 num_arms: int,
                 context_dim: int,
                 hidden_dim: int = 32,
                 learning_rate: float = 0.01,
                 alpha_init: float = 1.0,
                 beta_init: float = 1.0):
        """
        Initialize the contextual Thompson Sampling algorithm.

        Args:
            num_arms: Number of arms in the bandit
            context_dim: Dimension of context features
            hidden_dim: Hidden layer dimension for the neural network
            learning_rate: Learning rate for neural network training
            alpha_init: Initial alpha parameter for Beta distributions
            beta_init: Initial beta parameter for Beta distributions
        """
        self.num_arms = num_arms
        self.context_dim = context_dim
        self.alpha_init = alpha_init
        self.beta_init = beta_init

        # Initialize Beta distributions for each arm
        self.alphas = np.full(num_arms, alpha_init)
        self.betas = np.full(num_arms, beta_init)

        # Initialize neural network for context-aware adjustments
        self.nn = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_arms * 2),  # Output alpha and beta adjustments for each arm
            nn.Softplus()  # Ensure positive values
        )

        self.optimizer = optim.Adam(self.nn.parameters(), lr=learning_rate)

        # Store training data
        self.contexts = []
        self.arms = []
        self.rewards = []

    def _adjust_beta_params(self, context: np.ndarray) -> np.ndarray:
        """
        Adjust Beta parameters using neural network based on context.

        Args:
            context: Context features (shape: [context_dim])

        Returns:
            Adjusted alpha and beta parameters (shape: [num_arms * 2])
        """
        context_tensor = torch.FloatTensor(context).unsqueeze(0)
        adjustments = self.nn(context_tensor).squeeze(0)

        # Split adjustments into alpha and beta for each arm
        adjustments = adjustments.view(self.num_arms, 2)
        alpha_adjustments = adjustments[:, 0].detach().numpy()
        beta_adjustments = adjustments[:, 1].detach().numpy()

        # Apply adjustments to original parameters
        adjusted_alphas = self.alphas * (1 + alpha_adjustments)
        adjusted_betas = self.betas * (1 + beta_adjustments)

        return adjusted_alphas, adjusted_betas

    def select_arm(self, context: np.ndarray) -> int:
        """
        Select an arm using contextual Thompson Sampling.

        Args:
            context: Context features (shape: [context_dim])

        Returns:
            Selected arm index
        """
        # Get adjusted Beta parameters
        adjusted_alphas, adjusted_betas = self._adjust_beta_params(context)

        # Sample from adjusted Beta distributions
        samples = np.array([
            np.random.beta(alpha, beta)
            for alpha, beta in zip(adjusted_alphas, adjusted_betas)
        ])

        # Select arm with highest sample
        return int(np.argmax(samples))

    def update(self,
               context: np.ndarray,
               arm: int,
               reward: float) -> None:
        """
        Update the algorithm with new observation.

        Args:
            context: Context features (shape: [context_dim])
            arm: Selected arm index
            reward: Received reward
        """
        # Store observation for neural network training
        self.contexts.append(context)
        self.arms.append(arm)
        self.rewards.append(reward)

        # Update Beta distribution for the selected arm
        if reward > 0:
            self.alphas[arm] += 1
        self.betas[arm] += 1

        # Train neural network on recent observations
        if len(self.contexts) >= 10:  # Only train when we have enough data
            self._train_nn()

    def _train_nn(self) -> None:
        """
        Train the neural network on stored context-arm-reward tuples.
        """
        if len(self.contexts) < 10:
            return

        # Convert to tensors
        contexts = torch.FloatTensor(self.contexts[-50:])  # Use recent 50 samples
        arms = torch.LongTensor(self.arms[-50:])
        rewards = torch.FloatTensor(self.rewards[-50:])

        # Compute target adjustments (based on reward and current parameters)
        # This is a simplified approach - in practice, you might want more sophisticated targets
        targets = torch.zeros_like(contexts)

        # Simple target: adjust parameters based on reward
        for i, (arm, reward) in enumerate(zip(arms, rewards)):
            if reward > 0:
                targets[i, arm] = 1.0  # Positive reward increases alpha
            else:
                targets[i, arm] = -0.5  # Negative reward increases beta

        # Forward pass
        self.optimizer.zero_grad()
        predictions = self.nn(contexts)

        # Simple loss - you could use more sophisticated loss functions
        loss = nn.MSELoss()(predictions, targets)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        # Clear stored data to prevent memory issues
        if len(self.contexts) > 100:
            self.contexts = self.contexts[-50:]
            self.arms = self.arms[-50:]
            self.rewards = self.rewards[-50:]

# Example usage and testing
if __name__ == "__main__":
    # Simple test
    num_arms = 3
    context_dim = 5

    # Create algorithm instance
    cts = ContextualThompsonSampling(num_arms, context_dim)

    # Simulate some context and selections
    for i in range(20):
        context = np.random.rand(context_dim)
        arm = cts.select_arm(context)
        reward = np.random.choice([0, 1])  # Binary reward
        cts.update(context, arm, reward)

        if i % 5 == 0:
            print(f"Step {i}: Selected arm {arm}, reward {reward}")

================================================================================
🔍 PERFORMANCE ANALYZER
================================================================================
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, List, Optional, Dict, Any
from collections import defaultdict
import random

class ContextualThompsonSampling:
    """
    Contextual Thompson Sampling for multi-armed bandits.

    This implementation extends standard Thompson Sampling by incorporating
    context information through a neural network that adjusts Beta distribution
    parameters based on observed contexts.
    """

    def __init__(self,
                 num_arms: int,
                 context_dim: int,
                 hidden_dim: int = 32,
                 learning_rate: float = 0.01,
                 alpha_init: float = 1.0,
                 beta_init: float = 1.0):
        """
        Initialize the contextual Thompson Sampling algorithm.

        Args:
            num_arms: Number of arms in the bandit
            context_dim: Dimension of context features
            hidden_dim: Hidden layer dimension for the neural network
            learning_rate: Learning rate for neural network training
            alpha_init: Initial alpha parameter for Beta distributions
            beta_init: Initial beta parameter for Beta distributions
        """
        self.num_arms = num_arms
        self.context_dim = context_dim
        self.alpha_init = alpha_init
        self.beta_init = beta_init

        # Initialize Beta distributions for each arm
        self.alphas = np.full(num_arms, alpha_init)
        self.betas = np.full(num_arms, beta_init)

        # Initialize neural network for context-aware adjustments
        self.nn = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_arms * 2),  # Output alpha and beta adjustments for each arm
            nn.Softplus()  # Ensure positive values
        )

        self.optimizer = optim.Adam(self.nn.parameters(), lr=learning_rate)

        # Store training data
        self.contexts = []
        self.arms = []
        self.rewards = []

    def _adjust_beta_params(self, context: np.ndarray) -> np.ndarray:
        """
        Adjust Beta parameters using neural network based on context.

        Args:
            context: Context features (shape: [context_dim])

        Returns:
            Adjusted alpha and beta parameters (shape: [num_arms * 2])
        """
        context_tensor = torch.FloatTensor(context).unsqueeze(0)
        adjustments = self.nn(context_tensor).squeeze(0)

        # Split adjustments into alpha and beta for each arm
        adjustments = adjustments.view(self.num_arms, 2)
        alpha_adjustments = adjustments[:, 0].detach().numpy()
        beta_adjustments = adjustments[:, 1].detach().numpy()

        # Apply adjustments to original parameters
        adjusted_alphas = self.alphas * (1 + alpha_adjustments)
        adjusted_betas = self.betas * (1 + beta_adjustments)

        return adjusted_alphas, adjusted_betas

    def select_arm(self, context: np.ndarray) -> int:
        """
        Select an arm using contextual Thompson Sampling.

        Args:
            context: Context features (shape: [context_dim])

        Returns:
            Selected arm index
        """
        # Get adjusted Beta parameters
        adjusted_alphas, adjusted_betas = self._adjust_beta_params(context)

        # Sample from adjusted Beta distributions
        samples = np.array([
            np.random.beta(alpha, beta)
            for alpha, beta in zip(adjusted_alphas, adjusted_betas)
        ])

        # Select arm with highest sample
        return int(np.argmax(samples))

    def update(self,
               context: np.ndarray,
               arm: int,
               reward: float) -> None:
        """
        Update the algorithm with new observation.

        Args:
            context: Context features (shape: [context_dim])
            arm: Selected arm index
            reward: Received reward
        """
        # Store observation for neural network training
        self.contexts.append(context)
        self.arms.append(arm)
        self.rewards.append(reward)

        # Update Beta distribution for the selected arm
        if reward > 0:
            self.alphas[arm] += 1
        self.betas[arm] += 1

        # Train neural network on recent observations
        if len(self.contexts) >= 10:  # Only train when we have enough data
            self._train_nn()

    def _train_nn(self) -> None:
        """
        Train the neural network on stored context-arm-reward tuples.
        """
        if len(self.contexts) < 10:
            return

        # Convert to tensors
        contexts = torch.FloatTensor(self.contexts[-50:])  # Use recent 50 samples
        arms = torch.LongTensor(self.arms[-50:])
        rewards = torch.FloatTensor(self.rewards[-50:])

        # Compute target adjustments (based on reward and current parameters)
        # This is a simplified approach - in practice, you might want more sophisticated targets
        targets = torch.zeros_like(contexts)

        # Simple target: adjust parameters based on reward
        for i, (arm, reward) in enumerate(zip(arms, rewards)):
            if reward > 0:
                targets[i, arm] = 1.0  # Positive reward increases alpha
            else:
                targets[i, arm] = -0.5  # Negative reward increases beta

        # Forward pass
        self.optimizer.zero_grad()
        predictions = self.nn(contexts)

        # Simple loss - you could use more sophisticated loss functions
        loss = nn.MSELoss()(predictions, targets)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        # Clear stored data to prevent memory issues
        if len(self.contexts) > 100:
            self.contexts = self.contexts[-50:]
            self.arms = self.arms[-50:]
            self.rewards = self.rewards[-50:]

# Example usage and testing
if __name__ == "__main__":
    # Simple test
    num_arms = 3
    context_dim = 5

    # Create algorithm instance
    cts = ContextualThompsonSampling(num_arms, context_dim)

    # Simulate some context and selections
    for i in range(20):
        context = np.random.rand(context_dim)
        arm = cts.select_arm(context)
        reward = np.random.choice([0, 1])  # Binary reward
        cts.update(context, arm, reward)

        if i % 5 == 0:
            print(f"Step {i}: Selected arm {arm}, reward {reward}")

================================================================================
🔍 CODE REVIEWER
================================================================================
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, List, Optional, Dict, Any
from collections import defaultdict

class ContextualThompsonSampling:
    """
    Contextual Thompson Sampling for multi-armed bandits.

    This implementation extends standard Thompson Sampling by incorporating
    context information through a neural network that adjusts Beta distribution
    parameters based on observed contexts.

    Attributes:
        num_arms (int): Number of arms in the bandit.
        context_dim (int): Dimension of context features.
        hidden_dim (int): Hidden layer dimension for the neural network.
        learning_rate (float): Learning rate for neural network training.
        alpha_init (float): Initial alpha parameter for Beta distributions.
        beta_init (float): Initial beta parameter for Beta distributions.
    """

    def __init__(self, num_arms: int, context_dim: int,
                 hidden_dim: int = 32, learning_rate: float = 0.01,
                 alpha_init: float = 1.0, beta_init: float = 1.0):
        self.num_arms = num_arms
        self.context_dim = context_dim
        self.alpha_init = alpha_init
        self.beta_init = beta_init

        # Initialize Beta distributions for each arm
        self.alphas = np.full(num_arms, alpha_init)
        self.betas = np.full(num_arms, beta_init)

        # Initialize neural network for context-aware adjustments
        self.nn = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_arms * 2),  # Output alpha and beta adjustments for each arm
            nn.Softplus()  # Ensure positive values
        )

        self.optimizer = optim.Adam(self.nn.parameters(), lr=learning_rate)

        # Store training data
        self.contexts = []
        self.arms = []
        self.rewards = []

    def _adjust_beta_params(self, context: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Adjust Beta parameters using neural network based on context.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])

        Returns:
            adjusted_alphas (np.ndarray): Adjusted alpha parameters for each arm
            adjusted_betas (np.ndarray): Adjusted beta parameters for each arm
        """
        context_tensor = torch.FloatTensor(context).unsqueeze(0)
        adjustments = self.nn(context_tensor).squeeze(0)

        # Split adjustments into alpha and beta for each arm
        adjustments = adjustments.view(self.num_arms, 2)
        alpha_adjustments = adjustments[:, 0].detach().numpy()
        beta_adjustments = adjustments[:, 1].detach().numpy()

        # Apply adjustments to original parameters
        adjusted_alphas = self.alphas * (1 + alpha_adjustments)
        adjusted_betas = self.betas * (1 + beta_adjustments)

        return adjusted_alphas, adjusted_betas

    def select_arm(self, context: np.ndarray) -> int:
        """
        Select an arm using contextual Thompson Sampling.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])

        Returns:
            arm_index (int): Selected arm index
        """
        # Get adjusted Beta parameters
        adjusted_alphas, adjusted_betas = self._adjust_beta_params(context)

        # Sample from adjusted Beta distributions
        samples = np.array([
            np.random.beta(alpha, beta)
            for alpha, beta in zip(adjusted_alphas, adjusted_betas)
        ])

        # Select arm with highest sample
        return int(np.argmax(samples))

    def update(self, context: np.ndarray, arm_index: int, reward: float) -> None:
        """
        Update the algorithm with new observation.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])
            arm_index (int): Selected arm index
            reward (float): Received reward
        """
        # Store observation for neural network training
        self.contexts.append(context)
        self.arms.append(arm_index)
        self.rewards.append(reward)

        # Update Beta distribution for the selected arm
        if reward > 0:
            self.alphas[arm_index] += 1
        self.betas[arm_index] += 1

        # Train neural network on recent observations
        self._train_nn()

    def _train_nn(self) -> None:
        """
        Train the neural network on stored context-arm-reward tuples.
        """
        if len(self.contexts) < 10:
            return

        # Convert to tensors
        contexts = torch.FloatTensor(self.contexts[-50:])  # Use recent 50 samples
        arms = torch.LongTensor(self.arms[-50:])
        rewards = torch.FloatTensor(self.rewards[-50:])

        # Compute target adjustments (based on reward and current parameters)
        targets = self._compute_targets(rewards, arms)

        # Forward pass
        self.optimizer.zero_grad()
        predictions = self.nn(contexts)

        # Simple loss - you could use more sophisticated loss functions
        loss = nn.MSELoss()(predictions, targets)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        # Clear stored data to prevent memory issues
        if len(self.contexts) > 100:
            self.contexts = self.contexts[-50:]
            self.arms = self.arms[-50:]
            self.rewards = self.rewards[-50:]

    def _compute_targets(self, rewards: torch.Tensor, arms: torch.Tensor) -> torch.Tensor:
        """
        Compute target adjustments based on reward and current parameters.

        Args:
            rewards (torch.Tensor): Received rewards
            arms (torch.Tensor): Selected arm indices

        Returns:
            targets (torch.Tensor): Target adjustments for neural network training
        """
        targets = torch.zeros_like(rewards)

        # Simple target: adjust parameters based on reward
        for i, (arm_index, reward) in enumerate(zip(arms, rewards)):
            if reward > 0:
                targets[i] += self.alphas[arm_index]
            else:
                targets[i] -= self.betas[arm_index]

        return targets

# Example usage and testing
if __name__ == "__main__":
    # Simple test
    num_arms = 3
    context_dim = 5

    # Create algorithm instance
    cts = ContextualThompsonSampling(num_arms, context_dim)

    # Simulate some context and selections
    for i in range(20):
        context = np.random.rand(context_dim)
        arm_index = cts.select_arm(context)
        reward = np.random.choice([0, 1])  # Binary reward
        cts.update(context, arm_index, reward)

        if i % 5 == 0:
            print(f"Step {i}: Selected arm {arm_index}, reward {reward}")

================================================================================
🔍 TEST VALIDATOR
================================================================================
❌ Validation failed: Unknown error

================================================================================
🔍 DOCUMENTATION CHECKER
================================================================================
import numpy as np
import torch
import torch.nn as nn
import torch.optim as optim
from typing import Tuple, List, Optional, Dict, Any
from collections import defaultdict
import random

class ContextualThompsonSampling:
    """
    Contextual Thompson Sampling for multi-armed bandits.

    This implementation extends standard Thompson Sampling by incorporating context information through a neural network that adjusts Beta distribution parameters based on observed contexts.

    Attributes:
        num_arms (int): Number of arms in the bandit
        context_dim (int): Dimension of context features
        hidden_dim (int, optional): Hidden layer dimension for the neural network. Defaults to 32.
        learning_rate (float, optional): Learning rate for neural network training. Defaults to 0.01.
        alpha_init (float, optional): Initial alpha parameter for Beta distributions. Defaults to 1.0.
        beta_init (float, optional): Initial beta parameter for Beta distributions. Defaults to 1.0.
    """

    def __init__( self, num_arms: int, context_dim: int, hidden_dim: int = 32, learning_rate: float = 0.01, alpha_init: float = 1.0, beta_init: float = 1.0):
        """
        Initialize the contextual Thompson Sampling algorithm.

        Args:
            num_arms (int): Number of arms in the bandit
            context_dim (int): Dimension of context features
            hidden_dim (int, optional): Hidden layer dimension for the neural network. Defaults to 32.
            learning_rate (float, optional): Learning rate for neural network training. Defaults to 0.01.
            alpha_init (float, optional): Initial alpha parameter for Beta distributions. Defaults to 1.0.
            beta_init (float, optional): Initial beta parameter for Beta distributions. Defaults to 1.0.
        """
        self.num_arms = num_arms
        self.context_dim = context_dim
        self.alpha_init = alpha_init
        self.beta_init = beta_init

        # Initialize Beta distributions for each arm
        self.alphas = np.full(num_arms, alpha_init)
        self.betas = np.full(num_arms, beta_init)

        # Initialize neural network for context-aware adjustments
        self.nn = nn.Sequential(
            nn.Linear(context_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, num_arms * 2),  # Output alpha and beta adjustments for each arm
            nn.Softplus()  # Ensure positive values
        )

        self.optimizer = optim.Adam(self.nn.parameters(), lr=learning_rate)

        # Store training data
        self.contexts: List[np.ndarray] = []
        self.arms: List[int] = []
        self.rewards: List[float] = []

    def _adjust_beta_params(self, context: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Adjust Beta parameters using neural network based on context.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])

        Returns:
            adjusted_alphas (np.ndarray): Adjusted alpha parameters for each arm (shape: [num_arms])
            adjusted_betas (np.ndarray): Adjusted beta parameters for each arm (shape: [num_arms])

        Raises:
            ValueError: If context array does not have the expected shape.

        Example:
            >>> cts = ContextualThompsonSampling(num_arms=3, context_dim=5)
            >>> adjusted_alphas, adjusted_betas = cts._adjust_beta_params(np.random.rand(5))
            >>> print(adjusted_alphas.shape)  # Output: (3,)
        """

        if not isinstance(context, np.ndarray):
            raise ValueError("Input must be a numpy array.")
        if context.shape != (self.context_dim,):
            raise ValueError(f"Context should have shape ({self.context_dim},), but got {context.shape}.")

        context_tensor = torch.FloatTensor(context).unsqueeze(0)
        adjustments = self.nn(context_tensor).squeeze(0)

        # Split adjustments into alpha and beta for each arm
        adjustments = adjustments.view(self.num_arms, 2)
        alpha_adjustments = adjustments[:, 0].detach().numpy()
        beta_adjustments = adjustments[:, 1].detach().numpy()

        # Apply adjustments to original parameters
        adjusted_alphas = self.alphas * (1 + alpha_adjustments)
        adjusted_betas = self.betas * (1 + beta_adjustments)

        return adjusted_alphas, adjusted_betas

    def select_arm(self, context: np.ndarray) -> int:
        """
        Select an arm using contextual Thompson Sampling.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])

        Returns:
            selected_arm (int): Selected arm index

        Example:
            >>> cts = ContextualThompsonSampling(num_arms=3, context_dim=5)
            >>> selected_arm = cts.select_arm(np.random.rand(5))
            >>> print(selected_arm)  # Output: An integer between 0 and 2
        """

        # Get adjusted Beta parameters
        adjusted_alphas, adjusted_betas = self._adjust_beta_params(context)

        # Sample from adjusted Beta distributions
        samples = np.array([
            np.random.beta(alpha, beta)
            for alpha, beta in zip(adjusted_alphas, adjusted_betas)
        ])

        # Select arm with highest sample
        return int(np.argmax(samples))

    def update(self, context: np.ndarray, arm: int, reward: float) -> None:
        """
        Update the algorithm with new observation.

        Args:
            context (np.ndarray): Context features (shape: [context_dim])
            arm (int): Selected arm index
            reward (float): Received reward

        Example:
            >>> cts = ContextualThompsonSampling(num_arms=3, context_dim=5)
            >>> selected_arm = cts.select_arm(np.random.rand(5))
            >>> cts.update(context=np.random.rand(5), arm=selected_arm, reward=random.choice([0.0, 1.0]))
        """

        # Store observation for neural network training
        self.contexts.append(context)
        self.arms.append(arm)
        self.rewards.append(reward)

        # Update Beta distribution for the selected arm
        if reward > 0:
            self.alphas[arm] += 1
        self.betas[arm] += 1

        # Train neural network on recent observations
        if len(self.contexts) >= 10:  # Only train when we have enough data
            self._train_nn()

    def _train_nn(self) -> None:
        """
        Train the neural network on stored context-arm-reward tuples.

        Example:
            >>> cts = ContextualThompsonSampling(num_arms=3, context_dim=5)
            >>> selected_arm = cts.select_arm(np.random.rand(5))
            >>> cts.update(context=np.random.rand(5), arm=selected_arm, reward=random.choice([0.0, 1.0]))
            >>> # After some updates
            >>> cts._train_nn()
        """

        if len(self.contexts) < 10:
            return

        # Convert to tensors
        contexts = torch.FloatTensor(self.contexts[-50:])  # Use recent 50 samples
        arms = torch.LongTensor(self.arms[-50:])
        rewards = torch.FloatTensor(self.rewards[-50:])

        # Compute target adjustments (based on reward and current parameters)
        targets = torch.zeros_like(contexts)

        for i, (arm, reward) in enumerate(zip(arms, rewards)):
            if reward > 0:
                targets[i, arm] += 1.0  # Positive reward increases alpha
            else:
                targets[i, arm] -= 0.5  # Negative reward increases beta

        # Forward pass
        self.optimizer.zero_grad()
        predictions = self.nn(contexts)

        loss = nn.MSELoss()(predictions, targets)

        # Backward pass
        loss.backward()
        self.optimizer.step()

        if len(self.contexts) > 100:
            self.contexts = self.contexts[-50:]
            self.arms = self.arms[-50:]
            self.rewards = self.rewards[-50:]

# Example usage and testing
if __name__ == "__main__":
    # Simple test
    num_arms = 3
    context_dim = 5

    cts = ContextualThompsonSampling(num_arms, context_dim)

    for i in range(20):
        context = np.random.rand(context_dim)
        arm = cts.select_arm(context)
        reward = np.random.choice([0.0, 1.0])
        cts.update(context, arm, reward)

        if i % 5 == 0:
            print(f"Step {i}: Selected arm {arm}, reward {reward}")

================================================================================
🏆 OVERALL VERDICT
================================================================================
⚠️  1 validation check(s) failed
🔧 Please review errors and retry.
