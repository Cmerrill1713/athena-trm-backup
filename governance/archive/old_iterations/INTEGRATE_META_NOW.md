# 🚀 INTEGRATE META DASHBOARD NOW — 5-8 Minutes

## Step 1: Verify Backend (30 seconds)

```bash
export META_PROMPTING=1
make stack-up

# Check if meta headers present
curl -i http://127.0.0.1:8014/health | grep -i "x-meta" || echo "✅ Meta headers come per-chat response"
```

**Expected:** Either see `x-meta-*` headers or confirmation they're on chat responses only.

---

## Step 2: Three Tiny Edits (5 minutes)

### Edit 1: Add Field to ChatMessage Model

**File:** Your existing `ChatMessage` struct (likely in `Models/ChatMessage.swift` or similar)

```swift
struct ChatMessage: Identifiable, Codable {
    let id: UUID
    var role: Role
    var content: String
    var timestamp: Date
    
    // ✅ ADD THIS LINE
    var metaPrompt: MetaPromptInfo? = nil
    
    // ... rest of your fields
}
```

---

### Edit 2: Parse Headers in Network Layer

**File:** Your API client (where you handle chat responses)

```swift
// After receiving response
let (data, response) = try await urlSession.data(for: request)

// ✅ ADD THIS BLOCK
if let http = response as? HTTPURLResponse {
    var meta = MetaPromptInfo.from(headers: http.allHeaderFields)
    
    // Optional: merge JSON body meta if present
    if let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
       let metaDict = json["meta"] as? [String: Any] {
        meta.merge(from: metaDict)
    }
    
    // Attach to your message
    currentMessage.metaPrompt = meta
}
```

**Alternative helper (if you want cleaner code):**

```swift
extension MetaPromptInfo {
    static func from(headers: [AnyHashable: Any], fallbackBody data: Data?) -> MetaPromptInfo {
        var meta = MetaPromptInfo.from(headers: headers)
        
        if let data = data,
           let json = try? JSONSerialization.jsonObject(with: data) as? [String: Any],
           let metaDict = json["meta"] as? [String: Any] {
            meta.merge(from: metaDict)
        }
        
        return meta
    }
}

// Usage:
let meta = MetaPromptInfo.from(headers: http.allHeaderFields, fallbackBody: data)
message.metaPrompt = meta
```

---

### Edit 3: Display Panel in Chat View

**File:** Your message row/cell view (where you render assistant messages)

```swift
struct MessageRow: View {
    let message: ChatMessage
    
    var body: some View {
        VStack(alignment: message.role == .user ? .trailing : .leading, spacing: 8) {
            // Your existing message bubble
            Text(message.content)
                .padding()
                .background(bubbleColor)
                .cornerRadius(16)
            
            // ✅ ADD THIS BLOCK (only for assistant messages)
            if message.role == .assistant, let meta = message.metaPrompt {
                MetaPromptPanel(meta: meta)
                    .padding(.top, 8)
            }
        }
    }
}
```

---

## Step 3: Build & Run (30 seconds)

```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 QA_MODE=1 swift run
```

---

## Step 4: Validate (2 minutes)

### Test 1: High Confidence + Tools
**Send:** "Run smoke tests and summarize failures"

**Expected Panel:**
```
🧠 Meta-Prompt Insight      ● High • 89%

🌟 Reasoned  📚 RAG  ⏱ 756ms  🔢 440 tok

Suggested Tools:
 🔨 pytest   🔨 truth   🔨 grep

📋 Orchestrator Plan              ⌄
  1. Parse request
  2. Execute pytest with markers
  3. Summarize failures
  📄 Copy Plan
```

---

### Test 2: Low Confidence + Clarifier
**Send:** "What about that?"

**Expected Panel:**
```
🧠 Meta-Prompt Insight      ● Low • 23%

🔄 Reflection  ⏱ 234ms

📋 Orchestrator Plan              ⌄
  1. Request clarification from user
```

---

### Test 3: Tool-Driving Request
**Send:** "Do a health check, then run smoke tests with maxfail=1 and show only failures"

**Expected Panel:**
```
🧠 Meta-Prompt Insight      ● High • 91%

🌟 Reasoned  📚 RAG  ⏱ 892ms  🔢 512 tok

Suggested Tools:
 🔨 curl   🔨 pytest   🔨 grep

📋 Orchestrator Plan              ⌄
  1. Health check all services
  2. Run smoke tests (maxfail=1)
  3. Filter and display failures only
  📄 Copy Plan
```

---

## Optional Polish (5 minutes)

### Add Settings Toggle

**File:** Your settings view or chat view

```swift
@AppStorage("showMetaPanel") private var showMetaPanel = true

// In your settings
Toggle("Show Meta-Prompt Panel", isOn: $showMetaPanel)

// In message row
if showMetaPanel, message.role == .assistant, let meta = message.metaPrompt {
    MetaPromptPanel(meta: meta)
}
```

---

