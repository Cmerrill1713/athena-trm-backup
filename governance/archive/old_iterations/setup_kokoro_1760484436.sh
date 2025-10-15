#!/bin/bash
# Setup Kokoro TTS for Athena

echo "🎤 Setting up Kokoro TTS for Athena"
echo "===================================="
echo ""

echo "1️⃣  Installing Kokoro and dependencies..."
pip3 install -q kokoro soundfile || pip3 install kokoro soundfile
echo "✅ Kokoro installed"
echo ""

echo "2️⃣  Installing espeak-ng (required for G2P)..."
if command -v espeak-ng &> /dev/null; then
    echo "✅ espeak-ng already installed"
else
    echo "Installing espeak-ng via Homebrew..."
    brew install espeak-ng || echo "⚠️  Please install espeak-ng manually"
fi
echo ""

echo "3️⃣  Testing Kokoro..."
python3 << 'EOF'
import sys
try:
    from kokoro import KPipeline
    import soundfile as sf
    import os
    
    print("Initializing Kokoro pipeline (American English)...")
    pipeline = KPipeline(lang_code='a')
    
    text = "This is Athena, speaking with the Kokoro neural voice. All systems nominal."
    
    print("Generating speech...")
    generator = pipeline(text, voice='af_heart', speed=1.0)
    
    output_file = "/tmp/athena_kokoro_test.wav"
    for i, (gs, ps, audio) in enumerate(generator):
        sf.write(output_file, audio, 24000)
        break  # Just the first segment
    
    print(f"✅ Generated: {output_file}")
    print("Playing audio...")
    os.system(f"afplay {output_file}")
    print("✅ Playback complete")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("   Run: pip3 install kokoro soundfile")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

echo ""
echo "✅ Kokoro setup complete!"
echo ""
echo "💡 Next steps:"
echo "   1. Run: make kokoro-server (starts HTTP TTS server)"
echo "   2. Run: make report-health (Athena will use Kokoro)"
echo "   3. Switch in app menu: Athena → Use Kokoro"

