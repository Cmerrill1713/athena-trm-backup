"""
Local LLM Interface for Remediation

Supports:
- Ollama (primary)
- LM Studio
- vLLM
- Any OpenAI-compatible endpoint
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
import requests

logger = logging.getLogger(__name__)


class LocalLLM:
    """Interface to local LLM inference servers"""
    
    def __init__(
        self,
        provider: str = "ollama",
        base_url: Optional[str] = None,
        model: Optional[str] = None
    ):
        self.provider = provider
        
        # Default endpoints
        if base_url is None:
            if provider == "ollama":
                self.base_url = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
            elif provider == "lmstudio":
                self.base_url = "http://localhost:1234"
            elif provider == "vllm":
                self.base_url = "http://localhost:8000"
            else:
                self.base_url = base_url or "http://localhost:11434"
        else:
            self.base_url = base_url
        
        # Default models
        if model is None:
            if provider == "ollama":
                self.model = os.getenv("REMEDIATION_MODEL", "qwen3-coder:30b")
            else:
                self.model = model or "mistral:7b"
        else:
            self.model = model
        
        logger.info(f"Initialized LocalLLM: provider={provider}, model={self.model}")
    
    def generate(
        self,
        prompt: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Generate text from prompt using local LLM"""
        
        if self.provider == "ollama":
            return self._generate_ollama(prompt, max_tokens, temperature, **kwargs)
        elif self.provider in ["lmstudio", "vllm"]:
            return self._generate_openai_compatible(prompt, max_tokens, temperature, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.provider}")
    
    def _generate_ollama(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate using Ollama API"""
        
        url = f"{self.base_url}/api/generate"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
        
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.base_url}")
            logger.error("Is Ollama running? Try: ollama serve")
            raise
        except Exception as e:
            logger.error(f"Ollama generation failed: {e}")
            raise
    
    def _generate_openai_compatible(
        self,
        prompt: str,
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Generate using OpenAI-compatible API (LM Studio, vLLM)"""
        
        url = f"{self.base_url}/v1/completions"
        
        payload = {
            "model": self.model,
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["choices"][0]["text"]
        
        except Exception as e:
            logger.error(f"OpenAI-compatible generation failed: {e}")
            raise
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 2048,
        temperature: float = 0.7,
        **kwargs
    ) -> str:
        """Chat completion (if supported by provider)"""
        
        if self.provider == "ollama":
            return self._chat_ollama(messages, max_tokens, temperature, **kwargs)
        else:
            # Convert to simple prompt for non-chat models
            prompt = "\n\n".join([f"{m['role']}: {m['content']}" for m in messages])
            return self.generate(prompt, max_tokens, temperature, **kwargs)
    
    def _chat_ollama(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        **kwargs
    ) -> str:
        """Chat using Ollama API"""
        
        url = f"{self.base_url}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            }
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            return result["message"]["content"]
        
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            raise
    
    @staticmethod
    def list_models(provider: str = "ollama", base_url: Optional[str] = None) -> List[str]:
        """List available models"""
        
        if base_url is None:
            base_url = "http://localhost:11434" if provider == "ollama" else "http://localhost:1234"
        
        if provider == "ollama":
            url = f"{base_url}/api/tags"
            try:
                response = requests.get(url, timeout=5)
                response.raise_for_status()
                models = response.json().get("models", [])
                return [m["name"] for m in models]
            except Exception as e:
                logger.error(f"Failed to list models: {e}")
                return []
        else:
            logger.warning(f"Model listing not implemented for {provider}")
            return []
    
    @staticmethod
    def is_available(provider: str = "ollama", base_url: Optional[str] = None) -> bool:
        """Check if local LLM server is available"""
        
        if base_url is None:
            base_url = "http://localhost:11434" if provider == "ollama" else "http://localhost:1234"
        
        try:
            if provider == "ollama":
                url = f"{base_url}/api/tags"
            else:
                url = f"{base_url}/v1/models"
            
            response = requests.get(url, timeout=2)
            return response.status_code == 200
        except:
            return False


# Convenience function
def generate_remediation_plan(incident_data: Dict[str, Any], model: Optional[str] = None) -> str:
    """Generate remediation plan using local LLM"""
    
    llm = LocalLLM(provider="ollama", model=model)
    
    prompt = f"""You are an expert code remediation system. Analyze this incident and generate a fix plan.

Incident Data:
{json.dumps(incident_data, indent=2)}

Generate a JSON remediation plan with:
{{
  "description": "Clear description of the fix",
  "changes": [
    {{
      "file": "path/to/file.py",
      "action": "modify|add|remove",
      "reason": "Why this change fixes the issue"
    }}
  ],
  "confidence": 0.85,
  "risk_level": "LOW|MEDIUM|HIGH",
  "estimated_time_minutes": 10
}}

Respond with ONLY the JSON, no explanation."""
    
    return llm.generate(prompt, max_tokens=1024, temperature=0.3)


if __name__ == "__main__":
    # Test local LLM
    print("Testing local LLM connection...\n")
    
    if LocalLLM.is_available("ollama"):
        print("✅ Ollama is available")
        models = LocalLLM.list_models("ollama")
        print(f"📦 Available models: {', '.join(models)}")
        
        # Test generation
        llm = LocalLLM()
        response = llm.generate("Say 'Hello from local LLM!'", max_tokens=50)
        print(f"\n💬 Response: {response}")
    else:
        print("❌ Ollama not available")
        print("   Start it with: ollama serve")
        print("   Pull a model: ollama pull deepseek-coder:6.7b")

