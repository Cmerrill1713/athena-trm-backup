# 🎨 **UX POLISH PLAN - PWA, Voice, Profiles**

## 🎯 **Mission: Zero-Friction Family Experience**

Polish the UX layer without touching stable infrastructure.

---

## ✅ **WHAT WE'RE BUILDING:**

### **1. User Profiles** 👥
**File:** `ui/profiles.js`

**Features:**
- ✅ Family member profiles (Christian, Wife, Kid 1, Kid 2, Guest)
- ✅ Role-based permissions (parent, child, guest)
- ✅ Per-profile preferences (voice, theme, tools)
- ✅ Kid mode (content filtering, homework help)
- ✅ Guest mode (time-limited sessions)
- ✅ Profile switcher in UI

**Benefits:**
- Each family member gets personalized experience
- Kids get safe, filtered content
- Guests get limited access
- Parents get full control

---

### **2. Voice Triggers** 🎤
**File:** `ui/voice-triggers.js`

**Features:**
- ✅ Wake word detection ("Hey Athena", "Hi Athena")
- ✅ Push-to-talk mode (hold spacebar to speak)
- ✅ Continuous listening option
- ✅ Web Speech API (offline, built into browser)
- ✅ Fallback to local Whisper (for unsupported browsers)
- ✅ Auto-send after wake word

**Benefits:**
- Hands-free interaction
- Natural conversation flow
- 100% local (no cloud API calls)
- Works on macOS, iOS, Android

---

### **3. PWA Enhancements** 📱
**File:** `ui/pwa-enhanced.js`

**Features:**
- ✅ Install prompt (one-click install)
- ✅ Offline support (service worker)
- ✅ Online/offline detection
- ✅ Update notifications
- ✅ Persistent storage request
- ✅ Storage quota monitoring
- ✅ Share API integration

**Benefits:**
- Install like a native app
- Works offline
- Automatic updates
- Share conversations
- Persistent data

---

## 🎯 **USER FLOWS:**

### **Flow 1: Profile Switching**
```
User clicks profile selector
  → Dropdown shows all family members
  → User selects profile
  → UI applies preferences (theme, voice, tools)
  → Permissions enforced (kid mode, guest limits)
  → Greeting updates
```

### **Flow 2: Wake Word Interaction**
```
User enables wake word
  → Athena listens continuously (Web Speech API)
  → User says "Hey Athena, what's for dinner?"
  → Wake word detected
  → Command extracted ("what's for dinner?")
  → Auto-sent to Athena
  → Response speaks aloud (if TTS enabled)
```

### **Flow 3: PWA Installation**
```
User visits athena-chat.html
  → "Install Athena App" button appears
  → User clicks install
  → macOS/iOS prompts to add to home screen
  → App installed
  → Launches like native app
  → Works offline
```

---

## 🔧 **INTEGRATION POINTS:**

### **Profiles → Backend:**
```javascript
// Send profile context with each request
fetch(`${BASE_URL}/v1/chat/completions`, {
    headers: {
        'X-User-Profile': currentProfile.id,
        'X-User-Role': currentProfile.role
    },
    body: JSON.stringify({
        model: 'athena-chat',
        messages: messages,
        temperature: currentProfile.preferences.temperature,
        // Content filter for kids
        safe_mode: currentProfile.permissions.content_filter
    })
})
```

### **Voice → Whisper:**
```javascript
// Push-to-talk or wake word → transcribe
const audioBlob = recordAudio();
const transcript = await transcribeWithWhisper(audioBlob);
input.value = transcript;
sendMessage();  // Auto-send if wake word
```

### **PWA → Service Worker:**
```javascript
// Cache strategy
sw.js:
  - Cache UI assets (HTML, CSS, JS)
  - Cache API responses (short TTL)
  - Network-first for chat
  - Cache-first for static assets
```

---

## 📱 **UI CHANGES:**

### **Add to `athena-chat.html`:**

**1. Profile Selector (Header):**
```html
<div id="profileSelector" class="profile-selector">
    <!-- Populated by profiles.js -->
</div>
```

