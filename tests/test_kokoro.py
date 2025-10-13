#!/usr/bin/env python3
"""Quick test of Kokoro TTS"""

print("🧪 Testing Kokoro TTS...")

try:
    print("1️⃣  Importing kokoro...")
    from kokoro import KPipeline
    print("✅ Import successful")
    
    print("2️⃣  Initializing pipeline...")
    pipeline = KPipeline(lang_code='a')
    print("✅ Pipeline initialized")
    
    print("3️⃣  Generating speech...")
    text = "This is Athena using Kokoro TTS. The voice should sound natural and warm."
    generator = pipeline(text, voice='af_heart')
    
    chunks = list(generator)
    print(f"✅ Generated {len(chunks)} audio chunks")
    
    print("4️⃣  Saving to file...")
    import soundfile as sf
    import numpy as np
    
    audio_data = [chunk[2] for chunk in chunks]
    combined = np.concatenate(audio_data)
    sf.write('/tmp/kokoro_test.wav', combined, 24000)
    print(f"✅ Saved to /tmp/kokoro_test.wav ({len(combined)/24000:.1f}s)")
    
    print("")
    print("🎧 Play the audio:")
    print("   afplay /tmp/kokoro_test.wav")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

