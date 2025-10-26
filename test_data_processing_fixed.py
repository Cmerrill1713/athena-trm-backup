#!/usr/bin/env python3
"""
TEST ACTUAL DATA PROCESSING - FIXED
Test with correct request formats
"""
import asyncio
import httpx
import base64
import struct
import io

BASE = "http://localhost"

async def test_multimodal():
    print("🎭 TESTING ACTUAL MULTIMODAL PROCESSING (FIXED)")
    print("="*80)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        
        # ================================================================
        # TEST 1: Kokoro TTS - Simple Text
        # ================================================================
        print("\n1️⃣  Kokoro TTS - Generate Speech")
        print("-"*80)
        
        try:
            r = await client.post(f"{BASE}:8091/synthesize",
                json={
                    "text": "Hello world",
                    "voice": "en_US-female",
                    "format": "wav"
                })
            
            if r.status_code == 200:
                data = r.json()
                audio_b64 = data.get("audio", "")
                duration = data.get("duration_ms", 0)
                
                # Decode to check size
                if audio_b64:
                    audio_bytes = base64.b64decode(audio_b64)
                    print(f"  ✅ Kokoro generated audio!")
                    print(f"     Raw audio: {len(audio_bytes)} bytes")
                    print(f"     Base64: {len(audio_b64)} chars")
                    print(f"     Duration: {duration}ms")
                    print(f"     Sample rate: {data.get('sample_rate', 0)}Hz")
                else:
                    print(f"  ⚠️  Kokoro returned but no audio data")
            else:
                print(f"  ❌ Kokoro failed: {r.status_code}")
                # Get detailed error
                try:
                    error = r.json()
                    print(f"     Error: {error.get('detail', r.text[:80])}")
                except:
                    print(f"     Response: {r.text[:80]}")
        except Exception as e:
            print(f"  ❌ Kokoro error: {str(e)[:60]}")
        
        # ================================================================
        # TEST 2: FastVLM - Check API format first
        # ================================================================
        print("\n2️⃣  FastVLM - Image Analysis")
        print("-"*80)
        
        # Get health to see expected format
        try:
            health = await client.get(f"{BASE}:8088/health")
            print(f"  FastVLM Health: {health.json()}")
        except:
            pass
        
        # Try with correct key
        test_image_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
        
        try:
            # Try "image" key
            r = await client.post(f"{BASE}:8088/analyze",
                json={
                    "image": test_image_b64,
                    "prompt": "What is in this image?"
                })
            
            if r.status_code == 200:
                result = r.json()
                print(f"  ✅ FastVLM analyzed image!")
                print(f"     Caption: {result.get('caption', 'N/A')}")
                print(f"     Confidence: {result.get('confidence', 0)}")
            else:
                print(f"  ❌ FastVLM failed: {r.status_code}")
                try:
                    error = r.json()
                    print(f"     Error: {error}")
                except:
                    print(f"     Response: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ FastVLM error: {str(e)[:60]}")
        
        # ================================================================
        # TEST 3: Whisper - Real Audio with Proper Format
        # ================================================================
        print("\n3️⃣  Whisper STT - Audio Transcription")
        print("-"*80)
        
        # Generate longer audio (3 seconds)
        sample_rate = 16000
        duration = 3.0
        num_samples = int(sample_rate * duration)
        
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
        
        # Add some non-zero samples (simple tone)
        import math
        frequency = 440  # A note
        for i in range(num_samples):
            value = int(16000 * math.sin(2 * math.pi * frequency * i / sample_rate))
            wav_buffer.write(struct.pack('<h', value))
        
        audio_bytes = wav_buffer.getvalue()
        
        try:
            files = {"audio": ("test.wav", audio_bytes, "audio/wav")}
            r = await client.post(f"{BASE}:8095/transcribe", files=files)
            
            if r.status_code == 200:
                result = r.json()
                print(f"  ✅ Whisper transcribed audio!")
                print(f"     Text: '{result.get('text', 'N/A')}'")
                print(f"     Language: {result.get('language', 'N/A')}")
            else:
                print(f"  ❌ Whisper failed: {r.status_code}")
                try:
                    error = r.json()
                    print(f"     Error: {error.get('detail', r.text[:80])}")
                except:
                    print(f"     Response: {r.text[:100]}")
        except Exception as e:
            print(f"  ❌ Whisper error: {str(e)[:60]}")
    
    print("\n" + "="*80)
    print("📊 ACTUAL DATA PROCESSING RESULTS")
    print("="*80)
    print("\n✅ Tested with real binary data (not just health checks)!")
    print("   Results show which services can process actual data.")

if __name__ == "__main__":
    asyncio.run(test_multimodal())
