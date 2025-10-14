#!/usr/bin/env python3
"""
Test script to verify URL encoding is correct and no '+' signs appear
"""

import urllib.parse

def test_url_encoding():
    """Test that spaces are encoded as %20, not +"""
    print("🧪 Testing URL encoding...")
    
    test_summaries = [
        "All systems nominal. 7-day success 100.0%. 30 decisions last 24 hours.",
        "Status degraded. 2 active alerts. 7-day success 92.5%. P95 1800ms.",
        "Status critical. 5 active alerts. 7-day success 88.0%. P95 2800ms."
    ]
    
    for summary in test_summaries:
        print(f"\n📝 Testing: {summary[:50]}...")
        
        # Test with quote_via=quote (correct way - no +)
        encoded_correct = urllib.parse.urlencode({"summary": summary}, quote_via=urllib.parse.quote)
        has_plus_correct = "+" in encoded_correct
        
        # Test with default urlencode (old way - has +)
        encoded_default = urllib.parse.urlencode({"summary": summary})
        has_plus_default = "+" in encoded_default
        
        if has_plus_correct:
            print("   ❌ FAIL: quote_via=quote still has '+' signs")
            print(f"      {encoded_correct[:80]}...")
        else:
            print("   ✅ PASS: quote_via=quote uses %20 for spaces")
        
        if has_plus_default:
            print("   ℹ️  INFO: Default urlencode would have used '+' (old behavior)")
        
        # Verify %20 is present
        if "%20" in encoded_correct:
            print("   ✅ PASS: Spaces encoded as %20")
        else:
            print("   ⚠️  WARN: No %20 found (maybe no spaces in summary?)")

def test_swift_decoding():
    """Test that Swift properly decodes both + and %20"""
    print("\n🧪 Testing Swift URL decoding logic...")
    
    test_cases = [
        ("All+systems+nominal", "All systems nominal", "Decodes + as space"),
        ("All%20systems%20nominal", "All systems nominal", "Decodes %20 as space"),
        ("100.0%25", "100.0%", "Decodes %25 as %"),
        ("7-day+success+100.0%25", "7-day success 100.0%", "Mixed encoding")
    ]
    
    for encoded, expected, description in test_cases:
        # Simulate Swift's urlQueryDecoded
        plus_fixed = encoded.replace("+", " ")
        decoded = urllib.parse.unquote(plus_fixed)
        
        if decoded == expected:
            print(f"   ✅ PASS: {description}")
            print(f"      '{encoded}' -> '{decoded}'")
        else:
            print(f"   ❌ FAIL: {description}")
            print(f"      '{encoded}' -> '{decoded}' (expected '{expected}')")

def test_end_to_end():
    """Test the full end-to-end flow"""
    print("\n🧪 Testing end-to-end URL generation...")
    
    # Simulate what open_report() does
    title = "Daily System Health"
    summary = "All systems nominal. 7-day success 100.0%. 30 decisions last 24 hours."
    
    params = {
        "title": title,
        "summary": summary,
        "report_id": "test123",
        "ts": "1234567890"
    }
    
    url = "athena://report?" + urllib.parse.urlencode(params, quote_via=urllib.parse.quote)
    
    print("   Generated URL (first 150 chars):")
    print(f"   {url[:150]}...")
    
    if "+" in url:
        print("   ❌ FAIL: URL contains '+' signs")
        # Find where the + appears
        idx = url.index("+")
        print(f"      Found at position {idx}: ...{url[max(0,idx-10):idx+20]}...")
    else:
        print("   ✅ PASS: URL contains no '+' signs")
    
    if "%20" in url:
        print("   ✅ PASS: Spaces encoded as %20")
    else:
        print("   ⚠️  WARN: No %20 found (maybe no spaces?)")

def main():
    print("🚀 Athena URL Encoding Test Suite")
    print("=" * 60)
    
    test_url_encoding()
    test_swift_decoding()
    test_end_to_end()
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("\n💡 Expected speech output (no plus signs):")
    print("   'All systems nominal. 7-day success 100.0 percent. 30 decisions last 24 hours.'")
    print("\n🔧 Fixes applied:")
    print("   • Python: quote_via=urllib.parse.quote (spaces -> %20, not +)")
    print("   • Swift: urlQueryDecoded extension (handles both + and %20)")

if __name__ == "__main__":
    main()

