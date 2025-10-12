#!/usr/bin/env python3
"""
Convert all VTT transcripts to text and embed into Weaviate
Works with both indydevdan_transcripts and ai_coding_transcripts
"""
import re
import json
import requests
from pathlib import Path
from datetime import datetime
import sys

WEAVIATE_URL = "http://localhost:8090"
TRANSCRIPT_DIRS = [
    Path("indydevdan_transcripts"),
    Path("ai_coding_transcripts")
]

def vtt_to_text(vtt_file):
    """Convert VTT subtitle file to plain text"""
    try:
        with open(vtt_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # Remove WEBVTT header
        content = re.sub(r'WEBVTT\n.*?\n\n', '', content, flags=re.DOTALL)

        # Remove timestamps and formatting
        lines = []
        for line in content.split('\n'):
            # Skip timestamp lines
            if '-->' in line or line.strip().isdigit() or not line.strip():
                continue
            # Remove HTML tags
            line = re.sub(r'<[^>]+>', '', line)
            if line.strip():
                lines.append(line.strip())

        return ' '.join(lines)
    except Exception as e:
        print(f"  ⚠️  VTT parse error: {e}")
        return None

def embed_to_weaviate(title, transcript, video_url, channel_name):
    """Embed transcript into Weaviate LearnedPattern"""
    try:
        headers = {"Content-Type": "application/json"}

        # Extract topic keywords from title
        keywords = []
        topic_patterns = [
            "claude", "cursor", "aider", "coding", "agent", "ai",
            "prompt", "openai", "gemini", "llm", "engineering"
        ]
        for keyword in topic_patterns:
            if keyword.lower() in title.lower():
                keywords.append(keyword)

        data = {
            "class": "LearnedPattern",
            "properties": {
                "pattern_type": "video_transcript",
                "title": f"{channel_name}: {title[:70]}",
                "description": f"Tutorial by {channel_name} covering {title[:100]}",
                "pattern_data": json.dumps({
                    "source": "youtube",
                    "channel": channel_name,
                    "video_url": video_url,
                    "transcript": transcript[:50000],  # Limit to 50K chars
                    "full_length": len(transcript),
                    "keywords": keywords,
                    "timestamp": datetime.now().isoformat()
                }),
                "tags": ["youtube", "tutorial", "ai-coding"] + keywords + [channel_name.lower().replace(" ", "-")],
                "success_rate": 1.0,
                "usage_count": 0
            }
        }

        response = requests.post(
            f"{WEAVIATE_URL}/v1/objects",
            headers=headers,
            json=data,
            timeout=30
        )

        return response.status_code in [200, 201]
    except Exception as e:
        print(f"  ⚠️  Weaviate error: {str(e)[:50]}")
        return False

def process_directory(base_dir):
    """Process all VTT files in a directory"""
    if not base_dir.exists():
        return 0, 0

    vtt_files = list(base_dir.rglob("*.vtt"))
    if not vtt_files:
        return 0, 0

    print(f"\n📁 Processing: {base_dir.name}")
    print(f"   Found: {len(vtt_files)} VTT files")

    converted = 0
    embedded = 0

    for vtt_file in vtt_files:
        # Skip if already processed
        txt_file = vtt_file.with_suffix('.txt')
        if txt_file.exists():
            continue

        # Get channel name from directory structure
        channel_name = vtt_file.parent.name.replace("_", " ")
        title = vtt_file.stem.replace('.en', '')

        # Convert VTT to text
        transcript = vtt_to_text(vtt_file)
        if not transcript or len(transcript) < 100:
            continue

        # Save as text
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(f"Title: {title}\n")
            f.write(f"Channel: {channel_name}\n")
            f.write("="*70 + "\n\n")
            f.write(transcript)

        converted += 1

        # Embed to Weaviate
        video_url = f"https://www.youtube.com/watch?v={vtt_file.stem.split('.')[-1] if '.' in vtt_file.stem else 'unknown'}"
        if embed_to_weaviate(title, transcript, video_url, channel_name):
            embedded += 1

        # Progress indicator
        if converted % 10 == 0:
            print(f"  📝 Processed {converted} transcripts...")

    return converted, embedded

def main():
    print("🚀 Converting & Embedding All AI Coding Transcripts")
    print("="*70)

    total_converted = 0
    total_embedded = 0

    for transcript_dir in TRANSCRIPT_DIRS:
        converted, embedded = process_directory(transcript_dir)
        total_converted += converted
        total_embedded += embedded

    print("\n" + "="*70)
    print("📊 FINAL SUMMARY")
    print("="*70)
    print(f"✅ Converted: {total_converted} transcripts")
    print(f"✅ Embedded:  {total_embedded} into Weaviate")

    # Check total in Weaviate
    try:
        response = requests.post(
            f"{WEAVIATE_URL}/v1/graphql",
            headers={"Content-Type": "application/json"},
            json={"query": "{ Aggregate { LearnedPattern(where: {operator: Equal, path: [\"pattern_type\"], valueText: \"video_transcript\"}) { meta { count } } } }"},
            timeout=10
        )
        data = response.json()
        total_in_db = data['data']['Aggregate']['LearnedPattern'][0]['meta']['count']
        print(f"🗄️  Total video transcripts in Weaviate: {total_in_db}")
    except:
        pass

    print(f"\n📁 Files location:")
    for d in TRANSCRIPT_DIRS:
        if d.exists():
            print(f"   - {d.absolute()}")

if __name__ == "__main__":
    main()
