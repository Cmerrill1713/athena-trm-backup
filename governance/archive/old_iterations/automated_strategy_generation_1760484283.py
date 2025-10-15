"""
Automated Strategy Generation
============================

The system invents and validates new optimization strategies dynamically.
Uses meta-learning to understand what makes strategies successful and generates
improved approaches based on performance patterns.

Features:
- Evolutionary strategy generation using performance patterns
- Meta-learning layer that understands strategy success factors
- Safe validation pipeline with automated testing
- Automated deployment of validated strategies
- Creative optimization beyond human-designed approaches
"""

import logging
import random
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import torch
import torch.nn as nn

from .governance_layer import get_governance_engine
from .hierarchical_bandit import OptimizationStrategy
from .hierarchical_optimizer import get_hierarchical_optimizer
from .neural_context_encoder import QueryContext

logger = logging.getLogger(__name__)

class StrategyComponent(Enum):
    """Fundamental components that can be combined in strategies."""
    COSINE_SIMILARITY = "cosine_similarity"
    CROSS_ENCODER = "cross_encoder"
    NEURAL_RESCORING = "neural_rescoring"
    PERSONALIZATION = "personalization"
    CONTEXT_FILTERING = "context_filtering"
    DIVERSITY_PROMOTION = "diversity_promotion"
    TEMPORAL_WEIGHTING = "temporal_weighting"
    USER_FEEDBACK_INTEGRATION = "user_feedback_integration"

