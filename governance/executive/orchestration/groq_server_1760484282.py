"""
Groq AI MCP Server
Provides ultra-fast inference with Groq's LPU technology
"""
import os
from typing import List

from fastmcp import FastMCP

mcp = FastMCP("groq-ai", dependencies=["groq"])

@mcp.tool()
def groq_chat(
    messages: List[dict],
    model: str = "mixtral-8x7b-32768"
) -> dict:
    """
    Ultra-fast chat inference with Groq
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Groq model (mixtral-8x7b-32768, llama2-70b-4096, etc.)
    
    Returns:
        Chat completion response
    """
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ_API_KEY not set"}

        client = Groq(api_key=api_key)

        response = client.chat.completions.create(
            model=model,
            messages=messages
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
def groq_transcribe(audio_file_path: str, model: str = "whisper-large-v3") -> dict:
    """
    Transcribe audio using Groq Whisper (ultra-fast)
    
    Args:
        audio_file_path: Path to audio file
        model: Whisper model (whisper-large-v3)
    
    Returns:
        Transcription text
    """
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ_API_KEY not set"}

        client = Groq(api_key=api_key)

        with open(audio_file_path, "rb") as file:
            response = client.audio.transcriptions.create(
                file=file,
                model=model
            )

        return {
            "text": response.text,
            "model": model,
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def groq_list_models() -> dict:
    """
    List available Groq models
    
    Returns:
        List of available models
    """
    try:
        from groq import Groq

        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            return {"error": "GROQ_API_KEY not set"}

        client = Groq(api_key=api_key)
        models = client.models.list()

        return {
            "models": [{"id": m.id, "created": m.created} for m in models.data],
            "count": len(models.data),
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

