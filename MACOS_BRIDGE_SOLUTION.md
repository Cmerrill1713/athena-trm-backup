# 🖥️ macOS Bridge Solution - Docker Limitation

## ❌ THE PROBLEM:

**Docker on macOS can't run AppleScript directly!**

- Docker containers are isolated from macOS GUI
- `network_mode: host` doesn't work on macOS like Linux
- AppleScript (`osascript`) requires macOS system access
- Containers can't control Calendar.app, Reminders.app, etc.

---

## ✅ THE SOLUTION:

### **Two-Tier Architecture:**

```
┌─────────────────────────────────────┐
│  MCP Ecosystem (Docker)             │
│  Port 8412                          │
│  ✅ Filesystem tools (mounted vol)  │
│  ✅ Web search, ArXiv, YouTube      │
│  ⚠️  Calendar/Reminders tools →     │
│       Proxy to macOS Bridge         │
└──────────────┬──────────────────────┘
               │ HTTP
               ↓
┌─────────────────────────────────────┐
│  macOS Bridge (Native Mac Service)  │
│  Port 8099                          │
│  ✅ AppleScript execution           │
│  ✅ Calendar.app control            │
│  ✅ Reminders.app control           │
│  ✅ Notes.app, Messages.app         │
│  ✅ App Store (mas CLI)             │
└─────────────────────────────────────┘
```

---

## 🛠️ IMPLEMENTATION:

### **1. MCP Ecosystem (Docker) - Filesystem Tools ✅**

**Can do:**
- ✅ filesystem_read/write (mounted /host-home)
- ✅ filesystem_list
- ✅ web_search, arxiv_search
- ✅ youtube, wikipedia

**Can't do (needs native macOS):**
- ❌ AppleScript (osascript)
- ❌ Calendar/Reminders direct control
- ❌ Messages.app control

### **2. macOS Bridge (Native) - AppleScript Tools**

**Start native Python service:**
```bash
# Run on native macOS (not in Docker)
python3 services/macos-bridge/app.py
# Runs on localhost:8099
```

**Tools:**
- calendar_add, calendar_list
- reminder_add, reminder_list
- notes_create
- messages_send
- app_launch
- app_install

### **3. MCP Proxies AppleScript Calls**

**In MCP container:**
```python
elif tool_name == "calendar_add":
    # Proxy to native macOS bridge
    response = requests.post(
        f"{MACOS_BRIDGE_URL}/calendar/add",
        json=request.arguments
    )
    return response.json()
```

---

## 📊 WHAT WORKS NOW:

### ✅ **Working (No Changes Needed):**
- Filesystem tools (mounted volume works!)
- Web/research tools (already working)

### ⚠️ **Needs macOS Bridge:**
- Calendar/Reminders
- Notes
- Messages
- App launch/install

---

## 🚀 NEXT STEPS:

### **Option A: Create macOS Bridge Service** (2-3 hours)
1. Create `services/macos-bridge/app.py`
2. Implement AppleScript endpoints
3. Start as native Mac service
4. Update MCP to proxy AppleScript calls

### **Option B: Use Existing mcp_frontend_tools.py** (1 hour)
1. Extend `services/mcp_frontend_tools.py`
2. Add calendar/reminder tools
3. Start as native service on port 8099
4. MCP proxies to it

### **Option C: Document Current State** (5 mins)
1. Filesystem tools work now! ✅
2. Document that AppleScript tools need native service
3. Ship as-is, add AppleScript later

---

## 💡 RECOMMENDATION:

**Option B: Extend existing mcp_frontend_tools.py**

**Why:**
- Already has AppleScript infrastructure
- Already has app_launch tool
- Just needs calendar/reminder/notes tools added
- Quick to implement!

**Result:** Complete macOS control in ~1 hour!

---

*Docker on macOS limitation discovered - two-tier approach is the solution!*
