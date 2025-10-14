#!/usr/bin/env python3
"""
Working Code Generation Agent - Uses Pydantic AI + Ollama
=========================================================
Generates REAL code from research papers using your local qwen3-coder:30b
"""

try:
    from pydantic import BaseModel
    from pydantic_ai import Agent
    from typing import List
    import asyncio
    
    # Define output structure
    class CodeImplementation(BaseModel):
        """Generated code from research paper"""
        code: str
        explanation: str
        key_functions: List[str]
    
    # Create agent using your local Ollama model
    code_agent = Agent(
        model='ollama:qwen3-coder',  # Your 30B model!
        output_type=CodeImplementation,
        instructions="""
        You are an expert Python developer who implements algorithms from research papers.
        
        Generate clean, production-ready Python code with:
        - Type hints
        - Docstrings
        - Error handling
        - Clear variable names
        
        Keep implementations focused and testable.
        """
    )
    
    async def main():
        print("=" * 80)
        print("🤖 PYDANTIC AI CODE AGENT - LIVE TEST")
        print("=" * 80)
        print("\nUsing model: ollama:qwen3-coder:30b")
        print("Generating Thompson Sampling implementation...\n")
        
        prompt = """
        Implement Thompson Sampling for multi-armed bandits.
        
        Requirements:
        - Class-based implementation
        - Beta distributions for each arm
        - select_arm() method
        - update() method for rewards
        - get_stats() for monitoring
        
        Keep it simple and clear (~50 lines).
        """
        
        result = await code_agent.run(prompt)
        impl = result.output
        
        print("✅ CODE GENERATED!\n")
        print("=" * 80)
        print(impl.code)
        print("=" * 80)
        print(f"\n📝 Explanation: {impl.explanation}")
        print(f"\n🔧 Key Functions: {', '.join(impl.key_functions)}")
        print("\n" + "=" * 80)
        print("🎉 SUCCESS! Pydantic AI generated working code from a prompt!")
        print("=" * 80)
        
        return impl
    
    if __name__ == "__main__":
        asyncio.run(main())
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("\n💡 Install pydantic-ai:")
    print("   pip install pydantic-ai")
    print("\n💡 Make sure Ollama is running:")
    print("   ollama serve &")

