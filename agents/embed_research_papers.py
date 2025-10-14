#!/usr/bin/env python3
"""
Embed Research Papers for RAG
==============================
Embeds generated research implementations and their descriptions into vector DB
"""

import asyncio
from pathlib import Path
from typing import List
import httpx


class ResearchPaperEmbedder:
    """Embeds research papers into vector DB for RAG retrieval"""
    
    def __init__(self, qdrant_host: str = "http://localhost:6333"):
        self.qdrant_host = qdrant_host
        self.collection_name = "research_papers"
        self.embedding_model = "ollama:qwen3-embedding:4b"  # Your local model
        
    async def create_collection(self):
        """Create Qdrant collection for research papers"""
        async with httpx.AsyncClient() as client:
            try:
                response = await client.put(
                    f"{self.qdrant_host}/collections/{self.collection_name}",
                    json={
                        "vectors": {
                            "size": 768,  # qwen3-embedding dimension
                            "distance": "Cosine"
                        }
                    }
                )
                print(f"✅ Collection created: {response.status_code}")
            except Exception as e:
                print(f"⚠️  Collection may already exist: {e}")
    
    async def get_embedding(self, text: str) -> List[float]:
        """Get embedding from Ollama"""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "http://localhost:11434/api/embeddings",
                json={
                    "model": "qwen3-embedding",
                    "prompt": text
                }
            )
            data = response.json()
            return data["embedding"]
    
    async def embed_implementation(self, file_path: Path):
        """Embed a single implementation file"""
        
        # Read implementation
        with open(file_path, 'r') as f:
            code = f.read()
        
        # Extract docstring/description
        description = ""
        if '"""' in code:
            parts = code.split('"""')
            if len(parts) >= 3:
                description = parts[1].strip()
        
        # Create embedding payload
        text_to_embed = f"{file_path.stem}\n\n{description}\n\n{code[:500]}"
        
        print(f"📝 Embedding: {file_path.stem}")
        embedding = await self.get_embedding(text_to_embed)
        
        # Store in Qdrant
        async with httpx.AsyncClient() as client:
            response = await client.put(
                f"{self.qdrant_host}/collections/{self.collection_name}/points",
                json={
                    "points": [{
                        "id": hash(file_path.stem) & 0x7FFFFFFF,  # Positive int ID
                        "vector": embedding,
                        "payload": {
                            "filename": file_path.name,
                            "module": file_path.stem,
                            "description": description[:500],
                            "code_snippet": code[:1000],
                            "path": str(file_path),
                            "type": "research_implementation"
                        }
                    }]
                }
            )
            
            if response.status_code in [200, 201]:
                print(f"✅ Embedded: {file_path.stem}")
            else:
                print(f"❌ Failed: {file_path.stem} - {response.text}")
    
    async def embed_all_implementations(self):
        """Embed all research implementations"""
        providers_dir = Path("orchestrator/providers")
        
        # Find all Python files (excluding __init__ and stub)
        implementations = [
            f for f in providers_dir.glob("*.py")
            if f.stem not in ["__init__", "capability_stub", "registry"]
        ]
        
        print(f"📚 Found {len(implementations)} implementations to embed")
        
        # Create collection
        await self.create_collection()
        
        # Embed each implementation
        for impl_file in implementations:
            try:
                await self.embed_implementation(impl_file)
            except Exception as e:
                print(f"❌ Error embedding {impl_file.stem}: {e}")
        
        print(f"\n✅ Embedded {len(implementations)} research implementations!")
    
    async def test_retrieval(self, query: str):
        """Test retrieving similar implementations"""
        print(f"\n🔍 Testing retrieval for: '{query}'")
        
        # Get query embedding
        embedding = await self.get_embedding(query)
        
        # Search Qdrant
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.qdrant_host}/collections/{self.collection_name}/points/search",
                json={
                    "vector": embedding,
                    "limit": 3,
                    "with_payload": True
                }
            )
            
            results = response.json()
            
            if "result" in results:
                print("\n📊 Top matches:")
                for i, match in enumerate(results["result"], 1):
                    print(f"\n{i}. {match['payload']['module']} (score: {match['score']:.3f})")
                    print(f"   {match['payload']['description'][:100]}...")
            else:
                print("No results found")


async def main():
    print("=" * 80)
    print("🔬 RESEARCH PAPER EMBEDDING FOR RAG")
    print("=" * 80)
    
    embedder = ResearchPaperEmbedder()
    
    # Embed all implementations
    await embedder.embed_all_implementations()
    
    # Test retrieval
    await embedder.test_retrieval("How can I do contextual decision making?")
    await embedder.test_retrieval("Optimize prompts based on performance")
    
    print("\n" + "=" * 80)
    print("✅ Research papers embedded and ready for RAG!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())

