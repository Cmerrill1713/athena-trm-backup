#!/usr/bin/env python3
"""
Vision → RAG Service
Handles image captioning and ingests results into Weaviate with RAG citations
Port: 8016
"""
import base64
import hashlib
import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional

import requests
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Add path for common imports
# Need to go up to GitHub root: universal-ai-tools -> AI-Projects -> GitHub
github_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, github_root)

from common.ops import add_health_endpoints

# Prometheus metrics
from prometheus_client import Counter, Histogram

app = FastAPI(title="Vision RAG Service", version="1.0.0")

# Add standard health + metrics endpoints
add_health_endpoints(app)

# Custom Prometheus metrics
VISION_REQUESTS = Counter('vision_requests_total', 'Total vision requests', ['status', 'operation'])
VISION_LATENCY = Histogram('vision_request_duration_seconds', 'Vision request latency', ['operation'])

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8080")
FASTVLM_URL = os.getenv("FASTVLM_URL", "http://localhost:8811")
VISION_ROUTER_URL = os.getenv("VISION_ROUTER_URL", "http://localhost:8811/v1/vision")

# Models
class VisionDescribeRequest(BaseModel):
    kind: str = "vision.describe"
    prompt: str
    imageBase64: str  # data:image/png;base64,...
    metadata: Optional[Dict[str, str]] = None

class Citation(BaseModel):
    id: str
    title: str
    snippet: str
    source: str

class VisionDescribeResponse(BaseModel):
    text: str
    citations: Optional[List[Citation]] = None
    ingested_object_id: Optional[str] = None
    provider: Optional[str] = None
    latency_ms: Optional[int] = None

# Helper functions
def compute_image_hash(image_data: bytes) -> str:
    """Compute SHA256 hash of image data"""
    return hashlib.sha256(image_data).hexdigest()

def extract_image_data(data_uri: str) -> tuple[bytes, str]:
    """Extract image bytes and format from data URI"""
    if not data_uri.startswith("data:image/"):
        raise ValueError("Invalid data URI")

    # Parse: data:image/png;base64,iVBORw0...
    parts = data_uri.split(',', 1)
    if len(parts) != 2:
        raise ValueError("Invalid data URI format")

    mime_part = parts[0]  # data:image/png;base64
    b64_data = parts[1]

    # Extract format
    format_part = mime_part.split('/')[1].split(';')[0]  # png

    # Decode base64
    image_bytes = base64.b64decode(b64_data)

    return image_bytes, format_part

def caption_image(image_data_uri: str, prompt: str, provider_override: Optional[str] = None) -> tuple[str, str, int]:
    """
    Send image to vision router for captioning
    Returns: (caption, provider_used, latency_ms)
    """
    start = datetime.now()

    try:
        # Parse the data URI to extract image data
        import base64
        import io

        # Remove data URI prefix if present
        if image_data_uri.startswith('data:'):
            # Format: data:image/png;base64,<data>
            header, encoded = image_data_uri.split(',', 1)
            image_bytes = base64.b64decode(encoded)
        else:
            # Assume it's already base64 encoded
            image_bytes = base64.b64decode(image_data_uri)

        # FastVLM expects multipart/form-data with file upload
        files = {
            'image': ('image.png', io.BytesIO(image_bytes), 'image/png')
        }
        data = {
            'prompt': prompt
        }

        response = requests.post(
            VISION_ROUTER_URL,
            files=files,
            data=data,
            timeout=30
        )
        response.raise_for_status()

        response_data = response.json()
        caption = response_data.get("text", "")
        provider = "fastvlm"

        latency = int((datetime.now() - start).total_seconds() * 1000)

        return caption, provider, latency

    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Vision service error: {str(e)}")

def ingest_to_weaviate(caption: str, image_hash: str, prompt: str, metadata: Dict) -> tuple[str, List[Citation]]:
    """
    Ingest caption and metadata into Weaviate
    Returns: (object_id, citations)
    """
    try:
        # Create Weaviate object
        headers = {"Content-Type": "application/json"}
        data = {
            "class": "LearnedPattern",
            "properties": {
                "pattern_type": "vision_analysis",
                "title": f"Vision: {caption[:60]}...",
                "description": caption,
                "pattern_data": json.dumps({
                    "source": "vision_rag",
                    "image_hash": image_hash,
                    "prompt": prompt,
                    "caption": caption,
                    "metadata": metadata,
                    "timestamp": datetime.now().isoformat()
                }),
                "tags": ["vision", "image-analysis", "rag"] + metadata.get("app", "").lower().split(),
                "success_rate": 1.0,
                "usage_count": 0
            }
        }

        response = requests.post(
            f"{WEAVIATE_URL}/v1/objects",
            headers=headers,
            json=data,
            timeout=30
        )

        if not response.ok:
            raise Exception(f"Weaviate error: {response.status_code}")

        object_id = response.json().get("id", "unknown")

        # Search for related content (RAG citations)
        citations = search_related_content(caption, k=3)

        return object_id, citations

    except Exception as e:
        print(f"⚠️  Weaviate ingest warning: {e}")
        return "ingestion_failed", []

