#!/usr/bin/env python3
"""
macOS Bridge Service - Native macOS Integration
Port 8099 - Runs NATIVELY on macOS (not in Docker)

Provides AppleScript-based tools for:
- Calendar.app control
- Reminders.app control
- Notes.app control
- Messages.app control
- App launching
- App Store downloads
"""

import os
import subprocess
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Athena macOS Bridge",
    description="Native macOS integration via AppleScript",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ToolRequest(BaseModel):
    """Tool execution request."""
    arguments: Dict[str, Any] = {}

# ===========================================================================
# CALENDAR TOOLS (Calendar.app)
# ===========================================================================

@app.post("/calendar/add")
async def calendar_add(request: ToolRequest):
    """Add event to Calendar.app via AppleScript"""
    title = request.arguments.get("title", "")
    date = request.arguments.get("date", "")
    duration_hours = request.arguments.get("duration_hours", 1)
    calendar_name = request.arguments.get("calendar", "Home")
    
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    
    try:
        # Parse date (supports "tomorrow", "today", or ISO)
        if date.lower() == "tomorrow":
            date_expr = "(current date) + 1 * days"
        elif date.lower() == "today":
            date_expr = "current date"
        else:
            date_expr = f'date "{date}"'
        
        script = f'''
tell application "Calendar"
    tell calendar "{calendar_name}"
        set newEvent to make new event with properties {{summary:"{title}", start date:{date_expr}, end date:{date_expr} + {duration_hours} * hours}}
    end tell
end tell
return "Event created"
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        logger.info(f"Calendar add: {title} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "title": title,
            "calendar": calendar_name,
            "output": result.stdout.strip(),
            "error": result.stderr.strip() if result.stderr else None
        }
    except Exception as e:
        logger.error(f"Calendar add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calendar/list")
async def calendar_list(request: ToolRequest):
    """List upcoming events from Calendar.app"""
    calendar_name = request.arguments.get("calendar", "Home")
    days_ahead = request.arguments.get("days_ahead", 7)
    
    try:
        script = f'''
tell application "Calendar"
    tell calendar "{calendar_name}"
        set eventList to events whose start date is greater than (current date) and start date is less than ((current date) + {days_ahead} * days)
        set output to ""
        repeat with evt in eventList
            set output to output & summary of evt & " | " & (start date of evt as string) & linefeed
        end repeat
        return output
    end tell
