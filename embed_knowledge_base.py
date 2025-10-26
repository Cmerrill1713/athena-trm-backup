#!/usr/bin/env python3
"""
Embed knowledge_base/ into Weaviate for semantic search
"""
import json
import requests
from pathlib import Path
from typing import List, Dict
import time

WEAVIATE_URL = "http://localhost:8090"
OLLAMA_URL = "http://localhost:11434"

def get_embedding(text: str, max_retries: int = 3) -> List[float]:
    """Get text embedding from Ollama with retry logic"""
    for attempt in range(max_retries):
        try:
            response = requests.post(
                f"{OLLAMA_URL}/api/embeddings",
                json={"model": "nomic-embed-text", "prompt": text[:2000]},  # Limit to 2000 chars
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            if "embedding" not in data:
                print(f"    ⚠️  Unexpected response: {data}")
                time.sleep(1)
                continue
            return data["embedding"]
        except Exception as e:
            print(f"    ⚠️  Attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2)
            else:
                raise
    raise Exception("Failed to get embedding after retries")


def chunk_document(content: str, chunk_size: int = 300) -> List[str]:
    """Split document into smaller chunks (words)"""
    words = content.split()
    chunks = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i + chunk_size])
        if chunk.strip():  # Only add non-empty chunks
            chunks.append(chunk)
    return chunks


def embed_knowledge_base():
    """Embed all markdown files into Weaviate"""
    kb_path = Path("knowledge_base")
    
    print("🚀 Embedding Knowledge Base")
    print("=" * 50)
    
    # Check Ollama has embedding model
    print("\n1️⃣ Checking for embedding model...")
    try:
        test_embedding = get_embedding("test")
        print(f"✅ Embedding model working (dimension: {len(test_embedding)})")
    except Exception as e:
        print(f"❌ Error: {e}")
        return
    
    # Process each markdown file
    print("\n2️⃣ Processing documents...")
    total_chunks = 0
    
    for md_file in sorted(kb_path.glob("**/*.md")):
        print(f"\n📄 {md_file.name}")
        try:
            content = md_file.read_text()
            chunks = chunk_document(content)
            print(f"   {len(chunks)} chunks")
            
            for i, chunk in enumerate(chunks):
                # Get embedding
                embedding = get_embedding(chunk)
                
                # Create object in Weaviate
                obj = {
                    "class": "DocsV2",
                    "properties": {
                        "source": md_file.name,
                        "content": chunk,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    },
                    "vector": embedding
                }
                
                # Upload to Weaviate
                response = requests.post(
                    f"{WEAVIATE_URL}/v1/objects",
                    json=obj
                )
                
                if response.status_code == 200:
                    print(f"  ✅ Chunk {i+1}/{len(chunks)}", end="\r")
                    total_chunks += 1
                else:
                    print(f"  ❌ Failed: {response.text}")
                
                time.sleep(0.1)  # Rate limiting
            
            print(f"  ✅ Completed {len(chunks)} chunks")
            
        except Exception as e:
            print(f"  ❌ Error processing {md_file.name}: {e}")
            continue
    
    print(f"\n✅ Embedded {total_chunks} chunks from {len(list(kb_path.glob('**/*.md')))} documents")
    
    # Verify
    print("\n3️⃣ Verifying...")
    response = requests.get(f"{WEAVIATE_URL}/v1/objects")
    count = len(response.json()["objects"])
    print(f"✅ Weaviate now has {count} objects")


def test_semantic_search(query: str):
    """Test semantic search"""
    print(f"\n🔍 Testing: '{query}'")
    
    # Get query embedding
    query_embedding = get_embedding(query)
    
    # Search Weaviate using nearVector
    gql_query = {
        "query": """
        {
          Get {
            DocsV2(
              nearVector: {
                vector: %s
              }
              limit: 3
            ) {
              source
              content
              _additional {
                distance
              }
            }
          }
        }
        """ % json.dumps(query_embedding)
    }
    
    response = requests.post(
        f"{WEAVIATE_URL}/v1/graphql",
        json=gql_query
    )
    
    if response.status_code != 200:
        print(f"❌ Search failed: {response.text}")
        return
    
    results = response.json()["data"]["Get"]["DocsV2"]
    
    print("\nResults:")
    for i, result in enumerate(results, 1):
        distance = result["_additional"]["distance"]
        similarity = 1 - distance
        print(f"\n{i}. {result['source']} (similarity: {similarity:.2%})")
        print(f"   {result['content'][:150]}...")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        if len(sys.argv) > 2:
            test_semantic_search(" ".join(sys.argv[2:]))
        else:
            test_semantic_search("What are tiny AI models?")
    else:
        embed_knowledge_base()
        print("\n" + "="*50)
        print("🎉 Knowledge base is now embedded!")
        print("\nTest it with:")
        print("  python3 embed_knowledge_base.py test 'What are tiny AI models?'")
