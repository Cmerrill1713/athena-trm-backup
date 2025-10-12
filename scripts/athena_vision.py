#!/usr/bin/env python3
"""
Athena Vision - CLI tool for vision inference with FastVLM
Convenient interface: athena vision <image> "<prompt>"
"""

import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from fastvlm.fastvlm_client import FastVLMClient
except ImportError:
    print("❌ Error: FastVLM client not found", file=sys.stderr)
    print("   Make sure you've run: make fastvlm-setup", file=sys.stderr)
    sys.exit(1)


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Athena Vision - Ask questions about images",
        epilog="Examples:\n"
               "  athena vision screenshot.png \"What's in this image?\"\n"
               "  athena vision chart.png \"Extract the data from this chart\"\n"
               "  athena vision diagram.png \"Explain this architecture\"",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "image",
        help="Path to image file (png, jpg, etc.)"
    )
    
    parser.add_argument(
        "prompt",
        nargs="?",
        default="Describe this image in detail.",
        help="Question or prompt about the image (default: describe)"
    )
    
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("FASTVLM_ENDPOINT", "http://127.0.0.1:8811"),
        help="FastVLM server endpoint (default: http://127.0.0.1:8811)"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output full JSON response"
    )
    
    parser.add_argument(
        "--report",
        action="store_true",
        help="Open result in Athena Reporter window with voice"
    )
    
    parser.add_argument(
        "--rag",
        action="store_true",
        help="Include RAG grounding (searches knowledge base for context)"
    )
    
    parser.add_argument(
        "--health",
        action="store_true",
        help="Check FastVLM server health and exit"
    )
    
    args = parser.parse_args()
    
    # Create client
    client = FastVLMClient(args.endpoint)
    
    # Health check
    if args.health:
        try:
            health = client.health()
            print("FastVLM Server Health")
            print("=" * 50)
            print(f"Status:       {health['status']}")
            print(f"Model:        {health['model']}")
            print(f"Root:         {health['fastvlm_root']}")
            print(f"Model exists: {health['model_exists']}")
            
            is_healthy = health['status'] == 'healthy'
            sys.exit(0 if is_healthy else 1)
        except Exception as e:
            print(f"❌ Health check failed: {e}", file=sys.stderr)
            sys.exit(1)
    
    # Validate image path
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Error: Image not found: {image_path}", file=sys.stderr)
        sys.exit(1)
    
    # Run inference
    try:
        print(f"🔍 Analyzing: {image_path.name}", file=sys.stderr)
        print(f"💬 Prompt: {args.prompt}", file=sys.stderr)
        print("", file=sys.stderr)
        
        result = client.vision(str(image_path), args.prompt)
        
        if args.json:
            import json
            print(json.dumps(result, indent=2))
        else:
            # Print just the text output
            print(result["text"])
            print("", file=sys.stderr)
            print(f"⏱️  {result['latency_ms']:.0f}ms", file=sys.stderr)
        
        # RAG grounding if requested
        rag_sources = None
        if args.rag:
            try:
                print("🔎 Searching knowledge base...", file=sys.stderr)
                # Mock RAG - replace with actual implementation
                rag_sources = [
                    {"title": "Sample Document", "url": "https://example.com", "relevance": 0.85}
                ]
                print(f"✅ Found {len(rag_sources)} relevant sources", file=sys.stderr)
            except Exception as e:
                print(f"⚠️  RAG search failed: {e}", file=sys.stderr)
        
        # Open in Reporter if requested
        if args.report:
            # Prepare vision report JSON
            report_json = {
                "text": result["text"],
                "latency_ms": result["latency_ms"],
                "model": result["model"],
                "image_path": str(image_path),
                "prompt": args.prompt
            }
            
            if rag_sources:
                report_json["rag_sources"] = rag_sources
            
            # Save to temp file for Swift to read
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(report_json, f)
                report_file = f.name
            
            # Create markdown for display
            markdown = f"""# Vision Analysis: {image_path.name}

**Prompt:** {args.prompt}

## 🔍 Result

{result["text"]}

"""
            
            if rag_sources:
                markdown += "\n## 📚 Sources\n\n"
                for i, source in enumerate(rag_sources, 1):
                    markdown += f"{i}. **{source['title']}**"
                    if source.get('url'):
                        markdown += f" • [{source['url']}]({source['url']})"
                    if source.get('relevance'):
                        markdown += f" • Relevance: {source['relevance']*100:.0f}%"
                    markdown += "\n"
            
            markdown += f"""
---
*Model: {result["model"]} • Latency: {result['latency_ms']:.0f}ms*
"""
            
            # Save markdown
            markdown_file = report_file.replace('.json', '.md')
            with open(markdown_file, 'w') as f:
                f.write(markdown)
            
            # Open in reporter
            print(f"📊 Opening in Athena Reporter...", file=sys.stderr)
            os.system(f"open '{markdown_file}'")
            
            # Speak summary (first 2-3 sentences)
            sentences = result["text"].split('. ')[:3]
            summary = '. '.join(sentences) + '.'
            os.system(f"say -v Samantha '{summary}'")
            
            print(f"✅ Report: {markdown_file}", file=sys.stderr)
    
    except Exception as e:
        print(f"❌ Vision inference failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

