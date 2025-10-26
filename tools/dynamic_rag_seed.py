#!/usr/bin/env python3
"""
Dynamic RAG Seeder - Multi-Granularity Chunking
Generates coarse, fine, and ultra-fine chunks for different query complexities
"""

import asyncio
import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration
WEAVIATE_URL = os.getenv("WEAVIATE_URL", "http://localhost:8090")
RAG_GATEWAY_URL = os.getenv("RAG_GATEWAY_URL", "http://localhost:8087")
SEED_ROOT = os.getenv("SEED_ROOT", "/Users/christianmerrill/Documents/GitHub/agi_core")
SEED_GLOBS = os.getenv("SEED_GLOBS", "**/*.py,**/*.md,**/*.swift,**/*.sh").split(",")

class ChunkGranularity(Enum):
    COARSE = "coarse"    # 600-800 chars, small overlap
    FINE = "fine"        # 400-600 chars, medium overlap  
    ULTRA_FINE = "ultra_fine"  # 200-400 chars, high overlap

@dataclass
class ChunkConfig:
    """Configuration for different chunk granularities"""
    size_range: Tuple[int, int]
    overlap_range: Tuple[int, int]
    max_chunks_per_file: int
    preserve_structure: bool

CHUNK_CONFIGS = {
    ChunkGranularity.COARSE: ChunkConfig(
        size_range=(600, 800),
        overlap_range=(50, 80),
        max_chunks_per_file=50,
        preserve_structure=False
    ),
    ChunkGranularity.FINE: ChunkConfig(
        size_range=(400, 600),
        overlap_range=(80, 120),
        max_chunks_per_file=100,
        preserve_structure=True
    ),
    ChunkGranularity.ULTRA_FINE: ChunkConfig(
        size_range=(200, 400),
        overlap_range=(100, 150),
        max_chunks_per_file=200,
        preserve_structure=True
    )
}

