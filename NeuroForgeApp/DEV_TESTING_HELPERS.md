# 🔍 Dev Testing Helpers - Operations Window

**Purpose**: Quick self-test tools for Ops window behavior  
**Audience**: Developers, QA testers  
**Location**: Add to QA menu or debug overlay

---

## 🧪 Quick Test Helpers

### Force Low Confidence Trigger

**Goal**: Test auto-open on low confidence

**Method 1 - Natural Query**:
```
Send: "that thing?"
Send: "you know, the stuff"
Send: "hmm, maybe?"
```
**Expected**: Vague queries should trigger low confidence

**Method 2 - Mock Response** *(Dev only)*:
```swift
// In ChatViewEnhanced, add debug button:
Button("Force Low Confidence") {
    let mockMessage = ChatMessage(
        role: .assistant,
        content: "Test response",
        meta: MetaPromptInfo(
            enabled: true,
            confidence: 0.25,  // Below threshold
            style: "uncertain"
        )
    )
    messages.append(mockMessage)
    handleInterestingEvent(mockMessage)
}
```

---

### Force Error Trigger

**Goal**: Test auto-open on error detection

**Method 1 - UI Trigger**:
```
1. Don't send any message
2. Tap [RAG] button
3. Error: "No user message to query"
```
**Expected**: Ops auto-opens with "Error detected" toast

**Method 2 - Mock Response** *(Dev only)*:
```swift
Button("Force Error") {
    let mockMessage = ChatMessage(
        role: .assistant,
        content: "ERROR: Connection timeout while processing request",
        meta: nil
    )
    messages.append(mockMessage)
    handleInterestingEvent(mockMessage)
}
```

---

### Health Flip Test

**Goal**: Test health monitoring and display

**Stop Kokoro**:
```bash
# Terminal
pkill -f "kokoro.*serve"
# Or: make stop-kokoro (if Makefile target exists)
```

**In App**:
1. Tap [Health] button
2. Expected: `Kokoro ⚠️` in toast
3. Open Ops (⌘⌥O)
4. Expected: Health summary shows `Kokoro ⚠️`

**Restart Kokoro**:
```bash
cd /Users/christianmerrill/Documents/GitHub/kokoro
python serve.py &
```

**In App**:
1. Tap [Health] again
2. Expected: `Kokoro ✅`
3. Ops window updates to green

---

### Debounce Test

**Goal**: Verify auto-open respects 5s debounce

**Steps**:
1. Send vague query: "that?" → Ops opens
2. **Immediately** send another: "this?" → **Should NOT open** (debounced)
3. Wait 5 seconds
4. Send third: "what?" → **Should open** (debounce expired)

**Expected**: Only opens on first and third

---

### Session Limit Test

**Goal**: Verify max 5 auto-opens per session

**Steps**:
1. Send 5 vague/error queries rapidly
2. Count auto-opens (should be 5 max, some debounced)
3. On 6th trigger → Toast: "Auto-open limit reached (5/session)"
4. Restart app → Counter resets

**Expected**: Limit enforced, clear toast

---

### Threshold Test

**Goal**: Verify confidence threshold is respected

**Setup**:
1. Open Settings (⌘⌥,)
2. Set threshold to **80%**

**Test**:
1. Send normal query: "What's 2+2?"
2. Even high confidence (85%) is below 80%
3. Expected: **Does NOT auto-open** (confidence > threshold)

**Wait, that's backwards! Let me fix:**

Actually, the threshold should be: "Open if confidence < threshold"

So:
- Threshold 35% → Opens if confidence < 35%
- Threshold 80% → Opens if confidence < 80% (more triggers)

**Corrected Test**:
1. Set threshold to **10%** (very low)
2. Send normal query
3. Expected: Does NOT auto-open (confidence too high)
4. Set threshold to **90%** (very high)
5. Send normal query
6. Expected: DOES auto-open (most responses trigger)

---

### Auto-Open Toggle Test

**Goal**: Verify toggle disables all auto-opens

**Steps**:
1. Open Settings (⌘⌥,)
2. Toggle "Auto-open" **OFF**
3. Send vague query → No auto-open
4. Tap [RAG] with no context → No auto-open
5. Manual ⌘⌥O → **Still works**

