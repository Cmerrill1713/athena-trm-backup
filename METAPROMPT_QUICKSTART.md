# 🧠 Meta-Prompt Dashboard — Quick Start

**Make Athena's reasoning visible in your SwiftUI app.**

---

## ⚡ 3-Step Integration (10 minutes)

### Step 1: Update Your Message Model
```swift
struct ChatMessage: Identifiable {
    let id: UUID
    var role: Role
    var content: String
    var metaPrompt: MetaPromptInfo? = nil  // ✅ ADD THIS
}
```

### Step 2: Parse Headers in API Client
```swift
// After receiving HTTP response
guard let http = response as? HTTPURLResponse else { return }

// ✅ Parse meta headers
var meta = MetaPromptInfo.from(headers: http.allHeaderFields)

// Optional: merge JSON body meta
if let json = /* parse JSON */, let metaDict = json["meta"] as? [String: Any] {
    meta.merge(from: metaDict)
}

// Attach to message
message.metaPrompt = meta
```

### Step 3: Display in Chat View
```swift
struct MessageRow: View {
    let message: ChatMessage
    
    var body: some View {
        VStack(alignment: .leading) {
            Text(message.content)  // Your existing bubble
            
            // ✅ ADD META PANEL
            if let meta = message.metaPrompt {
                MetaPromptPanel(meta: meta)
            }
        }
    }
}
```

---

## ✅ Done!

Run your app and send a message. You'll see:

```
╭─────────────────────────────────────────╮
│ 🧠 Meta-Prompt Insight   ● High • 89%  │
│                                         │
│ 🌟 Reasoned  📚 RAG  ⏱ 756ms  🔢 440tok│
│                                         │
│ Suggested Tools:                        │
│  🔨 pytest   🔨 grep   🔨 tail          │
│                                         │
│ 📋 Orchestrator Plan              ⌄     │
╰─────────────────────────────────────────╯
```

---

## 🧪 Test It

### Start Backend
```bash
export META_PROMPTING=1
make stack-up
```

### Run App
```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

### Send Test Prompts

**Vague (low confidence):**
> "What about logs?"

Panel shows:
- 🔴 Low confidence (< 34%)
- 🔄 Reflection badge
- Plan: "Request clarification"

**Precise (high confidence):**
> "Run smoke tests and show results"

Panel shows:
- 🟢 High confidence (> 67%)
- 📚 RAG badge
- Plan: 4 specific steps
- Tools: `pytest`, `truth`, `watchdog`

---

## 🎨 What's Included

### Visual Elements
- **Confidence Pill**: Color-coded (Red/Orange/Green)
- **Style Badge**: Reasoned, Terse, Creative
- **RAG Badge**: When retrieval used
- **Reflection Badge**: When reflection loop ran
- **Metrics**: Latency (ms) + Token count
- **Tools**: Flow layout chips
- **Plan**: Expandable numbered list

### Interactions
- Tap plan to expand/collapse
- Copy plan to clipboard
- Auto-hides when meta disabled
- Smooth animations

### Accessibility
- Full VoiceOver support
- High contrast mode
- Dynamic Type
- Keyboard navigation

---

## 📚 Full Documentation

- **Integration Guide**: `NeuroForgeApp/METAPROMPT_INTEGRATION.md`
- **Example Code**: `NeuroForgeApp/Sources/MetaPrompt/MetaPromptExample.swift`
- **Models**: `NeuroForgeApp/Sources/MetaPrompt/MetaPromptModels.swift`
- **UI**: `NeuroForgeApp/Sources/MetaPrompt/MetaPromptPanel.swift`

---

## 🔧 Backend Headers

Your backend already emits these (if `META_PROMPTING=1`):

```
x-meta-enabled: true
x-meta-confidence: 0.89
x-meta-style: reasoned
x-meta-rag: 1
x-meta-reflection: 0
x-meta-plan: ["Step 1","Step 2","Step 3"]
x-meta-tools: ["pytest","grep"]
x-latency-ms: 756
x-prompt-tokens: 142
x-completion-tokens: 298
```

---

## 🎯 Why This Matters

### For Users
- **Transparency**: See what AI is thinking
- **Trust**: Understand reasoning process
- **Confidence**: Know when to trust responses

### For Developers
- **Debug**: See why AI chose a path
- **Tune**: Identify low-confidence patterns
- **Improve**: Understand tool selection

### For Product
- **Differentiation**: Few AI apps show reasoning
- **Professional**: Signals advanced AI
- **Trustworthy**: Builds user confidence

---

## 🚀 Optional Enhancements

### Settings Toggle
```swift
@AppStorage("showMetaPrompt") var showMeta = true

if showMeta, let meta = message.metaPrompt {
    MetaPromptPanel(meta: meta)
}
```

### Live Panel at Top
```swift
// Shows latest assistant message's meta
if let latestMeta = messages.last(where: { $0.role == .assistant })?.metaPrompt {
    MetaPromptPanel(meta: latestMeta)
        .padding()
}
```

### Confidence Sparkline
```swift
// Track trend over last N messages
let confidences = messages
    .compactMap { $0.metaPrompt?.confidence }
    .suffix(10)

ConfidenceSparkline(values: confidences)
```

---

## ⚡ Quick Reference

| Feature | Description | Color |
|---------|-------------|-------|
| 🔴 Low | Confidence < 34% | Red |
| 🟠 Med | Confidence 34-66% | Orange |
| 🟢 High | Confidence > 67% | Green |
| 🌟 Style | reasoned/terse/creative | Blue |
| 📚 RAG | Retrieval used | Green |
| 🔄 Reflection | Reflection loop ran | Orange |
| ⏱️ Latency | Response time (ms) | Gray |
| 🔢 Tokens | Prompt + completion | Gray |
| 🔨 Tools | Suggested tools | Purple |
| 📋 Plan | Orchestrator steps | Expandable |

---

## 🐛 Troubleshooting

### Panel Never Shows
1. Check `META_PROMPTING=1` in backend
2. Verify headers in network inspector
3. Add logging: `print("Meta: \(meta)")`

### Panel Empty
1. Check header format (JSON arrays as strings)
2. Verify header keys match (case-insensitive)
3. Check both headers and JSON body

### Confidence Always 0
1. Ensure `x-meta-confidence` is float (0.0-1.0)
2. Not percentage (87, not 0.87)

---

## 📊 Stats

| Metric | Value |
|--------|-------|
| Files | 4 |
| Lines of Code | ~730 |
| Lines of Docs | ~500 |
| Integration Time | 10-15 min |
| Backend Changes | None (already supported) |
| Testing Time | 5 min |

---

## ✅ Checklist

- [ ] Files added to project
- [ ] `ChatMessage.metaPrompt` field added
- [ ] API client parsing headers
- [ ] `MetaPromptPanel` displayed in chat
- [ ] Backend emitting meta headers
- [ ] Tested with vague prompt (low confidence)
- [ ] Tested with precise prompt (high confidence)
- [ ] Verified accessibility
- [ ] Added settings toggle (optional)

---

**Status:** Ready to use ✅  
**Impact:** High (transparency + trust)  
**Effort:** Minimal (10-15 minutes)  

**Makes AI reasoning visible. Builds user confidence. Professional polish.** 🧠✨

