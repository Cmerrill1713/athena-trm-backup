#!/usr/bin/env python3
"""
TEST ACTUAL DATA PROCESSING
Test with real image and audio data
"""
import asyncio
import httpx
import base64
import os
from pathlib import Path

BASE = "http://localhost"

async def test_actual_processing():
    print("🎭 TESTING ACTUAL DATA PROCESSING")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # ================================================================
        # TEST 1: FastVLM Image Analysis (Real Image)
        # ================================================================
        print("\n1️⃣  FastVLM - Testing with REAL Image")
        print("-"*80)
        
        # Create simple test image (1x1 red pixel PNG)
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        
        try:
            r = await client.post(f"{BASE}:8088/analyze",
                json={
                    "image_b64": test_image_b64,
                    "prompt": "Describe this image"
                })
            
            if r.status_code == 200:
                result = r.json()
                print(f"  ✅ FastVLM analyzed image!")
                print(f"     Caption: {result.get('caption', 'N/A')[:60]}...")
                print(f"     Confidence: {result.get('confidence', 0)}")
            else:
                print(f"  ❌ FastVLM failed: {r.status_code}")
                print(f"     Response: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ FastVLM error: {str(e)[:50]}")
        
        # ================================================================
        # TEST 2: Whisper Audio Transcription (Real Audio)
        # ================================================================
        print("\n2️⃣  Whisper - Testing with REAL Audio")
        print("-"*80)
        
        # Create simple WAV file (silence, 1 second)
        import struct
        import io
        
        # Generate 1 second of silence at 16kHz
        sample_rate = 16000
        duration = 1.0
        num_samples = int(sample_rate * duration)
        
        # WAV header
        wav_buffer = io.BytesIO()
        wav_buffer.write(b'RIFF')
        wav_buffer.write(struct.pack('<I', 36 + num_samples * 2))
        wav_buffer.write(b'WAVE')
        wav_buffer.write(b'fmt ')
        wav_buffer.write(struct.pack('<I', 16))
        wav_buffer.write(struct.pack('<H', 1))  # PCM
        wav_buffer.write(struct.pack('<H', 1))  # Mono
        wav_buffer.write(struct.pack('<I', sample_rate))
        wav_buffer.write(struct.pack('<I', sample_rate * 2))
        wav_buffer.write(struct.pack('<H', 2))
        wav_buffer.write(struct.pack('<H', 16))
        wav_buffer.write(b'data')
        wav_buffer.write(struct.pack('<I', num_samples * 2))
        
        # Silent samples
        for _ in range(num_samples):
            wav_buffer.write(struct.pack('<h', 0))
        
        audio_bytes = wav_buffer.getvalue()
        
        try:
            # Send as multipart form data
            files = {"audio": ("test.wav", audio_bytes, "audio/wav")}
            
            # Use httpx with files parameter
            r = await client.post(f"{BASE}:8095/transcribe", files=files)
            
            if r.status_code == 200:
                result = r.json()
                print(f"  ✅ Whisper transcribed audio!")
                print(f"     Text: '{result.get('text', 'N/A')}'")
                print(f"     Language: {result.get('language', 'N/A')}")
            else:
                print(f"  ❌ Whisper failed: {r.status_code}")
                print(f"     Response: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ Whisper error: {str(e)[:50]}")
        
        # ================================================================
        # TEST 3: Kokoro TTS (Real Audio Generation)
        # ================================================================
        print("\n3️⃣  Kokoro TTS - Testing REAL Audio Generation")
        print("-"*80)
        
        try:
            r = await client.post(f"{BASE}:8091/synthesize",
                json={"text": "Hello, this is Athena speaking. Testing text to speech.", "voice": "en_US-female"})
            
            if r.status_code == 200:
                result = r.json()
                audio = result.get("audio", "")
                duration = result.get("duration_ms", 0)
                
                if len(audio) > 1000:  # Real audio should be > 1KB
                    print(f"  ✅ Kokoro generated REAL audio!")
                    print(f"     Audio size: {len(audio)} bytes (base64)")
                    print(f"     Duration: {duration}ms")
                    print(f"     Sample rate: {result.get('sample_rate', 'N/A')}Hz")
                else:
                    print(f"  ⚠️  Kokoro returned audio but seems small: {len(audio)} bytes")
            else:
                print(f"  ❌ Kokoro failed: {r.status_code}")
                print(f"     Response: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ Kokoro error: {str(e)[:50]}")
    
    print("\n" + "="*80)
    print("📊 ACTUAL DATA PROCESSING TEST RESULTS")
    print("="*80)
    print("\n✅ Tested real image, audio, and TTS generation!")
    print("   See results above for details.")

if __name__ == "__main__":
    asyncio.run(test_actual_processing())
