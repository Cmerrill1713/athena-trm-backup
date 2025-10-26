#!/usr/bin/env python3
"""
PDF Fetcher — Download Papers from Queue

Downloads PDFs via egress proxy, validates, deduplicates.

Usage:
    HTTP_PROXY=http://egress-proxy:3128 python3 scripts/fetch_pdfs.py --out data/papers/
"""

import argparse
import hashlib
import os
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import requests


def fetch_pdf(url: str, output_path: str, timeout: int = 30) -> tuple[bool, Optional[str]]:
    """
    Fetch PDF from URL with validation.
    
    Returns:
        (success, error_message)
    """
    try:
        print(f"  Fetching: {url[:80]}...")
        
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
        
        # Validate content type
        content_type = response.headers.get('Content-Type', '')
        if 'pdf' not in content_type.lower() and not url.endswith('.pdf'):
            return False, f"Not a PDF (Content-Type: {content_type})"
        
        # Stream to file
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        # Validate file size
        file_size = os.path.getsize(output_path)
        if file_size < 1024:  # Less than 1KB probably not valid
            os.remove(output_path)
            return False, f"File too small ({file_size} bytes)"
        
        # Validate PDF header
        with open(output_path, 'rb') as f:
            header = f.read(5)
            if header != b'%PDF-':
                os.remove(output_path)
                return False, "Invalid PDF header"
        
        return True, None
        
    except requests.RequestException as e:
        return False, str(e)
    except Exception as e:
        return False, f"Unexpected error: {e}"


def compute_hash(file_path: str) -> str:
    """Compute SHA256 hash of file."""
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="Fetch PDFs from queue")
    ap.add_argument("--queue-db", default="data/papers/queue.db", help="Queue database")
    ap.add_argument("--out", default="data/papers/pdfs", help="PDF output directory")
    ap.add_argument("--limit", type=int, default=10, help="Max papers to fetch per run")
    ap.add_argument("--throttle", type=float, default=2.0, help="Seconds between fetches")
    args = ap.parse_args()
    
    # Ensure output directory exists
    Path(args.out).mkdir(parents=True, exist_ok=True)
    
    # Connect to queue
    conn = sqlite3.connect(args.queue_db)
    conn.row_factory = sqlite3.Row
    
    # Get queued papers
    cursor = conn.execute("""
        SELECT * FROM papers
        WHERE status = 'queued'
        ORDER BY score DESC, added_at ASC
        LIMIT ?
    """, (args.limit,))
    
    papers = cursor.fetchall()
    print(f"📥 Fetching {len(papers)} papers from queue...")
    print("")
    
    fetched = 0
    errors = 0
    duplicates = 0
    
    for paper in papers:
        paper_id = paper['id']
        url = paper['url']
        title = paper['title'] or 'untitled'
        
        # Generate filename
        safe_title = "".join(c for c in title[:50] if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{paper_id}_{safe_title}.pdf"
        output_path = os.path.join(args.out, filename)
        
        # Skip if already exists
        if os.path.exists(output_path):
            print(f"⏭️  [{paper_id}] Already exists: {filename}")
            duplicates += 1
            continue
        
        # Fetch PDF
        success, error = fetch_pdf(url, output_path)
        
        if success:
            # Compute hash for deduplication
            file_hash = compute_hash(output_path)
            
            # Update database
            conn.execute("""
                UPDATE papers
                SET status = 'fetched',
                    fetched_at = ?,
                    error = NULL
                WHERE id = ?
            """, (datetime.utcnow().isoformat(), paper_id))
            conn.commit()
            
            fetched += 1
            file_size = os.path.getsize(output_path)
            print(f"  ✅ [{paper_id}] {filename} ({file_size // 1024}KB, hash: {file_hash[:12]}...)")
        else:
            # Update error
            conn.execute("""
                UPDATE papers
                SET status = 'error',
                    error = ?
                WHERE id = ?
            """, (error, paper_id))
            conn.commit()
            
            errors += 1
            print(f"  ❌ [{paper_id}] {error}")
        
        # Throttle
        if fetched + errors < len(papers):
            time.sleep(args.throttle)
    
    print("")
    print(f"📊 Summary:")
    print(f"  ✅ Fetched: {fetched}")
    print(f"  ⏭️  Duplicates: {duplicates}")
    print(f"  ❌ Errors: {errors}")
    
    conn.close()


if __name__ == "__main__":
    main()