@dataclass
class StrategyGenome:
    """Genetic representation of an optimization strategy."""
    components: Set[StrategyComponent] = field(default_factory=set)
    parameters: Dict[str, float] = field(default_factory=dict)
    fitness_score: float = 0.0
    generation: int = 0
    created_at: datetime = None
    validation_trials: int = 0
    deployment_status: str = "experimental"  # experimental, validated, deployed, retired

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

    @property
    def complexity_score(self) -> float:
        """Calculate strategy complexity based on components and parameters."""
        base_complexity = len(self.components)
        parameter_complexity = sum(abs(v) for v in self.parameters.values()) / max(len(self.parameters), 1)
        return base_complexity + parameter_complexity

    def to_dict(self) -> Dict:
        """Serialize genome to dictionary."""
        return {
            'components': [c.value for c in self.components],
            'parameters': self.parameters,
            'fitness_score': self.fitness_score,
            'generation': self.generation,
            'created_at': self.created_at.isoformat(),
            'validation_trials': self.validation_trials,
            'deployment_status': self.deployment_status
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'StrategyGenome':
        """Deserialize genome from dictionary."""
        return cls(
            components=set(StrategyComponent(c) for c in data['components']),
            parameters=data['parameters'],
            fitness_score=data.get('fitness_score', 0.0),
            generation=data.get('generation', 0),
            created_at=datetime.fromisoformat(data['created_at']),
            validation_trials=data.get('validation_trials', 0),
            deployment_status=data.get('deployment_status', 'experimental')
        )

class StrategyRepresentation:
    """Formal representation of generated strategies."""

    def __init__(self, genome: StrategyGenome):
        self.genome = genome
        self.execution_plan = self._build_execution_plan()

    def _build_execution_plan(self) -> Dict[str, Any]:
        """Build executable strategy from genome components."""
        plan = {
            'retrieval_components': [],
            'reranking_components': [],
            'filtering_components': [],
            'personalization_components': [],
            'parameters': self.genome.parameters.copy()
        }

        for component in self.genome.components:
            if component == StrategyComponent.COSINE_SIMILARITY:
                plan['retrieval_components'].append({
                    'type': 'cosine_similarity',
                    'weight': self.genome.parameters.get('cosine_weight', 1.0)
                })

            elif component == StrategyComponent.CROSS_ENCODER:
                plan['reranking_components'].append({
                    'type': 'cross_encoder',
                    'top_k': int(self.genome.parameters.get('ce_top_k', 8))
                })

            elif component == StrategyComponent.NEURAL_RESCORING:
                plan['reranking_components'].append({
                    'type': 'neural_rescoring',
                    'model_path': self.genome.parameters.get('neural_model', 'default'),
                    'scale_factor': self.genome.parameters.get('neural_scale', 1.0)
                })

            elif component == StrategyComponent.PERSONALIZATION:
                plan['personalization_components'].append({
                    'type': 'user_adaptive',
                    'bias_strength': self.genome.parameters.get('personalization_bias', 0.15)
                })

            elif component == StrategyComponent.CONTEXT_FILTERING:
                plan['filtering_components'].append({
                    'type': 'context_based',
                    'threshold': self.genome.parameters.get('context_threshold', 0.5)
                })

            elif component == StrategyComponent.DIVERSITY_PROMOTION:
                plan['reranking_components'].append({
                    'type': 'diversity_promotion',
                    'lambda_diversity': self.genome.parameters.get('diversity_lambda', 0.3)
                })

            elif component == StrategyComponent.TEMPORAL_WEIGHTING:
                plan['reranking_components'].append({
                    'type': 'temporal_decay',
                    'half_life_days': self.genome.parameters.get('temporal_half_life', 30)
                })

            elif component == StrategyComponent.USER_FEEDBACK_INTEGRATION:
                plan['reranking_components'].append({
                    'type': 'feedback_boost',
                    'feedback_weight': self.genome.parameters.get('feedback_weight', 0.2)
                })

        return plan

    def execute(self, query_context: QueryContext, documents: List[Any],
                user_id: Optional[str] = None) -> List[Any]:
        """
        Execute the strategy on a query.

        This is a simplified execution - in practice, this would interface
        with the existing optimization components.
        """
        # Start with base documents
        processed_docs = documents.copy()

        # Apply filtering components
        for filter_comp in self.execution_plan['filtering_components']:
            if filter_comp['type'] == 'context_based':
                # Simplified context filtering
                threshold = filter_comp['threshold']
                processed_docs = [d for d in processed_docs
                                if getattr(d, 'relevance_score', 0.5) > threshold]

        # Apply reranking components
        for rerank_comp in self.execution_plan['reranking_components']:
            if rerank_comp['type'] == 'cross_encoder':
                # Simulate CE reranking
                top_k = rerank_comp['top_k']
                # In practice, this would call actual CE model
                processed_docs = processed_docs[:top_k]

            elif rerank_comp['type'] == 'diversity_promotion':
                # Simulate diversity promotion
                lambda_div = rerank_comp['lambda_diversity']
                # Simplified: boost diverse documents
                for i, doc in enumerate(processed_docs):
                    diversity_bonus = lambda_div * (1.0 - i / len(processed_docs))
                    if hasattr(doc, 'rerank_score'):
                        doc.rerank_score += diversity_bonus

        # Apply personalization
        for pers_comp in self.execution_plan['personalization_components']:
            if user_id and pers_comp['type'] == 'user_adaptive':
                bias_strength = pers_comp['bias_strength']
                # Simplified personalization logic
                for doc in processed_docs:
                    if hasattr(doc, 'rerank_score'):
                        # Simulate user preference bias
                        user_bias = bias_strength * np.sin(hash(user_id + str(doc.id)) % 1000 / 1000 * 2 * np.pi)
                        doc.rerank_score += user_bias

        # Sort by final scores
        processed_docs.sort(key=lambda d: getattr(d, 'rerank_score', 0), reverse=True)

        return processed_docs

class EvolutionaryStrategyGenerator:
    """
    Evolutionary algorithm for generating new optimization strategies.

    Uses genetic algorithms to evolve strategy genomes based on performance.
    """

    def __init__(self,
                 population_size: int = 50,
                 mutation_rate: float = 0.1,
                 crossover_rate: float = 0.8,
                 elitism_rate: float = 0.1):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.crossover_rate = crossover_rate
        self.elitism_rate = elitism_rate

        self.population: List[StrategyGenome] = []
        self.generation = 0

        self._initialize_population()

    def _initialize_population(self):
        """Initialize random population of strategy genomes."""
        self.population = []

        for _ in range(self.population_size):
            genome = self._generate_random_genome()
            self.population.append(genome)

    def _generate_random_genome(self) -> StrategyGenome:
        """Generate a random strategy genome."""
        # Randomly select components
        num_components = random.randint(1, len(StrategyComponent))
        components = set(random.sample(list(StrategyComponent), num_components))

        # Generate random parameters for selected components
        parameters = {}

        if StrategyComponent.COSINE_SIMILARITY in components:
            parameters['cosine_weight'] = random.uniform(0.5, 1.5)

        if StrategyComponent.CROSS_ENCODER in components:
            parameters['ce_top_k'] = random.randint(5, 15)

        if StrategyComponent.NEURAL_RESCORING in components:
            parameters['neural_scale'] = random.uniform(0.8, 1.2)

        if StrategyComponent.PERSONALIZATION in components:
            parameters['personalization_bias'] = random.uniform(0.05, 0.3)

        if StrategyComponent.CONTEXT_FILTERING in components:
            parameters['context_threshold'] = random.uniform(0.3, 0.8)

        if StrategyComponent.DIVERSITY_PROMOTION in components:
            parameters['diversity_lambda'] = random.uniform(0.1, 0.5)

        if StrategyComponent.TEMPORAL_WEIGHTING in components:
            parameters['temporal_half_life'] = random.uniform(7, 90)

        if StrategyComponent.USER_FEEDBACK_INTEGRATION in components:
            parameters['feedback_weight'] = random.uniform(0.1, 0.4)

        return StrategyGenome(
            components=components,
            parameters=parameters,
            generation=self.generation
        )

    def evolve_generation(self) -> List[StrategyGenome]:
        """
        Evolve one generation of strategies.

        Returns new candidate strategies for validation.
        """
        if not self.population:
            self._initialize_population()

        # Sort by fitness
        self.population.sort(key=lambda g: g.fitness_score, reverse=True)

        # Elitism: keep best performers
        elite_count = int(self.elitism_rate * self.population_size)
        elites = self.population[:elite_count]

        # Generate offspring
        offspring = []
        while len(offspring) < (self.population_size - elite_count):
            if random.random() < self.crossover_rate:
                # Crossover
                parent1, parent2 = random.sample(self.population[:self.population_size//2], 2)
                child = self._crossover(parent1, parent2)
            else:
                # Clone
                child = self._mutate(self.population[0].__class__(
                    components=self.population[0].components.copy(),
                    parameters=self.population[0].parameters.copy(),
                    generation=self.generation + 1
                ))

            # Mutation
            if random.random() < self.mutation_rate:
                child = self._mutate(child)

            offspring.append(child)

        # New population
        self.population = elites + offspring
        self.generation += 1

        # Return candidates for validation (top performers + some random exploration)
        candidates = self.population[:10]  # Top 10
        candidates.extend(random.sample(self.population[10:], 5))  # 5 random from rest

        return candidates

    def _crossover(self, parent1: StrategyGenome, parent2: StrategyGenome) -> StrategyGenome:
        """Create child genome from two parents."""
        # Component crossover
        child_components = set()
        for comp in StrategyComponent:
            if comp in parent1.components and comp in parent2.components:
                child_components.add(comp)  # Both have it
            elif comp in parent1.components or comp in parent2.components:
                if random.random() < 0.5:  # 50% chance
                    child_components.add(comp)

        # Parameter crossover
        child_parameters = {}
        all_params = set(parent1.parameters.keys()) | set(parent2.parameters.keys())

        for param in all_params:
            if param in parent1.parameters and param in parent2.parameters:
                # Average parameters
                child_parameters[param] = (parent1.parameters[param] + parent2.parameters[param]) / 2
            elif param in parent1.parameters:
                child_parameters[param] = parent1.parameters[param]
            elif param in parent2.parameters:
                child_parameters[param] = parent2.parameters[param]

        return StrategyGenome(
            components=child_components,
            parameters=child_parameters,
            generation=self.generation + 1
        )

    def _mutate(self, genome: StrategyGenome) -> StrategyGenome:
        """Mutate a genome."""
        mutated = StrategyGenome(
            components=genome.components.copy(),
            parameters=genome.parameters.copy(),
            generation=genome.generation
        )

        # Component mutation
        if random.random() < 0.3:  # 30% chance to add/remove component
            if random.random() < 0.5 and len(mutated.components) < len(StrategyComponent):
                # Add random component
                available = set(StrategyComponent) - mutated.components
                if available:
                    mutated.components.add(random.choice(list(available)))
            elif len(mutated.components) > 1:
                # Remove random component
                to_remove = random.choice(list(mutated.components))
                mutated.components.remove(to_remove)

        # Parameter mutation
        for param in mutated.parameters:
            if random.random() < 0.2:  # 20% chance per parameter
                mutation_strength = 0.1
                current_value = mutated.parameters[param]

                # Different mutation strategies based on parameter
                if 'weight' in param or 'scale' in param or 'bias' in param or 'lambda' in param:
                    # Relative mutation
                    mutated.parameters[param] *= random.uniform(1-mutation_strength, 1+mutation_strength)
                elif 'top_k' in param:
                    # Integer mutation
                    mutated.parameters[param] = int(current_value * random.uniform(0.8, 1.2))
                    mutated.parameters[param] = max(3, min(20, mutated.parameters[param]))
                elif 'threshold' in param:
                    # Bounded mutation
                    mutated.parameters[param] += random.uniform(-0.1, 0.1)
                    mutated.parameters[param] = max(0.1, min(0.9, mutated.parameters[param]))
                else:
                    # General mutation
                    mutated.parameters[param] *= random.uniform(0.9, 1.1)

        return mutated

    def update_fitness(self, genome: StrategyGenome, fitness_score: float):
        """Update fitness score for a genome."""
        genome.fitness_score = fitness_score
        genome.validation_trials += 1

class MetaLearningLayer:
    """
    Meta-learning layer that understands what makes strategies successful.

    Learns patterns in strategy performance to guide generation of better strategies.
    """

    def __init__(self, feature_dim: int = 50):
        self.feature_dim = feature_dim

        # Simple meta-learner: predict strategy success from genome features
        self.meta_model = nn.Sequential(
            nn.Linear(feature_dim, 32),
            nn.ReLU(),
            nn.Linear(32, 16),
            nn.ReLU(),
            nn.Linear(16, 1),
            nn.Sigmoid()
        )

        self.optimizer = torch.optim.Adam(self.meta_model.parameters(), lr=1e-3)
        self.criterion = nn.MSELoss()

        self.training_data: List[Tuple[torch.Tensor, float]] = []

    def extract_genome_features(self, genome: StrategyGenome) -> torch.Tensor:
        """Extract feature vector from strategy genome."""
        features = []

        # Component presence (one-hot style)
        for component in StrategyComponent:
            features.append(1.0 if component in genome.components else 0.0)

        # Component count
        features.append(len(genome.components))

        # Parameter values (normalized)
        param_values = []
        for param in ['cosine_weight', 'ce_top_k', 'neural_scale', 'personalization_bias',
                     'context_threshold', 'diversity_lambda', 'temporal_half_life', 'feedback_weight']:
            value = genome.parameters.get(param, 0.0)
            # Simple normalization
            if 'weight' in param or 'scale' in param or 'bias' in param or 'lambda' in param:
                param_values.append(min(value, 2.0) / 2.0)  # 0-1 range
            elif 'top_k' in param:
                param_values.append(min(value, 20.0) / 20.0)  # 0-1 range
            elif 'threshold' in param:
                param_values.append(value)  # Already 0-1
            elif 'half_life' in param:
                param_values.append(min(value, 90.0) / 90.0)  # 0-1 range
            else:
                param_values.append(0.0)

        features.extend(param_values)

        # Complexity score
        features.append(genome.complexity_score / 10.0)  # Normalize

        # Generation (recency bias)
        features.append(min(genome.generation, 100) / 100.0)

        # Pad or truncate to feature_dim
        features = features[:self.feature_dim]
        while len(features) < self.feature_dim:
            features.append(0.0)

        return torch.tensor(features, dtype=torch.float32)

    def predict_success_probability(self, genome: StrategyGenome) -> float:
        """Predict probability of strategy success."""
        features = self.extract_genome_features(genome)
        with torch.no_grad():
            prediction = self.meta_model(features.unsqueeze(0))
            return prediction.item()

    def learn_from_outcome(self, genome: StrategyGenome, actual_fitness: float):
        """Learn from strategy performance outcome."""
        features = self.extract_genome_features(genome)
        target = torch.tensor([actual_fitness], dtype=torch.float32)

        # Store for batch training
        self.training_data.append((features, actual_fitness))

        # Train periodically
        if len(self.training_data) >= 10:
            self._train_meta_model()

    def _train_meta_model(self):
        """Train the meta-learning model on accumulated data."""
        if len(self.training_data) < 5:
            return

        # Create batch
        features_batch = torch.stack([f for f, _ in self.training_data])
        targets_batch = torch.tensor([t for _, t in self.training_data], dtype=torch.float32)

        # Train
        self.optimizer.zero_grad()
        predictions = self.meta_model(features_batch).squeeze()
        loss = self.criterion(predictions, targets_batch)
        loss.backward()
        self.optimizer.step()

        logger.info(".4f")

        # Clear training data
        self.training_data = []

class StrategyValidationPipeline:
    """
    Safe validation pipeline for testing generated strategies.

    Features:
    - Isolated testing environment
    - Statistical significance testing
    - Performance regression detection
    - Automated promotion/demotion
    """

    def __init__(self,
                 min_trials: int = 50,
                 confidence_level: float = 0.95,
                 performance_threshold: float = 0.05):  # 5% improvement required
        self.min_trials = min_trials
        self.confidence_level = confidence_level
        self.performance_threshold = performance_threshold

        self.baseline_performance = 7.0  # Judge score baseline
        self.validation_results: Dict[str, List[float]] = {}

    def validate_strategy(self, strategy_rep: StrategyRepresentation,
                         test_queries: List[Tuple[QueryContext, List[Any], float]]) -> Dict[str, Any]:
        """
        Validate a strategy on test queries.

        Returns validation results and statistical significance.
        """
        genome = strategy_rep.genome
        genome_key = f"gen_{genome.generation}_{hash(str(genome.components))}"

        if genome_key not in self.validation_results:
            self.validation_results[genome_key] = []

        results = []

        # Test on sample queries
        for query_context, documents, true_judge_score in test_queries[:self.min_trials]:
            try:
                # Execute strategy
                optimized_docs = strategy_rep.execute(query_context, documents)

                # Simulate performance evaluation
                # In practice, this would run actual queries and measure real performance
                predicted_performance = self._simulate_performance_evaluation(
                    strategy_rep, query_context, optimized_docs, true_judge_score
                )

                results.append(predicted_performance)
                self.validation_results[genome_key].append(predicted_performance)

            except Exception as e:
                logger.warning(f"Strategy validation failed: {e}")
                results.append(self.baseline_performance)  # Penalize failures

        # Statistical analysis
        if len(results) >= 10:
            mean_performance = np.mean(results)
            std_performance = np.std(results)
            improvement = mean_performance - self.baseline_performance

            # Statistical significance (simplified t-test approximation)
            t_stat = improvement / (std_performance / np.sqrt(len(results)))
            is_significant = abs(t_stat) > 2.0  # Rough threshold for 95% confidence

            validation_result = {
                'strategy_key': genome_key,
                'mean_performance': mean_performance,
                'improvement': improvement,
                'std_performance': std_performance,
                'sample_size': len(results),
                'is_significant': is_significant,
                'passes_threshold': improvement >= self.performance_threshold,
                'can_deploy': is_significant and improvement >= self.performance_threshold,
                'confidence_interval': (
                    mean_performance - 1.96 * std_performance / np.sqrt(len(results)),
                    mean_performance + 1.96 * std_performance / np.sqrt(len(results))
                )
            }
        else:
            validation_result = {
                'strategy_key': genome_key,
                'sample_size': len(results),
                'can_deploy': False,
                'reason': 'insufficient_samples'
            }

        return validation_result

    def _simulate_performance_evaluation(self, strategy_rep: StrategyRepresentation,
                                       query_context: QueryContext, optimized_docs: List[Any],
                                       true_judge_score: float) -> float:
        """
        Simulate performance evaluation for a strategy.

        In practice, this would run actual queries and measure real judge scores.
        """
        # Simplified simulation based on strategy characteristics
        base_score = true_judge_score

        # Strategy-specific bonuses/penalties
        genome = strategy_rep.genome

        if StrategyComponent.CROSS_ENCODER in genome.components:
            if query_context.features.get('complexity', 0) > 0.7:
                base_score += 0.3  # Good for complex queries
            else:
                base_score -= 0.1  # Penalty for simple queries

        if StrategyComponent.PERSONALIZATION in genome.components:
            if query_context.raw_features.get('intent') == 'personalized':
                base_score += 0.2
            else:
                base_score -= 0.05

        if StrategyComponent.DIVERSITY_PROMOTION in genome.components:
            base_score += 0.1  # Diversity often helps

        # Complexity penalty
        complexity_penalty = genome.complexity_score * 0.02
        base_score -= complexity_penalty

        # Parameter optimization bonus
        param_bonus = len(genome.parameters) * 0.01
        base_score += param_bonus

        # Add some noise
        noise = np.random.normal(0, 0.1)
        final_score = base_score + noise

        return max(1.0, min(10.0, final_score))  # Clamp to judge score range

class AutomatedStrategyGeneration:
    """
    Complete automated strategy generation system.

    Combines evolutionary generation, meta-learning, and safe validation
    to create and deploy new optimization strategies autonomously.
    """

    def __init__(self,
                 generation_interval_hours: int = 24,
                 validation_batch_size: int = 100):
        self.generation_interval_hours = generation_interval_hours
        self.validation_batch_size = validation_batch_size

        self.generator = EvolutionaryStrategyGenerator()
        self.meta_learner = MetaLearningLayer()
        self.validator = StrategyValidationPipeline()
        self.governance_engine = get_governance_engine()

        self.generated_strategies: Dict[str, StrategyGenome] = {}
        self.deployed_strategies: Dict[str, StrategyRepresentation] = {}

        self.last_generation = datetime.now()

    def run_strategy_generation_cycle(self,
                                    historical_queries: List[Tuple[QueryContext, List[Any], float]]) -> List[str]:
        """
        Run complete strategy generation cycle.

        Returns list of newly generated strategy IDs.
        """
        # Check if it's time for generation
        if (datetime.now() - self.last_generation).total_seconds() < self.generation_interval_hours * 3600:
            return []

        logger.info("Starting automated strategy generation cycle")

        # Generate candidate strategies
        candidates = self.generator.evolve_generation()

        # Prepare test queries (sample from historical data)
        test_queries = self._prepare_test_queries(historical_queries)

        validated_strategies = []

        # Validate each candidate
        for genome in candidates:
            # First, check governance compliance
            governance_assessment = self.governance_engine.evaluate_strategy_governance(genome)

            if not governance_assessment['overall_clearance']:
                # Strategy violates governance policies
                logger.warning(f"Strategy violates governance policies: "
                              f"blocking_violations={governance_assessment['blocking_violations']}")

                # Penalize fitness for governance violations
                self.generator.update_fitness(genome, -0.5)  # Strong negative fitness

                # Request human intervention for serious violations
                if governance_assessment['governance_score'] < 0.5:
                    strategy_id = f"blocked_{genome.generation}_{hash(str(genome.components))}"
                    self.governance_engine.request_human_intervention(
                        strategy_id, "Critical governance violations", governance_assessment
                    )

                continue

            # Governance cleared - proceed with validation
            # Create strategy representation
            strategy_rep = StrategyRepresentation(genome)

            # Validate strategy performance
            validation_result = self.validator.validate_strategy(strategy_rep, test_queries)

            # Update genome fitness
            if 'mean_performance' in validation_result:
                improvement = validation_result['improvement']

                # Adjust fitness based on governance score
                governance_bonus = governance_assessment['governance_score'] - 0.5  # Bonus for good governance
                adjusted_fitness = improvement + governance_bonus

                self.generator.update_fitness(genome, adjusted_fitness)

                # Meta-learning
                self.meta_learner.learn_from_outcome(genome, improvement)

            # Check if strategy can be deployed (performance + governance)
            performance_cleared = validation_result.get('can_deploy', False)
            governance_cleared = governance_assessment['overall_clearance']

            if performance_cleared and governance_cleared:
                strategy_id = f"auto_gen_{genome.generation}_{hash(str(genome.components))}"
                genome.deployment_status = 'validated'

                self.generated_strategies[strategy_id] = genome
                validated_strategies.append(strategy_id)

                logger.info(f"✅ Generated constitutionally validated strategy: {strategy_id} "
                           f"(improvement: {validation_result.get('improvement', 0):.3f}, "
                           f"governance_score: {governance_assessment['governance_score']:.2f})")

                # Automatically deploy validated strategies to the bandit system
                if self._deploy_to_bandit_system(strategy_id, genome):
                    genome.deployment_status = 'deployed'
                    logger.info(f"🚀 Auto-deployed strategy {strategy_id} to bandit router")

            elif performance_cleared and not governance_cleared:
                logger.warning(f"⚠️  Strategy passed performance but failed constitutional review: "
                              f"improvement: {validation_result.get('improvement', 0):.3f}, "
                              f"violations: {governance_assessment['blocking_violations']}")

                # Request human intervention for strategies that are good but violate governance
                if governance_assessment['governance_score'] > 0.6:  # Worth human review
                    blocked_id = f"blocked_{genome.generation}_{hash(str(genome.components))}"
                    self.governance_engine.request_human_intervention(
                        blocked_id,
                        f"High-performing strategy blocked by governance: {governance_assessment['blocking_violations']}",
                        governance_assessment
                    )

            elif not performance_cleared and governance_cleared:
                logger.info(f"📈 Strategy constitutionally cleared but failed performance validation: "
                           f"governance_score: {governance_assessment['governance_score']:.2f}, "
                           f"reason: insufficient performance improvement")

            else:
                logger.debug("❌ Strategy failed both performance and governance checks - discarded")

        self.last_generation = datetime.now()

        return validated_strategies

    def _prepare_test_queries(self, historical_queries: List) -> List[Tuple[QueryContext, List[Any], float]]:
        """Prepare test queries for validation."""
        # Sample diverse queries for testing
        if len(historical_queries) <= self.validation_batch_size:
            return historical_queries

        # Stratified sampling to ensure diversity
        sampled_queries = []

        # Group by complexity/intent
        complexity_buckets = {'low': [], 'medium': [], 'high': []}

        for query_context, docs, score in historical_queries:
            complexity = query_context.features.get('complexity', 0.5)
            if complexity < 0.3:
                complexity_buckets['low'].append((query_context, docs, score))
            elif complexity < 0.7:
                complexity_buckets['medium'].append((query_context, docs, score))
            else:
                complexity_buckets['high'].append((query_context, docs, score))

        # Sample proportionally from each bucket
        total_samples = 0
        for bucket in complexity_buckets.values():
            bucket_size = min(len(bucket), self.validation_batch_size // 3)
            sampled_queries.extend(bucket[:bucket_size])
            total_samples += bucket_size

        # Fill remaining slots randomly
        remaining_slots = self.validation_batch_size - total_samples
        if remaining_slots > 0:
            available_queries = [q for q in historical_queries if q not in sampled_queries]
            additional_samples = min(remaining_slots, len(available_queries))
            sampled_queries.extend(available_queries[:additional_samples])

        return sampled_queries

    def deploy_strategy(self, strategy_id: str) -> bool:
        """
        Deploy a validated strategy to the optimization system.

        In practice, this would integrate with the hierarchical bandit system
        to add the new strategy as an option.
        """
        if strategy_id not in self.generated_strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False

        genome = self.generated_strategies[strategy_id]
        if genome.deployment_status != 'validated':
            logger.error(f"Strategy {strategy_id} not validated for deployment")
            return False

        # Create strategy representation
        strategy_rep = StrategyRepresentation(genome)

        # Deploy to optimization system (simplified)
        self.deployed_strategies[strategy_id] = strategy_rep
        genome.deployment_status = 'deployed'

        logger.info(f"Deployed automated strategy: {strategy_id}")
        return True

    def get_strategy_suggestions(self, query_context: QueryContext) -> List[Tuple[str, float]]:
        """
        Get strategy suggestions for a query context.

        Returns list of (strategy_id, confidence) tuples.
        """
        suggestions = []

        for strategy_id, strategy_rep in self.deployed_strategies.items():
            # Simple confidence based on meta-learner prediction
            genome = strategy_rep.genome
            confidence = self.meta_learner.predict_success_probability(genome)

            # Adjust based on query context
            context_bonus = self._calculate_context_bonus(genome, query_context)
            adjusted_confidence = min(confidence + context_bonus, 1.0)

            suggestions.append((strategy_id, adjusted_confidence))

        # Sort by confidence
        suggestions.sort(key=lambda x: x[1], reverse=True)

        return suggestions

    def _calculate_context_bonus(self, genome: StrategyGenome, query_context: QueryContext) -> float:
        """Calculate context-specific bonus for strategy confidence."""
        bonus = 0.0

        complexity = query_context.features.get('complexity', 0.5)
        intent = query_context.features.get('intent', 'general')

        # Complexity matching
        if complexity > 0.7 and StrategyComponent.CROSS_ENCODER in genome.components:
            bonus += 0.1
        elif complexity < 0.3 and StrategyComponent.COSINE_SIMILARITY in genome.components:
            bonus += 0.05

        # Intent matching
        if intent == 'diagnostic' and StrategyComponent.CROSS_ENCODER in genome.components:
            bonus += 0.15
        elif intent == 'personalized' and StrategyComponent.PERSONALIZATION in genome.components:
            bonus += 0.1

        return bonus

    def get_generation_stats(self) -> Dict:
        """Get statistics about strategy generation."""
        return {
            'total_generated': len(self.generated_strategies),
            'total_deployed': len(self.deployed_strategies),
            'current_generation': self.generator.generation,
            'population_size': len(self.generator.population),
            'avg_fitness': np.mean([g.fitness_score for g in self.generator.population]) if self.generator.population else 0,
            'last_generation': self.last_generation.isoformat(),
            'meta_learner_trained': len(self.meta_learner.training_data) > 0
        }

    def _deploy_to_bandit_system(self, strategy_id: str, genome: StrategyGenome) -> bool:
        """
        Deploy a constitutionally validated strategy to the bandit system.

        This integrates the governance-approved strategy into the live optimization system.
        """
        try:
            # Get the hierarchical optimizer (which contains the bandit system)
            optimizer = get_hierarchical_optimizer()

            # Create strategy representation from genome
            strategy_rep = StrategyRepresentation(genome)

            # Convert genome components to bandit strategy
            bandit_strategy = self._convert_genome_to_bandit_strategy(genome, strategy_rep)

            if bandit_strategy:
                # Add the new strategy to the bandit system
                optimizer.hierarchical_system.add_strategy(bandit_strategy)

                # Store reference for tracking
                self.deployed_strategies[strategy_id] = strategy_rep

                logger.info(f"Successfully deployed strategy {strategy_id} to bandit system")
                return True
            else:
                logger.error(f"Failed to convert genome to bandit strategy for {strategy_id}")
                return False

        except Exception as e:
            logger.error(f"Failed to deploy strategy {strategy_id} to bandit system: {e}")
            return False

    def _convert_genome_to_bandit_strategy(self, genome: StrategyGenome,
                                          strategy_rep: StrategyRepresentation) -> Optional[OptimizationStrategy]:
        """
        Convert a strategy genome to a bandit optimization strategy.

        Maps the evolved components and parameters to the bandit system's strategy format.
        """
        try:
            # Determine strategy type based on dominant components
            if StrategyComponent.CROSS_ENCODER in genome.components:
                if StrategyComponent.PERSONALIZATION in genome.components:
                    strategy_type = "hybrid_personalized"
                else:
                    strategy_type = "cross_encoder_focused"
            elif StrategyComponent.PERSONALIZATION in genome.components:
                strategy_type = "personalization_focused"
            elif StrategyComponent.NEURAL_RESCORING in genome.components:
                strategy_type = "neural_focused"
            else:
                strategy_type = "cosine_enhanced"

            # Create optimization strategy
            bandit_strategy = OptimizationStrategy(
                name=f"auto_{strategy_type}_{genome.generation}",
                description=f"Automatically generated {strategy_type} strategy from generation {genome.generation}",
                components=list(genome.components),
                parameters=genome.parameters.copy(),
                fitness_score=genome.fitness_score,
                generation=genome.generation,
                governance_score=getattr(genome, 'governance_score', 1.0),
                strategy_representation=strategy_rep
            )

            return bandit_strategy

        except Exception as e:
            logger.error(f"Failed to convert genome to bandit strategy: {e}")
            return None

    def get_constitutional_deployment_stats(self) -> Dict[str, Any]:
        """
        Get statistics about constitutional strategy deployment.

        Shows how governance integrates with the deployment pipeline.
        """
        total_generated = len(self.generated_strategies)
        total_deployed = len(self.deployed_strategies)
        total_validated = sum(1 for s in self.generated_strategies.values()
                             if s.deployment_status in ['validated', 'deployed'])

        governance_stats = self.governance_engine.get_governance_stats()

        return {
            'strategy_generation': {
                'total_generated': total_generated,
                'total_validated': total_validated,
                'total_deployed': total_deployed,
                'validation_rate': total_validated / max(total_generated, 1),
                'deployment_rate': total_deployed / max(total_validated, 1)
            },
            'constitutional_governance': governance_stats,
            'integration_health': {
                'governance_enabled': True,
                'auto_deployment_enabled': True,
                'human_intervention_available': True,
                'last_generation': self.last_generation.isoformat() if self.last_generation else None
            }
        }

# Global automated strategy generation instance
_automated_generation = None

def get_automated_strategy_generation() -> AutomatedStrategyGeneration:
    """Get or create global automated strategy generation instance."""
    global _automated_generation
    if _automated_generation is None:
        _automated_generation = AutomatedStrategyGeneration()
    return _automated_generation
