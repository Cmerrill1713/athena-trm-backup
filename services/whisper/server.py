#!/usr/bin/env python3
"""
Athena Whisper STT Service
Provides local speech-to-text using faster-whisper
"""

import os
import logging
import tempfile
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Athena Whisper STT",
    description="Local speech-to-text using faster-whisper",
    version="1.0.0"
)

# Add CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global model instance
model = None
MODEL_SIZE = os.getenv("WHISPER_MODEL", "base")  # tiny, base, small, medium, large

def load_model():
    """Load Whisper model on first use."""
    global model
    if model is not None:
        return model
    
    logger.info(f"Loading Whisper model: {MODEL_SIZE}")
    
    try:
        from faster_whisper import WhisperModel
        
        # Use CPU with int8 for efficiency
        model = WhisperModel(
            MODEL_SIZE,
            device="cpu",
            compute_type="int8",
            download_root="/app/models"
        )
        
        logger.info(f"✅ Whisper {MODEL_SIZE} model loaded")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load Whisper: {e}")
        logger.warning("⚠️ Whisper not available - running in placeholder mode")
        model = "placeholder"
        return None

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "athena-whisper-stt",
        "model": MODEL_SIZE,
        "loaded": model is not None and model != "placeholder"
    }

@app.post("/transcribe")
async def transcribe_audio(
    audio: UploadFile = File(...),
    language: Optional[str] = None
):
    """
    Transcribe audio file to text.
    
    Accepts: WAV, MP3, M4A, WEBM, OGG
    Returns: Transcribed text
    """
    whisper = load_model()
    
    if whisper is None:
        # Placeholder mode
        return {
            "text": "[Whisper STT not available - install faster-whisper model]",
            "language": "en",
            "model": MODEL_SIZE,
            "placeholder": True
        }
    
    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            content = await audio.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name
        
        logger.info(f"Transcribing audio file: {audio.filename} ({len(content)} bytes)")
        
        # Transcribe
        segments, info = whisper.transcribe(
            tmp_path,
            language=language,
            beam_size=5,
            vad_filter=True  # Voice activity detection
        )
        
        # Collect all segments
        transcription = " ".join([segment.text for segment in segments])
        
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)
        
        logger.info(f"✅ Transcribed: {transcription[:100]}...")
        
        return {
            "text": transcription,
            "language": info.language,
            "language_probability": info.language_probability,
            "duration": info.duration,
            "model": MODEL_SIZE,
            "placeholder": False
        }
        
    except Exception as e:
        logger.error(f"Transcription error: {e}", exc_info=True)
        
        # Clean up on error
        if 'tmp_path' in locals():
            Path(tmp_path).unlink(missing_ok=True)
        
        raise HTTPException(
            status_code=500,
            detail=f"Transcription failed: {str(e)}"
        )

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "athena-whisper-stt",
        "version": "1.0.0",
        "model": MODEL_SIZE,
        "endpoints": {
            "/health": "Health check",
            "/transcribe": "POST audio file for transcription"
        }
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8095))
    uvicorn.run(app, host="0.0.0.0", port=port)

