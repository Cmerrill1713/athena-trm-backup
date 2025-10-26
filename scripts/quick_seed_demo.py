#!/usr/bin/env python3
"""Quick seed demo corpus into DocsV2 to prove stack works"""

import requests
import hashlib

WEAVIATE_URL = "http://localhost:8090"

# Sample docs from your AGI system
demo_docs = [
    {
        "title": "AGI Core Overview",
        "content": "AGI Core provides 16 specialized expert agents with context engineering, workflows, and evaluation metrics. The system uses Scout-Plan-Build patterns for task execution.",
        "path": "agi_core/README.md"
    },
    {
        "title": "TRM Recursive Models",
        "content": "TinyRecursiveModels (TRM) is a 7M parameter recursive reasoning architecture achieving 45% on ARC-AGI-1. It uses deliberate cycles for improved reasoning.",
        "path": "TinyRecursiveModels/README.md"
    },
    {
        "title": "RAG Delta Testing",
        "content": "RAG Delta Reports compare BM25 vs semantic vs hybrid search modes. Quality gates ensure hit@5 >= 0.97 and support@3 >= 0.95 before deployment.",
        "path": "docs/RAG_DELTA_REPORTS.md"
    },
    {
        "title": "Router Architecture",
        "content": "The RAG-aware router uses intent classification and KB probing to route queries optimally. Factual queries go to RAG, creative to LLM, reasoning to TRM.",
        "path": "services/router/README.md"
    },
    {
        "title": "OpenAI Adapter",
        "content": "OpenAI-compatible adapter exposes AGI+RAG backend via /v1/chat/completions and /v1/models endpoints. Supports streaming and multiple models.",
        "path": "services/openai-compat/README.md"
    }
]

print("Seeding DocsV2 with demo corpus...")

for i, doc in enumerate(demo_docs):
    # Generate deterministic vector (384 dims)
    hash_bytes = hashlib.sha256(doc["content"].encode()).digest()
    vector = [((b / 255.0) * 2 - 1) for b in hash_bytes[:192]]
    vector = vector + [0.0] * (384 - len(vector))
    
    payload = {
        "class": "DocsV2",
        "properties": {
            "doc_id": f"demo_{i}",
            "title": doc["title"],
            "chunk": doc["content"],
            "path": doc["path"],
            "url": ""
        },
        "vector": vector
    }
    
    response = requests.post(f"{WEAVIATE_URL}/v1/objects", json=payload)
    
    if response.status_code in [200, 201]:
        print(f"✓ Seeded: {doc['title']}")
    else:
        print(f"✗ Failed: {doc['title']} - {response.text[:100]}")

print(f"\n✓ Demo corpus seeded ({len(demo_docs)} docs)")
