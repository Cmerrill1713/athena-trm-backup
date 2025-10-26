#!/usr/bin/env python3
"""
Paper Curation — Add Research Papers to Ingestion Queue

Reads SearXNG search results and adds high-quality papers to queue.

Usage:
    python3 scripts/curate_add.py artifacts/search.json --min-score 0.6
"""

import argparse
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any


def init_queue(db_path: str):
    """Initialize SQLite queue database."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT,
            doi TEXT,
            source TEXT,
            score REAL,
            added_at TEXT,
            status TEXT DEFAULT 'queued',
            fetched_at TEXT,
            embedded_at TEXT,
            error TEXT
        )
    """)
    conn.execute("CREATE INDEX IF NOT EXISTS idx_status ON papers(status)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_doi ON papers(doi)")
    conn.commit()
    return conn


def parse_searxng_results(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse SearXNG JSON results."""
    results = []
    
    for result in data.get('results', []):
        url = result.get('url', '')
        title = result.get('title', '')
        
        # Extract DOI if available
        doi = None
        if 'doi.org/' in url:
            doi = url.split('doi.org/')[-1].split('?')[0]
        
        # Detect source
        source = 'unknown'
        if 'arxiv.org' in url:
            source = 'arxiv'
        elif 'acm.org' in url:
            source = 'acm'
        elif 'ieee.org' in url:
            source = 'ieee'
        elif 'semanticscholar.org' in url:
            source = 'semantic_scholar'
        elif 'pubmed' in url or 'ncbi.nlm.nih.gov' in url:
            source = 'pubmed'
        
        # Score (if available)
        score = result.get('score', 0.5)
        
        results.append({
            'url': url,
            'title': title,
            'doi': doi,
            'source': source,
            'score': score
        })
    
    return results


def add_to_queue(conn: sqlite3.Connection, papers: List[Dict[str, Any]], min_score: float):
    """Add papers to queue."""
    added = 0
    skipped = 0
    
    for paper in papers:
        if paper['score'] < min_score:
            skipped += 1
            continue
        
        try:
            conn.execute("""
                INSERT INTO papers (url, title, doi, source, score, added_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                paper['url'],
                paper['title'],
                paper['doi'],
                paper['source'],
                paper['score'],
                datetime.utcnow().isoformat()
            ))
            added += 1
        except sqlite3.IntegrityError:
            # Already in queue
            skipped += 1
    
    conn.commit()
    return added, skipped


def main():
    ap = argparse.ArgumentParser(description="Add papers to ingestion queue")
    ap.add_argument("search_results", help="SearXNG JSON results file")
    ap.add_argument("--min-score", type=float, default=0.6, help="Minimum score threshold")
    ap.add_argument("--queue-db", default="data/papers/queue.db", help="Queue database path")
    args = ap.parse_args()
    
    # Ensure queue directory exists
    Path(args.queue_db).parent.mkdir(parents=True, exist_ok=True)
    
    # Load search results
    with open(args.search_results, 'r') as f:
        data = json.load(f)
    
    # Parse papers
    papers = parse_searxng_results(data)
    print(f"📄 Found {len(papers)} papers in search results")
    
    # Initialize queue
    conn = init_queue(args.queue_db)
    
    # Add to queue
    added, skipped = add_to_queue(conn, papers, args.min_score)
    
    print(f"✅ Added {added} papers to queue")
    print(f"⏭️  Skipped {skipped} papers (below threshold or duplicate)")
    
    # Show queue stats
    cursor = conn.execute("SELECT status, COUNT(*) FROM papers GROUP BY status")
    print("\nQueue status:")
    for status, count in cursor:
        print(f"  {status}: {count}")
    
    conn.close()


if __name__ == "__main__":
    main()

