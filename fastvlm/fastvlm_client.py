#!/usr/bin/env python3
"""
FastVLM Client - Python client for FastVLM server
Used by Athena's routing system to call vision models
"""

import os
import time
from typing import Dict, Any, Optional
from pathlib import Path

import requests


class FastVLMClient:
    """Client for FastVLM vision inference"""
    
    def __init__(self, endpoint: str = "http://127.0.0.1:8811"):
        """
        Initialize FastVLM client
        
        Args:
            endpoint: FastVLM server endpoint
        """
        self.endpoint = endpoint.rstrip("/")
        self.session = requests.Session()
    
    def health(self) -> Dict[str, Any]:
        """
        Check FastVLM server health
        
        Returns:
            Health status dict
        """
        response = self.session.get(f"{self.endpoint}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    
    def is_healthy(self) -> bool:
        """
        Check if server is healthy
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            health = self.health()
            return health.get("status") == "healthy"
        except Exception:
            return False
    
    def vision(
        self,
        image_path: str,
        prompt: str = "Describe the image.",
        timeout: int = 120
    ) -> Dict[str, Any]:
        """
        Run vision inference on an image
        
        Args:
            image_path: Path to image file
            prompt: Vision prompt/question
            timeout: Request timeout in seconds
        
        Returns:
            Response dict with keys:
                - text: Model output
                - latency_ms: Inference latency
                - model: Model name
                - image_size: Image size in bytes
        
        Raises:
            FileNotFoundError: If image file doesn't exist
            requests.HTTPError: If server returns error
            requests.Timeout: If request times out
        """
        image_path = Path(image_path)
        if not image_path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(image_path, "rb") as f:
            files = {
                "image": (image_path.name, f, "application/octet-stream")
            }
            data = {
                "prompt": prompt
            }
            
            response = self.session.post(
                f"{self.endpoint}/v1/vision",
                files=files,
                data=data,
                timeout=timeout
            )
        
        response.raise_for_status()
        return response.json()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close session"""
        self.session.close()


# Singleton instance for routing system
_client_instance: Optional[FastVLMClient] = None


def get_client(endpoint: Optional[str] = None) -> FastVLMClient:
    """
    Get or create singleton FastVLM client
    
    Args:
        endpoint: Optional endpoint override
    
    Returns:
        FastVLM client instance
    """
    global _client_instance
    
    if endpoint is None:
        endpoint = os.environ.get("FASTVLM_ENDPOINT", "http://127.0.0.1:8811")
    
    if _client_instance is None or _client_instance.endpoint != endpoint:
        _client_instance = FastVLMClient(endpoint)
    
    return _client_instance


def call_fastvlm(
    image_path: str,
    prompt: str = "Describe the image.",
    endpoint: Optional[str] = None
) -> str:
    """
    Convenience function to call FastVLM and return just the text
    
    Args:
        image_path: Path to image file
        prompt: Vision prompt
        endpoint: Optional endpoint override
    
    Returns:
        Model output text
    """
    client = get_client(endpoint)
    result = client.vision(image_path, prompt)
    return result["text"]


# CLI support
if __name__ == "__main__":
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="FastVLM Client CLI")
    parser.add_argument("image", help="Path to image file")
    parser.add_argument("--prompt", default="Describe the image.", help="Vision prompt")
    parser.add_argument("--endpoint", default="http://127.0.0.1:8811", help="FastVLM server endpoint")
    parser.add_argument("--json", action="store_true", help="Output JSON instead of just text")
    parser.add_argument("--health", action="store_true", help="Check server health")
    
    args = parser.parse_args()
    
    client = FastVLMClient(args.endpoint)
    
    if args.health:
        try:
            health = client.health()
            print(f"Status: {health['status']}")
            print(f"Model: {health['model']}")
            print(f"Root: {health['fastvlm_root']}")
            print(f"Model exists: {health['model_exists']}")
            sys.exit(0 if health['status'] == 'healthy' else 1)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    try:
        start = time.time()
        result = client.vision(args.image, args.prompt)
        elapsed = time.time() - start
        
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            print(result["text"])
            print(f"\n⏱️  {result['latency_ms']:.0f}ms inference, {elapsed*1000:.0f}ms total", file=sys.stderr)
    
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