**2. Voice Control Buttons:**
```html
<button class="tool-btn" id="wakeWordBtn" onclick="toggleWakeWord()">
    🔊 Wake Word
</button>
<button class="tool-btn" id="pushToTalkBtn" 
        onmousedown="startPushToTalk()" 
        onmouseup="stopPushToTalk()">
    🎤 Hold to Speak
</button>
```

**3. Online/Offline Indicator:**
```html
<div id="onlineStatus" class="status-indicator">
    🌐 Online
</div>
```

**4. Install Button:**
```html
<button id="pwaInstallBtn" class="pwa-install-btn" style="display:none;">
    📱 Install Athena App
</button>
```

**5. Script Imports:**
```html
<script src="profiles.js"></script>
<script src="voice-triggers.js"></script>
<script src="pwa-enhanced.js"></script>
```

---

## 🎨 **STYLING UPDATES:**

### **Profile Badge:**
```css
.profile-selector {
    position: absolute;
    top: 15px;
    right: 150px;
}

#profileSelect {
    background: rgba(255,255,255,0.1);
    color: white;
    border: 1px solid rgba(255,255,255,0.2);
    border-radius: 8px;
    padding: 8px 12px;
    font-size: 14px;
    cursor: pointer;
}
```

### **Voice Button States:**
```css
.tool-btn.wake-word-active {
    animation: pulse 1s infinite;
    background: #4caf50;
}

@keyframes pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.7; }
}

.tool-btn.listening {
    background: #f44336;
    animation: listening 1.5s infinite;
}

@keyframes listening {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.1); }
}
```

### **Light Theme:**
```css
body.light-theme {
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    color: #333;
}

body.light-theme .chat-window {
    background: white;
    color: #333;
}

body.light-theme .message.assistant {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
}
```

---

## 🧪 **TESTING:**

### **Profile Switching:**
```javascript
// Test each profile
['christian', 'wife', 'kid1', 'kid2', 'guest'].forEach(id => {
    switchProfile(id);
    console.log(`Testing ${id}: permissions`, getCurrentProfile().permissions);
});
```

### **Voice Triggers:**
```javascript
// Test wake word
enableWakeWord();
// Say: "Hey Athena, what's the weather?"
// Expect: Auto-sent to chat

// Test push-to-talk
// Hold spacebar
// Speak
// Release
// Expect: Transcribed text in input
```

### **PWA Features:**
```javascript
// Test offline
// Disconnect WiFi
// Athena should still work for local queries
// UI should show offline indicator

// Test install
// Click "Install Athena App"
// Expect: Install prompt
// After install: app in Applications folder
```

---

## 📊 **ROLLOUT PLAN:**

### **Phase 1: Profiles (Low Risk)**
1. Add `profiles.js` to UI
2. Add profile selector to header
3. Test switching
4. Deploy

### **Phase 2: Voice Triggers (Medium Risk)**
1. Add `voice-triggers.js` to UI
2. Add wake word button
3. Test with Web Speech API
4. Test fallback to Whisper
5. Deploy

### **Phase 3: PWA Polish (Low Risk)**
1. Add `pwa-enhanced.js` to UI
2. Update `sw.js` for better caching
3. Test install prompt
4. Test offline mode
5. Deploy

---

## 💙 **BENEFITS:**

**Before:**
- One-size-fits-all UI
- Type-only interaction
- Browser-only access

**After:**
- Personalized per family member
- Voice + type interaction
- Native app experience
- Works offline

**Result:**
- Better for kids (filtered, homework mode)
- Better for parents (full access)
- Better for family (voice commands)
- Better for everyone (PWA install)

---

## 🚀 **NEXT STEPS:**

```bash
# 1. Integrate profiles
# Add scripts to athena-chat.html

# 2. Test profiles
# Switch between profiles, verify permissions

# 3. Enable voice
# Test wake word + push-to-talk

# 4. Test PWA
# Install, go offline, verify functionality

# 5. Deploy
# All changes are UI-only, zero backend impact
```

---

**Zero infrastructure changes. Pure UX polish! 🎨💙**
