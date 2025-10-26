#!/usr/bin/env python3
"""
Demo: AGI Agent using Knowledge Base Search

Shows how AGI agents can query the RAG knowledge base for factual information.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agi_core.tools import kb_search, KBSearchTool


async def demo_basic_search():
    """Basic KB search demo"""
    print("=" * 80)
    print("DEMO 1: Basic Knowledge Base Search")
    print("=" * 80)
    print()
    
    query = "How to train recursive models?"
    print(f"Query: {query}")
    print()
    
    results = await kb_search(query, top_k=3, mode="hybrid")
    
    print(f"Found {len(results)} results:\n")
    for i, result in enumerate(results):
        print(f"{i+1}. [{result.doc_id}] {result.title}")
        print(f"   Score: {result.score:.3f}")
        print(f"   Snippet: {result.chunk[:150]}...")
        print()


async def demo_agent_tool():
    """Demo AGI agent using KB search tool"""
    print("=" * 80)
    print("DEMO 2: AGI Agent with KB Search Tool")
    print("=" * 80)
    print()
    
    tool = KBSearchTool()
    
    try:
        # Simulate agent decision-making
        queries = [
            ("What is RAG?", "faq query"),
            ("How to implement vector search?", "howto query"),
            ("Best practices for embeddings", "policy/documentation query")
        ]
        
        for query, category in queries:
            print(f"Agent Query: {query} ({category})")
            results = await tool.search(query, top_k=2, mode="nearText")
            
            # Format for agent context
            formatted = tool.format_results_for_agent(results, max_context=500)
            print(formatted)
            print("-" * 80)
            print()
        
    finally:
        await tool.close()


async def demo_routing_integration():
    """Demo routing integration with KB awareness"""
    print("=" * 80)
    print("DEMO 3: Router + KB Integration")
    print("=" * 80)
    print()
    
    from services.router.rag_router import route_query
    
    queries = [
        "What is recursive reasoning?",
        "Brainstorm creative AGI ideas",
        "Compare BM25 vs semantic search",
        "Fix this error: NameError in Python"
    ]
    
    for query in queries:
        result = await route_query(query)
        print(f"Query: {query}")
        print(f"  → Route: {result.route.value}")
        print(f"  → Confidence: {result.confidence:.2f}")
        print(f"  → Reasoning: {result.reasoning}")
        
        if result.intent:
            print(f"  → Intent: {result.intent.category}")
        if result.probe_score:
            print(f"  → KB Probe: {result.probe_score:.3f}")
        
        print()


async def main():
    """Run all demos"""
    try:
        await demo_basic_search()
        await demo_agent_tool()
        await demo_routing_integration()
        
        print("=" * 80)
        print("✓ All demos complete!")
        print("=" * 80)
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

