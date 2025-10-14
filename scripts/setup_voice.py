#!/usr/bin/env python3
"""
Athena Voice Setup Helper

Sets up the preferred voice for Athena Reporter.
Run this once to pin your favorite voice.
"""

import subprocess
import sys

def list_available_voices():
    """List all available macOS voices"""
    try:
        result = subprocess.run(['say', '-v', '?'], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            print("❌ Failed to list voices")
            return []
        
        voices = []
        for line in result.stdout.strip().split('\n'):
            if '#' in line:
                # Parse: "Samantha (Enhanced)    #en_US   Samantha"
                parts = line.split('#')
                if len(parts) >= 2:
                    name_part = parts[0].strip()
                    lang_part = parts[1].strip().split()[0] if parts[1].strip() else ""
                    voice_name = parts[1].strip().split()[1] if len(parts[1].strip().split()) > 1 else name_part
                    
                    # Try to construct identifier
                    identifier = f"com.apple.ttsbundle.{voice_name}-compact"
                    
                    voices.append({
                        'name': voice_name,
                        'display': name_part,
                        'language': lang_part,
                        'identifier': identifier
                    })
        
        return voices
    except Exception as e:
        print(f"❌ Error listing voices: {e}")
        return []

def test_voice(identifier):
    """Test a voice by speaking"""
    try:
        print(f"🎤 Testing voice: {identifier}")
        subprocess.run([
            'say', '-v', identifier, 
            'Hi, I am Athena. This is a test of the selected voice.'
        ], timeout=5)
        return True
    except Exception as e:
        print(f"❌ Voice test failed: {e}")
        return False

def set_voice_in_app(identifier):
    """Set voice in the app using UserDefaults"""
    try:
        # Use defaults command to set the voice
        subprocess.run([
            'defaults', 'write', 'com.athena.reporter', 'athena.voice.id', identifier
        ], check=True)
        
        print(f"✅ Voice set: {identifier}")
        return True
    except Exception as e:
        print(f"❌ Failed to set voice: {e}")
        return False

def main():
    print("🎤 Athena Voice Setup")
    print("=" * 30)
    
    # List voices
    voices = list_available_voices()
    if not voices:
        print("❌ No voices found")
        sys.exit(1)
    
    # Filter for English voices (most common)
    english_voices = [v for v in voices if v['language'].startswith('en')]
    if english_voices:
        voices = english_voices
        print("📋 English voices found:")
    else:
        print("📋 All voices found:")
    
    # Show options
    for i, voice in enumerate(voices[:10]):  # Limit to first 10
        print(f"  {i+1:2d}. {voice['display']:<25} ({voice['language']})")
    
    print("\n💡 Recommended voices:")
    print("   • Samantha (Enhanced) - Clear, professional")
    print("   • Ava (Enhanced) - Warm, friendly") 
    print("   • Serena (Enhanced) - Smooth, articulate")
    
    # Get user choice
    try:
        choice = input(f"\nSelect voice (1-{min(len(voices), 10)}) or press Enter for Samantha: ").strip()
        
        if not choice:
            # Default to Samantha
            selected = next((v for v in voices if 'samantha' in v['name'].lower()), voices[0])
        else:
            idx = int(choice) - 1
            if 0 <= idx < len(voices):
                selected = voices[idx]
            else:
                print("❌ Invalid choice")
                sys.exit(1)
        
        print(f"\n🎯 Selected: {selected['display']}")
        
        # Test the voice
        if test_voice(selected['identifier']):
            print("✅ Voice test successful!")
            
            # Set in app
            if set_voice_in_app(selected['identifier']):
                print("\n🎉 Voice setup complete!")
                print(f"   Voice: {selected['display']}")
                print(f"   ID: {selected['identifier']}")
                print("\n💡 To test in Athena Reporter:")
                print("   1. Run: make reporter-build")
                print("   2. Run: make reporter-run")
                print("   3. Press ⌘T to test voice")
            else:
                print("❌ Failed to save voice preference")
                sys.exit(1)
        else:
            print("❌ Voice test failed - trying fallback")
            # Try without -compact suffix
            fallback_id = selected['identifier'].replace('-compact', '')
            if test_voice(fallback_id):
                set_voice_in_app(fallback_id)
                print(f"✅ Using fallback ID: {fallback_id}")
            else:
                print("❌ Voice not available")
                sys.exit(1)
                
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
