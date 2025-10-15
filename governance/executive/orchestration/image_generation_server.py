"""
Image Generation MCP Server
Provides image generation using multiple AI models
"""
import os
from typing import Literal, Optional

import requests
from fastmcp import FastMCP

mcp = FastMCP("image-generation", dependencies=["requests"])

@mcp.tool()
def generate_image_openai(
    prompt: str,
    size: Literal["1024x1024", "1792x1024", "1024x1792"] = "1024x1024",
    quality: Literal["standard", "hd"] = "standard",
    model: str = "dall-e-3"
) -> dict:
    """
    Generate image using OpenAI DALL-E
    
    Args:
        prompt: Image description
        size: Image size
        quality: Image quality (standard or hd)
        model: Model to use (dall-e-2 or dall-e-3)
    
    Returns:
        Generated image URL and metadata
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY not set", "status": "failed"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": model,
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality
        }

        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "url": result["data"][0]["url"],
                "revised_prompt": result["data"][0].get("revised_prompt"),
                "model": model,
                "size": size,
                "quality": quality,
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
def generate_image_stability(
    prompt: str,
    width: int = 1024,
    height: int = 1024,
    model: str = "stable-diffusion-xl-1024-v1-0"
) -> dict:
    """
    Generate image using Stability AI (Stable Diffusion)
    
    Args:
        prompt: Image description
        width: Image width (default: 1024)
        height: Image height (default: 1024)
        model: Model to use
    
    Returns:
        Generated image (base64) and metadata
    """
    try:
        api_key = os.getenv("STABILITY_API_KEY")
        if not api_key:
            return {"error": "STABILITY_API_KEY not set", "status": "failed"}

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        payload = {
            "text_prompts": [{"text": prompt}],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30
        }

        response = requests.post(
            f"https://api.stability.ai/v1/generation/{model}/text-to-image",
            headers=headers,
            json=payload,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "image_base64": result["artifacts"][0]["base64"],
                "seed": result["artifacts"][0]["seed"],
                "model": model,
                "width": width,
                "height": height,
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
def edit_image_openai(
    image_path: str,
    prompt: str,
    mask_path: Optional[str] = None,
    size: Literal["1024x1024", "512x512", "256x256"] = "1024x1024"
) -> dict:
    """
    Edit image using OpenAI DALL-E
    
    Args:
        image_path: Path to image file
        prompt: Edit instruction
        mask_path: Optional mask image path
        size: Output size
    
    Returns:
        Edited image URL
    """
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return {"error": "OPENAI_API_KEY not set", "status": "failed"}

        headers = {
            "Authorization": f"Bearer {api_key}"
        }

        files = {
            "image": open(image_path, "rb"),
            "prompt": (None, prompt),
            "size": (None, size)
        }

        if mask_path:
            files["mask"] = open(mask_path, "rb")

        response = requests.post(
            "https://api.openai.com/v1/images/edits",
            headers=headers,
            files=files,
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return {
                "url": result["data"][0]["url"],
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

if __name__ == "__main__":
    mcp.run()