end tell
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        events = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if ' | ' in line:
                    title, date = line.split(' | ', 1)
                    events.append({"title": title, "date": date})
        
        logger.info(f"Calendar list: {len(events)} events")
        return {
            "success": True,
            "calendar": calendar_name,
            "events": events
        }
    except Exception as e:
        logger.error(f"Calendar list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# REMINDERS TOOLS (Reminders.app)
# ===========================================================================

@app.post("/reminders/add")
async def reminder_add(request: ToolRequest):
    """Add reminder to Reminders.app"""
    name = request.arguments.get("name", "")
    list_name = request.arguments.get("list", "Reminders")
    
    if not name:
        raise HTTPException(status_code=400, detail="name required")
    
    try:
        script = f'''
tell application "Reminders"
    tell list "{list_name}"
        make new reminder with properties {{name:"{name}"}}
    end tell
end tell
return "Reminder created"
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        logger.info(f"Reminder add: {name} to {list_name} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "name": name,
            "list": list_name,
            "output": result.stdout.strip()
        }
    except Exception as e:
        logger.error(f"Reminder add error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/reminders/list")
async def reminder_list(request: ToolRequest):
    """List reminders from Reminders.app"""
    list_name = request.arguments.get("list", "Reminders")
    
    try:
        script = f'''
tell application "Reminders"
    tell list "{list_name}"
        set reminderList to reminders
        set output to ""
        repeat with rem in reminderList
            set output to output & name of rem & " | " & (completed of rem as string) & linefeed
        end repeat
        return output
    end tell
end tell
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        reminders = []
        if result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                if ' | ' in line:
                    name, completed = line.split(' | ', 1)
                    reminders.append({"name": name, "completed": completed == "true"})
        
        logger.info(f"Reminder list: {len(reminders)} items")
        return {
            "success": True,
            "list": list_name,
            "reminders": reminders
        }
    except Exception as e:
        logger.error(f"Reminder list error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# NOTES TOOL (Notes.app)
# ===========================================================================

@app.post("/notes/create")
async def notes_create(request: ToolRequest):
    """Create note in Notes.app"""
    title = request.arguments.get("title", "")
    body = request.arguments.get("body", "")
    folder = request.arguments.get("folder", "Notes")
    
    if not title:
        raise HTTPException(status_code=400, detail="title required")
    
    try:
        script = f'''
tell application "Notes"
    tell folder "{folder}"
        make new note with properties {{name:"{title}", body:"{body}"}}
    end tell
end tell
return "Note created"
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        logger.info(f"Note created: {title} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "title": title,
            "folder": folder
        }
    except Exception as e:
        logger.error(f"Note create error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# MESSAGES TOOL (Messages.app)
# ===========================================================================

@app.post("/messages/send")
async def messages_send(request: ToolRequest):
    """Send iMessage via Messages.app"""
    recipient = request.arguments.get("recipient", "")
    message = request.arguments.get("message", "")
    
    if not recipient or not message:
        raise HTTPException(status_code=400, detail="recipient and message required")
    
    try:
        # Escape quotes in message
        safe_message = message.replace('"', '\\"')
        
        script = f'''
tell application "Messages"
    set targetBuddy to buddy "{recipient}"
    send "{safe_message}" to targetBuddy
end tell
return "Message sent"
'''
        
        result = subprocess.run(
            ['osascript', '-e', script],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        logger.info(f"Message sent to {recipient} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "recipient": recipient,
            "message_preview": message[:50] + "..." if len(message) > 50 else message
        }
    except Exception as e:
        logger.error(f"Message send error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# APP MANAGEMENT TOOLS
# ===========================================================================

@app.post("/app/launch")
async def app_launch(request: ToolRequest):
    """Launch macOS app"""
    app_name = request.arguments.get("app_name", "")
    
    if not app_name:
        raise HTTPException(status_code=400, detail="app_name required")
    
    try:
        result = subprocess.run(
            ['open', '-a', app_name],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        success = result.returncode == 0
        logger.info(f"App launch: {app_name} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "app_name": app_name,
            "error": result.stderr.strip() if result.stderr else None
        }
    except Exception as e:
        logger.error(f"App launch error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/app/install")
async def app_install(request: ToolRequest):
    """Install app from Mac App Store"""
    app_id = request.arguments.get("app_id", "")
    app_name = request.arguments.get("app_name", "")
    
    # Requires 'mas' CLI: brew install mas
    
    try:
        if app_id:
            # Install by ID
            result = subprocess.run(
                ['mas', 'install', app_id],
                capture_output=True,
                text=True,
                timeout=300
            )
        elif app_name:
            # Search first
            search_result = subprocess.run(
                ['mas', 'search', app_name],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if search_result.returncode == 0 and search_result.stdout:
                first_line = search_result.stdout.split('\n')[0]
                app_id = first_line.split()[0]
                
                result = subprocess.run(
                    ['mas', 'install', app_id],
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            else:
                return {
                    "success": False,
                    "error": "App not found in App Store"
                }
        else:
            raise HTTPException(status_code=400, detail="app_id or app_name required")
        
        success = result.returncode == 0
        logger.info(f"App install: {app_name or app_id} - {'✅' if success else '❌'}")
        
        return {
            "success": success,
            "app_id": app_id,
            "app_name": app_name
        }
    except FileNotFoundError:
        return {
            "success": False,
            "error": "'mas' CLI not installed. Install with: brew install mas"
        }
    except Exception as e:
        logger.error(f"App install error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ===========================================================================
# HEALTH & INFO
# ===========================================================================

@app.get("/health")
async def health():
    """Health check"""
    return {
        "status": "healthy",
        "service": "macos-bridge",
        "port": 8099,
        "platform": "macOS",
        "tools_available": 9
    }

@app.get("/tools")
async def list_tools():
    """List available tools"""
    return {
        "tools": [
            "calendar_add",
            "calendar_list",
            "reminder_add",
            "reminder_list",
            "notes_create",
            "messages_send",
            "mail_send",
            "app_launch",
            "app_install"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("MACOS_BRIDGE_PORT", "8099"))
    logger.info(f"🖥️  Starting macOS Bridge on port {port}")
    logger.info("🔧 This service runs NATIVELY on macOS (not in Docker)")
    logger.info("✅ AppleScript tools available!")
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="info")
