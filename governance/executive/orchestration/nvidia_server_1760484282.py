"""
NVIDIA AI MCP Server
Provides tools for NVIDIA NIM and Triton Inference Server
"""
import os
from typing import Optional

import requests
from fastmcp import FastMCP

mcp = FastMCP("nvidia-ai", dependencies=["requests"])

@mcp.tool()
def nim_infer(
    model: str,
    prompt: str,
    max_tokens: int = 1024,
    api_key: Optional[str] = None
) -> dict:
    """
    Inference using NVIDIA NIM (NVIDIA Inference Microservices)
    
    Args:
        model: Model name (e.g., meta/llama-3-70b-instruct)
        prompt: Input prompt
        max_tokens: Maximum tokens to generate
        api_key: NVIDIA API key (optional, uses env var)
    
    Returns:
        Model response
    """
    try:
        api_key = api_key or os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return {"error": "NVIDIA_API_KEY not set"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens
        }

        response = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "content": result["choices"][0]["message"]["content"],
                "model": model,
                "usage": result.get("usage", {}),
                "status": "success"
            }
        else:
            return {"error": response.text, "status": "failed"}

    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def nim_list_models() -> dict:
    """
    List available NVIDIA NIM models
    
    Returns:
        List of available models
    """
    try:
        api_key = os.getenv("NVIDIA_API_KEY")
        if not api_key:
            return {"error": "NVIDIA_API_KEY not set"}

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        response = requests.get(
            "https://integrate.api.nvidia.com/v1/models",
            headers=headers,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "models": result.get("data", []),
                "status": "success"
            }
        else:
            return {"error": response.text, "status": "failed"}

    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

