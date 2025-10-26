#!/usr/bin/env python3
"""
Kokoro-82M TTS Server - Local text-to-speech
Port 8091 | Fast, high-quality TTS (82M parameters)
"""
import os
import sys
import base64
import logging
import struct
import io
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from prometheus_client import Histogram, Counter, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Kokoro-82M TTS Server",
    description="Local text-to-speech model",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Metrics
tts_latency = Histogram(
    'kokoro_latency_seconds',
    'Kokoro TTS latency',
    buckets=[0.05, 0.1, 0.2, 0.35, 0.5, 1.0]
)

tts_requests = Counter(
    'kokoro_requests_total',
    'Total Kokoro TTS requests',
    ['status', 'voice']
)

# Models
class SynthesizeRequest(BaseModel):
    text: str
    voice: str = "en_US-female"
    format: str = "wav"

class SynthesizeResponse(BaseModel):
    audio: str  # base64 WAV
    duration_ms: int
    sample_rate: int

# Global model
model = None

def load_model():
    """Load Kokoro-82M model."""
    global model
    if model is not None:
        return model
    
    logger.info("Loading Kokoro-82M model...")
    
    try:
        from kokoro import KPipeline
        model = KPipeline(lang_code='en-us')
        logger.info("✅ Kokoro-82M model loaded (real)")
        return model
    except Exception as e:
        logger.error(f"Failed to load Kokoro: {e}")
        logger.warning("⚠️  Kokoro not available - running in placeholder mode")
        model = "placeholder"  # Non-None to indicate attempted load
        return None  # Continue in placeholder mode instead of crashing

def generate_silence_wav(duration_sec: float = 1.0, sample_rate: int = 24000) -> bytes:
    """Generate silent WAV file (placeholder)."""
    num_samples = int(duration_sec * sample_rate)
    
    # WAV header
    buffer = io.BytesIO()
    buffer.write(b'RIFF')
    buffer.write(struct.pack('<I', 36 + num_samples * 2))  # File size
    buffer.write(b'WAVE')
    buffer.write(b'fmt ')
    buffer.write(struct.pack('<I', 16))  # fmt chunk size
    buffer.write(struct.pack('<H', 1))   # Audio format (PCM)
    buffer.write(struct.pack('<H', 1))   # Channels (mono)
    buffer.write(struct.pack('<I', sample_rate))  # Sample rate
    buffer.write(struct.pack('<I', sample_rate * 2))  # Byte rate
    buffer.write(struct.pack('<H', 2))   # Block align
    buffer.write(struct.pack('<H', 16))  # Bits per sample
    buffer.write(b'data')
    buffer.write(struct.pack('<I', num_samples * 2))  # Data size
    
    # Silent audio data
    for _ in range(num_samples):
        buffer.write(struct.pack('<h', 0))
    
    return buffer.getvalue()

@app.get("/health")
async def health():
    """Health check."""
    return {
        "status": "healthy",
        "service": "kokoro-82m",
        "port": 8091,
        "model_loaded": model is not None,
        "voices": ["en_US-female", "en_US-male"]
    }

@app.post("/synthesize", response_model=SynthesizeResponse)
async def synthesize(request: SynthesizeRequest):
    """Synthesize speech from text using Kokoro-82M."""
    import time
    import torch
    import scipy.io.wavfile as wavfile
    import tempfile
    import os
    start_time = time.time()
    
    try:
        # Load Kokoro model
        pipeline = load_model()
        
        # Map voice names to Kokoro voices
        voice_map = {
            'en_US-female': 'af_bella',  # or af_sarah, af_nicole
            'en_US-male': 'am_adam'      # or am_michael
        }
        kokoro_voice = voice_map.get(request.voice, 'af_bella')
        
        # Generate audio using Kokoro
        result_gen = pipeline(request.text, voice=kokoro_voice)
        results = list(result_gen)
        
        if not results:
            raise ValueError("No audio generated")
        
        result = results[0]
        audio_tensor = result.audio
        
        # Convert torch tensor to numpy array
        if isinstance(audio_tensor, torch.Tensor):
            audio_np = audio_tensor.cpu().numpy()
        else:
            audio_np = audio_tensor
        
        # Save to WAV format
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_wav:
            wavfile.write(tmp_wav.name, 24000, audio_np)
            
            # Read WAV file
            with open(tmp_wav.name, 'rb') as f:
                wav_bytes = f.read()
            
            os.unlink(tmp_wav.name)
        
        latency = time.time() - start_time
        tts_latency.observe(latency)
        tts_requests.labels(status='success', voice=request.voice).inc()
        
        audio_b64 = base64.b64encode(wav_bytes).decode()
        duration_ms = int(len(audio_np) / 24000 * 1000)
        
        logger.info(f"✅ Kokoro TTS synthesis: {len(request.text)} chars, {latency*1000:.0f}ms, voice={kokoro_voice}")
        
        return SynthesizeResponse(
            audio=audio_b64,
            duration_ms=duration_ms,
            sample_rate=24000
        )
    
    except Exception as e:
        tts_requests.labels(status='error', voice=request.voice).inc()
        logger.error(f"Synthesis failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Prometheus metrics."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("KOKORO_PORT", "8091"))
    host = os.getenv("KOKORO_HOST", "127.0.0.1")
    
    logger.info("=" * 60)
    logger.info("🎙️  Kokoro-82M TTS Server Starting")
    logger.info("=" * 60)
    logger.info(f"📍 Server: {host}:{port}")
    logger.info("🗣️  Model: Kokoro-82M (82M parameters)")
    logger.info("🎵 Voices: en_US-female, en_US-male")
    logger.info("=" * 60)
    
    # Pre-load model
    load_model()
    
    uvicorn.run(app, host=host, port=port, log_level="info")

