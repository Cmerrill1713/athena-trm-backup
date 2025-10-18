# 📱 **HOW TO VIEW LOGS (OSLog)**

All diagnostics now use Swift's OSLog - the proper way to log on macOS!

---

## 🎯 **METHOD 1: Terminal (Real-time)**

**Open TWO terminal windows:**

### **Terminal 1: Stream Logs**
```bash
log stream --predicate 'subsystem == "com.neuroforge.athena"' --level info
```

### **Terminal 2: Launch App**
```bash
cd /Users/christianmerrill/Documents/GitHub
/Users/christianmerrill/Library/Developer/Xcode/DerivedData/NeuroForgeApp-dylmcxgesfnrnxcdddijrrdsznam/Build/Products/Debug/NeuroForgeApp
```

**Now watch Terminal 1** - you'll see ALL logs in real-time!

---

## 🎯 **METHOD 2: Console.app (GUI)**

1. **Open Console.app** (in /Applications/Utilities/)
2. **Start streaming** (if not already)
3. **Filter:**
   - In search box, type: `subsystem:com.neuroforge.athena`
   - Or type: `FloatingChat` to see just the window logs
4. **Launch the app**
5. **Watch logs appear**

**You'll see:**
- 🪟 Window created
- isKeyWindow: true/false
- makeFirstResponder: true/false
- 👆 Field clicked (when you click)
- ✏️ Text changed (when you type)
- 📤 Sending to gateway (when you send)
- ✅ LLM reply (when it responds)

---

## 🎯 **METHOD 3: Xcode Console**

If you run from Xcode:
1. Open project in Xcode
2. Run (Cmd+R)
3. Check the console pane (bottom)
4. OSLog messages appear there automatically

---

## 🔍 **WHAT TO LOOK FOR**

### **When window opens:**
```
🪟 Floating chat window opened (NEW)
🪟 Window created
   - isKeyWindow: true   ← SHOULD BE TRUE
   - canBecomeKey: true  ← SHOULD BE TRUE
   - makeFirstResponder: true  ← SHOULD BE TRUE
```

### **When you CLICK the field:**
```
👆 Field clicked! Focus should be set now.
   - firstResponder exists: true  ← SHOULD BE TRUE
```

### **When you TYPE:**
```
✏️ Text changed: "h"
✏️ Text changed: "he"
✏️ Text changed: "hello"
```

### **When you press RETURN:**
```
⌨️ control:doCommandBy called - selector: insertNewline:
↩️ Enter key detected, sending...
📤 Sending to gateway: hello
✅ LLM reply: Hello! How can I help you today?...
```

---

## 🚨 **FAILURE MODES**

### **If you DON'T see "✏️ Text changed":**
→ Keyboard events not reaching the app
→ Check macOS Privacy settings (Accessibility)

### **If you see "isKeyWindow: false":**
→ Window can't become key
→ App not activating properly

### **If you see "makeFirstResponder: false":**
→ Field won't accept focus
→ Configuration issue

---

## 💡 **QUICK TEST COMMAND**

Run this BEFORE launching the app:
```bash
# In one terminal window:
log stream --predicate 'subsystem == "com.neuroforge.athena"' --level info | grep -E "🪟|👆|✏️|📤|✅|isKeyWindow|makeFirstResponder"
```

Then launch the app in another terminal or via Xcode.

**You'll instantly see all the diagnostic output!**

---

## 🎯 **TL;DR - EASIEST METHOD**

```bash
# Terminal 1:
log stream --predicate 'subsystem == "com.neuroforge.athena"' --level info

# Terminal 2:
cd /Users/christianmerrill/Documents/GitHub
/Users/christianmerrill/Library/Developer/Xcode/DerivedData/NeuroForgeApp-dylmcxgesfnrnxcdddijrrdsznam/Build/Products/Debug/NeuroForgeApp

# Now:
1. Press Cmd+Shift+F (opens floating window)
2. Click in the text field
3. Type "hello"
4. Press Return

# Watch Terminal 1 for all the emoji logs!
```

---

**This is the proper macOS way - no more fighting stdout!** 📱

