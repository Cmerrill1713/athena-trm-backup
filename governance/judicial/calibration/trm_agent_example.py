#!/usr/bin/env python3
"""PydanticAI + TRM Integration Example

This example shows how to use TRM as a reasoning tool within PydanticAI agents.
"""

import sys
from pathlib import Path
from typing import Optional

import torch
from pydantic import BaseModel

from pydantic_ai import Agent, RunContext

# Add TRM to path
TRM_PATH = Path(__file__).parent.parent.parent / 'TinyRecursiveModels'
sys.path.insert(0, str(TRM_PATH))

try:
    from models.recursive_reasoning.trm import TinyRecursiveReasoningModel_ACTV1
    TRM_AVAILABLE = True
except ImportError:
    print('Warning: TRM not available')
    TRM_AVAILABLE = False


class TRMReasoningTool:
    """TRM as a PydanticAI tool."""
    
    def __init__(self, checkpoint_path: Optional[str] = None):
        """Initialize TRM tool."""
        if not TRM_AVAILABLE:
            raise RuntimeError('TRM not available')
        
        # Determine device
        if torch.cuda.is_available():
            self.device = torch.device('cuda')
        elif torch.backends.mps.is_available():
            self.device = torch.device('mps')
        else:
            self.device = torch.device('cpu')
        
        # TRM config
        config = {
            'batch_size': 1,
            'seq_len': 512,
            'vocab_size': 50000,
            'num_puzzle_identifiers': 1000,
            'hidden_size': 512,
            'expansion': 4,
            'num_heads': 8,
            'H_cycles': 3,
            'L_cycles': 6,
            'L_layers': 2,
            'H_layers': 0,
            'pos_encodings': 'rope',
            'halt_max_steps': 16,
            'halt_exploration_prob': 0.0,
            'puzzle_emb_ndim': 512,
            'mlp_t': False,
            'puzzle_emb_len': 16,
            'no_ACT_continue': True,
        }
        
        # Initialize model
        self.model = TinyRecursiveReasoningModel_ACTV1(config)
        
        if checkpoint_path:
            state_dict = torch.load(checkpoint_path, map_location=self.device)
            self.model.load_state_dict(state_dict)
        
        self.model.to(self.device)
        self.model.eval()
        
        print(f'✓ TRM initialized on {self.device}')
    
    def recursive_reason(self, query: str, max_steps: int = 16) -> str:
        """Apply recursive reasoning to a query.
        
        This allows iterative refinement through multiple reasoning cycles.
        
        Args:
            query: Input query
            max_steps: Maximum reasoning steps
            
        Returns:
            Refined output after recursive reasoning
        """
        # Tokenize (placeholder - use proper tokenizer)
        tokens = self._tokenize(query)
        
        # Prepare batch
        batch = {
            'inputs': torch.tensor([tokens], device=self.device),
            'puzzle_identifiers': torch.tensor([0], device=self.device),
        }
        
        # Run TRM
        with torch.no_grad():
            carry = self.model.initial_carry(batch)
            
            steps = 0
            for _ in range(max_steps):
                carry, outputs = self.model(carry, batch)
                steps += 1
                
                if carry.halted.all():
                    break
        
        # Decode (placeholder - use proper detokenizer)
        result = self._detokenize(outputs['logits'])
        
        return f'[TRM: {steps} steps] {result}'
    
    def _tokenize(self, text: str):
        """Placeholder tokenization."""
        # In production, use proper tokenizer
        return [hash(word) % 50000 for word in text.split()][:512]
    
    def _detokenize(self, logits):
        """Placeholder detokenization."""
        # In production, use proper detokenizer
        return 'Reasoning complete (placeholder output)'


# Example 1: Simple Agent with TRM
class SimpleResponse(BaseModel):
    answer: str
    reasoning_steps: int


def create_simple_trm_agent(checkpoint_path: Optional[str] = None):
    """Create a simple agent with TRM reasoning."""
    # Initialize TRM tool
    if TRM_AVAILABLE:
        trm_tool = TRMReasoningTool(checkpoint_path)
    else:
        trm_tool = None
    
    # Create agent
    agent = Agent(
        'openai:gpt-4o-mini',
        result_type=SimpleResponse,
        system_prompt="""You are a helpful assistant with recursive reasoning capabilities.
        Use the recursive_reason tool for complex problems that benefit from iterative refinement.""",
    )
    
    # Register TRM as a tool
    if trm_tool:
        @agent.tool
        def recursive_reason(ctx: RunContext[None], query: str) -> str:
            """Use recursive reasoning for complex problems.
            
            This tool applies iterative refinement through multiple reasoning cycles,
            improving the quality of answers for complex queries.
            """
            return trm_tool.recursive_reason(query)
    
    return agent


# Example 2: Code Generation Agent with TRM
class CodeGenerationResult(BaseModel):
    code: str
    explanation: str
    test_cases: list[str]
    reasoning_steps: int


