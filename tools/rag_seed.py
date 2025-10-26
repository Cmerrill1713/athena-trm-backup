#!/usr/bin/env python3
"""
RAG Seeder - Fast repo → chunks → embeddings → Weaviate

Walks the repo, chunks files, generates embeddings, and upserts to Weaviate.
Uses the RAG Gateway for embeddings and Weaviate for storage.
"""

import os
import glob
import json
import hashlib
import time
import uuid
import requests
from pathlib import Path

# Config
WEAVIATE_URL = os.environ.get("WEAVIATE_URL", "http://localhost:8090")
GATEWAY_URL = os.environ.get("RAG_GATEWAY_URL", "http://localhost:8087")
ROOT = os.environ.get("SEED_ROOT", "/Users/christianmerrill/Documents/GitHub")
MAX_BYTES = int(os.environ.get("SEED_MAX_BYTES", "400000"))
GLOBS = os.environ.get("SEED_GLOBS", "**/*.py,**/*.md,**/*.swift,**/*.sh,**/*.yml,**/*.yaml").split(",")
CHUNK_SIZE = int(os.environ.get("CHUNK_SIZE", "1200"))
CHUNK_OVERLAP = int(os.environ.get("CHUNK_OVERLAP", "200"))

# Exclusions
EXCLUDE_DIRS = {'.git', 'node_modules', '__pycache__', '.venv', 'venv', 'build', 'dist', 'DerivedData'}
EXCLUDE_PATTERNS = {'.DS_Store', '.pyc', '.o', '.a', '.so', '.dylib'}

# State file for incremental updates
STATE_FILE = os.path.join(ROOT, ".rag_seed_state.json")

def chunks(s, n=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """Split text into overlapping chunks"""
    i = 0
    L = len(s)
    while i < L:
        yield s[i:i+n]
        i += (n - overlap)

def embed(text):
    """Get embedding vector from RAG Gateway"""
    try:
        r = requests.post(f"{GATEWAY_URL}/embed", json={"texts": [text]}, timeout=10)
        r.raise_for_status()
        return r.json()["vectors"][0]
    except Exception as e:
        print(f"⚠️  Embed failed: {e}")
        # Return None to skip this chunk
        return None

def upsert(doc_id, text, vector, path):
    """Upsert document to Weaviate"""
    payload = {
        "class": "Docs",
        "id": doc_id,
        "properties": {
            "text": text,
            "path": str(path),
            "ts": int(time.time())
        },
        "vector": vector
    }
    
    try:
        r = requests.post(f"{WEAVIATE_URL}/v1/objects", json=payload, timeout=10)
        # Tolerate duplicates (409) and treat as success
        if r.status_code not in (200, 201, 409):
            print(f"⚠️  Upsert warn {r.status_code}: {r.text[:200]}")
            return False
        return True
    except Exception as e:
        print(f"⚠️  Upsert error: {e}")
        return False

def ensure_schema():
    """Create Docs class in Weaviate if it doesn't exist"""
    try:
        schema = requests.get(f"{WEAVIATE_URL}/v1/schema", timeout=5).json()
        if any(c.get("class") == "Docs" for c in schema.get("classes", [])):
            print("✅ Schema 'Docs' already exists")
            return
        
        # Create new class
        r = requests.post(f"{WEAVIATE_URL}/v1/schema", json={
            "class": "Docs",
            "vectorizer": "none",  # We supply vectors manually
            "properties": [
                {"name": "text", "dataType": ["text"]},
                {"name": "path", "dataType": ["text"]},
                {"name": "ts", "dataType": ["number"]}
            ]
        }, timeout=10)
        r.raise_for_status()
        print("✅ Created schema 'Docs'")
    except Exception as e:
        print(f"❌ Schema check failed: {e}")
        raise

def load_state():
    """Load previous seeding state for incremental updates"""
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, 'r') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(state):
    """Save seeding state"""
    try:
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        print(f"⚠️  Could not save state: {e}")

def should_process_file(path, state):
    """Check if file needs processing based on mtime"""
    path_str = str(path)
    current_mtime = path.stat().st_mtime
    
    if path_str not in state:
        return True
    
    return current_mtime > state[path_str].get("mtime", 0)

def main():
    """Seed Weaviate with chunks from the repo"""
    print("════════════════════════════════════════════════════════════════")
    print("  📚 RAG Seeder - Ingesting Repo Docs (Incremental)")
    print("════════════════════════════════════════════════════════════════")
    print(f"Root: {ROOT}")
    print(f"Weaviate: {WEAVIATE_URL}")
    print(f"Gateway: {GATEWAY_URL}")
    print(f"Globs: {GLOBS}")
    print(f"Excludes: {EXCLUDE_DIRS}")
    print("")
    
    # Load previous state for incremental updates
    state = load_state()
    print(f"Loaded state: {len(state)} files previously processed")
    print("")
    
    # Ensure schema exists
    ensure_schema()
    print("")
    
    count = 0
    skipped = 0
    errors = 0
    unchanged = 0
    
    for pattern in GLOBS:
        pattern = pattern.strip()
        for path_str in glob.glob(os.path.join(ROOT, pattern), recursive=True):
            path = Path(path_str)
            
            # Skip directories, hidden files, excluded dirs, large files
            if path.is_dir():
                continue
            if path.name.startswith('.'):
                continue
            if any(excluded in path.parts for excluded in EXCLUDE_DIRS):
                continue
            if any(path.name.endswith(pattern) for pattern in EXCLUDE_PATTERNS):
                continue
            if path.stat().st_size > MAX_BYTES:
                skipped += 1
                continue
            
            # Check if file changed since last seed (incremental update)
            if not should_process_file(path, state):
                unchanged += 1
                continue
            
            # Read file
            try:
                with open(path, "r", errors="ignore") as f:
                    data = f.read()
            except Exception as e:
                errors += 1
                continue
            
            # Chunk and upsert
            for i, chunk_text in enumerate(chunks(data)):
                if len(chunk_text.strip()) < 50:
                    continue  # Skip tiny chunks
                
                # Generate deterministic UUID from path + chunk index
                hash_str = hashlib.sha1(f"{path}:{i}".encode()).hexdigest()
                # Convert first 32 hex chars to UUID format
                doc_id = str(uuid.UUID(hash_str[:32]))
                
                # Get embedding
                vector = embed(chunk_text)
                if vector is None:
                    errors += 1
                    continue
                
                # Upsert to Weaviate
                if upsert(doc_id, chunk_text, vector, path):
                    count += 1
                    if count % 10 == 0:
                        print(f"  Seeded {count} chunks...")
                else:
                    errors += 1
            
            # Update state for this file
            state[str(path)] = {
                "mtime": path.stat().st_mtime,
                "chunks": count,
                "last_seed": int(time.time())
            }
    
    # Save state for next run
    save_state(state)
    
    print("")
    print("════════════════════════════════════════════════════════════════")
    print(f"✅ Seeding complete!")
    print(f"   Chunks inserted: {count}")
    print(f"   Files unchanged: {unchanged} (skipped - already seeded)")
    print(f"   Files skipped:   {skipped} (too large)")
    print(f"   Errors:          {errors}")
    print(f"   State saved:     {STATE_FILE}")
    print("")
    print("Verify:")
    print(f"  curl -s '{WEAVIATE_URL}/v1/objects?class=Docs&limit=1' | jq .")
    print("")
    print("Re-run anytime for incremental updates (only processes changed files)")
    print("════════════════════════════════════════════════════════════════")

if __name__ == "__main__":
    main()

