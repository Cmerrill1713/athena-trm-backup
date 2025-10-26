# 🔍 VOICE ISSUE DIAGNOSIS

**Date:** October 18, 2025  
**Issue:** Audio generates but is silent

---

## 🎯 ROOT CAUSE IDENTIFIED:

**The Kokoro TTS service is using a PLACEHOLDER implementation that generates silent WAV files.**

### Evidence:
```bash
# Audio is being generated
File: /tmp/test_audio.wav
Type: RIFF (little-endian) data, WAVE audio, Microsoft PCM, 16 bit, mono 24000 Hz
Size: 42KB
Content: SILENT (all zeros)
```

### Code Confirms:
```python
# From services/kokoro/server.py
logger.warning("⚠️  Using placeholder Kokoro - replace with actual model")

# The generate_silence_wav function creates WAV files with zero audio data
def generate_silence_wav(duration_sec: float = 1.0, sample_rate: int = 24000) -> bytes:
    # ... generates silent PCM data
    for _ in range(num_samples):
        buffer.write(struct.pack('<h', 0))  # Zero = silence
```

---

## ✅ WHAT'S WORKING:

1. **TTS Endpoint** - ✅ Responding correctly
2. **Audio Generation** - ✅ Valid WAV files created
3. **Audio Format** - ✅ Proper WAV headers (16-bit PCM, 24kHz mono)
4. **Integration** - ✅ Router, multimodal chat, UI all wired correctly
5. **Dependencies** - ✅ All installed

**The infrastructure is 100% working - we just need the actual TTS model!**

---

## 🚀 SOLUTIONS:

### **Option 1: Use macOS Built-in TTS (Quick Fix)**
Use the system's `say` command for actual voice:

```python
import subprocess

def generate_real_audio(text: str, voice: str = "Samantha") -> bytes:
    """Generate audio using macOS say command."""
    # Generate AIFF first
    subprocess.run(['say', '-v', voice, '-o', '/tmp/tts.aiff', text])
    # Convert to WAV
    subprocess.run(['ffmpeg', '-i', '/tmp/tts.aiff', '-ar', '24000', '/tmp/tts.wav'])
    with open('/tmp/tts.wav', 'rb') as f:
        return f.read()
```

### **Option 2: Use Coqui TTS (Local, Free)**
```bash
pip install TTS

# Python code:
from TTS.api import TTS
tts = TTS("tts_models/en/ljspeech/tacotron2-DDC")
tts.tts_to_file(text="Hello world", file_path="output.wav")
```

### **Option 3: Use Piper TTS (Fast, Local)**
```bash
# Install
pip install piper-tts

# Usage
echo "Hello world" | piper --model en_US-lessac-medium --output_file output.wav
```

### **Option 4: Install Actual Kokoro-82M**
If Kokoro-82M is a real model, we need:
- Model weights
- Inference code
- Model dependencies

---

## 🔧 QUICK FIX - macOS System TTS:

Let me update the Kokoro service to use macOS `say` command:

```python
async def synthesize(request: SynthesizeRequest):
    import subprocess
    import tempfile
    
    # Use macOS say command
    with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp:
        # Generate audio
        subprocess.run([
            'say', 
            '-v', 'Samantha',  # or 'Alex' for male
            '-o', tmp.name.replace('.wav', '.aiff'),
            request.text
        ])
        
        # Convert AIFF to WAV
        subprocess.run([
            'ffmpeg', '-y', '-i', 
            tmp.name.replace('.wav', '.aiff'),
            '-ar', '24000',
            tmp.name
        ], capture_output=True)
        
        # Read WAV
        with open(tmp.name, 'rb') as f:
            wav_bytes = f.read()
    
    audio_b64 = base64.b64encode(wav_bytes).decode()
    return SynthesizeResponse(
        audio=audio_b64,
        duration_ms=len(wav_bytes) // (24000 * 2),  # 16-bit = 2 bytes per sample
        sample_rate=24000
    )
```

---

## 🎯 RECOMMENDED SOLUTION:

**Use macOS built-in TTS for now** - it's:
- ✅ Already installed
- ✅ High quality voices
- ✅ Fast
- ✅ No additional dependencies
- ✅ Works immediately

Then later upgrade to Coqui TTS or Piper for production.

---

## 📝 CURRENT STATUS:

```
Infrastructure: ✅ 100% Working
Audio Pipeline: ✅ 100% Working
Integration: ✅ 100% Working
Actual Voice: ❌ Using placeholder (silent)
```

**The system is ready - we just need to swap the placeholder with a real TTS engine!**

Would you like me to implement the macOS `say` command fix for immediate working voice?
