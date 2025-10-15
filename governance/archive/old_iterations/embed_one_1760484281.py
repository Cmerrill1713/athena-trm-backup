#!/usr/bin/env python3
"""
Embed a single transcript file into Weaviate with deduplication
"""
import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path

import requests

WEAVIATE_URL = "http://localhost:8090"
STATE_FILE = Path(".embed_state.jsonl")

def get_doc_id(channel, video_id, chunk_index=0):
    """Generate stable document ID"""
    key = f"{channel}|{video_id}|{chunk_index}"
    return hashlib.sha256(key.encode()).hexdigest()

def check_if_embedded(doc_id):
    """Check if document already embedded"""
    if not STATE_FILE.exists():
        return False

    with open(STATE_FILE, 'r') as f:
        for line in f:
            try:
                record = json.loads(line.strip())
                if record.get("doc_id") == doc_id:
                    return True
            except:
                continue
    return False

def mark_as_embedded(doc_id, file_path):
    """Mark document as embedded"""
    with open(STATE_FILE, 'a') as f:
        record = {
            "doc_id": doc_id,
            "file": str(file_path),
            "embedded_at": datetime.now().isoformat()
        }
        f.write(json.dumps(record) + '\n')

def parse_transcript_file(file_path):
    """Parse transcript text file"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.split('\n')
    title = ""
    channel = ""
    transcript = content

    for line in lines[:10]:
        if line.startswith("Title:"):
            title = line.replace("Title:", "").strip()
        elif line.startswith("Channel:"):
            channel = line.replace("Channel:", "").strip()

    # Extract video ID from filename or content
    video_id = file_path.stem.split('_')[-1] if '_' in file_path.stem else hashlib.md5(title.encode()).hexdigest()[:12]

    return title, channel, video_id, transcript

def chunk_transcript(transcript, chunk_size=800, overlap=150):
    """Chunk transcript for better retrieval"""
    words = transcript.split()
    chunks = []

    for i in range(0, len(words), chunk_size - overlap):
        chunk = ' '.join(words[i:i + chunk_size])
        if len(chunk) > 100:  # Skip tiny chunks
            chunks.append(chunk)

    return chunks if chunks else [transcript]

def embed_chunk(title, channel, video_id, chunk_text, chunk_index, total_chunks):
    """Embed one chunk into Weaviate"""
    doc_id = get_doc_id(channel, video_id, chunk_index)

    # Check if already embedded
    if check_if_embedded(doc_id):
        return False, "already_embedded"

    try:
        # Extract keywords
        keywords = []
        for keyword in ["claude", "cursor", "aider", "coding", "agent", "ai", "prompt", "mcp"]:
            if keyword.lower() in chunk_text.lower():
                keywords.append(keyword)

        data = {
            "class": "LearnedPattern",
            "properties": {
                "pattern_type": "video_transcript",
                "title": f"{channel}: {title[:70]}" + (f" (Part {chunk_index+1}/{total_chunks})" if total_chunks > 1 else ""),
                "description": chunk_text[:500],
                "pattern_data": json.dumps({
                    "source": "youtube",
                    "channel": channel,
                    "video_id": video_id,
                    "doc_id": doc_id,
                    "chunk_index": chunk_index,
                    "total_chunks": total_chunks,
                    "transcript": chunk_text,
                    "full_length": len(chunk_text),
                    "keywords": keywords,
                    "timestamp": datetime.now().isoformat()
                }),
                "tags": ["youtube", "tutorial", "ai-coding"] + keywords + [channel.lower().replace(" ", "-")],
                "success_rate": 1.0,
                "usage_count": 0
            }
        }

        response = requests.post(
            f"{WEAVIATE_URL}/v1/objects",
            headers={"Content-Type": "application/json"},
            json=data,
            timeout=30
        )

        if response.status_code in [200, 201]:
            return True, doc_id
        else:
            return False, f"error_{response.status_code}"

    except Exception as e:
        return False, str(e)[:50]

def main():
    if len(sys.argv) < 2:
        print("Usage: embed_one.py <transcript_file.txt>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"❌ File not found: {file_path}")
        sys.exit(1)

    print(f"📄 Processing: {file_path.name}")

    # Parse file
    title, channel, video_id, transcript = parse_transcript_file(file_path)
    print(f"   Channel: {channel}")
    print(f"   Title: {title[:60]}...")
    print(f"   Length: {len(transcript):,} chars")

    # Chunk if needed
    if len(transcript) > 50000:
        chunks = chunk_transcript(transcript, chunk_size=800, overlap=150)
        print(f"   Chunks: {len(chunks)}")
    else:
        chunks = [transcript]

    # Embed each chunk
    embedded = 0
    for i, chunk in enumerate(chunks):
        success, result = embed_chunk(title, channel, video_id, chunk, i, len(chunks))
        if success:
            mark_as_embedded(result, file_path)
            embedded += 1

    print(f"✅ Embedded: {embedded}/{len(chunks)} chunks")

    return 0 if embedded > 0 else 1

if __name__ == "__main__":
    sys.exit(main())

