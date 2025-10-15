# ⏱️ 60-Second Validation Checklist

**Time to Complete**: ~60 seconds  
**Purpose**: Verify all Operations window features work  
**Prerequisites**: App running with services up

---

## ✅ Part 1: Pop-Out Controls (15s)

### Test All Three Methods

- [ ] **Toolbar Button**: Click "Pop Out" → Ops window opens
- [ ] **Keyboard**: Press **⌘⌥O** → Ops window opens
- [ ] **Menu**: **Tools** → **Show Operations Window** → opens

**Expected**: Window opens via all three methods

---

## ✅ Part 2: Ops Content (20s)

### Verify Live Updates

1. **Send a normal message**: "Hello"
   - [ ] Ops window updates with confidence
   - [ ] Meta JSON appears

2. **Tap [Health] button**
   - [ ] Health summary updates in Ops
   - [ ] Shows: `Bridge ✅ Athena ✅ UAT ✅ Kokoro ✅`

**Expected**: Real-time updates in Ops window

---

## ✅ Part 3: Meta Telemetry (15s)

### Test Confidence Display

1. **Send**: "What's 2+2?"
   - [ ] High confidence (>80%) shows **green**
   - [ ] Tools and plan displayed

2. **Send**: "Explain quantum entanglement"
   - [ ] Medium confidence (65-80%) shows **orange**
   - [ ] More detailed plan

**Expected**: Confidence color-coded correctly

---

## ✅ Part 4: Auto-Open (NEW) (10s)

### Test Smart Triggers

1. **Configure Settings**: 
   - Press **⌘⌥,** or **Settings** → **Operations Settings**
   - [ ] "Auto-open Operations window" is ON
   - [ ] Threshold is 35% (default)

2. **Trigger low confidence**:
   - Send complex/ambiguous query
   - [ ] If confidence < 35%, Ops auto-opens
   - [ ] Toast shows: "⚠️ Low confidence detected"

3. **Trigger error**:
   - Tap [RAG] with no message (causes error)
   - [ ] Ops auto-opens
   - [ ] Toast shows: "⚠️ Error detected"

**Expected**: Ops opens automatically on interesting events

---

## ✅ Bonus: Settings Panel (Quick)

### Verify Controls Work

- [ ] Open: **Settings** → **Operations Settings** (⌘⌥,)
- [ ] Toggle "Auto-open" OFF
- [ ] Adjust confidence slider (0-80%)
- [ ] Toggle "Show meta-prompt panels"
- [ ] Click "Restore Defaults"

**Expected**: Settings persist across launches

---

## ✅ Fallback Tests (Optional)

### Verify Graceful Degradation

1. **Stop Kokoro**:
   ```bash
   # Kill Kokoro process
   pkill -f kokoro
   ```
   - [ ] Hold Space, speak
   - [ ] System TTS speaks (fallback works)
   - [ ] Health shows: `Kokoro ⚠️`

2. **Restart Kokoro**:
   ```bash
   cd kokoro && python serve.py &
   ```
   - [ ] Tap [Health]
   - [ ] Health shows: `Kokoro ✅`

**Expected**: App stays usable with degraded services

---

## 🎯 Quick Visual Check

**Ops Window Should Show**:
```
┌─────────────────────────────┐
│ Operations              [x] │
├─────────────────────────────┤
│ ❤️  Service Health          │
│    Bridge ✅  Athena ✅      │
│    UAT ✅  Kokoro ✅         │
├─────────────────────────────┤
│ 🧠 Meta-Prompt              │
│    Confidence: [████░░] 75% │
│    Style: reasoned          │
│    Tools: [grep] [curl]     │
│    Plan:                    │
│      1. Parse intent        │
│      2. Generate response   │
├─────────────────────────────┤
│ {} Raw Meta (JSON)          │
│    { "confidence": 0.75 }   │
└─────────────────────────────┘
```

---

## 🐛 Common Issues

### Ops Window Won't Open
**Fix**: Check window isn't already open (⌘Tab to find it)

### No Meta Data
**Fix**: Send a chat message to populate

### Auto-Open Not Working
**Fix**: Check Settings → Auto-open is ON

### Health Not Updating
**Fix**: Tap [Health] button to trigger probe

---

## ✅ Success Criteria

**All green means ready for demo**:

- ✅ Ops opens via toolbar, keyboard, menu
- ✅ Content updates live
- ✅ Confidence color-coded
- ✅ Auto-open on low confidence
- ✅ Auto-open on errors
- ✅ Settings persist
- ✅ Health tracking works
- ✅ Fallbacks graceful

---

## 🚀 Demo Script (If All Pass)

**Show stakeholders**:

1. **Open Ops**: "Watch this monitoring window" (⌘⌥O)
2. **Send message**: "What's the weather?" → Show confidence
3. **Trigger low confidence**: Complex query → Ops auto-opens
4. **Show health**: Tap [Health] → Real-time status
5. **Show meta**: Point to JSON → "Full telemetry"

---

## 📊 Validation Results

**Date**: _________  
**Tester**: _________  
**Status**: ☐ PASS  ☐ FAIL (details below)

**Notes**:
```
[Write any issues or observations here]
```

---

**Time Elapsed**: ___ seconds  
**Ready for Demo**: ☐ YES  ☐ NO

---

## 🎯 Next Steps After Validation

**If PASS**:
- ✅ Ready to demo
- ✅ Tag release
- ✅ Update changelog

**If FAIL**:
- Check logs: `tail -f logs/*.log`
- Review linter: `xcodebuild -scheme NeuroForgeApp`
- Check services: `./tools/probe_services.sh`

---

**⏱️ Target: < 60 seconds**  
**✅ Covers all critical paths**  
**🚀 Demo-ready validation**

