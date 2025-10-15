#!/Users/christianmerrill/Documents/GitHub/kokoro-venv/bin/python3
"""
Kokoro TTS Server for Athena

High-quality TTS using Kokoro-82M model.
Much better than macOS built-in voices.

Usage:
    ./scripts/kokoro_server.py [port]

Endpoints:
    POST http://127.0.0.1:8020/tts
    Body: {"text": "...", "voice": "af_heart", "format": "wav"}

    GET http://127.0.0.1:8020/health
    GET http://127.0.0.1:8020/voices
"""

from flask import Flask, request, jsonify, Response
import io
import soundfile as sf
import logging
import numpy as np

# Lazy import to avoid startup delay
pipeline = None

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_pipeline():
    """Lazy-load Kokoro pipeline"""
    global pipeline
    if pipeline is None:
        logger.info("🧠 Loading Kokoro-82M pipeline...")
        from kokoro import KPipeline
        pipeline = KPipeline(lang_code='a')  # American English
        logger.info("✅ Kokoro pipeline loaded (82M params)")
    return pipeline

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    try:
        get_pipeline()  # Ensure pipeline loads
        return jsonify({
            "status": "ok",
            "model": "Kokoro-82M",
            "voices": ["af_heart", "af_sky", "af", "am"]
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/tts', methods=['POST'])
def tts():
    """
    Text-to-speech endpoint

    Body:
        {
            "text": "Text to speak",
            "voice": "af_heart" (optional, default: af_heart),
            "format": "wav" (optional),
            "speed": 1.0 (optional, default: 1.0)
        }

    Returns: Audio file (WAV format, 24kHz)
    """
    try:
        data = request.json or {}
        text = data.get('text', '')
        voice = data.get('voice', 'af_heart')
        speed = float(data.get('speed', 1.0))

        if not text:
            return jsonify({"error": "No text provided"}), 400

        logger.info(f"🎙️  TTS: {len(text)} chars, voice={voice}, speed={speed}")

        # Generate audio
        pipe = get_pipeline()
        generator = pipe(text, voice=voice, speed=speed)

        # Collect all audio chunks
        audio_chunks = []
        for i, (gs, ps, audio) in enumerate(generator):
            audio_chunks.append(audio)
            logger.debug(f"   Chunk {i}: {len(audio)} samples, text: {gs[:50]}...")

        if not audio_chunks:
            return jsonify({"error": "No audio generated"}), 500

        # Combine chunks
        combined = np.concatenate(audio_chunks)

        # Convert to WAV bytes
        wav_buffer = io.BytesIO()
        sf.write(wav_buffer, combined, 24000, format='WAV')
        wav_bytes = wav_buffer.getvalue()

        duration = len(combined) / 24000
        logger.info(f"✅ Generated {len(wav_bytes)} bytes ({duration:.1f}s, {len(audio_chunks)} chunks)")

        return Response(wav_bytes, mimetype='audio/wav')

    except Exception as e:
        logger.error(f"❌ TTS error: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/voices', methods=['GET'])
def list_voices():
    """List available Kokoro voices"""
    voices = [
        {"id": "af_heart", "name": "Heart (Female, Warm)", "lang": "en-US", "recommended": True},
        {"id": "af_sky", "name": "Sky (Female, Clear)", "lang": "en-US"},
        {"id": "af", "name": "Default Female", "lang": "en-US"},
        {"id": "am", "name": "Default Male", "lang": "en-US"}
    ]
    return jsonify({"voices": voices, "model": "Kokoro-82M"})

if __name__ == '__main__':
    import sys

    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8020

    print("🚀 Kokoro TTS Server for Athena")
    print("=" * 60)
    print(f"📡 Server: http://127.0.0.1:{port}")
    print("📋 Endpoints:")
    print("   • POST /tts     - Generate speech")
    print("   • GET  /health  - Health check")
    print("   • GET  /voices  - List available voices")
    print("")
    print("🎤 Model: Kokoro-82M (82M parameters)")
    print("💡 Recommended voice: af_heart (warm female)")
    print("=" * 60)
    print("")

    app.run(host='127.0.0.1', port=port, debug=False, threaded=True)
