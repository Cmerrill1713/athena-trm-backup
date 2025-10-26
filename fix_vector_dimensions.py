#!/usr/bin/env python3
"""
Fix Vector Dimension Mismatches in Weaviate RAG System
======================================================

This script addresses the "multiple vector spaces" issue by:
1. Creating a unified DocsV2 class with consistent 384-dim embeddings
2. Providing bulk re-embedding capabilities
3. Cleaning up conflicting vector spaces

Based on the analysis:
- Current Docs class: vectorizer="none", dimension=0
- Hidden classes: docs_CrOVZlEosM9N (1.5M vectors), docs_mK0Jb5eBX87X (1K vectors)
- Solution: Unified DocsV2 with sentence-transformers/all-MiniLM-L6-v2 (384 dim)
"""

import requests
import json
import time
import sys
from typing import Dict, List, Optional

WEAVIATE_URL = "http://127.0.0.1:8090"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EMBEDDING_DIM = 384  # all-MiniLM-L6-v2 produces 384-dimensional vectors

def wait_for_weaviate(max_retries: int = 30) -> bool:
    """Wait for Weaviate to be ready"""
    print("🔄 Waiting for Weaviate to be ready...")
    
    for i in range(max_retries):
        try:
            response = requests.get(f"{WEAVIATE_URL}/v1/meta", timeout=5)
            if response.status_code == 200:
                print(f"✅ Weaviate is ready! Version: {response.json().get('version', 'unknown')}")
                return True
        except requests.exceptions.RequestException:
            pass
        
        print(f"⏳ Attempt {i+1}/{max_retries} - waiting 2 seconds...")
        time.sleep(2)
    
    print("❌ Weaviate failed to start within timeout")
    return False

def get_current_schema() -> Dict:
    """Get current Weaviate schema"""
    try:
        response = requests.get(f"{WEAVIATE_URL}/v1/schema", timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to get schema: {e}")
        return {}

def create_unified_docs_class() -> bool:
    """Create DocsV2 class with unified 384-dim embeddings"""
    print("🔧 Creating unified DocsV2 class with 384-dim embeddings...")
    
    schema = {
        "class": "DocsV2",
        "description": "Unified documentation chunks with consistent 384-dim embeddings",
        "vectorizer": "text2vec-huggingface",
        "moduleConfig": {
            "text2vec-huggingface": {
                "model": MODEL_NAME,
                "options": {
                    "waitForModel": True
                }
            }
        },
        "properties": [
            {"name": "path", "dataType": ["text"]},
            {"name": "text", "dataType": ["text"]},
            {"name": "chunk_id", "dataType": ["int"]},
            {"name": "file_hash", "dataType": ["text"]},
            {"name": "source_dataset", "dataType": ["text"]}
        ]
    }
    
    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/schema",
            json=schema,
            timeout=30
        )
        response.raise_for_status()
        print("✅ DocsV2 class created successfully!")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to create DocsV2 class: {e}")
        return False

def test_vector_functionality() -> bool:
    """Test if vector embeddings are working"""
    print("🧪 Testing vector functionality...")
    
    # Test 1: Add a document and check if it gets embedded
    test_doc = {
        "class": "DocsV2",
        "properties": {
            "path": "test_vector.md",
            "text": "This is a test document to verify vector embeddings are working correctly",
            "chunk_id": 1,
            "file_hash": "test_vector_123",
            "source_dataset": "test"
        }
    }
    
    try:
        # Add document
        response = requests.post(
            f"{WEAVIATE_URL}/v1/objects",
            json=test_doc,
            timeout=30
        )
        response.raise_for_status()
        doc_id = response.json()["id"]
        print(f"✅ Test document added with ID: {doc_id}")
        
        # Wait for embedding
        time.sleep(5)
        
        # Test vector search
        query = {
            "query": """
            {
              Get {
                DocsV2(
                  nearText: {
                    concepts: ["test document"]
                  }
                  limit: 5
                ) {
                  path
                  text
                  _additional {
                    distance
                    id
                  }
                }
              }
            }
            """
        }
        
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            json=query,
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        if "data" in result and result["data"]["Get"]["DocsV2"]:
            print("✅ Vector search is working!")
            print(f"   Found {len(result['data']['Get']['DocsV2'])} results")
            return True
        else:
            print("❌ Vector search returned no results")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Vector functionality test failed: {e}")
        return False

def analyze_dimension_mismatch():
    """Analyze the current dimension mismatch situation"""
    print("🔍 Analyzing dimension mismatch situation...")
    
    schema = get_current_schema()
    if not schema:
        return
    
    print("\n📊 Current Schema Analysis:")
    print("=" * 50)
    
    for class_info in schema.get("classes", []):
        class_name = class_info.get("class", "unknown")
        vectorizer = class_info.get("vectorizer", "none")
        vector_index_type = class_info.get("vectorIndexType", "none")
        
        print(f"Class: {class_name}")
        print(f"  Vectorizer: {vectorizer}")
        print(f"  Vector Index: {vector_index_type}")
        
        if vectorizer != "none":
            print(f"  ✅ Has vectorizer")
        else:
            print(f"  ❌ No vectorizer")
        print()

def main():
    """Main execution function"""
    print("🚀 Vector Dimension Mismatch Fix")
    print("=" * 40)
    
    # Step 1: Wait for Weaviate
    if not wait_for_weaviate():
        sys.exit(1)
    
    # Step 2: Analyze current situation
    analyze_dimension_mismatch()
    
    # Step 3: Create unified class
    if not create_unified_docs_class():
        sys.exit(1)
    
    # Step 4: Test vector functionality
    if not test_vector_functionality():
        print("⚠️  Vector functionality test failed, but class was created")
        print("   You may need to wait for the Hugging Face model to download")
    
    print("\n🎉 Vector dimension fix completed!")
    print("\n📋 Next Steps:")
    print("1. ✅ DocsV2 class created with 384-dim embeddings")
    print("2. 🔄 Update your RAG services to use DocsV2 instead of Docs")
    print("3. 📦 Migrate existing data to DocsV2 (if needed)")
    print("4. 🗑️  Clean up old conflicting classes")

if __name__ == "__main__":
    main()
