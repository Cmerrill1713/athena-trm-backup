import random
from typing import List, Dict, Tuple
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class RolloutResult:
    """Represents the result of a single rollout simulation."""
    success: bool
    reward: float
    steps_taken: int

@dataclass
class ActionStats:
    """Tracks statistics for a single action across rollouts."""
    action: str
    total_rollouts: int
    successful_rollouts: int
    total_reward: float
    avg_reward: float
    success_rate: float

class SimpleWorldModel:
    """A lightweight world model that tracks transition probabilities."""

    def __init__(self):
        self.transition_counts: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.state_counts: Dict[str, int] = defaultdict(int)
        self.action_counts: Dict[str, int] = defaultdict(int)
        self.total_transitions = 0

    def update_transition(self, state: str, action: str, next_state: str) -> None:
        """Update transition probabilities based on observed outcome."""
        self.transition_counts[state][action][next_state] += 1
        self.state_counts[state] += 1
        self.action_counts[action] += 1
        self.total_transitions += 1

    def get_transition_prob(self, state: str, action: str, next_state: str) -> float:
        """Get probability of transitioning from state to next_state given action."""
        if self.transition_counts[state][action][next_state] == 0:
            # Return uniform probability for unseen transitions
            return 1.0 / max(1, len(self.transition_counts[state][action]))
        return self.transition_counts[state][action][next_state] / sum(self.transition_counts[state][action].values())

    def sample_next_state(self, state: str, action: str) -> str:
        """Sample next state based on transition probabilities."""
        if state not in self.transition_counts or action not in self.transition_counts[state]:
            # Return uniform sampling if no data
            return state  # Stay in same state if no transitions recorded

        transitions = self.transition_counts[state][action]
        total = sum(transitions.values())

        # Sample based on probabilities
        rand = random.random()
        cumulative = 0.0

        for next_state, count in transitions.items():
            cumulative += count / total
            if rand <= cumulative:
                return next_state

        # Fallback (should not happen)
        return list(transitions.keys())[0]