def create_code_generation_agent(checkpoint_path: Optional[str] = None):
    """Create a code generation agent with TRM."""
    if TRM_AVAILABLE:
        trm_tool = TRMReasoningTool(checkpoint_path)
    else:
        trm_tool = None
    
    agent = Agent(
        'openai:gpt-4o-mini',
        result_type=CodeGenerationResult,
        system_prompt="""You are an expert code generation assistant.
        
        For complex algorithms or data structures:
        1. Use recursive_reason to plan the implementation
        2. Generate clean, well-commented code
        3. Provide test cases
        
        The recursive reasoning tool helps with:
        - Breaking down complex problems
        - Ensuring correctness through iterative refinement
        - Generating robust solutions""",
    )
    
    if trm_tool:
        @agent.tool
        def recursive_reason(ctx: RunContext[None], problem: str) -> str:
            """Apply recursive reasoning to plan code implementation."""
            return trm_tool.recursive_reason(problem)
    
    return agent


# Example 3: Multi-Step Task Agent with TRM
class TaskPlan(BaseModel):
    steps: list[str]
    dependencies: dict[str, list[str]]
    estimated_time: str


class TaskResult(BaseModel):
    plan: TaskPlan
    execution_order: list[str]
    reasoning_iterations: int


def create_task_planning_agent(checkpoint_path: Optional[str] = None):
    """Create a task planning agent with TRM."""
    if TRM_AVAILABLE:
        trm_tool = TRMReasoningTool(checkpoint_path)
    else:
        trm_tool = None
    
    agent = Agent(
        'openai:gpt-4o-mini',
        result_type=TaskResult,
        system_prompt="""You are a task planning assistant.
        
        For complex multi-step tasks:
        1. Use recursive_reason to break down the task
        2. Identify dependencies
        3. Create an execution order
        4. Estimate time requirements
        
        The recursive reasoning ensures complete and correct task decomposition.""",
    )
    
    if trm_tool:
        @agent.tool
        def recursive_reason(ctx: RunContext[None], task_description: str) -> str:
            """Recursively reason about task decomposition and dependencies."""
            return trm_tool.recursive_reason(task_description, max_steps=20)
    
    return agent


# Demo functions
def demo_simple_agent():
    """Demo the simple TRM agent."""
    print('\n' + '='*60)
    print('Demo 1: Simple Agent with TRM Reasoning')
    print('='*60)
    
    agent = create_simple_trm_agent()
    
    result = agent.run_sync(
        "Explain how to solve a Rubik's cube using recursive reasoning."
    )
    
    print(f'\nAnswer: {result.data.answer}')
    print(f'Reasoning Steps: {result.data.reasoning_steps}')


def demo_code_generation():
    """Demo the code generation agent."""
    print('\n' + '='*60)
    print('Demo 2: Code Generation with TRM')
    print('='*60)
    
    agent = create_code_generation_agent()
    
    result = agent.run_sync("""
    Generate a Python function to implement a binary search tree with:
    - Insert operation
    - Delete operation
    - In-order traversal
    
    Use recursive reasoning to ensure correctness.
    """)
    
    print(f'\nCode:\n{result.data.code}')
    print(f'\nExplanation: {result.data.explanation}')
    print(f'\nTest Cases: {result.data.test_cases}')
    print(f'\nReasoning Steps: {result.data.reasoning_steps}')


def demo_task_planning():
    """Demo the task planning agent."""
    print('\n' + '='*60)
    print('Demo 3: Task Planning with TRM')
    print('='*60)
    
    agent = create_task_planning_agent()
    
    result = agent.run_sync("""
    Plan a project to migrate a monolithic application to microservices.
    The application has:
    - User authentication
    - Payment processing
    - Inventory management
    - Order processing
    - Notification system
    """)
    
    print('\nPlan Steps:')
    for i, step in enumerate(result.data.plan.steps, 1):
        print(f'  {i}. {step}')
    
    print(f'\nExecution Order: {result.data.execution_order}')
    print(f'Estimated Time: {result.data.plan.estimated_time}')
    print(f'Reasoning Iterations: {result.data.reasoning_iterations}')


def main():
    """Main demo function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='PydanticAI + TRM Examples')
    parser.add_argument('--checkpoint', type=str, help='Path to TRM checkpoint')
    parser.add_argument('--demo', choices=['simple', 'code', 'task', 'all'], 
                       default='all', help='Which demo to run')
    
    args = parser.parse_args()
    
    if not TRM_AVAILABLE:
        print('Warning: TRM not available. Examples will use fallback mode.')
    
    print('PydanticAI + TRM Integration Examples')
    print('='*60)
    
    if args.demo in ['simple', 'all']:
        demo_simple_agent()
    
    if args.demo in ['code', 'all']:
        demo_code_generation()
    
    if args.demo in ['task', 'all']:
        demo_task_planning()
    
    print('\n' + '='*60)
    print('Demos complete!')


if __name__ == '__main__':
    main()

