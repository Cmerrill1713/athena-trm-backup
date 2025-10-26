# 🛠️ MCP ECOSYSTEM TOOLS AUDIT

**Date:** October 26, 2025  
**Question:** "Is the MCP ecosystem running in docker?"  
**Answer:** ✅ **YES! Running on port 8412**

---

## ✅ WHAT'S RUNNING:

### Docker Container:
```
Container: athena-mcp-ecosystem
Status: Up 6 hours (healthy)
Port: 127.0.0.1:8412:8412
Service: mcp-ecosystem
Tools Available: 11
```

### Health Check:
```json
{
  "status": "healthy",
  "service": "mcp-ecosystem",
  "port": 8412,
  "tools_available": 11
}
```

---

## 📊 CURRENT MCP TOOLS (6 Working):

### ✅ **Available & Working:**

1. **web_search** - DuckDuckGo web search
2. **arxiv_search** - Research papers from arXiv
3. **youtube_get_transcript** - YouTube video transcripts
4. **wikipedia_search** - Wikipedia content
5. **vision_analyze** - Image analysis (placeholder)
6. **code_execute** - Code execution (placeholder)

### ❌ **NOT Available (Need to Add):**

7. **filesystem_read** - Read files from macOS
8. **filesystem_write** - Write files to macOS
9. **calendar_add** - Add events to Calendar.app
10. **reminder_add** - Add tasks to Reminders.app
11. **notes_create** - Create notes in Notes.app
12. **mail_send** - Send emails via Mail.app
13. **messages_send** - Send iMessages
14. **app_launch** - Launch Mac apps
15. **app_install** - Install apps from App Store

---

## 🎯 THE GAP:

**We have:**
- ✅ Web search tools (working!)
- ✅ Research tools (working!)
- ✅ Basic MCP infrastructure

**We're missing:**
- ❌ macOS system control
- ❌ Filesystem access
- ❌ Calendar/Reminders integration
- ❌ App Store integration
- ❌ Process management

---

## 📱 WHAT WE NEED TO ADD:

### **Option 1: Add to Existing MCP Container** (Recommended)

**Extend `services/mcp-ecosystem/app.py` with:**

```python
# Add these tool endpoints:

@app.post("/tool/filesystem_read")
async def filesystem_read(request: ToolRequest):
    """Read file from macOS filesystem"""
    path = request.arguments.get("path")
    with open(path, 'r') as f:
        return {"content": f.read()}

@app.post("/tool/filesystem_write")
async def filesystem_write(request: ToolRequest):
    """Write file to macOS filesystem"""
    path = request.arguments.get("path")
    content = request.arguments.get("content")
    with open(path, 'w') as f:
        f.write(content)
    return {"success": True}

@app.post("/tool/calendar_add")
async def calendar_add(request: ToolRequest):
    """Add event to Calendar.app via AppleScript"""
    import subprocess
    title = request.arguments.get("title")
    date = request.arguments.get("date")
    
    script = f'''
    tell application "Calendar"
        tell calendar "Family"
            make new event with properties {{summary:"{title}"}}
        end tell
    end tell
    '''
    
    result = subprocess.run(['osascript', '-e', script], 
                          capture_output=True, text=True)
    return {"success": result.returncode == 0}

@app.post("/tool/reminder_add")
async def reminder_add(request: ToolRequest):
    """Add reminder to Reminders.app via AppleScript"""
    import subprocess
    name = request.arguments.get("name")
    list_name = request.arguments.get("list", "Reminders")
    
    script = f'''
    tell application "Reminders"
        tell list "{list_name}"
            make new reminder with properties {{name:"{name}"}}
        end tell
    end tell
    '''
    
    result = subprocess.run(['osascript', '-e', script],
                          capture_output=True, text=True)
    return {"success": result.returncode == 0}

# ... add more tools ...
```

**Location:** `services/mcp-ecosystem/app.py`  
**Effort:** 2-3 hours  
**Result:** All tools in one container!

---

### **Option 2: Separate macOS Bridge Service**

Create new service: `services/macos-bridge/`

**Pros:**
- Separation of concerns
- Can run with different permissions
- Easier to secure

**Cons:**
- More containers to manage
- Network overhead

---

## 🔐 SECURITY CONSIDERATIONS:

