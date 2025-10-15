"""
Mistral AI MCP Server
Provides tools for Mistral's chat and embedding models
"""
import os
from typing import List

from fastmcp import FastMCP

mcp = FastMCP("mistral-ai", dependencies=["mistralai"])

@mcp.tool()
def mistral_chat(
    messages: List[dict],
    model: str = "mistral-large-latest"
) -> dict:
    """
    Chat with Mistral AI
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Mistral model (mistral-large-latest, mistral-medium, etc.)
    
    Returns:
        Chat completion response
    """
    try:
        from mistralai.client import MistralClient
        from mistralai.models.chat_completion import ChatMessage

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return {"error": "MISTRAL_API_KEY not set"}

        client = MistralClient(api_key=api_key)

        chat_messages = [
            ChatMessage(role=msg["role"], content=msg["content"])
            for msg in messages
        ]

        response = client.chat(
            model=model,
            messages=chat_messages
        )

        return {
            "content": response.choices[0].message.content,
            "model": response.model,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            },
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def mistral_embed(texts: List[str], model: str = "mistral-embed") -> dict:
    """
    Generate embeddings using Mistral
    
    Args:
        texts: List of texts to embed
        model: Embedding model
    
    Returns:
        List of embeddings
    """
    try:
        from mistralai.client import MistralClient

        api_key = os.getenv("MISTRAL_API_KEY")
        if not api_key:
            return {"error": "MISTRAL_API_KEY not set"}

        client = MistralClient(api_key=api_key)

        response = client.embeddings(
            model=model,
            input=texts
        )

        return {
            "embeddings": [e.embedding for e in response.data],
            "count": len(response.data),
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

