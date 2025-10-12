# ⚡ Meta Dashboard Integration — DO THIS NOW

**5-8 minutes to transparent AI reasoning**

---

## ✅ Step 1: Verify Backend (30s)

```bash
export META_PROMPTING=1
make stack-up
```

---

## ✅ Step 2: Edit ChatMessage Model (1 min)

**File:** Your `ChatMessage` struct

```swift
struct ChatMessage: Identifiable, Codable {
    // ... existing fields ...
    var metaPrompt: MetaPromptInfo? = nil  // ✅ ADD THIS
}
```

---

## ✅ Step 3: Parse in Network Layer (2 min)

**File:** Your API client (where you handle responses)

```swift
let (data, response) = try await urlSession.data(for: request)

// ✅ ADD THIS
if let http = response as? HTTPURLResponse {
    let meta = MetaPromptInfo.from(headers: http.allHeaderFields, fallbackBody: data)
    message.metaPrompt = meta
}
```

---

## ✅ Step 4: Display in Chat View (2 min)

**File:** Your message row view

```swift
struct MessageRow: View {
    var body: some View {
        VStack(alignment: .leading) {
            // Your existing message bubble
            Text(message.content)
            
            // ✅ ADD THIS (only for assistant messages)
            if message.role == .assistant, let meta = message.metaPrompt {
                MetaPromptPanel(meta: meta)
            }
        }
    }
}
```

---

## ✅ Step 5: Build & Test (2 min)

```bash
cd NeuroForgeApp
API_BASE=http://127.0.0.1:8014 swift run
```

**Test prompt:**
> "Run smoke tests and summarize failures"

**Expected panel:**
```
🧠 Meta-Prompt Insight      ● High • 89%
🌟 Reasoned  📚 RAG  ⏱ 756ms
Tools: pytest, grep, truth
Plan: 4 steps (expandable)
```

---

## ✅ Done!

**That's it. 3 edits. AI reasoning now visible.**

---

## Quick Reference

| Confidence | Color | Threshold |
|------------|-------|-----------|
| Low | 🔴 Red | ≤ 34% |
| Med | 🟠 Orange | 34-67% |
| High | 🟢 Green | ≥ 67% |

---

## Test Scenarios

**High Confidence:**
```
"Run smoke tests for backends and show failures"
→ 🟢 High • 92%, tools: pytest, grep
```

**Low Confidence:**
```
"What about that?"
→ 🔴 Low • 23%, 🔄 Reflection, plan: "Clarify"
```

**Tool-Driving:**
```
"Health check then smoke tests maxfail=1"
→ 🟢 High • 91%, tools: curl, pytest
```

---

## Files to Reference

- **Fast path:** `NeuroForgeApp/INTEGRATE_META_NOW.md`
- **Complete:** `NeuroForgeApp/METAPROMPT_INTEGRATION.md`
- **Quick:** `METAPROMPT_QUICKSTART.md`
- **Helpers:** `NeuroForgeApp/Sources/MetaPrompt/MetaPromptHelpers.swift`

---

## Troubleshooting (30s each)

**Panel not showing?**
```swift
print("Meta: \(message.metaPrompt)")
// Check: enabled = true
```

**Always low confidence?**
- This is real! System is uncertain
- Try more precise prompts
- Watch confidence improve after clarification

**No tools showing?**
- Normal if request didn't need tools
- Try: "Run health checks" or "Execute smoke tests"

---

**Time:** 5-8 minutes  
**Edits:** 3 files, ~15 lines  
**Impact:** Massive transparency  

**Your AI's thinking is about to be visible.** 🧠✨