### **Current MCP Container:**
- ✅ Runs in Docker
- ✅ Network isolated
- ⚠️ Can't access macOS system by default

### **To Add macOS Control:**
Need to modify `docker-compose.yml`:

```yaml
athena-mcp-ecosystem:
  # ... existing config ...
  volumes:
    - /Users/christianmerrill:/host-home:rw  # Access user home
    - /Applications:/host-apps:ro            # Access Mac apps
  privileged: true                           # For AppleScript
  # OR mount Docker socket for app_launch
  - /var/run/docker.sock:/var/run/docker.sock:ro
```

**Security Risk:**
- Giving Docker container access to macOS filesystem
- AppleScript requires automation permissions

**Mitigation:**
- ✅ Judicial oversight (already have!)
- ✅ Path allowlist
- ✅ Audit logging
- ✅ User confirmation for sensitive actions

---

## 💡 BETTER APPROACH (User's Insight):

### **Don't Run macOS Tools in Docker!**

**Problem:** Docker containers can't easily control macOS GUI apps

**Solution:** Run macOS Bridge as **native Mac service** (not in Docker)

```
┌─────────────────────────────────────┐
│  MCP Ecosystem (Docker)             │
│  Port 8412                          │
│  ✅ Web search, ArXiv, YouTube      │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  macOS Bridge (Native Mac)          │
│  Port 8099                          │
│  ✅ Calendar, Reminders, Notes      │
│  ✅ AppleScript, Shortcuts          │
│  ✅ App Store, File system          │
└─────────────────────────────────────┘
```

**Benefits:**
- ✅ Native macOS access (no Docker limitations)
- ✅ Full automation permissions
- ✅ Can control any Mac app
- ✅ Cleaner separation

---

## 🚀 RECOMMENDED ARCHITECTURE:

### **Keep Separate:**

1. **MCP Ecosystem (Docker)** - Web/research tools
   - web_search
   - arxiv_search
   - youtube_get_transcript
   - wikipedia_search
   - Already working! ✅

2. **macOS Bridge (Native)** - System control
   - calendar_*
   - reminder_*
   - notes_*
   - mail_*
   - messages_*
   - app_launch
   - app_install
   - filesystem_*
   - Run natively on macOS! 🚀

---

## ✅ WHAT EXISTS TODAY:

**MCP Ecosystem (Docker - Port 8412):**
- ✅ Running and healthy
- ✅ 6 tools working
- ✅ Web search, ArXiv, YouTube

**MCP Frontend Tools (services/mcp_frontend_tools.py):**
- ⚠️ Exists but NOT running
- Has: xcode_build, app_launch, ui_typing_probe
- Uses: AppleScript (osascript)
- Port: 8413 (not in docker-compose)

**Calendar Monitor (NeuroForge):**
- ✅ Exists: `calendar_monitor.py`
- Syncs macOS Calendar
- Not exposed as API

---

## 🎯 ACTION PLAN:

### **Quick Win (1-2 hours):**

1. **Add macOS tools to MCP ecosystem container**
   - Add filesystem_read, filesystem_write
   - Add calendar/reminder tools via AppleScript
   - Update docker-compose with necessary volumes/permissions

### **OR Better Approach (2-3 hours):**

2. **Run macOS Bridge as native service**
   - Start `mcp_frontend_tools.py` (already exists!)
   - Extend with calendar/reminder/notes tools
   - Add to docker-compose as external service
   - Keep MCP ecosystem for web tools

---

## 💭 RECOMMENDATION:

**Option 2: Native macOS Bridge**

**Why:**
- ✅ Already have `mcp_frontend_tools.py`
- ✅ Native Mac access (no Docker issues)
- ✅ Full automation permissions
- ✅ Cleaner architecture

**Add to docker-compose:**
```yaml
  macos-bridge:
    image: athena/macos-bridge:latest
    network_mode: "host"  # Access localhost Mac services
    volumes:
      - /Users/christianmerrill:/home:rw
    # This runs NATIVELY, not in Docker
```

**Or simpler:** Just run as systemd/launchd service on macOS!

---

**Bottom Line:**  
- ✅ MCP ecosystem running in Docker (web tools)
- ❌ macOS control tools NOT in Docker (need native access)
- 🚀 Solution: Run macOS Bridge natively, keep MCP for web tools

**Next:** Add macOS tools to the ecosystem!
