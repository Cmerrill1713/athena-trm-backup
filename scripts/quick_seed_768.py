#!/usr/bin/env python3
"""Seed DocsV2 with 768-dim vectors"""
import requests

WEAVIATE_URL = "http://localhost:8090"
EMBED_URL = "http://localhost:8086"

demo_docs = [
    {"title": "AGI Core Overview", "content": "AGI Core provides 16 specialized expert agents with context engineering and workflows.", "path": "agi_core/README.md"},
    {"title": "TRM Recursive Models", "content": "TinyRecursiveModels is a 7M parameter recursive reasoning architecture achieving 45% on ARC-AGI-1.", "path": "TinyRecursiveModels/README.md"},
    {"title": "RAG Delta Testing", "content": "RAG Delta Reports compare BM25 vs semantic vs hybrid search modes with quality gates.", "path": "docs/RAG_DELTA_REPORTS.md"},
]

print("Clearing DocsV2...")
requests.delete(f"{WEAVIATE_URL}/v1/schema/DocsV2")

print("Creating DocsV2 schema with 768 dimensions...")
schema = {
    "class": "DocsV2",
    "vectorIndexConfig": {"distance": "cosine"},
    "properties": [
        {"name": "doc_id", "dataType": ["text"]},
        {"name": "title", "dataType": ["text"]},
        {"name": "chunk", "dataType": ["text"]},
        {"name": "path", "dataType": ["text"]},
        {"name": "url", "dataType": ["text"]}
    ]
}
requests.post(f"{WEAVIATE_URL}/v1/schema", json=schema)

print("Seeding with 768-dim vectors...")
for i, doc in enumerate(demo_docs):
    # Get real embedding
    embed_resp = requests.post(f"{EMBED_URL}/embed", json={"texts": [doc["content"]], "tier": "base"})
    vector = embed_resp.json()["vectors"][0]
    
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
    
    resp = requests.post(f"{WEAVIATE_URL}/v1/objects", json=payload)
    if resp.status_code in [200, 201]:
        print(f"✓ {doc['title']}")
    else:
        print(f"✗ {doc['title']}: {resp.text[:100]}")

print(f"\n✓ Seeded {len(demo_docs)} docs with 768-dim vectors")
