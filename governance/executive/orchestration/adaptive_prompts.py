import random
import numpy as np
from typing import List, Dict, Tuple
from collections import deque
from dataclasses import dataclass
from scipy.special import softmax

@dataclass
class PromptVariant:
    """Represents a prompt variant with its performance metrics."""
    prompt: str
    count: int = 0
    total_reward: float = 0.0
    rewards: deque = None

    def __post_init__(self):
        if self.rewards is None:
            self.rewards = deque(maxlen=100)

class AdaptivePromptOptimizer:
    """Adaptive prompt optimization using reinforcement learning."""

    def __init__(self, initial_prompts: List[str], learning_rate: float = 0.01):
        self.prompt_variants: Dict[str, PromptVariant] = {
            prompt: PromptVariant(prompt) for prompt in initial_prompts
        }
        self.learning_rate = learning_rate
        self.prompt_history: List[Tuple[str, float]] = []
        self._population_size = len(initial_prompts)

    def sample_prompt(self) -> str:
        """Sample a prompt using weighted probability based on performance."""
        if not self.prompt_variants:
            raise ValueError("No prompt variants available")

        prompts = list(self.prompt_variants.keys())
        rewards = [self._get_weighted_reward(p) for p in prompts]
        probabilities = softmax(np.array(rewards) * 10)  # Temperature scaling

        selected_prompt = random.choices(prompts, weights=probabilities)[0]
        return selected_prompt

    def update_prompt(self, prompt: str, reward: float) -> None:
        """Update prompt variant with new reward."""
        if prompt not in self.prompt_variants:
            self.prompt_variants[prompt] = PromptVariant(prompt)

        variant = self.prompt_variants[prompt]
        variant.count += 1
        variant.total_reward += reward
        variant.rewards.append(reward)
        self.prompt_history.append((prompt, reward))

    def _get_weighted_reward(self, prompt: str) -> float:
        """Calculate weighted reward for prompt selection."""
        variant = self.prompt_variants[prompt]
        if variant.count == 0:
            return 0.0

        # Use recent performance with decay
        recent_rewards = list(variant.rewards)
        if not recent_rewards:
            return variant.total_reward / variant.count

        # Weight recent rewards more heavily
        weights = np.array([0.1 ** i for i in range(len(recent_rewards)-1, -1, -1)])
        weighted_avg = np.average(recent_rewards, weights=weights)
        return weighted_avg

    def mutate_prompt(self, prompt: str, mutation_rate: float = 0.3) -> str:
        """Generate a mutated version of the prompt."""
        # Simple mutation: random word replacement or addition
        words = prompt.split()
        if not words:
            return prompt

        mutated_words = []
        for word in words:
            if random.random() < mutation_rate:
                # Replace with random word or add new word
                if random.random() < 0.5:
                    mutated_words.append(f"mutated_{random.randint(1, 100)}")
                else:
                    mutated_words.append(word + "_mutated")
            else:
                mutated_words.append(word)

        return " ".join(mutated_words)

    def update_population(self, elite_size: int = 2) -> None:
        """Generate new prompts from top performing variants."""
        # Sort by performance
        sorted_prompts = sorted(
            self.prompt_variants.items(),
            key=lambda x: self._get_weighted_reward(x[0]),
            reverse=True
        )

        # Keep top performers
        top_prompts = [prompt for prompt, _ in sorted_prompts[:elite_size]]

        # Generate new variants through mutation
        new_prompts = []
        for prompt in top_prompts:
            mutated = self.mutate_prompt(prompt)
            new_prompts.append(mutated)

        # Add new variants to population
        for new_prompt in new_prompts:
            if new_prompt not in self.prompt_variants:
                self.prompt_variants[new_prompt] = PromptVariant(new_prompt)

    def get_performance_metrics(self) -> Dict:
        """Get current performance metrics for all prompts."""
        metrics = {}
        for prompt, variant in self.prompt_variants.items():
            if variant.count > 0:
                metrics[prompt] = {
                    'count': variant.count,
                    'avg_reward': variant.total_reward / variant.count,
                    'recent_rewards': list(variant.rewards)
                }
        return metrics
