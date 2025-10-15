#!/usr/bin/env python3
"""
Kokoro TTS FastAPI Service
Simple web service wrapper for Kokoro TTS on port 8020
"""

import io
import base64
import os
import sys
from typing import Optional
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Add path for common imports
# Need to go up to GitHub root: kokoro -> GitHub
github_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, github_root)

# Try to import common.ops, but don't fail if not available
try:
    from common.ops import add_health_endpoints
    HAS_COMMON_OPS = True
except ImportError:
    HAS_COMMON_OPS = False

# Prometheus metrics
from prometheus_client import Counter, Histogram, generate_latest, REGISTRY

try:
    from kokoro import KPipeline
    KOKORO_AVAILABLE = True
    # Global pipeline instance
    pipeline: Optional[KPipeline] = None
except ImportError:
    KOKORO_AVAILABLE = False
    pipeline = None

app = FastAPI(title="Kokoro TTS Service", version="1.0.0")

# Add standard health + metrics endpoints if available
if HAS_COMMON_OPS:
    add_health_endpoints(app)
else:
    # Add basic metrics endpoint
    @app.get("/metrics")
    async def metrics():
        """Prometheus metrics endpoint"""
        return generate_latest(REGISTRY)

# Custom Prometheus metrics
TTS_REQUESTS = Counter('tts_requests_total', 'Total TTS requests', ['status', 'voice'])
TTS_LATENCY = Histogram('tts_request_duration_seconds', 'TTS request latency', ['voice'])
TTS_AUDIO_LENGTH = Histogram('tts_audio_length_seconds', 'Generated audio length')

class TTSRequest(BaseModel):
    text: str
    voice: str = "af_heart"
    speed: float = 1.0
    language: str = "a"  # American English

class TTSResponse(BaseModel):
    audio_base64: str
    model: str = "Kokoro-82M"
    status: str = "ok"
    voices: list = ["af_heart", "af_sky", "af", "am"]

@app.on_event("startup")
async def startup_event():
    global pipeline
    if KOKORO_AVAILABLE:
        try:
            pipeline = KPipeline(lang_code='a')
            print("✅ Kokoro TTS pipeline initialized")
        except Exception as e:
            print(f"❌ Failed to initialize Kokoro pipeline: {e}")
            pipeline = None
    else:
        print("⚠️  Kokoro not available - install with: pip install kokoro")

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "model": "Kokoro-82M",
        "status": "ok" if pipeline is not None else "error",
        "voices": ["af_heart", "af_sky", "af", "am"],
        "available": KOKORO_AVAILABLE
    }

@app.get("/voices")
async def list_voices():
    """List available voices"""
    return {
        "voices": ["af_heart", "af_sky", "af", "am"],
        "default": "af_heart"
    }

@app.post("/synthesize")
async def synthesize_speech(request: TTSRequest):
    """Convert text to speech using Kokoro TTS"""
    if not KOKORO_AVAILABLE:
        raise HTTPException(status_code=503, detail="Kokoro TTS not available")
    
    if pipeline is None:
        raise HTTPException(status_code=503, detail="Kokoro pipeline not initialized")
    
    with TTS_LATENCY.labels(voice=request.voice).time():
        try:
            # Generate audio
            audio_chunks = []
            for result in pipeline(request.text, voice=request.voice, speed=request.speed):
                audio_chunks.append(result.audio)
            
            if not audio_chunks:
                raise HTTPException(status_code=400, detail="No audio generated")
            
            # Combine audio chunks (simple concatenation)
            import numpy as np
            combined_audio = np.concatenate(audio_chunks)
            
            # Calculate audio length
            audio_length_seconds = len(combined_audio) / 24000.0  # 24kHz sample rate
            
            # Convert to WAV format
            import soundfile as sf
            buffer = io.BytesIO()
            sf.write(buffer, combined_audio, 24000, format='WAV')
            buffer.seek(0)
            
            # Encode as base64
            audio_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            # Record success metrics
            TTS_REQUESTS.labels(status='success', voice=request.voice).inc()
            TTS_AUDIO_LENGTH.observe(audio_length_seconds)
            
            return TTSResponse(audio_base64=audio_base64)
            
        except Exception as e:
            TTS_REQUESTS.labels(status='error', voice=request.voice).inc()
            raise HTTPException(status_code=500, detail=f"TTS generation failed: {str(e)}")

@app.post("/tts")
async def tts_endpoint(request: TTSRequest):
    """Alias for /synthesize for compatibility"""
    return await synthesize_speech(request)

if __name__ == "__main__":
    print("🚀 Starting Kokoro TTS Service on port 8020")
    uvicorn.run(app, host="0.0.0.0", port=8020, log_level="info")
