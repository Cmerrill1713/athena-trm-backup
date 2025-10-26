#!/usr/bin/env python3
"""
Dynamic RAG Seeder - Multi-Tier with UUID Support
Seeds ChunkMini (coarse), ChunkBase (fine), ChunkLong (ultra-fine)
"""

import os
import re
import time
import json
import uuid
import pathlib
import hashlib
from typing import List, Dict, Any, Tuple
import requests

# Configuration
ROOT = pathlib.Path(os.getenv("SEED_ROOT", ".")).resolve()
WVV = os.getenv("WEAVIATE_URL", "http://localhost:8090")
BATCH = 64

IGNORES = (".git", "node_modules", "__pycache__", ".venv", "build", "dist", "DerivedData")

def iter_files():
    """Iterate over all eligible files in the repo"""
    for p in ROOT.rglob("*"):
        if any(seg in p.parts for seg in IGNORES):
            continue
        if p.is_file() and p.suffix.lower() in (
            ".py", ".swift", ".md", ".ts", ".tsx", ".rs", ".go", 
            ".json", ".yaml", ".yml", ".sh", ".js", ".jsx"
        ):
            yield p

def chunk(text: str, size: int, overlap: int) -> List[str]:
    """Create overlapping chunks from text"""
    out, i = [], 0
    n = len(text)
    while i < n:
        end = min(i + size, n)
        chunk_text = text[i:end]
        
        # Try to break at word boundaries if not at end
        if end < n:
            # Look for good break points
            for break_char in ['\n\n', '\n', '. ', '; ', ', ', ' ']:
                break_pos = chunk_text.rfind(break_char)
                if break_pos > size * 0.7:  # Don't make chunks too small
                    chunk_text = chunk_text[:break_pos + len(break_char)]
                    break
        
        if chunk_text.strip():
            out.append(chunk_text)
        
        i += max(1, size - overlap)
    
    return out

def canonical_id_for(path: str, idx: int) -> str:
    """Generate stable canonical ID for deduplication across tiers"""
    # Use UUIDv5 with repo namespace for stability
    ns = uuid.uuid5(uuid.NAMESPACE_URL, "athena://repo")
    return str(uuid.uuid5(ns, f"{path}:{idx}"))

def get_embeddings(texts: List[str], tier: str) -> List[List[float]]:
    """Get embeddings from embedding service"""
    embedding_url = os.getenv("EMBEDDING_SERVICE_URL", "http://localhost:8086")
    
    try:
        r = requests.post(
            f"{embedding_url}/embed",
            json={"texts": texts, "tier": tier},
            timeout=30
        )
        r.raise_for_status()
        return r.json()["vectors"]
    except Exception as e:
        print(f"⚠️  Embedding failed for tier {tier}: {e}")
        return []

def upsert(objs: List[Dict], class_name: str, tier: str) -> int:
    """Upsert batch of objects to Weaviate with embeddings"""
    if not objs:
        return 0
    
    # Extract texts for embedding
    texts = [obj["properties"]["text"] for obj in objs]
    
    # Get embeddings for this tier
    vectors = get_embeddings(texts, tier)
    
    if not vectors or len(vectors) != len(objs):
        print(f"⚠️  Embedding mismatch: expected {len(objs)}, got {len(vectors)}")
        return 0
    
    # Add vectors to objects
    for obj, vector in zip(objs, vectors):
        obj["vector"] = vector
    
    url = f"{WVV}/v1/batch/objects"
    payload = {"objects": objs}
    
    try:
        r = requests.post(url, json=payload, timeout=30)
        r.raise_for_status()
        return len(objs)
    except Exception as e:
        print(f"⚠️  Upsert failed for {class_name}: {e}")
        return 0

def make_obj(class_name: str, weaviate_id: str, props: Dict[str, Any]) -> Dict[str, Any]:
    """Create Weaviate object with proper structure"""
    return {
        "class": class_name,
        "id": weaviate_id,
        "properties": props
    }

