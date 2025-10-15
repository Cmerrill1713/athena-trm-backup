#!/usr/bin/env python3
"""
MCP Ecosystem Master Orchestrator
Starts all MCP servers and provides a unified HTTP gateway
"""
import os
import subprocess
from typing import Dict

import uvicorn
from fastapi import FastAPI, HTTPException

app = FastAPI(title="MCP Ecosystem Gateway", version="1.0.0")

# Track running servers
running_servers: Dict[str, subprocess.Popen] = {}

SERVER_MAP = {
    "youtube": "/mcp/python_servers/youtube_server.py",
    "research": "/mcp/python_servers/research_server.py",
    "web": "/mcp/python_servers/web_server.py",
    "storage": "/mcp/python_servers/store_client.py",
    "filesystem": "/mcp/python_servers/filesystem_server.py",
    "code_execution": "/mcp/python_servers/code_execution_server.py",
    "image_generation": "/mcp/python_servers/image_generation_server.py",
    "vision": "/mcp/python_servers/vision_server.py",
    "google": "/mcp/python_servers/google_server.py",
    "microsoft": "/mcp/python_servers/microsoft_server.py",
    "aws": "/mcp/python_servers/aws_server.py",
    "nvidia": "/mcp/python_servers/nvidia_server.py",
    "cohere": "/mcp/python_servers/cohere_server.py",
    "mistral": "/mcp/python_servers/mistral_server.py",
    "groq": "/mcp/python_servers/groq_server.py",
}

@app.get("/")
async def root():
    """Root endpoint with server information"""
    return {
        "service": "MCP Ecosystem Gateway",
        "version": "1.0.0",
        "servers_available": len(SERVER_MAP),
        "servers": list(SERVER_MAP.keys()),
        "status": "running"
    }

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "servers_available": len(SERVER_MAP),
        "servers_configured": list(SERVER_MAP.keys())
    }

@app.get("/servers")
async def list_servers():
    """List all available MCP servers"""
    servers_info = []
    for name, path in SERVER_MAP.items():
        exists = os.path.exists(path)
        servers_info.append({
            "name": name,
            "path": path,
            "exists": exists,
            "category": _get_category(name)
        })

    return {
        "servers": servers_info,
        "total": len(servers_info)
    }

@app.get("/servers/{server_name}/tools")
async def get_server_tools(server_name: str):
    """Get tools available in a specific server"""
    if server_name not in SERVER_MAP:
        raise HTTPException(status_code=404, detail=f"Server '{server_name}' not found")

    server_path = SERVER_MAP[server_name]
    if not os.path.exists(server_path):
        raise HTTPException(status_code=404, detail=f"Server file not found: {server_path}")

    # Parse tools from the server file
    tools = _parse_tools(server_path)

    return {
        "server": server_name,
        "tools": tools,
        "count": len(tools)
    }

def _get_category(server_name: str) -> str:
    """Categorize server"""
    categories = {
        "youtube": "Content",
        "research": "Content",
        "web": "Content",
        "storage": "Infrastructure",
        "filesystem": "Agent Autonomy",
        "code_execution": "Agent Autonomy",
        "image_generation": "Agent Autonomy",
        "vision": "Agent Autonomy",
        "google": "AI Models",
        "microsoft": "AI Models",
        "aws": "AI Models",
        "nvidia": "AI Models",
        "cohere": "AI Models",
        "mistral": "AI Models",
        "groq": "AI Models",
    }
    return categories.get(server_name, "Other")

def _parse_tools(filepath: str) -> list:
    """Parse @mcp.tool() or @tool() decorated functions from file"""
    tools = []
    try:
        with open(filepath, 'r') as f:
            content = f.read()

        import re
        # Find all @tool() or @mcp.tool() decorators
        pattern = r'@(?:mcp\.)?tool\(\)\s+def\s+(\w+)\([^)]*\):'
        matches = re.finditer(pattern, content)

        for match in matches:
            tool_name = match.group(1)
            # Try to extract docstring
            rest = content[match.end():]
            docstring_match = re.search(r'"""\s*(.*?)\s*"""', rest, re.DOTALL)
            description = docstring_match.group(1).split('\n')[0] if docstring_match else ""

            tools.append({
                "name": tool_name,
                "description": description.strip()
            })
    except Exception as e:
        print(f"Error parsing {filepath}: {e}")

    return tools

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 MCP ECOSYSTEM GATEWAY STARTING")
    print("="*70)
    print(f"\n📊 {len(SERVER_MAP)} MCP Servers Available:")

    for name, path in SERVER_MAP.items():
        exists = "✅" if os.path.exists(path) else "❌"
        print(f"   {exists} {name}")

    print("\n🌐 Starting HTTP Gateway on port 8412...")
    print("="*70 + "\n")

    # Start FastAPI server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8412,
        log_level="info"
    )