class DynamicRAGSeeder:
    def __init__(self):
        self.state_file = Path(SEED_ROOT) / ".dynamic_rag_seed_state.json"
        self.state = self.load_state()
        
    def load_state(self) -> Dict[str, Any]:
        """Load seeding state for incremental updates"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}")
        return {"files": {}, "last_run": 0}
    
    def save_state(self):
        """Save seeding state"""
        self.state["last_run"] = time.time()
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
    
    def should_process_file(self, file_path: Path) -> bool:
        """Check if file should be processed based on state"""
        file_stat = file_path.stat()
        file_key = str(file_path.relative_to(Path(SEED_ROOT)))
        
        # Check if file is new or modified
        if file_key not in self.state["files"]:
            return True
            
        last_mtime = self.state["files"][file_key].get("mtime", 0)
        return file_stat.st_mtime > last_mtime
    
    def get_file_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        lang_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.swift': 'swift',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.h': 'c',
            '.sh': 'bash',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        return lang_map.get(ext, 'unknown')
    
    def extract_code_structure(self, content: str, lang: str) -> List[Dict[str, Any]]:
        """Extract code structure (functions, classes, etc.)"""
        structures = []
        
        if lang == 'python':
            # Extract functions and classes
            func_pattern = r'^(?:async\s+)?def\s+(\w+)\s*\('
            class_pattern = r'^class\s+(\w+)'
            
            for match in re.finditer(func_pattern, content, re.MULTILINE):
                structures.append({
                    'type': 'function',
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
            
            for match in re.finditer(class_pattern, content, re.MULTILINE):
                structures.append({
                    'type': 'class',
                    'name': match.group(1),
                    'line': content[:match.start()].count('\n') + 1
                })
        
        return structures
    
    def create_chunks(self, content: str, file_path: Path, granularity: ChunkGranularity) -> List[Dict[str, Any]]:
        """Create chunks with specified granularity"""
        config = CHUNK_CONFIGS[granularity]
        lang = self.get_file_language(file_path)
        structures = self.extract_code_structure(content, lang)
        
        chunks = []
        lines = content.split('\n')
        
        # For ultra-fine granularity, try to preserve code structure
        if granularity == ChunkGranularity.ULTRA_FINE and structures:
            chunk_index = 0
            for structure in structures[:config.max_chunks_per_file]:
                start_line = max(0, structure['line'] - 1)
                end_line = min(len(lines), start_line + 20)  # ~20 lines per chunk
                
                chunk_lines = lines[start_line:end_line]
                chunk_text = '\n'.join(chunk_lines)
                
                if len(chunk_text) >= config.size_range[0]:
                    chunks.append({
                        'text': chunk_text,
                        'symbol': structure['name'],
                        'section': f"{structure['type']}:{structure['name']}",
                        'granularity': granularity.value,
                        'start_line': start_line + 1,
                        'end_line': end_line
                    })
                    chunk_index += 1
                    
            # Fill remaining chunks with sliding window
            remaining_chunks = config.max_chunks_per_file - len(chunks)
            if remaining_chunks > 0:
                chunks.extend(self._sliding_window_chunks(content, remaining_chunks, config))
        else:
            # Use sliding window approach for coarse and fine
            chunks = self._sliding_window_chunks(content, config.max_chunks_per_file, config)
        
        return chunks
    
    def _sliding_window_chunks(self, content: str, max_chunks: int, config: ChunkConfig) -> List[Dict[str, Any]]:
        """Create chunks using sliding window approach"""
        chunks = []
        content_len = len(content)
        
        if content_len == 0:
            return chunks
            
        # Calculate step size based on overlap
        avg_size = sum(config.size_range) // 2
        avg_overlap = sum(config.overlap_range) // 2
        step_size = max(1, avg_size - avg_overlap)
        
        start = 0
        chunk_index = 0
        
        while start < content_len and chunk_index < max_chunks:
            # Determine chunk size with some randomness
            size_variance = (config.size_range[1] - config.size_range[0]) // 4
            chunk_size = config.size_range[0] + (chunk_index % 4) * size_variance
            
            end = min(start + chunk_size, content_len)
            chunk_text = content[start:end]
            
            # Try to break at word/sentence boundaries
            if end < content_len:
                # Look for good break points
                for break_char in ['\n\n', '\n', '. ', '; ', '} ', ') ']:
                    break_pos = chunk_text.rfind(break_char)
                    if break_pos > chunk_size * 0.7:  # Don't make chunks too small
                        chunk_text = chunk_text[:break_pos + len(break_char)]
                        end = start + len(chunk_text)
                        break
            
            if len(chunk_text.strip()) >= config.size_range[0] // 2:  # Minimum viable chunk
                chunks.append({
                    'text': chunk_text.strip(),
                    'granularity': config.__class__.__name__.lower().replace('config', ''),
                    'start_pos': start,
                    'end_pos': end
                })
            
            start += step_size
            chunk_index += 1
        
        return chunks
    
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for texts"""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    f"{RAG_GATEWAY_URL}/embed",
                    json={"texts": texts}
                )
                response.raise_for_status()
                return response.json()["vectors"]
        except Exception as e:
            logger.warning(f"Embedding generation failed: {e}")
            # Fallback to hash-based embeddings
            return self._hash_embeddings(texts)
    
    def _hash_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate deterministic hash-based embeddings as fallback"""
        vectors = []
        for text in texts:
            hash_obj = hashlib.sha256(text.encode())
            hash_bytes = hash_obj.digest()
            
            vector = []
            for i in range(0, min(len(hash_bytes), 96), 4):
                chunk = hash_bytes[i:i+4]
                while len(chunk) < 4:
                    chunk += b'\x00'
                val = int.from_bytes(chunk, 'big') / (2**32)
                vector.append(val)
            
            while len(vector) < 768:
                vector.append(0.0)
            
            vectors.append(vector[:768])
        
        return vectors
    
    async def upsert_chunks(self, chunks: List[Dict[str, Any]], class_name: str) -> int:
        """Upsert chunks to Weaviate"""
        if not chunks:
            return 0
            
        try:
            # Generate embeddings
            texts = [chunk['text'] for chunk in chunks]
            vectors = await self.generate_embeddings(texts)
            
            # Prepare objects for upsert
            objects = []
            for chunk, vector in zip(chunks, vectors):
                # Generate canonical ID
                canonical_id = chunk.get('canonical_id', '')
                if not canonical_id:
                    canonical_id = hashlib.sha256(
                        f"{chunk.get('repo_path', '')}:{chunk.get('text', '')[:100]}".encode()
                    ).hexdigest()
                
                obj = {
                    "id": canonical_id,
                    "properties": {
                        "canonical_id": canonical_id,
                        "repo_path": chunk.get('repo_path', ''),
                        "file": chunk.get('file', ''),
                        "symbol": chunk.get('symbol', ''),
                        "lang": chunk.get('lang', ''),
                        "section": chunk.get('section', ''),
                        "text": chunk['text'],
                        "granularity": chunk.get('granularity', 'fine'),
                        "source_mtime": chunk.get('source_mtime', 0),
                        "commit": chunk.get('commit', '')
                    },
                    "vector": vector
                }
                objects.append(obj)
            
            # Batch upsert
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{WEAVIATE_URL}/v1/batch/objects",
                    json={"objects": objects}
                )
                
                if response.status_code == 200:
                    return len(objects)
                else:
                    logger.error(f"Upsert failed: {response.status_code} - {response.text}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Upsert failed: {e}")
            return 0
    
    async def ensure_schema(self, class_name: str):
        """Ensure Weaviate class exists"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Check if class exists
                response = await client.get(f"{WEAVIATE_URL}/v1/schema/{class_name}")
                if response.status_code == 200:
                    logger.info(f"✅ Schema '{class_name}' already exists")
                    return
                    
                logger.info(f"❌ Schema '{class_name}' does not exist - this is expected for new classes")
                
        except Exception as e:
            logger.warning(f"Schema check failed: {e}")
    
    async def seed_file(self, file_path: Path) -> Dict[str, int]:
        """Seed a single file with all granularities"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            if len(content.strip()) == 0:
                return {"coarse": 0, "fine": 0, "ultra_fine": 0}
            
            # File metadata
            file_stat = file_path.stat()
            repo_path = str(file_path.relative_to(Path(SEED_ROOT)))
            lang = self.get_file_language(file_path)
            
            # Generate canonical ID for this file
            canonical_id = hashlib.sha256(repo_path.encode()).hexdigest()
            
            results = {}
            
            # Create chunks for each granularity
            for granularity in ChunkGranularity:
                chunks = self.create_chunks(content, file_path, granularity)
                
                if not chunks:
                    results[granularity.value] = 0
                    continue
                
                # Prepare chunks for upsert
                prepared_chunks = []
                for i, chunk in enumerate(chunks):
                    chunk_canonical_id = f"{canonical_id}:{granularity.value}:{i}"
                    prepared_chunks.append({
                        'canonical_id': chunk_canonical_id,
                        'repo_path': repo_path,
                        'file': file_path.name,
                        'symbol': chunk.get('symbol', ''),
                        'lang': lang,
                        'section': chunk.get('section', f"chunk_{i}"),
                        'text': chunk['text'],
                        'granularity': granularity.value,
                        'source_mtime': file_stat.st_mtime,
                        'commit': 'unknown'  # TODO: Get from git
                    })
                
                # Determine target class
                class_mapping = {
                    ChunkGranularity.COARSE: "ChunkMini",
                    ChunkGranularity.FINE: "Docs",  # Keep existing class
                    ChunkGranularity.ULTRA_FINE: "ChunkLong"
                }
                
                class_name = class_mapping[granularity]
                await self.ensure_schema(class_name)
                
                # Upsert chunks
                inserted = await self.upsert_chunks(prepared_chunks, class_name)
                results[granularity.value] = inserted
                
                if inserted > 0:
                    logger.info(f"  Seeded {inserted} {granularity.value} chunks to {class_name}")
            
            # Update state
            file_key = str(file_path.relative_to(Path(SEED_ROOT)))
            self.state["files"][file_key] = {
                "mtime": file_stat.st_mtime,
                "size": file_stat.st_size,
                "chunks": results
            }
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to seed {file_path}: {e}")
            return {"coarse": 0, "fine": 0, "ultra_fine": 0}
    
    async def run(self):
        """Run the dynamic RAG seeder"""
        print("=" * 80)
        print("  🧠 Dynamic RAG Seeder - Multi-Granularity Chunking")
        print("=" * 80)
        print(f"Root: {SEED_ROOT}")
        print(f"Weaviate: {WEAVIATE_URL}")
        print(f"Gateway: {RAG_GATEWAY_URL}")
        print(f"Globs: {SEED_GLOBS}")
        
        # Find files to process
        root_path = Path(SEED_ROOT)
        files_to_process = []
        
        for glob_pattern in SEED_GLOBS:
            pattern = glob_pattern.strip()
            if pattern:
                files_to_process.extend(root_path.glob(pattern))
        
        # Filter files
        exclude_dirs = {'.git', 'node_modules', 'venv', '.venv', '__pycache__', 'dist', 'build', 'DerivedData'}
        files_to_process = [
            f for f in files_to_process 
            if f.is_file() and not any(part in exclude_dirs for part in f.parts)
        ]
        
        # Filter by state
        files_to_process = [f for f in files_to_process if self.should_process_file(f)]
        
        print(f"\nFound {len(files_to_process)} files to process")
        
        if not files_to_process:
            print("No files to process - all up to date!")
            return
        
        # Process files
        total_chunks = {"coarse": 0, "fine": 0, "ultra_fine": 0}
        processed_files = 0
        
        for file_path in files_to_process:
            try:
                results = await self.seed_file(file_path)
                for granularity, count in results.items():
                    total_chunks[granularity] += count
                
                processed_files += 1
                if processed_files % 10 == 0:
                    print(f"  Processed {processed_files}/{len(files_to_process)} files...")
                    
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
        
        # Save state
        self.save_state()
        
        # Summary
        print("\n" + "=" * 80)
        print("✅ Dynamic seeding complete!")
        print(f"   Files processed: {processed_files}")
        print(f"   Coarse chunks (ChunkMini): {total_chunks['coarse']}")
        print(f"   Fine chunks (Docs): {total_chunks['fine']}")
        print(f"   Ultra-fine chunks (ChunkLong): {total_chunks['ultra_fine']}")
        print(f"   Total chunks: {sum(total_chunks.values())}")
        print(f"   State saved: {self.state_file}")
        print("\nVerify:")
        print("  curl -s 'http://localhost:8090/v1/objects?class=ChunkMini&limit=1' | jq .")
        print("  curl -s 'http://localhost:8090/v1/objects?class=ChunkLong&limit=1' | jq .")
        print("=" * 80)

async def main():
    seeder = DynamicRAGSeeder()
    await seeder.run()

if __name__ == "__main__":
    asyncio.run(main())
