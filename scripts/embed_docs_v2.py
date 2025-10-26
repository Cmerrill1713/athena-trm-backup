#!/usr/bin/env python3
"""
Embed Documents to Weaviate DocsV2

Processes PDFs, extracts text, chunks, embeds, and upserts to Weaviate.

Usage:
    python3 scripts/embed_docs_v2.py --input data/papers/pdfs --class DocsV2
"""

import argparse
import hashlib
import json
import os
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

import requests
from sentence_transformers import SentenceTransformer


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract text from PDF using pdftotext."""
    try:
        result = subprocess.run(
            ['pdftotext', pdf_path, '-'],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
    except Exception as e:
        print(f"  ⚠️  Failed to extract text: {e}")
        return ""


def chunk_text(text: str, chunk_size: int = 512, overlap: int = 128) -> List[str]:
    """Split text into overlapping chunks."""
    words = text.split()
    chunks = []
    
    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk) > 50:  # Skip tiny chunks
            chunks.append(chunk)
    
    return chunks


def embed_chunks(chunks: List[str], model: SentenceTransformer) -> List[List[float]]:
    """Compute embeddings for chunks."""
    embeddings = model.encode(chunks, show_progress_bar=False)
    return embeddings.tolist()


def upsert_to_weaviate(
    weaviate_url: str,
    class_name: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Dict[str, Any]
):
    """Upsert chunks to Weaviate."""
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        doc_id = f"{metadata['source_file']}_{i}"
        
        obj = {
            "class": class_name,
            "id": hashlib.sha256(doc_id.encode()).hexdigest()[:32],  # Deterministic UUID
            "properties": {
                "doc_id": doc_id,
                "content": chunk,
                "source": metadata.get('source', 'unknown'),
                "doi": metadata.get('doi'),
                "title": metadata.get('title'),
                "chunk_index": i,
                "total_chunks": len(chunks),
                "indexed_at": datetime.utcnow().isoformat()
            },
            "vector": embedding
        }
        
        # Upsert to Weaviate
        response = requests.post(
            f"{weaviate_url}/v1/objects",
            json=obj,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code not in (200, 201):
            print(f"    ⚠️  Failed to upsert chunk {i}: {response.text[:100]}")


def main():
    ap = argparse.ArgumentParser(description="Embed documents to Weaviate")
    ap.add_argument("--input", required=True, help="PDF directory")
    ap.add_argument("--class", dest="clazz", default="DocsV2", help="Weaviate class")
    ap.add_argument("--model", default="all-MiniLM-L6-v2", help="Embedding model")
    ap.add_argument("--weaviate-url", default="http://localhost:8080", help="Weaviate URL")
    ap.add_argument("--queue-db", default="data/papers/queue.db", help="Queue database")
    ap.add_argument("--chunk-size", type=int, default=512, help="Chunk size (words)")
    ap.add_argument("--overlap", type=int, default=128, help="Chunk overlap (words)")
    args = ap.parse_args()
    
    # Load embedding model
    print(f"📦 Loading embedding model: {args.model}")
    model = SentenceTransformer(args.model)
    print(f"   Embedding dimension: {model.get_sentence_embedding_dimension()}")
    print("")
    
    # Connect to queue (optional)
    queue_conn = None
    if os.path.exists(args.queue_db):
        queue_conn = sqlite3.connect(args.queue_db)
    
    # Process PDFs
    pdf_files = list(Path(args.input).glob("*.pdf"))
    print(f"📄 Found {len(pdf_files)} PDFs to process")
    print("")
    
    processed = 0
    errors = 0
    
    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")
        
        # Extract metadata from filename (if from queue)
        paper_id = pdf_path.stem.split('_')[0] if '_' in pdf_path.stem else None
        
        # Extract text
        text = extract_text_from_pdf(str(pdf_path))
        if not text or len(text) < 100:
            print(f"  ❌ No text extracted")
            errors += 1
            continue
        
        print(f"  📝 Extracted {len(text)} characters")
        
        # Chunk text
        chunks = chunk_text(text, args.chunk_size, args.overlap)
        print(f"  ✂️  Created {len(chunks)} chunks")
        
        # Compute embeddings
        print(f"  🧠 Computing embeddings...")
        embeddings = embed_chunks(chunks, model)
        
        # Prepare metadata
        metadata = {
            'source_file': pdf_path.stem,
            'source': 'research_paper',
            'title': pdf_path.stem.replace('_', ' '),
            'doi': None  # TODO: Extract from queue DB if available
        }
        
        # Upsert to Weaviate
        print(f"  ⬆️  Uploading to Weaviate...")
        upsert_to_weaviate(args.weaviate_url, args.clazz, chunks, embeddings, metadata)
        
        # Update queue status
        if queue_conn and paper_id:
            queue_conn.execute("""
                UPDATE papers
                SET status = 'embedded',
                    embedded_at = ?
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), int(paper_id)))
            queue_conn.commit()
        
        processed += 1
        print(f"  ✅ Processed: {pdf_path.name}")
        print("")
    
    print(f"📊 Summary:")
    print(f"  ✅ Processed: {processed}")
    print(f"  ❌ Errors: {errors}")
    
    if queue_conn:
        queue_conn.close()


if __name__ == "__main__":
    main()

