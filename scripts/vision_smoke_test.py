#!/usr/bin/env python3
"""
Vision Smoke Test - Test FastVLM with 6 image types

Tests:
1. Document scan (OCR)
2. Chart/graph (data extraction)
3. UI screenshot (interface understanding)
4. Whiteboard/handwriting
5. Photo (general vision)
6. Technical diagram

Generates synthetic test images and validates responses.
"""

import sys
import os
import time
import tempfile
from pathlib import Path
from typing import Dict, Any

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("❌ PIL not installed. Run: pip install pillow")
    sys.exit(1)


def create_test_images() -> Dict[str, tuple[str, str, str]]:
    """
    Create synthetic test images
    
    Returns:
        Dict mapping test_name to (image_path, prompt, expected_content)
    """
    test_dir = tempfile.mkdtemp(prefix="fastvlm_smoke_")
    tests = {}
    
    # 1. Document scan (OCR)
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    draw.text((20, 80), "Invoice #12345\nTotal: $500.00", fill='black')
    doc_path = os.path.join(test_dir, "document.png")
    img.save(doc_path)
    tests["document_ocr"] = (
        doc_path,
        "Extract all text from this document",
        "invoice"
    )
    
    # 2. Chart (data extraction)
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    # Simple bar chart
    draw.rectangle([50, 250, 90, 200], fill='blue')
    draw.rectangle([120, 250, 160, 150], fill='blue')
    draw.rectangle([190, 250, 230, 180], fill='blue')
    draw.text((20, 20), "Sales Chart", fill='black')
    draw.text((50, 260), "Q1", fill='black')
    draw.text((120, 260), "Q2", fill='black')
    draw.text((190, 260), "Q3", fill='black')
    chart_path = os.path.join(test_dir, "chart.png")
    img.save(chart_path)
    tests["chart_data"] = (
        chart_path,
        "What type of chart is this? Describe the data shown.",
        "chart"
    )
    
    # 3. UI screenshot (interface)
    img = Image.new('RGB', (400, 300), color='lightgray')
    draw = ImageDraw.Draw(img)
    # Mock UI elements
    draw.rectangle([10, 10, 390, 50], fill='darkblue')
    draw.text((20, 25), "App Name", fill='white')
    draw.rectangle([50, 100, 200, 140], fill='blue', outline='black')
    draw.text((80, 115), "Button 1", fill='white')
    draw.rectangle([50, 160, 200, 200], fill='green', outline='black')
    draw.text((80, 175), "Button 2", fill='white')
    ui_path = os.path.join(test_dir, "ui.png")
    img.save(ui_path)
    tests["ui_screenshot"] = (
        ui_path,
        "Describe the UI elements you see",
        "button"
    )
    
    # 4. Whiteboard (handwriting simulation)
    img = Image.new('RGB', (400, 200), color='white')
    draw = ImageDraw.Draw(img)
    # Simulate rough handwriting
    draw.line([(50, 100), (100, 80), (150, 100), (200, 90)], fill='black', width=3)
    draw.text((50, 150), "Notes: TODO", fill='black')
    whiteboard_path = os.path.join(test_dir, "whiteboard.png")
    img.save(whiteboard_path)
    tests["whiteboard"] = (
        whiteboard_path,
        "What text or drawings do you see?",
        "todo"
    )
    
    # 5. Photo (colored shapes)
    img = Image.new('RGB', (400, 300), color='skyblue')
    draw = ImageDraw.Draw(img)
    draw.ellipse([100, 50, 300, 250], fill='red')
    draw.rectangle([150, 200, 250, 280], fill='yellow')
    photo_path = os.path.join(test_dir, "photo.png")
    img.save(photo_path)
    tests["photo_scene"] = (
        photo_path,
        "Describe the colors and shapes in this image",
        "red"
    )
    
    # 6. Technical diagram (boxes and arrows)
    img = Image.new('RGB', (400, 300), color='white')
    draw = ImageDraw.Draw(img)
    # Architecture boxes
    draw.rectangle([50, 50, 150, 100], outline='black', width=2)
    draw.text((70, 70), "Client", fill='black')
    draw.rectangle([250, 50, 350, 100], outline='black', width=2)
    draw.text((270, 70), "Server", fill='black')
    draw.line([(150, 75), (250, 75)], fill='black', width=2)
    draw.polygon([(240, 70), (250, 75), (240, 80)], fill='black')
    diagram_path = os.path.join(test_dir, "diagram.png")
    img.save(diagram_path)
    tests["tech_diagram"] = (
        diagram_path,
        "Describe this system architecture diagram",
        "client"
    )
    
    return tests


