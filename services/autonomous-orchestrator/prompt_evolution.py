"""
Prompt Evolution via Genetic Algorithm
Automatically optimize prompts based on response quality
"""
import random
import asyncio
import time
from typing import List, Dict, Tuple
import httpx
import logging

logger = logging.getLogger(__name__)

class PromptEvolver:
    def __init__(self, 
                 population_size: int = 10,
                 mutation_rate: float = 0.3,
                 generations: int = 5):
        self.population_size = population_size
        self.mutation_rate = mutation_rate
        self.generations = generations
        self.llm_endpoint = "http://localhost:8080/v1/chat/completions"
        logger.info(f"🧬 PromptEvolver initialized (pop={population_size}, gens={generations})")
    
    async def fitness_function(self, prompt: str, test_cases: List[Dict]) -> float:
        """
        Evaluate prompt quality
        Returns: Score 0-1 (higher is better)
        """
        scores = []
        
        for test_case in test_cases:
            query = test_case["query"]
            expected = test_case.get("expected_keywords", [])
            
            try:
                # Get response with this prompt
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(
                        self.llm_endpoint,
                        json={
                            "messages": [
                                {"role": "system", "content": prompt},
                                {"role": "user", "content": query}
                            ],
                            "max_tokens": 200
                        }
                    )
                
                if response.status_code == 200:
                    answer = response.json()["choices"][0]["message"]["content"]
                    
                    # Score based on expected keywords
                    keyword_matches = sum(1 for kw in expected if kw.lower() in answer.lower())
                    score = keyword_matches / max(len(expected), 1)
                    
                    # Bonus for brevity
                    if len(answer) < 500:
                        score += 0.1
                    
                    # Penalty for excessive length
                    if len(answer) > 1000:
                        score -= 0.1
                    
                    scores.append(max(0.0, min(score, 1.0)))
                else:
                    scores.append(0.0)
                    
            except Exception as e:
                logger.warning(f"Fitness evaluation failed: {e}")
                scores.append(0.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        return avg_score
    
    def mutate(self, prompt: str) -> str:
        """
        Mutate a prompt (genetic variation)
        """
        mutations = [
            lambda p: p.replace("Please", "Kindly"),
            lambda p: p.replace("explain", "describe in detail"),
            lambda p: p + " Be concise.",
            lambda p: p + " Cite sources when possible.",
            lambda p: p.replace("You are", "Act as"),
            lambda p: f"{p}\n\nFormat: Answer in 2-3 sentences.",
            lambda p: p.replace("assistant", "expert"),
            lambda p: p + " Use technical terminology.",
            lambda p: p + " Explain like I'm 5.",
            lambda p: p.replace("helpful", "exceptionally helpful and precise"),
        ]
        
        if random.random() < self.mutation_rate:
            mutation = random.choice(mutations)
            try:
                mutated = mutation(prompt)
                return mutated
            except:
                return prompt
        return prompt
    
    def crossover(self, prompt1: str, prompt2: str) -> str:
        """
        Combine two prompts (genetic recombination)
        """
        sentences1 = [s.strip() for s in prompt1.split(". ") if s.strip()]
        sentences2 = [s.strip() for s in prompt2.split(". ") if s.strip()]
        
        if not sentences1 or not sentences2:
            return prompt1
        
        # Take half from each
        mid1 = len(sentences1) // 2
        mid2 = len(sentences2) // 2
        
        child_sentences = sentences1[:mid1] + sentences2[mid2:]
        child = ". ".join(child_sentences)
        
        if not child.endswith('.'):
            child += "."
        
        return child
    
    async def evolve(self, 
                     initial_prompt: str,
                     test_cases: List[Dict]) -> Tuple[str, float]:
        """
        Evolve prompt over multiple generations
        
        Returns: (best_prompt, best_score)
        """
        logger.info(f"🧬 Starting prompt evolution ({self.generations} generations, {len(test_cases)} test cases)")
        
        # Initialize population
        population = [initial_prompt]
        for i in range(self.population_size - 1):
            mutated = self.mutate(initial_prompt)
            population.append(mutated)
            logger.debug(f"  Initial variant {i+1}: {mutated[:50]}...")
        
        best_prompt = initial_prompt
        best_score = 0.0
        
        for gen in range(self.generations):
            logger.info(f"📊 Generation {gen+1}/{self.generations}")
            
            # Evaluate all prompts
            fitness_scores = []
            for idx, prompt in enumerate(population):
                score = await self.fitness_function(prompt, test_cases)
                fitness_scores.append((prompt, score))
                logger.debug(f"  Prompt {idx+1}: score={score:.2%}")
            
            # Sort by fitness
            fitness_scores.sort(key=lambda x: x[1], reverse=True)
            
            # Track best
            if fitness_scores[0][1] > best_score:
                best_prompt = fitness_scores[0][0]
                best_score = fitness_scores[0][1]
                logger.info(f"✨ New best prompt (score: {best_score:.2%})")
                logger.info(f"   {best_prompt[:100]}...")
            
            # Selection: keep top 50%
            survivors = [p for p, s in fitness_scores[:self.population_size//2]]
            
            # Generate next generation
            new_population = survivors.copy()
            
            while len(new_population) < self.population_size:
                if random.random() < 0.5 and len(survivors) > 0:
                    # Mutation
                    parent = random.choice(survivors)
                    child = self.mutate(parent)
                elif len(survivors) >= 2:
                    # Crossover
                    parent1 = random.choice(survivors)
                    parent2 = random.choice(survivors)
                    child = self.crossover(parent1, parent2)
                else:
                    # Fallback to mutation
                    child = self.mutate(survivors[0] if survivors else initial_prompt)
                
                new_population.append(child)
            
            population = new_population
        
        logger.info(f"🏆 Evolution complete! Best score: {best_score:.2%}")
        logger.info(f"   Best prompt: {best_prompt}")
        
        return best_prompt, best_score

