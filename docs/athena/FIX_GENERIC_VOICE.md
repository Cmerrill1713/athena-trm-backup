# 🎤 Fix Generic Voice - Install Enhanced Samantha

## ✅ **Root Cause Identified**

You're hearing **Samantha Compact** (quality=1), which sounds robotic/generic.

**Current voice**: `com.apple.voice.compact.en-US.Samantha` **(q=1)** ← This IS the generic sound

**What you need**: `com.apple.voice.premium.en-US.Samantha` **(q=2+)** ← Natural, smooth

## 🛠️ **Solution: Install Enhanced Samantha**

### Step 1: Open Voice Settings

```bash
# Quick link
open "x-apple.systempreferences:com.apple.preference.universalaccess?SpokenContent"
```

OR manually:
1. **System Settings**
2. **Accessibility**
3. **Spoken Content**
4. **System Voice** → **Manage Voices...**

### Step 2: Download Enhanced Samantha

1. Find **English (United States)**
2. Find **Samantha**
3. Click **Download** next to **Enhanced** (NOT Compact)
4. Wait for download to complete (~200-500 MB)

### Step 3: Reboot (Important!)

```bash
sudo reboot
```

macOS sometimes doesn't fully activate enhanced voices until after a reboot.

### Step 4: Verify Enhanced Version

After reboot:

```bash
# Test the enhanced voice
say -v "Samantha" "This is the enhanced Samantha voice. It should sound smooth and natural, not robotic."

# Check quality in Swift
swift test_voice.swift | grep "quality="
# Should show: quality=2 or higher (not q=1)
```

### Step 5: Rebuild Athena

```bash
make reporter-build
make test-voice
```

## 🎯 **Expected Results**

### Before (Compact q=1)
- ❌ Robotic, monotone
- ❌ Sounds like old TTS
- ❌ Generic voice quality
- Voice: `com.apple.voice.compact.en-US.Samantha` **q=1**

### After (Enhanced q=2+)
- ✅ Smooth, natural
- ✅ Human-like inflection
- ✅ Pleasant to listen to
- Voice: `com.apple.voice.premium.en-US.Samantha` **q=2** or **q=3**

## 🔄 **Alternative: Use Kokoro TTS (High-Quality Neural Voice)**

If you want a truly unique, high-quality voice without relying on macOS:

### Option A: Kokoro Local (Best Quality)

```bash
# Install Kokoro
pip3 install kokoro soundfile
brew install espeak-ng

# Test it
python3 scripts/test_kokoro.py
```

Then integrate with Athena Reporter's HTTP TTS backend.

### Option B: Different macOS Voice

Try other built-in voices:

```bash
# List all female US English voices
say -v '?' | grep "en_US"

# Test each one
say -v "Allison" "This is Allison."
say -v "Susan" "This is Susan."
say -v "Vicki" "This is Vicki."
```

Pick the one you like and update `VoiceSentinel.swift`:

```swift
enum PreferredVoice {
    static let name = "Allison"  // or Susan, Vicki, etc.
    static let fallbacks = [
        "com.apple.voice.premium.en-US.Allison",
        "com.apple.voice.compact.en-US.Allison"
    ]
}
```

## 📋 **Verification Checklist**

After installing Enhanced Samantha:

- [ ] Downloaded Enhanced (not Compact) in System Settings
- [ ] Rebooted Mac
- [ ] `say -v "Samantha"` sounds natural (not robotic)
- [ ] `swift test_voice.swift` shows `q=2` or higher
- [ ] Rebuilt app: `make reporter-build`
- [ ] App test sounds natural: `make test-voice`

## 🚨 **Why This Matters**

**Compact voices (q=1)** are small, fast, but low-quality:
- Designed for basic accessibility
- Sound robotic/mechanical
- ~10-50 MB download

**Enhanced voices (q=2+)** are natural, human-like:
- High-quality neural TTS
- Smooth inflection and pacing
- ~200-500 MB download

**The compact version IS what people call "generic voice"!**

---

**Status**: The Voice Sentinel is working correctly - it's locking Samantha. The issue is you have **Compact Samantha**, which sounds generic. Install **Enhanced Samantha** to get the natural voice.