**Expected**: Toggle fully disables auto-open, manual still works

---

## 🎯 Dev Menu Integration

Add to QA menu or debug overlay:

```swift
Menu("🧪 Ops Tests") {
    Button("Force Low Confidence") { /* ... */ }
    Button("Force Error") { /* ... */ }
    Button("Reset Session Counters") {
        ops.resetSessionCounters()
    }
    Divider()
    Button("Open Ops") { openWindow(id: "ops") }
    Button("Open Settings") { openWindow(id: "ops-settings") }
}
```

---

## 📊 Expected Behavior Matrix

| Trigger | Auto-Open ON | Threshold | Result |
|---------|--------------|-----------|--------|
| Confidence 90% | ✓ | 35% | ❌ No open (above threshold) |
| Confidence 25% | ✓ | 35% | ✅ Opens (below threshold) |
| Confidence 25% | ✗ | 35% | ❌ No open (toggle off) |
| Error text | ✓ | Any | ✅ Opens (error trigger) |
| Error text | ✗ | Any | ❌ No open (toggle off) |
| 2nd trigger <5s | ✓ | 35% | ❌ No open (debounced) |
| 6th trigger | ✓ | 35% | ❌ No open (session limit) |
| Manual ⌘⌥O | Any | Any | ✅ Always works |

---

## 🧯 Reset Everything

**Clean slate for testing**:

```swift
// Reset settings
UserDefaults.standard.removeObject(forKey: "autoOpenOps")
UserDefaults.standard.removeObject(forKey: "opsConfidenceThreshold")
UserDefaults.standard.removeObject(forKey: "showMetaPanels")

// Reset session counters
ops.resetSessionCounters()

// Close all windows
// ⌘W on Ops window
```

**Or**: Settings → Restore Defaults (only resets settings, not session)

---

## 🐛 Common Issues

### Auto-Open Fires Too Often
**Check**: Debounce is 5s, verify timer working
**Fix**: Add logging to `shouldAutoOpen()`

### Auto-Open Never Fires
**Check**: Toggle is ON in Settings
**Check**: Threshold is reasonable (35% default)
**Fix**: Test with forced low confidence

### Session Limit Not Enforced
**Check**: Counter increments in `recordAutoOpen()`
**Fix**: Add logging to verify `autoOpensThisSession`

### Settings Don't Persist
**Check**: @AppStorage keys match PERSISTENCE_KEYS.md
**Fix**: Verify UserDefaults.standard is being used

---

## 📝 Logging Helpers

Add to OpsState for debugging:

```swift
func shouldAutoOpen() -> (allowed: Bool, reason: String?) {
    #if DEBUG
    print("[OpsState] Checking auto-open: session=\(autoOpensThisSession)/\(maxAutoOpensPerSession)")
    if let last = lastAutoOpenAt {
        print("[OpsState] Last opened \(Date().timeIntervalSince(last))s ago")
    }
    #endif
    
    // ... existing logic
}
```

---

## ✅ Test Coverage Checklist

- [ ] Force low confidence → Opens
- [ ] Force error → Opens
- [ ] Debounce (<5s) → Blocks
- [ ] Debounce (>5s) → Allows
- [ ] Session limit (5) → Blocks 6th
- [ ] Toggle OFF → Blocks all
- [ ] Threshold respected
- [ ] Manual open always works
- [ ] Settings persist
- [ ] Restart resets session

---

## 🎯 Quick Validation Script

Run this sequence:

```
1. Send "that?" → Should open
2. Immediately send "this?" → Should NOT open (debounce)
3. Wait 6s, send "what?" → Should open
4. Repeat 3 more times → 5th opens
5. Send 6th → Toast: "limit reached"
6. ⌘⌥, → Toggle OFF
7. Send "error" → Should NOT open
8. ⌘⌥O → Should open (manual)
9. ⌘⌥, → Toggle ON, adjust threshold
10. Test threshold behavior
```

**Time**: ~2 minutes  
**Coverage**: All main paths

---

**For full validation**: See `60_SECOND_VALIDATION.md`  
**For production testing**: See `FINAL_POLISH_COMPLETE.md`

