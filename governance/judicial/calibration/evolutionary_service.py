#!/usr/bin/env python3
"""
Athena Evolutionary Service
Genetic algorithms, optimization, and adaptive learning
"""
import json
import os
import random
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import psycopg2
import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import redis

app = FastAPI(title="Athena Evolutionary Service", version="1.0.0")

# Redis connection
redis_client = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379"))

class OptimizationRequest(BaseModel):
    objective: str  # "maximize", "minimize"
    parameters: Dict[str, Dict[str, float]]  # param_name: {min, max, current}
    population_size: int = 50
    generations: int = 100
    mutation_rate: float = 0.1
    crossover_rate: float = 0.8
    target_metric: str  # What metric to optimize

class OptimizationResponse(BaseModel):
    best_solution: Dict[str, float]
    fitness_score: float
    generation: int
    convergence_data: List[Dict[str, Any]]
    optimization_time_ms: float

class EvolutionRequest(BaseModel):
    system_component: str  # "routing", "prompt_optimization", "model_selection"
    performance_data: List[Dict[str, Any]]
    constraints: Optional[Dict[str, Any]] = None

class EvolutionResponse(BaseModel):
    recommendations: List[Dict[str, Any]]
    confidence_score: float
    evolution_stage: str
    next_actions: List[str]

class Individual:
    def __init__(self, parameters: Dict[str, float]):
        self.parameters = parameters
        self.fitness = 0.0

    def mutate(self, mutation_rate: float, bounds: Dict[str, Tuple[float, float]]):
        """Apply mutation to parameters"""
        for param, value in self.parameters.items():
            if random.random() < mutation_rate:
                min_val, max_val = bounds[param]
                # Gaussian mutation
                noise = np.random.normal(0, (max_val - min_val) * 0.1)
                new_value = value + noise
                self.parameters[param] = max(min_val, min(max_val, new_value))

    def crossover(self, other: 'Individual', crossover_rate: float) -> Tuple['Individual', 'Individual']:
        """Create two offspring through crossover"""
        if random.random() > crossover_rate:
            return Individual(self.parameters.copy()), Individual(other.parameters.copy())

        child1_params = {}
        child2_params = {}

        for param in self.parameters:
            if random.random() < 0.5:
                child1_params[param] = self.parameters[param]
                child2_params[param] = other.parameters[param]
            else:
                child1_params[param] = other.parameters[param]
                child2_params[param] = self.parameters[param]

        return Individual(child1_params), Individual(child2_params)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        redis_client.ping()
        conn = psycopg2.connect(os.getenv("POSTGRES_URL", "postgresql://localhost/athena"))
        conn.close()
        return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@app.post("/optimize", response_model=OptimizationResponse)