### Add Haptic Feedback

**File:** Your chat view model or where you handle new messages

```swift
@State private var lastConfidence: Double = 0

// When new message arrives
if let newConf = message.metaPrompt?.confidence {
    let delta = abs(newConf - lastConfidence)
    if delta > 0.3 {
        #if os(iOS)
        UIImpactFeedbackGenerator(style: .medium).impactOccurred()
        #endif
    }
    lastConfidence = newConf
}
```

---

### Log to Traces

**File:** Your trace/analytics handler

```swift
// When message arrives
if let meta = message.metaPrompt {
    logToTraces(
        confidence: meta.confidence,
        style: meta.style,
        rag: meta.rag,
        reflection: meta.reflection,
        tools: meta.tools,
        latency: meta.latencyMs
    )
}
```

---

## Troubleshooting (30-second fixes)

### Panel Never Appears

**Check:**
1. Backend has `META_PROMPTING=1`
2. Messages coming from Bridge (not mock)
3. `message.metaPrompt` is actually set

**Debug:**
```swift
print("Meta: \(message.metaPrompt)")
print("Meta enabled: \(message.metaPrompt?.enabled ?? false)")
```

---

### Confidence Always Low

**This is real!** Try:
- More precise prompts
- Watch panel: confidence should climb after reflection
- Check if backend is getting full context

---

### No Tool Chips

**This is normal** if:
- Request didn't need tools
- Tools haven't been selected yet

**Trigger tools with:**
- "Run health checks"
- "Execute smoke tests"
- "Check logs for errors"

---

### Panel Layout Issues

**Ensure container has space:**
```swift
VStack(alignment: .leading, spacing: 12) {
    // message bubble
    
    if let meta = message.metaPrompt {
        MetaPromptPanel(meta: meta)
            .frame(maxWidth: .infinity)  // ✅ Full width
    }
}
```

---

## Ship Checklist

- [ ] `MetaPromptInfo?` field added to `ChatMessage`
- [ ] Network layer parsing headers
- [ ] Panel displayed under assistant messages
- [ ] Tested with high confidence prompt
- [ ] Tested with low confidence prompt
- [ ] Tested with tool-driving prompt
- [ ] Confidence colors correct (🔴 Low ≤34%, 🟠 Med 34-67%, 🟢 High ≥67%)
- [ ] Copy plan button works
- [ ] Settings toggle present (optional)
- [ ] Haptic feedback (optional)
- [ ] Trace logging (optional)

---

## What You Should See

### On Vague Prompts
```
🔴 Low • 28%
🔄 Reflection
Plan: "Request clarification"
```

### On Precise Prompts
```
🟢 High • 92%
🌟 Reasoned  📚 RAG
Tools: pytest, grep, truth
Plan: 4 specific steps
```

### On Errors That Adapt
```
Initial: 🟠 Med • 45%
After adaptation: 🟢 High • 87%
Plan evolved from "Try X" to "Execute Y with constraint Z"
```

---

## Backend Headers (Reference)

Your Bridge already emits (when `META_PROMPTING=1`):

```
x-meta-enabled: true
x-meta-confidence: 0.89
x-meta-style: reasoned
x-meta-rag: 1
x-meta-reflection: 0
x-meta-plan: ["Step 1","Step 2","Step 3"]
x-meta-tools: ["pytest","truth","grep"]
x-latency-ms: 756
x-prompt-tokens: 142
x-completion-tokens: 298
```

**Or in JSON body:**
```json
{
  "message": "...",
  "meta": {
    "enabled": true,
    "confidence": 0.89,
    "style": "reasoned",
    "rag": true,
    "reflection": false,
    "plan": ["Step 1", "Step 2", "Step 3"],
    "tools": ["pytest", "truth", "grep"],
    "latency_ms": 756,
    "prompt_tokens": 142,
    "completion_tokens": 298
  }
}
```

`MetaPromptInfo.from()` handles both formats automatically.

---

## Success!

When you see this in your app, you're done:

```
╭──────────────────────────────────────────────╮
│ 🧠 Meta-Prompt Insight      ● High • 87%    │
│                                              │
│ 🌟 Reasoned  📚 RAG  🔄 Reflection  ⏱ 842ms │
│ 🔢 674 tok                                   │
│                                              │
│ Suggested Tools:                             │
│  🔨 pytest   🔨 truth   🔨 watchdog          │
│                                              │
│ 📋 Orchestrator Plan                    ⌄    │
│   1. Clarify user intent                     │
│   2. Select appropriate tools                │
│   3. Execute validation tests                │
│   4. Summarize results                       │
│   📄 Copy Plan                               │
╰──────────────────────────────────────────────╯
```

**Your AI's reasoning is now transparent and visible.** 🎯✨

---

**Time to complete:** 5-8 minutes  
**Files to edit:** 3  
**Lines to add:** ~15  
**Impact:** Massive (transparency + trust)  

**Let's ship it!** 🚀

