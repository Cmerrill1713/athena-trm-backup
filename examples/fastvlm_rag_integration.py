#!/usr/bin/env python3
"""
FastVLM + RAG Integration Example

Shows how to pipe vision output into RAG for grounded responses:
1. Extract info from image with FastVLM
2. Search relevant docs with RAG
3. Generate grounded response with citations

Use case: "What does this chart show?" → extract data → find context → explain with sources
"""

import sys
from pathlib import Path
from typing import List, Dict, Any

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def vision_to_rag_pipeline(
    image_path: str,
    user_question: str,
    rag_search_fn,
    llm_generate_fn,
    top_k: int = 5
) -> Dict[str, Any]:
    """
    Complete vision → RAG → generation pipeline
    
    Args:
        image_path: Path to image
        user_question: User's original question
        rag_search_fn: Function(query) -> List[doc] for RAG search
        llm_generate_fn: Function(prompt) -> str for generation
        top_k: Number of RAG documents to retrieve
    
    Returns:
        Dict with:
            - vision_output: Raw FastVLM output
            - rag_docs: Retrieved documents
            - final_answer: Grounded response
            - sources: List of sources used
    """
    from fastvlm.fastvlm_client import call_fastvlm
    
    # Step 1: Extract from image
    print(f"🔍 Analyzing image: {Path(image_path).name}")
    vision_output = call_fastvlm(
        image_path,
        f"Extract key information relevant to: {user_question}"
    )
    print(f"✅ Vision: {vision_output[:100]}...")
    
    # Step 2: Search RAG with vision output
    print(f"🔎 Searching knowledge base...")
    rag_query = f"{vision_output}\n\nOriginal question: {user_question}"
    docs = rag_search_fn(rag_query, top_k=top_k)
    print(f"✅ Found {len(docs)} relevant documents")
    
    # Step 3: Generate grounded response
    print(f"💭 Generating response...")
    
    # Build context from RAG docs
    context = "\n\n".join([
        f"[Source {i+1}: {doc.get('title', 'Unknown')}]\n{doc.get('content', '')}"
        for i, doc in enumerate(docs)
    ])
    
    prompt = f"""Based on this image analysis and supporting documentation, answer the question.

IMAGE ANALYSIS:
{vision_output}

SUPPORTING DOCUMENTATION:
{context}

QUESTION:
{user_question}

Provide a comprehensive answer with citations [Source N]. Be specific and reference the image data."""
    
    final_answer = llm_generate_fn(prompt)
    print(f"✅ Generated grounded response")
    
    # Extract sources
    sources = [
        {"title": doc.get('title', 'Unknown'), "url": doc.get('url', '')}
        for doc in docs
    ]
    
    return {
        "vision_output": vision_output,
        "rag_docs": docs,
        "final_answer": final_answer,
        "sources": sources,
        "image_path": image_path,
        "question": user_question
    }


# Example: Mock RAG search (replace with your actual RAG system)
def mock_rag_search(query: str, top_k: int = 5) -> List[Dict[str, Any]]:
    """
    Mock RAG search - replace with your actual implementation
    
    Real implementation might use:
    - Pinecone/Weaviate/Qdrant vector search
    - Elasticsearch BM25
    - Your custom retrieval system
    """
    # This is just example data
    mock_docs = [
        {
            "title": "Q3 Sales Report",
            "content": "Q3 sales increased 15% YoY due to new product launches...",
            "url": "https://docs.example.com/q3-sales",
            "score": 0.89
        },
        {
            "title": "Revenue Growth Strategy",
            "content": "Focus on enterprise customers drove revenue growth in Q3...",
            "url": "https://docs.example.com/strategy",
            "score": 0.85
        },
        {
            "title": "Market Analysis",
            "content": "Market conditions were favorable with 12% growth...",
            "url": "https://docs.example.com/market",
            "score": 0.82
        }
    ]
    
    print(f"⚠️  Using mock RAG - replace with actual search")
    return mock_docs[:top_k]


# Example: Mock LLM generation (replace with your actual LLM)
def mock_llm_generate(prompt: str) -> str:
    """
    Mock LLM generation - replace with your actual LLM
    
    Real implementation might use:
    - OpenAI GPT-4
    - Anthropic Claude
    - Your local Qwen/Llama model
    """
    return """Based on the chart analysis and documentation:

The chart shows quarterly sales data with Q2 representing the peak at approximately $150K [Source 1]. This aligns with the Q3 Sales Report which notes a 15% year-over-year increase [Source 1]. The growth trend is consistent with our Revenue Growth Strategy focused on enterprise customers [Source 2].

Key insights:
- Q1: ~$100K baseline
- Q2: ~$150K (peak, +50% QoQ)
- Q3: ~$125K (normalizing, -17% from Q2 but +15% YoY)

The market conditions described in the Market Analysis show 12% overall market growth [Source 3], suggesting our Q3 performance outpaced the market."""


def main():
    """Run example"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="FastVLM + RAG Integration Example"
    )
    parser.add_argument(
        "image",
        help="Path to image file"
    )
    parser.add_argument(
        "--question",
        default="What does this chart show and what are the business implications?",
        help="Question about the image"
    )
    
    args = parser.parse_args()
    
    print("╔═══════════════════════════════════════════════════════════╗")
    print("║         FastVLM + RAG Integration Example                 ║")
    print("╚═══════════════════════════════════════════════════════════╝\n")
    
    # Run pipeline
    result = vision_to_rag_pipeline(
        image_path=args.image,
        user_question=args.question,
        rag_search_fn=mock_rag_search,
        llm_generate_fn=mock_llm_generate,
        top_k=3
    )
    
    # Display results
    print("\n" + "="*70)
    print("RESULTS")
    print("="*70)
    
    print(f"\n📸 Image: {result['image_path']}")
    print(f"❓ Question: {result['question']}")
    
    print(f"\n🔍 Vision Output:")
    print(f"   {result['vision_output']}")
    
    print(f"\n📚 Sources Used ({len(result['sources'])}):")
    for i, source in enumerate(result['sources'], 1):
        print(f"   {i}. {source['title']}")
        if source['url']:
            print(f"      {source['url']}")
    
    print(f"\n💡 Final Answer:")
    print(f"   {result['final_answer']}")
    
    print("\n" + "="*70)
    print("✅ Pipeline complete!")
    print("\n💡 Next steps:")
    print("   1. Replace mock_rag_search with your RAG system")
    print("   2. Replace mock_llm_generate with your LLM")
    print("   3. Add Sentry tracing to each step")
    print("   4. Add metrics for vision→RAG quality")


if __name__ == "__main__":
    main()