class StatisticalPlanner:
    """Statistical Planning via Monte Carlo Tree Search rollouts."""

    def __init__(self,
                 actions: List[str],
                 num_rollouts: int = 100,
                 max_steps_per_rollout: int = 10,
                 exploration_weight: float = 1.0):
        """
        Initialize the Statistical Planner.

        Args:
            actions: List of possible actions
            num_rollouts: Number of rollouts to perform per action
            max_steps_per_rollout: Maximum steps per rollout simulation
            exploration_weight: Weight for exploration vs exploitation in Thompson sampling
        """
        self.actions = actions
        self.num_rollouts = num_rollouts
        self.max_steps_per_rollout = max_steps_per_rollout
        self.exploration_weight = exploration_weight
        self.world_model = SimpleWorldModel()
        self.action_stats: Dict[str, ActionStats] = {}
        self._reset_action_stats()

    def _reset_action_stats(self) -> None:
        """Reset action statistics."""
        self.action_stats = {
            action: ActionStats(
                action=action,
                total_rollouts=0,
                successful_rollouts=0,
                total_reward=0.0,
                avg_reward=0.0,
                success_rate=0.0
            )
            for action in self.actions
        }

    def _run_single_rollout(self, state: str, action: str) -> RolloutResult:
        """
        Run a single rollout simulation.

        Args:
            state: Current state
            action: Action to simulate

        Returns:
            RolloutResult with simulation outcome
        """
        current_state = state
        total_reward = 0.0
        steps_taken = 0

        # Simulate the action
        for _ in range(self.max_steps_per_rollout):
            steps_taken += 1

            # Get reward for current state-action pair
            reward = self._get_reward(current_state, action)
            total_reward += reward

            # Sample next state
            next_state = self.world_model.sample_next_state(current_state, action)

            # Check if we should terminate (simple termination condition)
            if random.random() < 0.1:  # 10% chance of termination
                break

            current_state = next_state

        # Success is determined by positive reward
        success = total_reward > 0

        return RolloutResult(
            success=success,
            reward=total_reward,
            steps_taken=steps_taken
        )

    def _get_reward(self, state: str, action: str) -> float:
        """
        Get reward for state-action pair.
        This is a simple reward function - in practice, this would be more complex.
        """
        # Simple reward function - can be extended
        if action == "explore":
            return 1.0  # Reward for exploration
        elif action == "exploit":
            return 2.0  # Higher reward for exploitation
        else:
            return 0.0  # Default reward

    def _perform_rollouts(self, state: str) -> Dict[str, ActionStats]:
        """
        Perform rollouts for all actions and return statistics.

        Args:
            state: Current state

        Returns:
            Dictionary mapping actions to their rollout statistics
        """
        action_results = {}

        for action in self.actions:
            total_reward = 0.0
            successful_rollouts = 0
            total_rollouts = self.num_rollouts

            for _ in range(self.num_rollouts):
                result = self._run_single_rollout(state, action)
                total_reward += result.reward

                if result.success:
                    successful_rollouts += 1

            # Calculate statistics
            avg_reward = total_reward / total_rollouts if total_rollouts > 0 else 0.0
            success_rate = successful_rollouts / total_rollouts if total_rollouts > 0 else 0.0

            action_results[action] = ActionStats(
                action=action,
                total_rollouts=total_rollouts,
                successful_rollouts=successful_rollouts,
                total_reward=total_reward,
                avg_reward=avg_reward,
                success_rate=success_rate
            )

        return action_results

    def _thompson_sampling(self, state: str) -> str:
        """
        Select action using Thompson Sampling for exploration/exploitation balance.

        Args:
            state: Current state

        Returns:
            Selected action
        """
        # For simplicity, we'll use a basic approach that balances exploration and exploitation
        # In a more sophisticated implementation, this would sample from posterior distributions

        best_action = None
        best_expected_value = float('-inf')

        for action in self.actions:
            stats = self.action_stats[action]

            # Expected value = success_rate * avg_reward
            expected_value = stats.success_rate * stats.avg_reward

            # Add exploration bonus (simple implementation)
            exploration_bonus = self.exploration_weight * (1.0 / max(1, stats.total_rollouts))
            expected_value += exploration_bonus

            if expected_value > best_expected_value:
                best_expected_value = expected_value
                best_action = action

        return best_action

    def select_action(self, state: str) -> str:
        """
        Select the best action using statistical planning with rollouts.

        Args:
            state: Current state

        Returns:
            Selected action
        """
        # Perform rollouts for all actions
        action_stats = self._perform_rollouts(state)

        # Update internal statistics
        for action, stats in action_stats.items():
            self.action_stats[action] = stats

        # Select action using Thompson Sampling or greedy approach
        return self._thompson_sampling(state)

    def update_world_model(self, state: str, action: str, next_state: str) -> None:
        """
        Update the world model with observed outcome.

        Args:
            state: Previous state
            action: Action taken
            next_state: Resulting state
        """
        self.world_model.update_transition(state, action, next_state)

    def get_action_statistics(self) -> Dict[str, ActionStats]:
        """
        Get current statistics for all actions.

        Returns:
            Dictionary of action statistics
        """
        return self.action_stats.copy()

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    actions = ["explore", "exploit", "wait"]
    planner = StatisticalPlanner(actions, num_rollouts=50, max_steps_per_rollout=5)

    # Simulate some planning
    current_state = "start"
    selected_action = planner.select_action(current_state)
    print(f"Selected action: {selected_action}")

    # Update world model with outcome
    planner.update_world_model(current_state, selected_action, "intermediate")

    # Get statistics
    stats = planner.get_action_statistics()
    for action, stat in stats.items():
        print(f"Action {action}: Success rate = {stat.success_rate:.2f}, Avg reward = {stat.avg_reward:.2f}")
