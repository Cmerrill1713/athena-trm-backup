#!/usr/bin/env python3
"""
Research Implementation Agent - Uses Pydantic AI to actually implement papers!
==============================================================================
Creates a functional agent that can read research paper descriptions and
generate working Python code implementations
"""

import sys
from pathlib import Path
from typing import List
from pydantic import BaseModel

# Add pydantic-ai to path
pydantic_ai_path = Path(__file__).parent.parent / "pydantic-ai" / "pydantic_ai_slim"
sys.path.insert(0, str(pydantic_ai_path))

from pydantic_ai import Agent

# Output model for code generation
class CodeImplementation(BaseModel):
    """Generated code implementation from research paper"""
    filename: str
    code: str
    docstring: str
    test_code: str
    dependencies: List[str]
    complexity_score: float  # 0.0-1.0

# Create the research implementation agent
research_code_agent = Agent(
    model='ollama:qwen2.5-coder',  # Use your local model
    output_type=CodeImplementation,
    instructions="""
    You are a Research Implementation Specialist. Your job is to read research
    paper descriptions and generate clean, production-ready Python implementations.
    
    When given a research paper concept, you should:
    
    1. **Understand the Algorithm**: Extract the key algorithmic steps
    2. **Generate Clean Code**: Write well-structured, typed Python code
    3. **Add Documentation**: Include comprehensive docstrings
    4. **Create Tests**: Generate pytest tests for validation
    5. **List Dependencies**: Specify all required packages
    
    **Code Quality Standards**:
    - Use type hints everywhere
    - Add docstrings (Google style)
    - Include error handling
    - Make code modular and testable
    - Follow PEP 8 style
    - Keep functions focused and small
    
    **Example Output Structure**:
    ```python
    from typing import Dict, List, Optional
    import numpy as np
    
    class ThompsonSampler:
        '''Thompson Sampling for Multi-Armed Bandits
        
        Implements the Thompson Sampling algorithm using Beta distributions
        for exploration-exploitation balance in multi-armed bandit problems.
        
        Args:
            n_arms: Number of arms/options to choose from
            alpha_prior: Prior successes for Beta distribution
            beta_prior: Prior failures for Beta distribution
        '''
        
        def __init__(self, n_arms: int, alpha_prior: float = 1.0, beta_prior: float = 1.0):
            self.n_arms = n_arms
            self.alpha = np.full(n_arms, alpha_prior)
            self.beta = np.full(n_arms, beta_prior)
        
        def select_arm(self) -> int:
            '''Select arm by sampling from Beta distributions'''
            samples = np.random.beta(self.alpha, self.beta)
            return int(np.argmax(samples))
        
        def update(self, arm: int, reward: float):
            '''Update distribution for selected arm'''
            if reward > 0:
                self.alpha[arm] += reward
            else:
                self.beta[arm] += abs(reward)
    ```
    
    Return your implementation in the CodeImplementation format.
    """,
    retries=2
)

# Helper function to run the agent
async def implement_from_paper(paper_description: str) -> CodeImplementation:
    """
    Generate code implementation from research paper description
    
    Args:
        paper_description: Description of the paper and its algorithms
        
    Returns:
        Code implementation with tests
    """
    result = await research_code_agent.run(paper_description)
    return result.output


# Demo usage
if __name__ == "__main__":
    import asyncio
    
    paper = """
    Paper: Contextual Thompson Sampling with Neural Network Function Approximation
    
    Algorithm Description:
    Traditional Thompson Sampling maintains separate Beta distributions for each arm
    (wins, losses). This paper extends it to be context-aware by using a small neural
    network to predict reward distributions based on context features.
    
    Key Steps:
    1. Maintain Beta(alpha, beta) distributions for each arm
    2. Train a small NN on (context, arm, reward) tuples  
    3. At decision time: NN adjusts Beta parameters based on current context
    4. Sample from adjusted Beta distributions
    5. Select arm with highest sample
    6. Observe reward and update both NN and Beta distributions
    
    Context features might include:
    - Task type (code, chat, reasoning)
    - Time of day
    - User history
    - Recent performance
    
    Target: Integrate with existing Thompson Sampling in orchestrator/scorer.py
    Dependencies: numpy, scipy, torch (for NN)
    
    Generate a complete, working implementation.
    """
    
    print("🔬 Generating implementation from research paper...")
    print("=" * 80)
    
    result = asyncio.run(implement_from_paper(paper))
    
    print("\n✅ IMPLEMENTATION GENERATED!\n")
    print(f"Filename: {result.filename}")
    print(f"Complexity: {result.complexity_score:.2f}")
    print(f"Dependencies: {', '.join(result.dependencies)}")
    print(f"\nDocumentation:\n{result.docstring}\n")
    print("=" * 80)
    print("GENERATED CODE:")
    print("=" * 80)
    print(result.code)
    print("\n" + "=" * 80)
    print("GENERATED TESTS:")
    print("=" * 80)
    print(result.test_code)
    print("\n" + "=" * 80)
    
    # Save to file
    output_dir = Path(__file__).parent.parent / "orchestrator" / "providers"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    code_file = output_dir / result.filename
    with open(code_file, 'w') as f:
        f.write(result.code)
    
    test_file = output_dir.parent / "tests" / f"test_{result.filename}"
    test_file.parent.mkdir(parents=True, exist_ok=True)
    with open(test_file, 'w') as f:
        f.write(result.test_code)
    
    print(f"💾 Saved implementation to: {code_file}")
    print(f"💾 Saved tests to: {test_file}")
    print("\n🎉 Research paper successfully implemented!")

