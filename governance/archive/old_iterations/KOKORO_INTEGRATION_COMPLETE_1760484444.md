# 🎙️ Kokoro Voice Integration - NeuroForgeApp

> **Professional TTS with Kokoro-82M, preserving CLI voice control**

---

## ✅ What Was Integrated

### VoiceManager Updated
- ✅ **Speech input** - Apple Speech Recognition (unchanged)
- ✅ **Voice output** - Kokoro TTS (primary), System TTS (fallback)
- ✅ **Auto-detection** - Checks Kokoro availability on speak
- ✅ **Graceful fallback** - System voice if Kokoro unavailable

---

## 🎯 Two Voice Systems (Coexist Perfectly)

### 1. CLI Voice (`athena_voice.sh`) - Backend Ops
```bash
# Infrastructure control via voice
athena "bring everything online"  → make stack-up
athena "ghost check"              → make truth
athena "ship it"                  → Deploy canary
athena "run smoke tests"          → make athena-tests
```

**Uses:** Shell script + Whisper transcription  
**Target:** Backend operations  
**Port:** N/A (runs commands directly)

### 2. SwiftUI Voice (NeuroForgeApp) - Chat Interface
```
Click mic → Speak → Release → Chat with Athena
                ↓
        Apple Speech transcribes
                ↓
        Sent to Bridge → Athena
                ↓
        Kokoro responds (warm natural voice)
```

**Uses:** Apple Speech (input) + Kokoro TTS (output)  
**Target:** Chat conversations  
**Port:** 8020 (Kokoro server)

**No conflict! Different purposes.**

---

## 🎙️ Kokoro Integration Details

### Auto-Detection Flow
1. User triggers TTS (voice response)
2. VoiceManager checks `http://127.0.0.1:8020/tts`
3. **Kokoro available** → HTTP POST to Kokoro
4. **Kokoro down** → Fallback to system voice
5. Audio plays

### Kokoro Request
```json
POST http://127.0.0.1:8020/tts
{
  "text": "Hello, I'm Athena",
  "voice": "af_heart",
  "format": "wav",
  "speed": 1.0
}
```

### Voice Used
- **Primary:** `af_heart` - Warm female voice ("serna")
- **Fallback:** System voice (Samantha)

---

## 🚀 Complete End-to-End Flow

### 1. Start Kokoro Server
```bash
cd /Users/christianmerrill/Documents/GitHub

# Manual start
python3 scripts/kokoro_server.py

# Or use LaunchAgent (auto-start)
launchctl load ~/Library/LaunchAgents/com.athena.kokoro.plist
```

### 2. Start Backend
```bash
make stack-up
make truth
```

### 3. Start Frontend
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

### 4. Test Chat Voice
1. Click mic button (or hold Space)
2. Say "Hello Athena"
3. Release
4. See transcript: "You (voice): Hello Athena"
5. **Hear Kokoro response** (warm natural voice)

### 5. Test CLI Voice (Parallel)
```bash
# In another terminal
./athena_voice.sh
"run smoke tests"
"show watchdog"
```

**Both work independently!**

---

## 🔍 How It Works

### Voice Input (Unchanged)
```swift
func startListening() async {
    // Apple Speech Recognition
    recognitionRequest = SFSpeechAudioBufferRecognitionRequest()
    recognitionTask = speechRecognizer.recognitionTask(with: recognitionRequest!)
    // ... transcribe voice to text
}
```

### Voice Output (New - Kokoro-first)
```swift
func speak(_ text: String) {
    // Try Kokoro
    speakViaKokoro(text, url: kokoroURL) { success in
        if !success {
            // Fallback to system
            self.speakViaSystem(text)
        }
    }
}
```

---

## 📋 Required Setup

### 1. Kokoro Server Running
```bash
# Check if running
curl -s http://127.0.0.1:8020/health

# Expected response:
{
  "status": "ok",
  "model": "Kokoro-82M",
  "voices": ["af_heart", "af_sky", "af", "am"]
}
```

