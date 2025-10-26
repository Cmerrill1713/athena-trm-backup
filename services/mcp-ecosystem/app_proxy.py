#!/usr/bin/env python3
"""
Simplified MCP Ecosystem with Proxy to macOS Bridge
"""
import os
import logging
import requests
import json
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, Any, List

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="MCP Ecosystem", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class ToolRequest(BaseModel):
    arguments: Dict[str, Any] = {}

# macOS Bridge URL
MACOS_BRIDGE_URL = os.getenv("MACOS_BRIDGE_URL", "http://host.docker.internal:8099")

def proxy_to_bridge(endpoint: str, arguments: dict) -> dict:
    """Proxy request to native macOS Bridge"""
    try:
        response = requests.post(f"{MACOS_BRIDGE_URL}{endpoint}", json={"arguments": arguments}, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"success": False, "error": "macOS Bridge not running. Start with: python3 services/macos-bridge/app.py"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/tool/{tool_name}")
async def execute_tool(tool_name: str, request: ToolRequest):
    """Execute MCP tool - proxy AppleScript tools to native bridge"""
    logger.info(f"Tool call: {tool_name}")
    
    # AppleScript tools - proxy to native bridge
    applescript_tools = {
        "calendar_add": "/calendar/add",
        "calendar_list": "/calendar/list",
        "reminder_add": "/reminders/add",
        "reminder_list": "/reminders/list",
        "notes_create": "/notes/create",
        "messages_send": "/messages/send",
        "app_launch": "/app/launch",
        "app_install": "/app/install"
    }
    
    if tool_name in applescript_tools:
        return proxy_to_bridge(applescript_tools[tool_name], request.arguments)
    
    # Filesystem tools - handled directly (mounted volume)
    elif tool_name == "filesystem_write":
        path = request.arguments.get("path", "").replace("~", "/host-home", 1)
        content = request.arguments.get("content", "")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return {"success": True, "path": path, "bytes_written": len(content)}
    
    elif tool_name == "filesystem_read":
        path = request.arguments.get("path", "").replace("~", "/host-home", 1)
        with open(path, 'r') as f:
            content = f.read()
        return {"success": True, "content": content}
    
    # Web/research tools - simplified placeholders
    elif tool_name == "web_search":
        return {"results": [{"title": "Web search placeholder", "url": "", "snippet": ""}]}
    elif tool_name == "arxiv_search":
        return {"papers": []}
    else:
        raise HTTPException(status_code=404, detail=f"Unknown tool: {tool_name}")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "mcp-ecosystem", "port": 8412, "tools_available": 18}

@app.get("/tools")
async def list_tools():
    return {"tools": ["web_search", "arxiv_search", "filesystem_read", "filesystem_write", "filesystem_list", "calendar_add", "calendar_list", "reminder_add", "reminder_list", "notes_create", "messages_send", "app_launch", "app_install"]}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8412, log_level="info")
