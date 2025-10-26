#!/usr/bin/env python3
"""
Ingest Prompt Library into Weaviate DocsV2
Loads prompt_library.md and agent_capabilities.md into the knowledge base
"""

import os
import sys
import requests
from pathlib import Path

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
EMBEDDING_SERVICE = os.getenv("EMBEDDING_SERVICE", "http://localhost:8086")
KB_FILES = [
    "knowledge_base/prompt_library.md",
    "knowledge_base/agent_capabilities.md"
]

def get_embedding(text: str) -> list:
    """Get 768-dim embedding from embedding service"""
    try:
        # API expects {"texts": ["text1", "text2"]} and returns {"embeddings": [[...]]}
        response = requests.post(
            f"{EMBEDDING_SERVICE}/embed",
            json={"texts": [text[:8000]]},  # Limit text length
            timeout=30
        )
        
        response.raise_for_status()
        data = response.json()
        
        # Get first embedding from the list
        # The API returns {"vectors": [[...]], "count": 1, "dimension": 768}
        vectors = data.get("vectors", data.get("embeddings", []))
        if vectors and len(vectors) > 0:
            return vectors[0]
        
        print(f"⚠️  No vectors in response: {list(data.keys())}")
        return None
        
    except Exception as e:
        print(f"❌ Embedding error: {e}")
        return None

def chunk_document(content: str, filename: str, chunk_size: int = 1000) -> list:
    """Split document into chunks for ingestion"""
    # Split by ## headers for better semantic chunks
    sections = content.split('\n## ')
    chunks = []
    
    for i, section in enumerate(sections):
        # Add header back if not first section
        if i > 0:
            section = '## ' + section
        
        # If section is too large, split by paragraphs
        if len(section) > chunk_size:
            paragraphs = section.split('\n\n')
            current_chunk = ""
            
            for para in paragraphs:
                if len(current_chunk) + len(para) < chunk_size:
                    current_chunk += para + "\n\n"
                else:
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = para + "\n\n"
            
            if current_chunk:
                chunks.append(current_chunk.strip())
        else:
            chunks.append(section.strip())
    
    # Create chunk objects with metadata
    chunk_objects = []
    for i, chunk_text in enumerate(chunks):
        # Extract title from chunk if possible
        lines = chunk_text.split('\n')
        title = lines[0].strip('#').strip() if lines else f"{filename} - Part {i+1}"
        
        chunk_objects.append({
            "title": title,
            "content": chunk_text,
            "source": filename,
            "chunk_index": i,
            "doc_type": "reference"
        })
    
    return chunk_objects

def ingest_to_weaviate(chunk_obj: dict) -> bool:
    """Ingest a single chunk into Weaviate DocsV2"""
    try:
        # Get embedding
        vector = get_embedding(chunk_obj["content"])
        if not vector:
            return False
        
        # Prepare object for Weaviate
        doc_object = {
            "class": "DocsV2",
            "properties": {
                "title": chunk_obj["title"],
                "content": chunk_obj["content"],
                "source": chunk_obj["source"],
                "url": f"file://knowledge_base/{chunk_obj['source']}",
                "doc_type": chunk_obj["doc_type"],
                "chunk_index": chunk_obj["chunk_index"]
            },
            "vector": vector
        }
        
        # Insert into Weaviate
        response = requests.post(
            f"{WEAVIATE_URL}/v1/objects",
            json=doc_object,
            timeout=10
        )
        
        if response.status_code in [200, 201]:
            return True
        else:
            print(f"⚠️  Weaviate returned {response.status_code}: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Ingestion error: {e}")
        return False

def main():
    print("🎨 PROMPT LIBRARY INGESTION")
    print("=" * 60)
    
    total_chunks = 0
    successful = 0
    failed = 0
    
    for kb_file in KB_FILES:
        file_path = Path(kb_file)
        
        if not file_path.exists():
            print(f"⚠️  File not found: {kb_file}")
            continue
        
        print(f"\n📄 Processing: {kb_file}")
        
        # Read file
        content = file_path.read_text()
        
        # Chunk it
        chunks = chunk_document(content, file_path.name)
        print(f"   Created {len(chunks)} chunks")
        
        # Ingest each chunk
        for i, chunk in enumerate(chunks, 1):
            print(f"   Ingesting chunk {i}/{len(chunks)}: {chunk['title'][:50]}...", end=" ")
            
            if ingest_to_weaviate(chunk):
                print("✅")
                successful += 1
            else:
                print("❌")
                failed += 1
            
            total_chunks += 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"📊 INGESTION SUMMARY:")
    print(f"   Total chunks: {total_chunks}")
    print(f"   ✅ Successful: {successful}")
    print(f"   ❌ Failed: {failed}")
    print(f"   Success rate: {(successful/total_chunks*100) if total_chunks > 0 else 0:.1f}%")
    
    if successful > 0:
        print(f"\n🎉 Prompt library loaded into DocsV2!")
        print(f"   Athena can now access {successful} knowledge chunks")
        print(f"   Try: 'Search the prompt library for chain-of-thought examples'")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())