### 2. Info.plist Permissions
Add to `NeuroForgeApp/Info.plist`:
```xml
<key>NSSpeechRecognitionUsageDescription</key>
<string>We use speech recognition to transcribe your voice messages.</string>

<key>NSMicrophoneUsageDescription</key>
<string>We need microphone access for voice chat.</string>
```

---

## 🎯 Voice States

| State | Description | Audio |
|-------|-------------|-------|
| **Idle** | Ready | Silent |
| **Listening** | Mic active | Waveform animating |
| **Transcribing** | Processing | Partial transcript shown |
| **Sending** | Sending to Athena | Loading |
| **Speaking** | Playing response | Kokoro or System TTS |

---

## 🧪 Testing

### Voice Input
- [ ] Click mic button
- [ ] Mic permission granted
- [ ] Speak "hello"
- [ ] See transcript appear
- [ ] Message sent to backend

### Voice Output (Kokoro)
- [ ] Kokoro server running (`:8020/health`)
- [ ] Send chat message
- [ ] Hear natural voice response (af_heart)
- [ ] Console shows: `🎙️  Playing Kokoro voice`

### Voice Output (Fallback)
- [ ] Stop Kokoro server
- [ ] Send chat message
- [ ] Console shows: `⚠️  Using system voice (Kokoro unavailable)`
- [ ] Hear system voice response

### CLI Voice (Parallel)
- [ ] CLI voice script works
- [ ] Can run backend commands
- [ ] No interference with SwiftUI voice

---

## 🔧 Configuration

### Change Kokoro Voice
```swift
// In VoiceManager.swift
let body: [String: Any] = [
    "text": text,
    "voice": "af_sky",  // Try: af_heart, af_sky, af, am
    "format": "wav",
    "speed": 1.0
]
```

### Adjust Speed
```swift
"speed": 1.1  // Faster
"speed": 0.9  // Slower
```

### Disable TTS
```swift
// In ChatView
voice.ttsEnabled = false
```

---

## 🚀 Production Checklist

- [ ] Kokoro server running
- [ ] LaunchAgent configured (auto-start)
- [ ] Backend running (`:8014`)
- [ ] Frontend builds successfully
- [ ] Mic permissions granted
- [ ] Voice input works
- [ ] Kokoro TTS works
- [ ] Fallback works when Kokoro down
- [ ] CLI voice still works independently

---

## 🎙️ Available Kokoro Voices

| Voice ID | Description | Quality | Use Case |
|----------|-------------|---------|----------|
| `af_heart` | ⭐ Warm female | ⭐⭐⭐⭐⭐ | Default (recommended) |
| `af_sky` | Clear female | ⭐⭐⭐⭐ | Professional |
| `af` | Default female | ⭐⭐⭐ | Generic |
| `am` | Default male | ⭐⭐⭐ | Alternative |

---

## 🛠️ Troubleshooting

### No Kokoro Voice (Fallback to System)
```bash
# Check Kokoro server
curl -s http://127.0.0.1:8020/health

# Restart if needed
pkill -f kokoro_server
python3 scripts/kokoro_server.py
```

### Mic Not Working
- Check System Settings → Privacy → Microphone
- Grant permission to NeuroForgeApp
- Restart app

### CLI Voice Conflicts
**They don't conflict!** CLI voice is separate script for backend ops.

---

## ✅ Integration Summary

**What Changed:**
- VoiceManager now uses Kokoro for TTS output
- Auto-detection with graceful fallback
- Speech input unchanged (Apple Speech)

**What Didn't Change:**
- CLI voice control (athena_voice.sh)
- Backend operations
- Text chat
- Existing features

**Result:**
- ✅ Professional natural voice (Kokoro)
- ✅ Fallback reliability (System voice)
- ✅ CLI voice still works (no conflicts)
- ✅ Complete voice-controlled stack

---

**Status:** ✅ KOKORO INTEGRATED  
**Quality:** ⭐⭐⭐⭐⭐ Professional TTS  
**Conflicts:** None

🎙️ **Your app now speaks with Athena's natural voice!** 🚀

