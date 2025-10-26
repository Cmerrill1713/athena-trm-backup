# 🪟 Operations Window - Real-Time Monitoring

**Feature**: Detachable operations window for live monitoring  
**Status**: ✅ Complete  
**Shortcut**: ⌘⌥O

---

## 🎯 What It Does

Pop-out window that shows real-time monitoring of:
- **Service Health**: Bridge, Athena, UAT, Kokoro status
- **Meta-Prompt Confidence**: 0-100% with color coding
- **Tools Used**: List of tools in last response
- **Plan Steps**: Reflection/reasoning plan
- **Raw Meta JSON**: Full meta-prompt payload

---

## 🚀 How to Use

### Open the Window

**Method 1: Toolbar Button**
- Click **"Operations"** button (rectangle.badge.plus icon)
- Located in top-right of main chat window

**Method 2: Keyboard Shortcut**
- Press **⌘⌥O** (Command-Option-O)

**Method 3: Menu**
- **Tools** → **Show Operations Window**

### What You See

```
┌─────────────────────────────────────┐
│ Operations                      [x] │
├─────────────────────────────────────┤
│ ❤️  Service Health                  │
│    Bridge ✅  Athena ✅  UAT ✅      │
│    Kokoro ✅                         │
├─────────────────────────────────────┤
│ 🧠 Meta-Prompt                      │
│    Confidence: [████████░░] 89%     │
│    Style: reasoned                   │
│    RAG: ✓  Reflection: —            │
│    Tools: [pytest] [grep] [curl]    │
│    Plan:                             │
│      1. Parse user intent            │
│      2. Check relevant context       │
│      3. Generate response            │
├─────────────────────────────────────┤
│ {} Raw Meta (JSON)                  │
│    {                                 │
│      "enabled": true,                │
│      "confidence": 0.89,             │
│      "style": "reasoned",            │
│      ...                             │
│    }                                 │
└─────────────────────────────────────┘
```

---

## 📊 What Gets Monitored

### Service Health
- **Source**: Health banner + multi-service probe
- **Updates**: When you tap [Health] button
- **Format**: `Bridge ✅  Athena ✅  UAT ✅  Kokoro ✅`

### Meta-Prompt Data
- **Source**: Response headers from Bridge/Athena
- **Updates**: After each assistant message
- **Fields**:
  - Confidence (0.0-1.0)
  - Style (reasoned, terse, creative, etc.)
  - RAG enabled (yes/no)
  - Reflection enabled (yes/no)
  - Tools used (array)
  - Plan steps (array)

### Color Coding

**Confidence**:
- 🟢 **Green**: 80%+ (High confidence)
- 🟠 **Orange**: 65-79% (Medium confidence)
- 🔴 **Red**: <65% (Low confidence)

**Health**:
- 🟢 **Green**: 4/4 services up
- 🟡 **Yellow**: 1-3 services up
- 🔴 **Red**: 0 services up

---

## 🎨 Features

### Always Synced
- Window mirrors main chat state
- Updates in real-time as you interact
- Can be open while chatting

### Detachable
- Move to second monitor
- Resize to fit your screen
- Close and reopen anytime

### JSON Inspector
- Full meta-prompt payload
- Pretty-printed for readability
- Selectable text for copying

---

## 🧪 Test It

1. **Launch app** with services running
2. **Press ⌘⌥O** or click **Operations** button
3. **Send a message** in chat
4. **Watch window update** with:
   - Confidence level
   - Tools used
   - Plan steps
   - Raw JSON

5. **Tap [Health]** button
6. **See health summary** update

---

## 🔧 Integration Points

### Data Flow

```
User sends message
  ↓
Bridge/Athena processes
  ↓
Response with meta headers
  ↓
ChatViewEnhanced receives
  ↓
OpsState.update(from:) called
  ↓
Operations window updates
```

### Code Structure

```
Sources/Ops/
├── OpsState.swift       # Shared state
└── OpsWindow.swift      # UI window

Sources/main.swift       # Window registration
Sources/Features/
└── ChatViewEnhanced.swift  # Data feeding
```

---

## 🎯 Use Cases

### Development
- Monitor meta-prompt confidence live
- Debug RAG integration
- Watch tool selection
- Verify plan generation

### Operations
- Check service health at a glance
- Monitor system responsiveness
- Verify meta headers present
- Debug integration issues

### Demonstrations
- Show meta-awareness to stakeholders
- Display confidence thresholds
- Prove tool orchestration
- Visualize reasoning plans

---

## 📝 Technical Details

### State Management
- **OpsState**: ObservableObject with @Published properties
- **Shared**: Injected via EnvironmentObject
- **Thread-safe**: Updates wrapped in MainActor.run

### Window Management
- **Type**: WindowGroup (native SwiftUI)
- **ID**: "ops"
- **Style**: .titleBar
- **Size**: 720×520 default, resizable

### Performance
- **Updates**: On-demand (when meta arrives)
- **Memory**: Minimal (just last meta snapshot)
- **CPU**: Negligible (passive display)

---

## 🐛 Troubleshooting

### Window Doesn't Open
- Check **Tools** menu has "Show Operations Window"
- Try **⌘⌥O** keyboard shortcut
- Restart app if needed

### No Data Showing
- Send a chat message to populate
- Ensure meta headers are present
- Check Bridge is returning meta

### Health Not Updating
- Tap **[Health]** button to trigger probe
- Verify services are running
- Check ServiceRegistry endpoints

---

## 🎨 Customization

### Modify What's Shown

Edit `OpsWindow.swift`:
```swift
// Add new fields
if let latency = ops.lastLatencyMs {
    Text("Latency: \(latency)ms")
}

// Change layout
VStack { ... } → HStack { ... }

// Add graphs
ConfidenceSparkline(history: ops.confidenceHistory)
```

### Change Window Size

Edit `main.swift`:
```swift
.defaultSize(width: 720, height: 520)  // ← Adjust
```

### Add More Data

Edit `OpsState.swift`:
```swift
@Published var lastLatencyMs: Int?
@Published var confidenceHistory: [Double] = []
```

---

## 🚀 Future Enhancements

**Potential additions**:
- [ ] Confidence sparkline graph
- [ ] Service latency chart
- [ ] Request/response timeline
- [ ] Tool usage statistics
- [ ] Export to JSON file
- [ ] Always-on-top mode
- [ ] Dark/light theme toggle

---

## 📚 Related Docs

- `SERVICE_INTEGRATION_GUIDE.md` - Service endpoints
- `ATHENA_INTEGRATION.md` - Voice orchestration
- `META_UX_COMPLETE.md` - Meta-prompt UX
- `METAPROMPT_INTEGRATION.md` - Meta headers

---

## ✅ Summary

**What**: Real-time operations monitoring window  
**How**: ⌘⌥O or toolbar button  
**Shows**: Health, confidence, tools, plan, JSON  
**Updates**: Live as you chat  
**Status**: ✅ Ready to use

---

**Press ⌘⌥O and start monitoring!** 🪟📊

