#!/usr/bin/env python3
"""
Migrate corpus from old format to DocsV2 with 768-dim vectors

Reads from old Weaviate classes and re-embeds into DocsV2 with proper dimensions.
"""

import sys
import requests
import time
from typing import List, Dict, Any

WEAVIATE_URL = "http://localhost:8090"
EMBED_URL = "http://localhost:8086"

def get_old_docs(class_name: str = "Docs", limit: int = 1000) -> List[Dict]:
    """Fetch documents from old class"""
    print(f"Fetching docs from {class_name}...")
    
    response = requests.get(
        f"{WEAVIATE_URL}/v1/objects",
        params={"class": class_name, "limit": limit}
    )
    
    if response.status_code == 200:
        data = response.json()
        docs = data.get("objects", [])
        print(f"  Found {len(docs)} documents")
        return docs
    else:
        print(f"  Failed to fetch: {response.text[:200]}")
        return []

def migrate_doc(doc: Dict, index: int) -> bool:
    """Migrate single document to DocsV2 with 768-dim embedding"""
    props = doc.get("properties", {})
    
    # Extract text content
    text = props.get("text", props.get("chunk", props.get("content", "")))
    if not text or len(text) < 10:
        return False
    
    # Generate 768-dim embedding
    try:
        embed_resp = requests.post(
            f"{EMBED_URL}/embed",
            json={"texts": [text[:1000]], "tier": "base"},  # Limit to 1000 chars for speed
            timeout=10
        )
        
        if embed_resp.status_code != 200:
            print(f"    Embedding failed: {embed_resp.text[:100]}")
            return False
        
        vector = embed_resp.json()["vectors"][0]
        
    except Exception as e:
        print(f"    Embedding error: {e}")
        return False
    
    # Create DocsV2 object
    payload = {
        "class": "DocsV2",
        "properties": {
            "doc_id": props.get("chunk_id", props.get("doc_id", f"migrated_{index}")),
            "title": props.get("title", "Untitled")[:500],
            "chunk": text[:2000],  # Limit chunk size
            "path": props.get("path", props.get("source", props.get("file_path", "unknown"))),
            "url": props.get("url", "")
        },
        "vector": vector
    }
    
    try:
        resp = requests.post(f"{WEAVIATE_URL}/v1/objects", json=payload, timeout=5)
        return resp.status_code in [200, 201]
    except Exception as e:
        print(f"    Upload error: {e}")
        return False

def main():
    """Run migration"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate corpus to DocsV2 with 768-dim vectors")
    parser.add_argument("--source-class", default="Docs", help="Source class name")
    parser.add_argument("--limit", type=int, default=100, help="Number of docs to migrate")
    parser.add_argument("--batch-size", type=int, default=10, help="Batch size")
    
    args = parser.parse_args()
    
    print("═" * 80)
    print("  CORPUS MIGRATION TO DocsV2 (768-dim)")
    print("═" * 80)
    print()
    
    # Check services
    print("Checking services...")
    try:
        requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=2).raise_for_status()
        print("  ✓ Weaviate")
    except:
        print("  ✗ Weaviate not responding")
        sys.exit(1)
    
    try:
        requests.get(f"{EMBED_URL}/health", timeout=2).raise_for_status()
        print("  ✓ Embedding service")
    except:
        print("  ✗ Embedding service not responding")
        sys.exit(1)
    
    print()
    
    # Fetch old docs
    old_docs = get_old_docs(args.source_class, args.limit)
    
    if not old_docs:
        print("No documents to migrate!")
        sys.exit(0)
    
    # Migrate
    print(f"\nMigrating {len(old_docs)} documents to DocsV2...")
    print(f"  Using 768-dim vectors (ollama/nomic-embed-text)")
    print()
    
    success = 0
    failed = 0
    
    for i, doc in enumerate(old_docs):
        if i > 0 and i % args.batch_size == 0:
            print(f"  Progress: {i}/{len(old_docs)} ({success} success, {failed} failed)")
            time.sleep(1)  # Rate limit
        
        if migrate_doc(doc, i):
            success += 1
        else:
            failed += 1
    
    print()
    print("═" * 80)
    print(f"  MIGRATION COMPLETE")
    print("═" * 80)
    print(f"  Success: {success}")
    print(f"  Failed: {failed}")
    print(f"  Total: {len(old_docs)}")
    print()
    
    # Verify
    verify_resp = requests.get(f"{WEAVIATE_URL}/v1/objects?class=DocsV2&limit=1")
    if verify_resp.status_code == 200:
        total = verify_resp.json().get("totalResults", 0)
        print(f"✓ DocsV2 now has {total} documents")
    
    print()
    print("Next steps:")
    print("  1. Test KB search: curl http://localhost:8088/kb/search -d '{\"query\":\"test\",\"topK\":3}'")
    print("  2. Run validation: make rag-eval")
    print("  3. If good, migrate more: python3 scripts/migrate_corpus_to_768.py --limit 1000")

if __name__ == "__main__":
    main()

