#!/usr/bin/env python3
"""
Persist Vision Results to Weaviate
Stores captions for RAG context
"""

import requests
import time
import hashlib
import json
from pathlib import Path
from typing import Optional

WEAVIATE_BASE = "http://localhost:8090/v1"

def put_vision_caption(image_path: str, caption: str, prompt: str, metadata: Optional[dict] = None):
    """
    Store vision caption in Weaviate for RAG

    Args:
        image_path: Path to the image file
        caption: The generated caption
        prompt: The prompt used
        metadata: Optional additional metadata (latency_ms, model, etc.)
    """
    # Read image and compute hash
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    image_hash = hashlib.sha256(image_bytes).hexdigest()

    # Prepare object
    obj = {
        "class": "VisionCaption",
        "properties": {
            "imageHash": image_hash,
            "prompt": prompt,
            "caption": caption,
            "timestamp": int(time.time()),
            "imagePath": str(Path(image_path).name),
            "imageSize": len(image_bytes)
        }
    }

    # Add optional metadata
    if metadata:
        obj["properties"]["latency_ms"] = metadata.get("latency_ms", 0)
        obj["properties"]["model"] = metadata.get("model", "unknown")

    # Store in Weaviate
    try:
        response = requests.post(
            f"{WEAVIATE_BASE}/objects",
            json=obj,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Failed to persist to Weaviate: {e}")
        return None

def ensure_schema_exists():
    """Ensure VisionCaption class exists in Weaviate"""
    schema = {
        "class": "VisionCaption",
        "description": "Vision model outputs for RAG context",
        "vectorizer": "text2vec-transformers",
        "moduleConfig": {
            "text2vec-transformers": {
                "vectorizeClassName": False
            }
        },
        "properties": [
            {
                "name": "imageHash",
                "dataType": ["text"],
                "description": "SHA256 hash of image"
            },
            {
                "name": "prompt",
                "dataType": ["text"],
                "description": "Prompt used for vision"
            },
            {
                "name": "caption",
                "dataType": ["text"],
                "description": "Generated caption",
                "moduleConfig": {
                    "text2vec-transformers": {
                        "skip": False,
                        "vectorizePropertyName": False
                    }
                }
            },
            {
                "name": "timestamp",
                "dataType": ["int"],
                "description": "Unix timestamp"
            },
            {
                "name": "imagePath",
                "dataType": ["text"],
                "description": "Original image filename"
            },
            {
                "name": "imageSize",
                "dataType": ["int"],
                "description": "Image size in bytes"
            },
            {
                "name": "latency_ms",
                "dataType": ["number"],
                "description": "Inference latency"
            },
            {
                "name": "model",
                "dataType": ["text"],
                "description": "Model used"
            }
        ]
    }

    try:
        # Check if class exists
        response = requests.get(f"{WEAVIATE_BASE}/schema/VisionCaption", timeout=3)
        if response.status_code == 200:
            print("✅ VisionCaption schema already exists")
            return True

        # Create class
        response = requests.post(
            f"{WEAVIATE_BASE}/schema",
            json=schema,
            timeout=5
        )
        response.raise_for_status()
        print("✅ VisionCaption schema created")
        return True

    except Exception as e:
        print(f"Warning: Could not create schema: {e}")
        return False

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 4:
        print("Usage: persist_vision_to_weaviate.py <image_path> <caption> <prompt>")
        sys.exit(1)

    ensure_schema_exists()

    result = put_vision_caption(
        image_path=sys.argv[1],
        caption=sys.argv[2],
        prompt=sys.argv[3]
    )

    if result:
        print(f"✅ Stored vision result: {result.get('id')}")
    else:
        print("❌ Failed to store result")