async def optimize_parameters(request: OptimizationRequest):
    """Run genetic algorithm optimization"""
    start_time = datetime.utcnow()

    try:
        # Extract parameter bounds
        bounds = {}
        for param, config in request.parameters.items():
            bounds[param] = (config["min"], config["max"])

        # Initialize population
        population = []
        for _ in range(request.population_size):
            params = {}
            for param, config in request.parameters.items():
                params[param] = random.uniform(config["min"], config["max"])
            population.append(Individual(params))

        # Evolution loop
        convergence_data = []
        best_individual = None

        for generation in range(request.generations):
            # Evaluate fitness (simplified - in production, this would call actual system)
            for individual in population:
                individual.fitness = evaluate_fitness(individual, request.target_metric)

            # Sort by fitness
            population.sort(key=lambda x: x.fitness, reverse=(request.objective == "maximize"))

            # Track best
            if best_individual is None or (
                (request.objective == "maximize" and population[0].fitness > best_individual.fitness) or
                (request.objective == "minimize" and population[0].fitness < best_individual.fitness)
            ):
                best_individual = population[0]

            # Record convergence data
            convergence_data.append({
                "generation": generation,
                "best_fitness": best_individual.fitness,
                "avg_fitness": sum(ind.fitness for ind in population) / len(population),
                "best_parameters": best_individual.parameters.copy()
            })

            # Create next generation
            new_population = []

            # Keep top 20% (elitism)
            elite_size = max(1, int(request.population_size * 0.2))
            new_population.extend(population[:elite_size])

            # Generate offspring
            while len(new_population) < request.population_size:
                parent1 = tournament_selection(population)
                parent2 = tournament_selection(population)
                child1, child2 = parent1.crossover(parent2, request.crossover_rate)
                child1.mutate(request.mutation_rate, bounds)
                child2.mutate(request.mutation_rate, bounds)
                new_population.extend([child1, child2])

            population = new_population[:request.population_size]

        optimization_time = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Store optimization results
        optimization_key = f"optimization:{request.target_metric}:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        redis_client.setex(
            optimization_key,
            86400,  # 24 hours
            json.dumps({
                "best_solution": best_individual.parameters,
                "fitness_score": best_individual.fitness,
                "convergence_data": convergence_data
            })
        )

        return OptimizationResponse(
            best_solution=best_individual.parameters,
            fitness_score=best_individual.fitness,
            generation=request.generations,
            convergence_data=convergence_data,
            optimization_time_ms=round(optimization_time, 2)
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")

@app.post("/evolve", response_model=EvolutionResponse)
async def evolve_system(request: EvolutionRequest):
    """Evolve system based on performance data"""
    try:
        recommendations = []
        confidence_score = 0.0
        evolution_stage = "analysis"
        next_actions = []

        if request.system_component == "routing":
            recommendations, confidence_score, evolution_stage, next_actions = evolve_routing(request.performance_data)
        elif request.system_component == "prompt_optimization":
            recommendations, confidence_score, evolution_stage, next_actions = evolve_prompts(request.performance_data)
        elif request.system_component == "model_selection":
            recommendations, confidence_score, evolution_stage, next_actions = evolve_models(request.performance_data)
        else:
            raise HTTPException(status_code=400, detail="Unknown system component")

        # Store evolution results
        evolution_key = f"evolution:{request.system_component}:{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        redis_client.setex(
            evolution_key,
            86400,
            json.dumps({
                "recommendations": recommendations,
                "confidence_score": confidence_score,
                "evolution_stage": evolution_stage,
                "performance_data": request.performance_data
            })
        )

        return EvolutionResponse(
            recommendations=recommendations,
            confidence_score=confidence_score,
            evolution_stage=evolution_stage,
            next_actions=next_actions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Evolution failed: {str(e)}")

def evaluate_fitness(individual: Individual, target_metric: str) -> float:
    """Evaluate fitness of an individual (simplified)"""
    # In production, this would call the actual system with these parameters
    # and measure the target metric (latency, accuracy, etc.)

    # Simplified fitness function
    fitness = 0.0
    for param, value in individual.parameters.items():
        # Example: optimize for values closer to 0.5 (normalized)
        fitness += 1.0 - abs(value - 0.5)

    return fitness / len(individual.parameters)

def tournament_selection(population: List[Individual], tournament_size: int = 3) -> Individual:
    """Select individual using tournament selection"""
    tournament = random.sample(population, min(tournament_size, len(population)))
    return max(tournament, key=lambda x: x.fitness)

def evolve_routing(performance_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float, str, List[str]]:
    """Evolve routing system based on performance"""
    recommendations = []
    confidence_score = 0.8
    evolution_stage = "optimization"
    next_actions = ["update_routing_weights", "test_new_routes", "monitor_performance"]

    # Analyze routing performance
    route_performance = {}
    for data_point in performance_data:
        route = data_point.get("route", "unknown")
        success = data_point.get("success", False)
        latency = data_point.get("latency_ms", 0)

        if route not in route_performance:
            route_performance[route] = {"successes": 0, "total": 0, "latencies": []}

        route_performance[route]["total"] += 1
        if success:
            route_performance[route]["successes"] += 1
        route_performance[route]["latencies"].append(latency)

    # Generate recommendations
    for route, stats in route_performance.items():
        success_rate = stats["successes"] / stats["total"] if stats["total"] > 0 else 0
        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0

        if success_rate < 0.8:
            recommendations.append({
                "type": "route_optimization",
                "route": route,
                "issue": "low_success_rate",
                "current_rate": success_rate,
                "suggestion": "increase_timeout_or_fallback"
            })

        if avg_latency > 1000:  # 1 second
            recommendations.append({
                "type": "performance_optimization",
                "route": route,
                "issue": "high_latency",
                "current_latency": avg_latency,
                "suggestion": "optimize_backend_or_caching"
            })

    return recommendations, confidence_score, evolution_stage, next_actions

def evolve_prompts(performance_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float, str, List[str]]:
    """Evolve prompt optimization based on performance"""
    recommendations = []
    confidence_score = 0.7
    evolution_stage = "refinement"
    next_actions = ["update_prompt_templates", "test_new_prompts", "measure_improvement"]

    # Analyze prompt performance
    prompt_scores = {}
    for data_point in performance_data:
        prompt_type = data_point.get("prompt_type", "unknown")
        quality_score = data_point.get("quality_score", 0)

        if prompt_type not in prompt_scores:
            prompt_scores[prompt_type] = []
        prompt_scores[prompt_type].append(quality_score)

    # Generate recommendations
    for prompt_type, scores in prompt_scores.items():
        avg_score = sum(scores) / len(scores) if scores else 0

        if avg_score < 0.7:
            recommendations.append({
                "type": "prompt_improvement",
                "prompt_type": prompt_type,
                "current_score": avg_score,
                "suggestion": "add_specificity_or_examples",
                "priority": "high" if avg_score < 0.5 else "medium"
            })

    return recommendations, confidence_score, evolution_stage, next_actions

def evolve_models(performance_data: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], float, str, List[str]]:
    """Evolve model selection based on performance"""
    recommendations = []
    confidence_score = 0.9
    evolution_stage = "selection"
    next_actions = ["update_model_weights", "test_new_models", "validate_selection"]

    # Analyze model performance
    model_performance = {}
    for data_point in performance_data:
        model = data_point.get("model", "unknown")
        accuracy = data_point.get("accuracy", 0)
        latency = data_point.get("latency_ms", 0)

        if model not in model_performance:
            model_performance[model] = {"accuracies": [], "latencies": []}

        model_performance[model]["accuracies"].append(accuracy)
        model_performance[model]["latencies"].append(latency)

    # Generate recommendations
    best_model = None
    best_score = -1

    for model, stats in model_performance.items():
        avg_accuracy = sum(stats["accuracies"]) / len(stats["accuracies"]) if stats["accuracies"] else 0
        avg_latency = sum(stats["latencies"]) / len(stats["latencies"]) if stats["latencies"] else 0

        # Combined score (accuracy - normalized latency)
        score = avg_accuracy - (avg_latency / 10000)  # Normalize latency

        if score > best_score:
            best_score = score
            best_model = model

    if best_model:
        recommendations.append({
            "type": "model_selection",
            "recommended_model": best_model,
            "score": best_score,
            "suggestion": "increase_usage_weight",
            "reasoning": "highest_accuracy_latency_balance"
        })

    return recommendations, confidence_score, evolution_stage, next_actions

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    try:
        # Count stored optimizations and evolutions
        optimization_count = len(redis_client.keys("optimization:*"))
        evolution_count = len(redis_client.keys("evolution:*"))

        metrics_data = f"""# HELP athena_evolutionary_optimizations_total Total optimization runs
# TYPE athena_evolutionary_optimizations_total counter
athena_evolutionary_optimizations_total {optimization_count}

# HELP athena_evolutionary_evolutions_total Total evolution runs
# TYPE athena_evolutionary_evolutions_total counter
athena_evolutionary_evolutions_total {evolution_count}
"""
        return {"content": metrics_data, "content_type": "text/plain"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate metrics: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8034)