def search_related_content(query: str, k: int = 3) -> List[Citation]:
    """Search Weaviate for related content to provide as citations"""
    try:
        gql = {
            "query": f"""
            {{ Get {{ 
                LearnedPattern(
                    limit: {k},
                    where: {{operator: Equal, path: ["pattern_type"], valueText: "video_transcript"}}
                ) {{ 
                    title description pattern_data tags 
                }} 
            }} }}
            """
        }

        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            headers={"Content-Type": "application/json"},
            json=gql,
            timeout=10
        )

        if not response.ok:
            return []

        patterns = response.json().get("data", {}).get("Get", {}).get("LearnedPattern", [])

        # Simple keyword matching for citations
        citations = []
        query_lower = query.lower()

        for i, pattern in enumerate(patterns[:k]):
            title = pattern.get("title", "")
            desc = pattern.get("description", "")

            # Score relevance
            score = 0.0
            if query_lower in title.lower():
                score += 2.0
            if query_lower in desc.lower():
                score += 1.0

            if score > 0 or i < 2:  # Include top 2 even if no direct match
                try:
                    pattern_data = json.loads(pattern.get("pattern_data", "{}"))
                    video_url = pattern_data.get("video_url", "")

                    citations.append(Citation(
                        id=f"weaviate-{i}",
                        title=title,
                        snippet=desc[:200],
                        source=video_url if video_url else f"weaviate://LearnedPattern/{i}"
                    ))
                except:
                    continue

        return citations

    except Exception as e:
        print(f"⚠️  Citation search error: {e}")
        return []

# API Endpoints
@app.post("/api/vision/describe", response_model=VisionDescribeResponse)
async def vision_describe(req: VisionDescribeRequest):
    """
    Describe an image and ingest into knowledge base with RAG citations
    
    Flow:
    1. Extract image data from base64
    2. Compute image hash
    3. Send to vision router for captioning (provider-agnostic)
    4. Ingest caption + metadata into Weaviate
    5. Search for related content (RAG citations)
    6. Return caption with citations
    """
    with VISION_LATENCY.labels(operation='describe').time():
        try:
            # Extract and hash image
            image_bytes, image_format = extract_image_data(req.imageBase64)
            image_hash = compute_image_hash(image_bytes)

            # Get caption from vision service
            caption, provider, latency = caption_image(req.imageBase64, req.prompt)

            # Ingest to Weaviate
            object_id, citations = ingest_to_weaviate(
                caption=caption,
                image_hash=image_hash,
                prompt=req.prompt,
                metadata=req.metadata or {}
            )

            # Record success metrics
            VISION_REQUESTS.labels(status='success', operation='describe').inc()

            return VisionDescribeResponse(
                text=caption,
                citations=citations if citations else None,
                ingested_object_id=object_id,
                provider=provider,
                latency_ms=latency
            )

        except ValueError as e:
            VISION_REQUESTS.labels(status='error', operation='describe').inc()
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            VISION_REQUESTS.labels(status='error', operation='describe').inc()
            raise HTTPException(status_code=500, detail=f"Vision RAG error: {str(e)}")

@app.get("/api/vision/health")
async def health():
    """Health check"""
    try:
        # Check Weaviate
        weaviate_ok = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=5).ok

        # Check vision service (optional)
        vision_ok = True  # Assume OK if router is available

        return {
            "status": "healthy" if (weaviate_ok and vision_ok) else "degraded",
            "weaviate": weaviate_ok,
            "vision_router": VISION_ROUTER_URL,
            "timestamp": datetime.now().isoformat()
        }
    except:
        return {"status": "unhealthy"}

@app.get("/api/vision/stats")
async def stats():
    """Get vision analysis statistics"""
    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json={"query": "{ Aggregate { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"vision_analysis\"}) { meta { count } } } }"},
            timeout=10
        )

        count = 0
        if response.ok:
            data = response.json()
            count = data.get("data", {}).get("Aggregate", {}).get("LearnedPattern", [{}])[0].get("meta", {}).get("count", 0)

        return {
            "total_vision_analyses": count,
            "weaviate_url": WEAVIATE_URL,
            "vision_router": VISION_ROUTER_URL
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("🚀 Starting Vision RAG Service on port 8016")
    print(f"📊 Weaviate: {WEAVIATE_URL}")
    print(f"🎨 Vision Router: {VISION_ROUTER_URL}")
    uvicorn.run(app, host="0.0.0.0", port=8016, log_level="info")

