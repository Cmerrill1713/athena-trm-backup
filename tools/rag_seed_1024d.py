#!/usr/bin/env python3
"""
RAG Seeder with 1024d embeddings (LONG tier - mxbai-embed-large)
Seeds the entire AGI codebase into Weaviate
"""
import os
import sys
import time
import json
import hashlib
import requests
from pathlib import Path
from typing import List, Dict

WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
OLLAMA_URL = os.getenv("OLLAMA_ENDPOINT", "http://localhost:11434")
SEED_ROOT = Path(os.getenv("SEED_ROOT", "/Users/christianmerrill/Documents/GitHub/agi_core"))
BATCH_SIZE = 10
CHUNK_SIZE = 600
CHUNK_OVERLAP = 100

# File extensions to include
INCLUDE_EXTS = {".py", ".md", ".sh", ".yml", ".yaml", ".json", ".txt"}
IGNORE_DIRS = {".git", "node_modules", "__pycache__", ".venv", "venv", "build", "dist", ".pytest_cache"}

print(f"🚀 RAG Seeder (1024d embeddings)")
print(f"   Weaviate: {WEAVIATE_URL}")
print(f"   Ollama: {OLLAMA_URL}")
print(f"   Seed root: {SEED_ROOT}")
print()

def create_schema():
    """Create Docs class with 1024d vectors"""
    print("📋 Creating Weaviate schema (1024d)...")
    
    schema = {
        "class": "Docs",
        "description": "Documentation chunks with 1024d embeddings",
        "vectorizer": "none",  # We provide vectors manually
        "properties": [
            {"name": "path", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "chunk_id", "dataType": ["int"]},
            {"name": "file_hash", "dataType": ["text"]},
        ]
    }
    
    try:
        # Delete if exists
        try:
            requests.delete(f"{WEAVIATE_URL}/v1/schema/Docs", timeout=30)
        except:
            pass
        
        # Create schema
        resp = requests.post(f"{WEAVIATE_URL}/v1/schema", json=schema, timeout=30)
        resp.raise_for_status()
        print("✅ Schema created")
    except Exception as e:
        print(f"❌ Schema creation failed: {e}")
        sys.exit(1)

def chunk_text(text: str) -> List[str]:
    """Chunk text into overlapping segments"""
    chunks = []
    i = 0
    while i < len(text):
        end = i + CHUNK_SIZE
        chunk = text[i:end]
        if chunk.strip():
            chunks.append(chunk)
        i += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks if chunks else [text[:CHUNK_SIZE]]

def get_embeddings(texts: List[str]) -> List[List[float]]:
    """Get 1024d embeddings from Ollama (mxbai-embed-large)"""
    embeddings = []
    
    for text in texts:
        try:
            resp = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": "mxbai-embed-large", "prompt": text[:2000]},  # Truncate to 2K chars
                timeout=60
            )
            resp.raise_for_status()
            data = resp.json()
            embedding = data.get("embedding", [])
            
            if len(embedding) == 1024:
                embeddings.append(embedding)
            else:
                print(f"⚠️  Got {len(embedding)}d embedding, expected 1024d")
                embeddings.append([0.0] * 1024)  # Zero vector as fallback
                
        except Exception as e:
            print(f"❌ Embedding failed: {e}")
            embeddings.append([0.0] * 1024)
    
    return embeddings

def seed_file(file_path: Path):
    """Seed a single file"""
    try:
        text = file_path.read_text(errors="ignore")
        if not text.strip():
            return 0
        
        chunks = chunk_text(text)
        rel_path = str(file_path.relative_to(SEED_ROOT.parent))
        file_hash = hashlib.sha256(text.encode()).hexdigest()[:16]
        
        # Get embeddings for all chunks
        embeddings = get_embeddings(chunks)
        
        # Batch insert
        objects = []
        for idx, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            objects.append({
                "class": "Docs",
                "properties": {
                    "path": rel_path,
                    "text": chunk,
                    "chunk_id": idx,
                    "file_hash": file_hash,
                },
                "vector": embedding
            })
        
        # Insert batch
        resp = requests.post(
            f"{WEAVIATE_URL}/v1/batch/objects",
            json={"objects": objects},
            timeout=60
        )
        resp.raise_for_status()
        
        return len(chunks)
        
    except Exception as e:
        print(f"❌ Failed to seed {file_path}: {e}")
        return 0

def main():
    create_schema()
    
    print(f"📁 Scanning {SEED_ROOT}...")
    files = []
    for file_path in SEED_ROOT.rglob("*"):
        if file_path.is_file() and file_path.suffix in INCLUDE_EXTS:
            if not any(ig in file_path.parts for ig in IGNORE_DIRS):
                files.append(file_path)
    
    print(f"📝 Found {len(files)} files to seed")
    print()
    
    total_chunks = 0
    start = time.time()
    
    for idx, file_path in enumerate(files, 1):
        chunks = seed_file(file_path)
        total_chunks += chunks
        
        if idx % 10 == 0:
            elapsed = time.time() - start
            rate = idx / elapsed if elapsed > 0 else 0
            eta = (len(files) - idx) / rate if rate > 0 else 0
            print(f"Progress: {idx}/{len(files)} files, {total_chunks} chunks, {rate:.1f} files/s, ETA: {eta/60:.1f}min")
    
    elapsed = time.time() - start
    print()
    print(f"✅ Seeding complete!")
    print(f"   Files: {len(files)}")
    print(f"   Chunks: {total_chunks}")
    print(f"   Time: {elapsed/60:.1f} minutes")
    print(f"   Rate: {len(files)/elapsed:.1f} files/s")

if __name__ == "__main__":
    main()