def run_vision_test(
    test_name: str,
    image_path: str,
    prompt: str,
    expected_content: str
) -> Dict[str, Any]:
    """
    Run a single vision test
    
    Returns:
        Test result dict
    """
    try:
        from fastvlm.fastvlm_client import FastVLMClient
        
        client = FastVLMClient()
        
        start = time.time()
        result = client.vision(image_path, prompt)
        elapsed = (time.time() - start) * 1000
        
        # Check if expected content is in response
        response_lower = result["text"].lower()
        expected_lower = expected_content.lower()
        contains_expected = expected_lower in response_lower
        
        return {
            "test": test_name,
            "status": "✅ PASS" if contains_expected else "⚠️  PARTIAL",
            "latency_ms": result["latency_ms"],
            "total_ms": elapsed,
            "expected": expected_content,
            "found": contains_expected,
            "response_length": len(result["text"]),
            "response_preview": result["text"][:100] + "..." if len(result["text"]) > 100 else result["text"]
        }
    
    except Exception as e:
        return {
            "test": test_name,
            "status": "❌ FAIL",
            "error": str(e),
            "latency_ms": 0,
            "total_ms": 0,
            "expected": expected_content,
            "found": False
        }


def print_section(title: str):
    """Print section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print('='*70)


def main():
    """Run smoke tests"""
    print("""
╔════════════════════════════════════════════════════════════════════╗
║                                                                    ║
║              FastVLM Vision Smoke Test Suite                       ║
║                     6 Image Types × Validation                     ║
║                                                                    ║
╚════════════════════════════════════════════════════════════════════╝
""")
    
    # Check server health first
    print_section("Pre-flight: Server Health")
    
    try:
        from fastvlm.fastvlm_client import FastVLMClient
        
        client = FastVLMClient()
        health = client.health()
        
        print(f"Status:       {health['status']}")
        print(f"Model:        {health['model']}")
        print(f"Model exists: {health['model_exists']}")
        
        if health['status'] != 'healthy':
            print("\n❌ Server not healthy. Start with: make fastvlm-server")
            sys.exit(1)
        
        print("✅ Server is healthy")
    
    except Exception as e:
        print(f"❌ Cannot connect to FastVLM server: {e}")
        print("   Start server with: make fastvlm-server")
        sys.exit(1)
    
    # Create test images
    print_section("Generating Test Images")
    tests = create_test_images()
    print(f"✅ Created {len(tests)} test images")
    
    # Run tests
    print_section("Running Vision Tests")
    
    results = []
    for test_name, (image_path, prompt, expected) in tests.items():
        print(f"\n🔍 Test: {test_name}")
        print(f"   Prompt: {prompt}")
        
        result = run_vision_test(test_name, image_path, prompt, expected)
        results.append(result)
        
        print(f"   {result['status']}")
        if result.get('error'):
            print(f"   Error: {result['error']}")
        else:
            print(f"   Latency: {result['latency_ms']:.0f}ms (server), {result['total_ms']:.0f}ms (total)")
            print(f"   Expected '{expected}': {'Found' if result['found'] else 'Not found'}")
            print(f"   Response: {result['response_preview']}")
    
    # Summary
    print_section("Test Summary")
    
    passed = sum(1 for r in results if r['status'] == "✅ PASS")
    partial = sum(1 for r in results if r['status'] == "⚠️  PARTIAL")
    failed = sum(1 for r in results if r['status'] == "❌ FAIL")
    total = len(results)
    
    print(f"\n  Results: {passed} passed, {partial} partial, {failed} failed (total: {total})")
    
    # Latency stats
    latencies = [r['latency_ms'] for r in results if r['latency_ms'] > 0]
    if latencies:
        latencies_sorted = sorted(latencies)
        p50 = latencies_sorted[len(latencies_sorted) // 2]
        p95 = latencies_sorted[int(len(latencies_sorted) * 0.95)]
        avg = sum(latencies) / len(latencies)
        
        print(f"\n  Latency: avg={avg:.0f}ms, p50={p50:.0f}ms, p95={p95:.0f}ms")
        
        if p95 > 3000:
            print(f"  ⚠️  p95 latency is high ({p95:.0f}ms > 3000ms)")
        elif p95 > 1500:
            print(f"  ⚠️  p95 latency is moderate ({p95:.0f}ms)")
        else:
            print(f"  ✅ p95 latency is good ({p95:.0f}ms)")
    
    # Detailed results table
    print(f"\n  {'Test':<20} {'Status':<12} {'Latency':<10} {'Expected Found'}")
    print(f"  {'-'*20} {'-'*12} {'-'*10} {'-'*14}")
    
    for r in results:
        test_name = r['test'][:18]
        status = r['status']
        latency = f"{r['latency_ms']:.0f}ms" if r['latency_ms'] > 0 else "N/A"
        found = "✓" if r['found'] else "✗"
        
        print(f"  {test_name:<20} {status:<12} {latency:<10} {found}")
    
    # Cleanup
    if results and results[0].get('error') is None:
        test_dir = Path(tests[list(tests.keys())[0]][0]).parent
        import shutil
        try:
            shutil.rmtree(test_dir)
            print("\n  🧹 Cleaned up test images")
        except:
            pass
    
    # Exit code
    if failed > 0:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1
    elif partial > 0:
        print("\n✅ All tests passed (some partial matches)")
        return 0
    else:
        print("\n🎉 All tests passed!")
        return 0


if __name__ == "__main__":
    sys.exit(main())