def seed_file(path: pathlib.Path) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Seed a single file with all three granularities"""
    try:
        text = path.read_text(errors="ignore")
    except Exception as e:
        print(f"⚠️  Failed to read {path}: {e}")
        return [], [], []
    
    if not text.strip():
        return [], [], []
    
    rel = str(path.relative_to(ROOT))
    mtime = path.stat().st_mtime
    lang = path.suffix.lstrip(".") or "txt"
    
    # Three granularities
    coarse = chunk(text, size=800, overlap=120)  # For ChunkMini
    fine = chunk(text, size=350, overlap=120)     # For ChunkBase (Docs)
    ultra = chunk(text, size=220, overlap=80)     # For ChunkLong
    
    def build_batch(chunks: List[str], granularity: str, class_name: str) -> List[Dict]:
        objs = []
        for i, c in enumerate(chunks):
            # Stable canonical ID for fusion/dedup
            canonical = canonical_id_for(rel, i)
            
            # Weaviate object ID must be valid UUIDv4
            weaviate_id = str(uuid.uuid4())
            
            props = {
                "canonical_id": canonical,
                "repo_path": rel,
                "file": path.name,
                "symbol": "",
                "section": f"chunk_{i}",
                "granularity": granularity,
                "lang": lang,
                "text": c,
                "commit": os.getenv("GIT_COMMIT", ""),
                "source_mtime": int(mtime)
            }
            
            objs.append(make_obj(class_name, weaviate_id, props))
        
        return objs
    
    return (
        build_batch(coarse, "coarse", "ChunkMini"),
        build_batch(fine, "fine", "Docs"),  # Use existing Docs class as ChunkBase
        build_batch(ultra, "ultra_fine", "ChunkLong")
    )

def main():
    """Main seeding function"""
    print("=" * 80)
    print("  🧠 Dynamic RAG Seeder - Multi-Tier with UUID Support")
    print("=" * 80)
    print(f"Root: {ROOT}")
    print(f"Weaviate: {WVV}")
    print(f"Batch size: {BATCH}")
    print()
    
    buf_mini, buf_base, buf_long = [], [], []
    total_files = 0
    total_mini = 0
    total_base = 0
    total_long = 0
    
    start_time = time.time()
    
    for f in iter_files():
        m, b, l = seed_file(f)
        
        buf_mini += m
        buf_base += b
        buf_long += l
        
        total_files += 1
        
        # Flush batches when they reach the limit
        if len(buf_mini) >= BATCH:
            count = upsert(buf_mini, "ChunkMini", "mini")
            total_mini += count
            buf_mini.clear()
        
        if len(buf_base) >= BATCH:
            count = upsert(buf_base, "Docs", "base")
            total_base += count
            buf_base.clear()
        
        if len(buf_long) >= BATCH:
            count = upsert(buf_long, "ChunkLong", "long")
            total_long += count
            buf_long.clear()
        
        # Progress indicator
        if total_files % 10 == 0:
            print(f"  Processed {total_files} files...")
    
    # Flush remaining buffers
    if buf_mini:
        total_mini += upsert(buf_mini, "ChunkMini", "mini")
    if buf_base:
        total_base += upsert(buf_base, "Docs", "base")
    if buf_long:
        total_long += upsert(buf_long, "ChunkLong", "long")
    
    elapsed = time.time() - start_time
    
    print()
    print("=" * 80)
    print("✅ Dynamic seeding complete!")
    print(f"   Files processed: {total_files}")
    print(f"   ChunkMini (coarse): {total_mini} chunks")
    print(f"   ChunkBase (fine): {total_base} chunks")
    print(f"   ChunkLong (ultra-fine): {total_long} chunks")
    print(f"   Total chunks: {total_mini + total_base + total_long}")
    print(f"   Time: {elapsed:.1f}s")
    print()
    print("Verify:")
    print("  curl -s 'http://localhost:8090/v1/objects?class=ChunkMini&limit=1' | jq .")
    print("  curl -s 'http://localhost:8090/v1/objects?class=ChunkLong&limit=1' | jq .")
    print()
    print("Test query:")
    print('  curl -X POST http://localhost:8087/query \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"query":"Where is the planner wired?","top_k":6}\' | jq .')
    print("=" * 80)

if __name__ == "__main__":
    main()

