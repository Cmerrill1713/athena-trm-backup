# 🎤 Athena Voice Hard-Lock - Complete

## ✅ **Problem Solved**

Athena was falling back to the generic system voice on every launch instead of using the configured voice (Samantha).

**Root Cause**: AVSpeechSynthesizer silently falls back to default when:
- The voice identifier doesn't match the installed voice
- No voice is explicitly set on each utterance
- The voice is set once but not persisted across runs

**Solution**: Hard-lock voice resolution with NO fallback to generic.

## 🎯 **Implementation**

### Hard-Lock Strategy

1. **Name-first resolution**: Find voice by exact name match
2. **Quality sorting**: Prefer higher quality (enhanced > compact)
3. **Identifier fallback**: Try multiple known identifier formats
4. **Preferred voices fallback**: Try other high-quality voices (Ava, Allison, etc.)
5. **Hard stop**: REFUSE to speak if no acceptable voice found (no generic fallback)

### Voice Manager (`VoiceManager.swift`)

```swift
final class VoiceManager {
    private(set) var voice: AVSpeechSynthesisVoice?
    private(set) var reason: String
    
    func resolvePreferredVoice() {
        // 1. Try exact name match
        let samantha = voices.filter { $0.name == "Samantha" }
            .sorted { $0.quality.rawValue > $1.quality.rawValue }
            .first
        
        // 2. Try known identifiers
        let knownIds = [
            "com.apple.voice.compact.en-US.Samantha",
            "com.apple.voice.premium.en-US.Samantha",
            // ... more variants
        ]
        
        // 3. Hard stop if not found
        guard let voice = resolvedVoice else {
            self.voice = nil
            self.reason = "Samantha not installed"
            // Show alert to user
            return
        }
    }
    
    func speak(_ text: String) {
        guard let v = voice else {
            NSSound.beep()
            print("🚫 Skipping speech: \(reason)")
            return  // REFUSE to speak with generic voice
        }
        // ... speak with locked voice
    }
}
```

### Key Features

- **No silent fallback**: Beeps and logs error if voice unavailable
- **Alert on missing voice**: Shows user-visible alert on launch
- **Quality preference**: Automatically selects highest quality variant
- **Debug logging**: Prints exactly which voice is being used
- **Multi-backend support**: Can switch between system voice and HTTP TTS (Kokoro)

## 📊 **Voice Resolution**

### Samantha Identifiers (in priority order)

1. `com.apple.voice.compact.en-US.Samantha` ← Most common
2. `com.apple.voice.premium.en-US.Samantha` ← Enhanced version
3. `com.apple.ttsbundle.Samantha-compact` ← Legacy
4. `com.apple.speech.synthesis.voice.samantha` ← Very old

### Test Results

```
🎤 Testing Voice Resolution
==========================

📋 Available voices: 191 total

🔍 Looking for Samantha...
   ✅ Found by name: Samantha [com.apple.voice.compact.en-US.Samantha] quality=1
   ✅ Found by ID: Samantha [com.apple.voice.compact.en-US.Samantha] quality=1

🗣️  Testing speech...
   Using voice: Samantha [com.apple.voice.compact.en-US.Samantha]
   ✅ Speech completed
```

## 🛠️ **Usage**

### Quick Commands

```bash
# Pin Samantha as Athena's voice
make pin-voice

# Test the voice (kill old instances, fresh launch)
make test-voice

# Generate health report with voice
make report-health

# Check voice status programmatically
swift test_voice.swift
```

### Voice Configuration Files

```bash
# Voice ID (used by VoiceManager)
~/.athena/voice.id
# Content: com.apple.voice.compact.en-US.Samantha

# Voice name (human-readable)
~/.athena/voice.name  
# Content: Samantha
```

### Switching Voices

To use a different voice (e.g., Ava, Allison):

```bash
# Find available voices
say -v '?' | grep -i "ava"

# Test it
say -v "Ava" "This is Athena with Ava's voice."

# Pin it
echo "com.apple.voice.compact.en-US.Ava" > ~/.athena/voice.id
echo "Ava" > ~/.athena/voice.name

# Rebuild and test
make reporter-build && make test-voice
```

## 🎤 **Backend Support**

### System Voice (AVSpeech)
```swift
// Default - uses hard-locked Samantha
AthenaSpeaker.shared.backend = .system
```

### Kokoro HTTP TTS
```swift
// Custom voice server (if running)
if let url = URL(string: "http://127.0.0.1:8020/tts") {
    AthenaSpeaker.shared.backend = .http(url: url, voice: "athena")
}
```

Switch via menu: **Athena → Use Kokoro (localhost:8020)**

## 🔍 **Debugging**

### Check Voice on Launch

The app prints voice status on startup:

```
🚀 Athena Reporter launched
🔊 Athena: locked: exact Samantha (com.apple.voice.compact.en-US.Samantha, q=1)
✅ Using voice: Samantha [com.apple.voice.compact.en-US.Samantha] en-US quality=1
🎤 Voice backend: system (hard-locked, no fallback)
```

### Check Voice During Speech

Every time the app speaks:

```
🔊 Speaking with: Samantha [com.apple.voice.compact.en-US.Samantha] en-US quality=1
```

### If Voice is Missing

```
❌ Athena Voice: Samantha not installed (en-US). Install in System Settings → Accessibility → Spoken Content → Voices (English US → Samantha).
🚫 Skipping speech: Samantha not installed
[Alert dialog appears]
```

## 🎯 **Why This Works**

### Before (Generic Voice Issues)

- ❌ AVSpeech silently fell back to default
- ❌ Voice identifier mismatches (`ttsbundle` vs `voice.compact`)
- ❌ No persistence across app restarts
- ❌ No feedback when voice unavailable
- ❌ Generic voice was "good enough" fallback

### After (Hard-Lock)

- ✅ Voice resolved by name + quality sorting
- ✅ Multiple identifier formats tried
- ✅ REFUSES to speak if voice unavailable
- ✅ Clear error messages and alerts
- ✅ Logs exact voice being used
- ✅ No silent fallback to generic

## 📋 **Verification Checklist**

- [x] VoiceManager hard-locks voice on init
- [x] Samantha identifier correct (`com.apple.voice.compact.en-US.Samantha`)
- [x] No fallback to generic voice
- [x] Alert shown if voice missing
- [x] Debug logging for voice selection
- [x] AthenaSpeaker uses VoiceManager
- [x] All speech calls go through AthenaSpeaker
- [x] Kokoro HTTP TTS backend supported
- [x] Make targets for easy testing
- [x] Voice test script (`test_voice.swift`)
- [x] Documentation complete

## 🚀 **Results**

**Expected Behavior**:
- ✅ Athena speaks with Samantha's voice EVERY TIME
- ✅ No more random generic voice
- ✅ Clear error if Samantha unavailable
- ✅ Consistent voice across all reports
- ✅ Quality sorting (enhanced > compact if both installed)

**Test It**:
```bash
# Full test cycle
make pin-voice        # Pin Samantha
make reporter-build   # Rebuild app
make test-voice       # Launch and test

# Should hear Samantha say:
# "All systems nominal. 7-day success 100.0 percent. 30 decisions last 24 hours."
```

---

**Status**: ✅ **COMPLETE** - Athena's voice is now hard-locked to Samantha with no fallback to generic. Clear error handling and debugging make it obvious if the voice is unavailable.
