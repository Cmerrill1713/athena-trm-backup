#!/usr/bin/env python3
"""
Router Probe - Test routing decisions for specific queries

Usage:
    python3 scripts/router_probe.py --q "What is our refund policy?"
    python3 scripts/router_probe.py --q "Brainstorm taglines"
"""

import sys
import asyncio
import argparse
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.router.rag_router import route_query


async def main():
    parser = argparse.ArgumentParser(description="Test router decisions")
    parser.add_argument("--q", "--query", dest="query", required=True, help="Query to route")
    parser.add_argument("--hint", default=None, help="Optional routing hint")
    
    args = parser.parse_args()
    
    print(f"Query: {args.query}")
    print("-" * 80)
    
    try:
        result = await route_query(args.query, user_hint=args.hint)
        
        print(f"✓ Route: {result.route.value}")
        print(f"  Confidence: {result.confidence:.2f}")
        print(f"  Reasoning: {result.reasoning}")
        
        if result.intent:
            print(f"  Intent: {result.intent.category} ({result.intent.confidence:.2f})")
        
        if result.probe_score is not None:
            print(f"  KB Probe: {result.probe_score:.3f}")
        
        print()
        
        # Exit code based on routing
        if result.route.value in ["rag", "hybrid", "trm_rag"]:
            sys.exit(0)  # RAG-aware routes
        else:
            sys.exit(0)  # LLM/TRM routes (still valid)
        
    except Exception as e:
        print(f"✗ Router probe failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

