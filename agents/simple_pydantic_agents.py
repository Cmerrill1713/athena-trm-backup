#!/usr/bin/env python3
"""
Simple Pydantic AI Agents - Real Functional Agents from Prompts!
================================================================
Shows how trivially easy it is to create powerful agents with just prompts
"""

import sys
from pathlib import Path

# Add pydantic-ai to path
pydantic_ai_path = Path(__file__).parent.parent / "pydantic-ai" / "pydantic_ai_slim"
sys.path.insert(0, str(pydantic_ai_path))

from pydantic import BaseModel
from pydantic_ai import Agent
from typing import List

# ============================================================================
# 1. CODE GENERATION AGENT (from research papers)
# ============================================================================

class GeneratedCode(BaseModel):
    """Complete code implementation"""
    code: str
    tests: str
    readme: str

code_agent = Agent(
    model='ollama:qwen2.5-coder',  # Your local model!
    output_type=GeneratedCode,
    instructions="""
    You are an expert code generator. When given a research paper algorithm,
    generate production-ready Python code with:
    - Clean implementation with type hints
    - Comprehensive tests
    - README with usage examples
    
    Always follow best practices and PEP 8.
    """
)

# ============================================================================
# 2. PAPER ANALYZER AGENT  
# ============================================================================

class PaperAnalysis(BaseModel):
    """Analysis of a research paper"""
    algorithms: List[str]
    complexity: str  # "simple", "medium", "complex"
    key_insight: str
    implementation_steps: List[str]
    dependencies: List[str]

analyzer_agent = Agent(
    model='ollama:qwen2.5-coder',
    output_type=PaperAnalysis,
    instructions="""
    You are a research paper analyst. Extract:
    - Core algorithms described
    - Implementation complexity  
    - Key insights
    - Step-by-step implementation plan
    - Required dependencies
    
    Be concise but thorough.
    """
)

# ============================================================================
# 3. TEST GENERATOR AGENT
# ============================================================================

class TestSuite(BaseModel):
    """Generated test suite"""
    test_code: str
    test_count: int
    coverage_areas: List[str]

test_agent = Agent(
    model='ollama:qwen2.5-coder',
    output_type=TestSuite,
    instructions="""
    You are a test generation specialist. Given code, generate:
    - Comprehensive pytest test suite
    - Unit tests for all functions
    - Edge case tests
    - Integration tests if applicable
    
    Aim for 90%+ code coverage.
    """
)

# ============================================================================
# 4. RESEARCH HUNTER AGENT
# ============================================================================

class PaperRecommendation(BaseModel):
    """Research paper recommendation"""
    title: str
    relevance_score: float
    reason: str
    should_implement: bool

hunter_agent = Agent(
    model='ollama:qwen2.5-coder',
    output_type=List[PaperRecommendation],
    instructions="""
    You are a research paper evaluator. Given paper titles and abstracts,
    score their relevance to autonomous AI systems, multi-armed bandits,
    and self-improving agents.
    
    Focus on:
    - Novel algorithms that can be implemented
    - Papers with practical applications
    - Techniques that enhance existing systems
    """
)

# ============================================================================
# USAGE EXAMPLE
# ============================================================================

async def implement_paper_with_pydantic_ai(paper_abstract: str):
    """Complete pipeline using Pydantic AI agents"""
    
    print("📊 Step 1: Analyzing paper...")
    analysis = await analyzer_agent.run(paper_abstract)
    print(f"✅ Found {len(analysis.output.algorithms)} algorithms")
    print(f"   Complexity: {analysis.output.complexity}")
    print(f"   Key Insight: {analysis.output.key_insight}")
    
    print("\n💻 Step 2: Generating implementation...")
    impl_prompt = f"""
    Implement this research paper:
    
    Algorithms: {', '.join(analysis.output.algorithms)}
    Steps: {chr(10).join(f'{i}. {s}' for i, s in enumerate(analysis.output.implementation_steps, 1))}
    Dependencies: {', '.join(analysis.output.dependencies)}
    
    Generate clean, production-ready code.
    """
    
    code_result = await code_agent.run(impl_prompt)
    print(f"✅ Generated {len(code_result.output.code)} chars of code")
    
    print("\n🧪 Step 3: Generating tests...")
    test_result = await test_agent.run(f"Generate tests for:\n\n{code_result.output.code}")
    print(f"✅ Generated {test_result.output.test_count} tests")
    
    return {
        "analysis": analysis.output,
        "code": code_result.output,
        "tests": test_result.output
    }


if __name__ == "__main__":
    
    print("=" * 80)
    print("🤖 PYDANTIC AI AGENTS - SIMPLE & POWERFUL")
    print("=" * 80)
    
    print("\n✅ Created 4 Functional Agents:")
    print("   1. Code Generation Agent")
    print("   2. Paper Analyzer Agent")
    print("   3. Test Generator Agent")
    print("   4. Research Hunter Agent")
    
    print("\n💡 Each agent is just:")
    print("   - A prompt (instructions)")
    print("   - An output type (Pydantic model)")
    print("   - A model (ollama:qwen2.5-coder)")
    
    print("\n🚀 To use:")
    print("   result = await code_agent.run('Implement Thompson Sampling')")
    print("   print(result.output.code)")
    
    print("\n" + "=" * 80)
    print("📄 EXAMPLE: Implementing a Paper")
    print("=" * 80)
    
    example_paper = """
    Title: Improved Thompson Sampling for Contextual Bandits
    
    Abstract: We enhance Thompson Sampling by incorporating context features.
    Instead of maintaining fixed Beta distributions, we use a small neural network
    to adjust the distributions based on context (task type, time, user).
    
    Algorithm:
    1. Initialize Beta(1, 1) for each arm
    2. Train NN on (context, arm, reward) history
    3. On decision: context → NN → adjusted Beta params
    4. Sample from adjusted Betas, pick max
    5. Update NN and Beta distributions with observed reward
    
    Result: 15% better regret bounds vs standard Thompson Sampling.
    """
    
    print("\n🔄 Running complete implementation pipeline...")
    print("(This would call your local LLM to generate real code)\n")
    
    # Note: Actual execution requires ollama running with qwen2.5-coder
    print("💡 To run for real:")
    print("   1. Start ollama: ollama serve")
    print("   2. Pull model: ollama pull qwen2.5-coder")
    print("   3. Run: python3 agents/simple_pydantic_agents.py")
    
    print("\n✨ The beauty of Pydantic AI:")
    print("   - No complex infrastructure needed")
    print("   - Just prompts + output types")
    print("   - Automatic validation")
    print("   - Structured outputs guaranteed")
    
    print("\n" + "=" * 80)

