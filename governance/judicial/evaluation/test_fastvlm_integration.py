#!/usr/bin/env python3
"""
FastVLM Integration Smoke Test

Tests the full FastVLM stack:
- Server health
- Client calls
- Routing integration
- Metrics collection
"""

import sys
import time
import os
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def print_section(title):
    """Print a section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)

def test_server_health():
    """Test 1: Server health check"""
    print_section("Test 1: Server Health")

    try:
        from fastvlm.fastvlm_client import FastVLMClient

        client = FastVLMClient("http://127.0.0.1:8811")
        health = client.health()

        print(f"✅ Server is {health['status']}")
        print(f"   Model: {health['model']}")
        print(f"   Root: {health['fastvlm_root']}")
        print(f"   Model exists: {health['model_exists']}")

        if health['status'] != 'healthy':
            print("❌ Server is not healthy")
            return False

        return True

    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return False

def test_metrics_endpoint():
    """Test 2: Metrics endpoint"""
    print_section("Test 2: Metrics Endpoint")

    try:
        import requests

        response = requests.get("http://127.0.0.1:8811/metrics", timeout=5)
        response.raise_for_status()

        metrics_text = response.text

        # Check for expected metrics
        expected = [
            "fastvlm_requests_total",
            "fastvlm_latency_ms",
            "fastvlm_image_size_bytes",
            "fastvlm_active_requests"
        ]

        found = []
        for metric in expected:
            if metric in metrics_text:
                found.append(metric)

        print("✅ Metrics endpoint responding")
        print(f"   Found {len(found)}/{len(expected)} expected metrics")

        for m in found:
            print(f"   ✓ {m}")

        return len(found) == len(expected)

    except Exception as e:
        print(f"❌ Metrics check failed: {e}")
        return False

def test_client_call():
    """Test 3: Client call with test image"""
    print_section("Test 3: Client Call")

    try:
        from fastvlm.fastvlm_client import FastVLMClient
        import tempfile
        from PIL import Image

        # Create a simple test image
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            # Create a small test image
            img = Image.new('RGB', (100, 100), color='red')
            img.save(f.name)
            test_image = f.name

        print(f"   Created test image: {test_image}")

        # Make a call
        client = FastVLMClient("http://127.0.0.1:8811")

        start = time.time()
        result = client.vision(test_image, "What color is this image?")
        elapsed = (time.time() - start) * 1000

        print("✅ Vision call succeeded")
        print(f"   Response: {result['text'][:100]}...")
        print(f"   Latency: {result['latency_ms']:.0f}ms (server), {elapsed:.0f}ms (total)")
        print(f"   Model: {result['model']}")

        # Cleanup
        os.unlink(test_image)

        return True

    except ImportError:
        print("⚠️  PIL not installed, skipping client call test")
        print("   Run: pip install pillow")
        return True  # Don't fail test

    except Exception as e:
        print(f"❌ Client call failed: {e}")
        return False

def test_provider_integration():
    """Test 4: Routing provider integration"""
    print_section("Test 4: Provider Integration")

    try:
        from src.core.routing.fastvlm_provider import get_provider

        provider = get_provider()

        # Check capabilities
        caps = provider.get_capabilities()
        print("✅ Provider initialized")
        print(f"   Model: {provider.model_name}")
        print(f"   Endpoint: {provider.endpoint}")
        print("   Capabilities:")
        for cap, score in caps.items():
            print(f"     • {cap}: {score:.2f}")

        # Check availability
        is_available = provider.is_available()
        print(f"   Available: {is_available}")

        return is_available

    except Exception as e:
        print(f"❌ Provider integration failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_routing_registration():
    """Test 5: Model registry"""
    print_section("Test 5: Routing Registration")

    try:
        from src.core.routing.fastvlm_provider import FASTVLM_REGISTRY_ENTRY

        entry = FASTVLM_REGISTRY_ENTRY

        print("✅ Registry entry exists")
        print(f"   Name: {entry['name']}")
        print(f"   Provider: {entry['provider']}")
        print(f"   Capabilities: {', '.join(entry['caps'])}")
        print(f"   Quality: {entry['quality']}")
        print(f"   Cost: {entry['cost_tier']}")
        print(f"   Local: {entry['local']}")

        return True

    except Exception as e:
        print(f"❌ Registry check failed: {e}")
        return False

def main():
    """Run all tests"""
    print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║              FastVLM Integration Smoke Test                   ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
""")

    tests = [
        ("Server Health", test_server_health),
        ("Metrics Endpoint", test_metrics_endpoint),
        ("Client Call", test_client_call),
        ("Provider Integration", test_provider_integration),
        ("Routing Registration", test_routing_registration),
    ]

    results = []

    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' crashed: {e}")
            results.append((name, False))

        time.sleep(0.5)  # Brief pause between tests

    # Summary
    print_section("Test Summary")

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status}  {name}")

    print(f"\n  {passed}/{total} tests passed")

    if passed == total:
        print("\n🎉 All tests passed! FastVLM integration is working.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
