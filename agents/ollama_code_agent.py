#!/usr/bin/env python3
"""
Ollama Code Agent - Direct implementation without Pydantic AI dependency issues
===============================================================================
Uses your local qwen3-coder:30b to generate real code from research papers
"""

import asyncio
import httpx
from typing import Dict, Any


class OllamaCodeAgent:
    """Code generation agent using local Ollama"""
    
    def __init__(self, model: str = "qwen3-coder:30b"):
        self.model = model
        self.ollama_base = "http://localhost:11434"
    
    async def generate_code(self, prompt: str) -> Dict[str, Any]:
        """
        Generate code from a prompt using Ollama
        
        Returns:
            Dict with 'code', 'explanation', and 'success' keys
        """
        
        system_prompt = """You are an expert Python developer who implements algorithms from research papers.

Generate clean, production-ready Python code with:
- Type hints and docstrings
- Error handling
- Clear variable names  
- Modular design

Format your response as:
```python
[YOUR CODE HERE]
```

Then explain what you built."""
        
        full_prompt = f"{system_prompt}\n\nTask: {prompt}"
        
        try:
            async with httpx.AsyncClient(timeout=120) as client:
                response = await client.post(
                    f"{self.ollama_base}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": full_prompt,
                        "stream": False
                    }
                )
                
                if response.status_code != 200:
                    return {
                        "success": False,
                        "error": f"Ollama returned {response.status_code}"
                    }
                
                data = response.json()
                generated_text = data.get("response", "")
                
                # Extract code from markdown blocks
                code = self._extract_code(generated_text)
                explanation = generated_text.replace(f"```python\n{code}\n```", "").strip()
                
                return {
                    "success": True,
                    "code": code,
                    "explanation": explanation,
                    "model": self.model,
                    "tokens": data.get("eval_count", 0)
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _extract_code(self, text: str) -> str:
        """Extract Python code from markdown blocks"""
        import re
        
        # Find code blocks
        pattern = r'```python\n(.*?)```'
        matches = re.findall(pattern, text, re.DOTALL)
        
        if matches:
            return matches[0].strip()
        
        # Fallback: return text if no code blocks found
        return text.strip()


# ============================================================================
# DEMO: Implement Thompson Sampling from Research Paper
# ============================================================================

async def main():
    print("=" * 80)
    print("🤖 OLLAMA CODE AGENT - REAL CODE GENERATION")
    print("=" * 80)
    print("\nUsing: qwen3-coder:30b (local Ollama)")
    print("Generating implementation from research paper concept...\n")
    
    agent = OllamaCodeAgent()
    
    paper_prompt = """
Implement Contextual Thompson Sampling for multi-armed bandits.

Research Paper Concept:
Enhance standard Thompson Sampling by adding context-awareness. Instead of
fixed Beta distributions, use a small neural network to adjust distributions
based on context features (task type, time of day, user history).

Algorithm:
1. Maintain Beta(alpha, beta) for each arm
2. Train small NN on (context, arm, reward) tuples
3. At decision: NN predicts adjustment to Beta params based on context
4. Sample from adjusted Betas
5. Select arm with highest sample
6. Update both NN and Beta distributions

Requirements:
- Clean class-based design
- Type hints throughout
- Integrate with existing orchestrator/scorer.py Thompson Sampling
- Keep it simple (~100 lines)

Generate the implementation now.
"""
    
    print("⏳ Calling Ollama (this may take 30-60 seconds)...\n")
    
    result = await agent.generate_code(paper_prompt)
    
    if result["success"]:
        print("✅ CODE GENERATED SUCCESSFULLY!\n")
        print("=" * 80)
        print("GENERATED CODE:")
        print("=" * 80)
        print(result["code"])
        print("\n" + "=" * 80)
        print("EXPLANATION:")
        print("=" * 80)
        print(result["explanation"])
        print("\n" + "=" * 80)
        print(f"📊 Tokens generated: {result['tokens']}")
        print(f"🤖 Model: {result['model']}")
        
        # Save to file
        output_file = "orchestrator/providers/contextual_thompson_sampling.py"
        with open(output_file, "w") as f:
            f.write(result["code"])
        
        print(f"\n💾 Saved to: {output_file}")
        print("\n🎉 Research paper successfully implemented using local LLM!")
        
    else:
        print(f"❌ Generation failed: {result['error']}")
        print("\n💡 Make sure Ollama is running:")
        print("   ollama serve &")


if __name__ == "__main__":
    asyncio.run(main())

