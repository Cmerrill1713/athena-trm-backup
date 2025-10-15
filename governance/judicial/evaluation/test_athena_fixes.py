#!/usr/bin/env python3
"""
Test Athena Reporter Fixes

Tests both the voice fix and the empty report fix.
"""

import subprocess
import time

def test_voice_fix():
    """Test that voice is properly pinned"""
    print("🎤 Testing Voice Fix")
    print("=" * 30)

    # Test voice with direct URL
    url = (
        "athena://report?"
        "title=Voice Test&"
        "summary=Hi, I am Athena. This is a voice test using your pinned voice settings.&"
        "md=# Voice Test\n\nThis is a test of the voice system.&"
        "nonce=voice_test&"
        "ts=123456"
    )

    print("🗣️  Opening voice test...")
    result = subprocess.run(["open", url], capture_output=True)

    if result.returncode == 0:
        print("✅ Voice test URL opened successfully")
        print("🔍 Check Console.app for voice logs:")
        print("   Look for: 🔊 Athena voice -> id=..., name=...")
        print("   Should show: Samantha or your preferred voice")
    else:
        print("❌ Failed to open voice test")

    time.sleep(2)

def test_report_fix():
    """Test that reports load properly from file"""
    print("\n📄 Testing Report Fix")
    print("=" * 30)

    # Generate a test report with file path
    title = "Test Report Fix"
    summary = "This report tests the markdown file loading fix. It should show full content instead of (empty report)."

    # Create a substantial markdown report
    md_content = """# Test Report Fix

## Status: ✅ Working

This report tests the markdown file loading fix.

### Key Features Tested

1. **File Path Loading** - Markdown loaded from temp file
2. **URL Length Handling** - No more truncation issues
3. **Content Preservation** - Full markdown rendered
4. **Voice Integration** - Proper voice pinning

### Sample Content

Here's some sample content to test rendering:

```python
def test_function():
    return "Hello, Athena!"
```

### Table Test

| Feature | Status | Notes |
|---------|--------|-------|
| Voice Pinning | ✅ | Should use Samantha |
| File Loading | ✅ | From temp file |
| Markdown Rendering | ✅ | Full content |
| Deduplication | ✅ | Single window |

### Long Content Test

This is a longer section to ensure that substantial reports load properly without truncation. The previous implementation had issues with URL length limits when passing markdown content directly in the URL parameters.

With the new file-based approach, we can handle reports of any size without worrying about URL encoding limits or truncation issues.

### Conclusion

Both fixes should now be working:
- ✅ Voice stays pinned (no more generic default)
- ✅ Reports load full content (no more empty reports)
"""

    # Use the actual report generator
    print("📊 Generating test report...")
    result = subprocess.run([
        "python3", "scripts/athena_report.py", "health"
    ], capture_output=True, text=True)

    print("📋 Report generation output:")
    for line in result.stderr.strip().split('\n'):
        if line.strip():
            print(f"   {line}")

    if result.returncode == 0:
        print("✅ Report generated successfully")
        print("🔍 Check the Athena Reporter window:")
        print("   - Should show full markdown content")
        print("   - Should NOT show '(empty report)'")
        print("   - Voice should be Samantha (not generic)")
    else:
        print("❌ Report generation failed")
        print(f"Error: {result.stderr}")

def check_voice_settings():
    """Check current voice settings"""
    print("\n🎛️  Current Voice Settings")
    print("=" * 30)

    try:
        # Check voice name
        result = subprocess.run([
            "defaults", "read", "com.athena.reporter", "athena.voice.name"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Voice name: {result.stdout.strip()}")
        else:
            print("❌ No voice name set")

        # Check voice ID
        result = subprocess.run([
            "defaults", "read", "com.athena.reporter", "athena.voice.id"
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Voice ID: {result.stdout.strip()}")
        else:
            print("❌ No voice ID set")

        # Check if Kokoro is disabled
        result = subprocess.run([
            "defaults", "read", "com.athena.reporter", "athena.voice.engine"
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print("✅ Kokoro disabled (good)")
        else:
            print(f"⚠️  Kokoro enabled: {result.stdout.strip()}")

    except Exception as e:
        print(f"❌ Error checking settings: {e}")

def main():
    print("🧪 Athena Reporter Fixes Test")
    print("=" * 40)

    check_voice_settings()
    test_voice_fix()
    test_report_fix()

    print("\n🎯 Test Summary")
    print("=" * 30)
    print("1. Voice Fix:")
    print("   - Check Console.app for voice logs")
    print("   - Should show: 🔊 Athena voice -> id=..., name=Samantha")
    print("   - Should NOT show generic system voice")
    print()
    print("2. Report Fix:")
    print("   - Check Athena Reporter window")
    print("   - Should show full markdown content")
    print("   - Should NOT show '(empty report)'")
    print("   - Should be single window (no duplicates)")
    print()
    print("3. If issues persist:")
    print("   - Run: python3 scripts/setup_voice.py")
    print("   - Check: defaults read com.athena.reporter")
    print("   - Rebuild: make reporter-build")

if __name__ == "__main__":
    main()
