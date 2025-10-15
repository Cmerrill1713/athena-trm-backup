"""
Vision MCP Server
Provides image analysis using vision-capable AI models
"""
import base64
import os

import requests
from fastmcp import FastMCP

mcp = FastMCP("vision", dependencies=["requests"])

def _encode_image(image_path: str) -> str:
    """Encode image to base64"""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

@mcp.tool()
def analyze_image_gpt4v(
    image_path: str,
    prompt: str = "What's in this image?",
    detail: str = "auto"
) -> dict:
    """
    Analyze image using GPT-4 Vision
    
    Args:
        image_path: Path to image file
        prompt: Question about the image
        detail: Detail level (low, high, auto)
    
    Returns:
        Image analysis from GPT-4V
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY not set", "status": "failed"}

        # Encode image
        base64_image = _encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

        payload = {
            "model": "gpt-4-vision-preview",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image}",
                                "detail": detail
                            }
                        }
                    ]
                }
            ],
            "max_tokens": 500
        }

        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "analysis": result["choices"][0]["message"]["content"],
                "model": "gpt-4-vision-preview",
                "usage": result.get("usage"),
                "status": "success"
            }
        else:
            return {
                "error": response.text,
                "status_code": response.status_code,
                "status": "failed"
            }

    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def analyze_image_claude(
    image_path: str,
    prompt: str = "What's in this image?",
    model: str = "claude-3-opus-20240229"
) -> dict:
    """
    Analyze image using Claude 3 (Opus/Sonnet with vision)
    
    Args:
        image_path: Path to image file
        prompt: Question about the image
        model: Claude model to use
    
    Returns:
        Image analysis from Claude
    """
    try:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            return {"error": "ANTHROPIC_API_KEY not set", "status": "failed"}

        # Encode image
        base64_image = _encode_image(image_path)

        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": model,
            "max_tokens": 1024,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": base64_image
                            }
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ]
                }
            ]
        }

        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "analysis": result["content"][0]["text"],
                "model": model,
                "usage": result.get("usage"),
                "status": "success"
            }
        else:
            return {
                "error": response.text,
                "status_code": response.status_code,
                "status": "failed"
            }

    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def analyze_image_gemini(
    image_path: str,
    prompt: str = "What's in this image?",
    model: str = "gemini-pro-vision"
) -> dict:
    """
    Analyze image using Google Gemini Vision
    
    Args:
        image_path: Path to image file
        prompt: Question about the image
        model: Gemini model to use
    
    Returns:
        Image analysis from Gemini
    """
    try:
        import google.generativeai as genai

        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            return {"error": "GOOGLE_API_KEY not set", "status": "failed"}

        genai.configure(api_key=api_key)

        # Load image
        from PIL import Image
        img = Image.open(image_path)

        # Create model and generate
        model_obj = genai.GenerativeModel(model)
        response = model_obj.generate_content([prompt, img])

        return {
            "analysis": response.text,
            "model": model,
            "status": "success"
        }

    except Exception as e:
        return {"error": str(e), "status": "failed"}

@mcp.tool()
def ocr_image(image_path: str) -> dict:
    """
    Extract text from image using OCR
    
    Args:
        image_path: Path to image file
    
    Returns:
        Extracted text
    """
    try:
        # Use GPT-4V for OCR
        return analyze_image_gpt4v(
            image_path,
            prompt="Extract all text from this image. Provide only the text content, preserving layout where possible."
        )

    except Exception as e:
        return {"error": str(e), "status": "failed"}

if __name__ == "__main__":
    mcp.run()

