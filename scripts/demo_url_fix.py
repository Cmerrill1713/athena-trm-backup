#!/usr/bin/env python3
"""
Visual demo of the URL encoding fix
"""

import urllib.parse

def demo_encoding():
    """Show the difference between old and new encoding"""
    summary = "All systems nominal. 7-day success 100.0%. 30 decisions last 24 hours."
    
    print("🎯 Athena URL Encoding Fix Demo")
    print("=" * 70)
    print()
    
    print("📝 Original text:")
    print(f"   {summary}")
    print()
    
    print("❌ OLD (form encoding - spaces become '+'):")
    old_url = "athena://report?" + urllib.parse.urlencode({"summary": summary})
    print(f"   {old_url}")
    print()
    print("   🗣️  Athena would say:")
    print(f"   'All+systems+nominal.+7-day+success+100.0%25.+30+decisions+last+24+hours.'")
    print()
    
    print("✅ NEW (percent encoding - spaces become '%20'):")
    new_url = "athena://report?" + urllib.parse.urlencode({"summary": summary}, quote_via=urllib.parse.quote)
    print(f"   {new_url}")
    print()
    print("   🗣️  Athena says:")
    print(f"   'All systems nominal. 7-day success 100.0 percent. 30 decisions last 24 hours.'")
    print()
    
    print("=" * 70)
    print()
    print("💡 Key differences:")
    print("   • Spaces: '+' → '%20'")
    print("   • Percent: '%25' (percent encoding is still needed)")
    print("   • Speech: Clean and natural!")
    print()
    print("🔧 Fixes:")
    print("   • Python: quote_via=urllib.parse.quote")
    print("   • Swift: .urlQueryDecoded extension (handles both + and %20)")

if __name__ == "__main__":
    demo_encoding()

