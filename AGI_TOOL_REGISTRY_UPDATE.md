# AGI Tool Registry Update

## Add Frontend Tools to AGI Core

To enable AGI to fix the frontend, add these tools to your AGI Core configuration:

### Option 1: Environment Variables (Quick)

Add to `docker-compose.yml` under `agi-core` service:

```yaml
environment:
  # ... existing vars ...
  - FRONTEND_XCODE_BUILD=http://host.docker.internal:8413/tool/xcode_build
  - FRONTEND_APP_LAUNCH=http://host.docker.internal:8413/tool/app_launch
  - FRONTEND_UI_TYPING_PROBE=http://host.docker.internal:8413/tool/ui_typing_probe
  - FRONTEND_SWIFT_REFLEX=http://host.docker.internal:8413/tool/swift_frontend_reflex
  - GIT_COMMIT_PUSH_PR=http://mcp-ecosystem:8412/tool/git_commit_push_pr
```

### Option 2: Tool Registry File (Recommended)

Create `agi_core/tool_registry.yaml`:

```yaml
tools:
  # MCP Ecosystem Tools
  mcp.web_search:
    url: http://athena-mcp-ecosystem:8412/tool/web_search
    timeout_ms: 10000
    
  mcp.fs.read:
    url: http://athena-mcp-ecosystem:8412/tool/file_read
    timeout_ms: 5000
    
  mcp.fs.write:
    url: http://athena-mcp-ecosystem:8412/tool/file_write
    timeout_ms: 5000
    
  mcp.fs.patch:
    url: http://athena-mcp-ecosystem:8412/tool/file_apply_patch
    timeout_ms: 5000
    
  mcp.shell:
    url: http://athena-mcp-ecosystem:8412/tool/shell
    timeout_ms: 30000

  # Frontend Tools (running on host)
  frontend.xcode_build:
    url: http://host.docker.internal:8413/tool/xcode_build
    timeout_ms: 120000  # 2 minutes for build
    
  frontend.app_launch:
    url: http://host.docker.internal:8413/tool/app_launch
    timeout_ms: 10000
    
  frontend.ui_typing_probe:
    url: http://host.docker.internal:8413/tool/ui_typing_probe
    timeout_ms: 15000
    
  frontend.swift_frontend_reflex:
    url: http://host.docker.internal:8413/tool/swift_frontend_reflex
    timeout_ms: 60000

  # Git Tools
  git.commit_push_pr:
    url: http://athena-mcp-ecosystem:8412/tool/git_commit_push_pr
    timeout_ms: 30000

  # LLM Tools
  uai.chat:
    url: http://uai:8080/v1/chat/completions
    timeout_ms: 30000
    
  gateway.llm:
    url: http://athena-api:8000/v1/chat/completions
    timeout_ms: 30000
```

Then update `agi_core/agi_service.py` to load it:

```python
import yaml

# Load tool registry
with open('agi_core/tool_registry.yaml') as f:
    TOOL_REGISTRY = yaml.safe_load(f)['tools']
```

### Option 3: Direct in Code (Fast Test)

Update the TOOL_REGISTRY in `agi_core/agi_service.py`:

```python
TOOL_REGISTRY = {
    # Existing tools
    "mcp.web_search": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/web_search",
    "mcp.fs.patch": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/file_apply_patch",
    "mcp.fs.read": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/file_read",
    "mcp.fs.write": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/file_write",
    "mcp.shell": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/shell",
    "uai.chat": os.getenv("UAI_URL", "http://uai:8080") + "/v1/chat/completions",
    "gateway.llm": os.getenv("GATEWAY_URL", "http://athena-api:8000") + "/v1/chat/completions",
    "vision.analyze": os.getenv("FASTVLM_URL", "http://athena-fastvlm:8088") + "/analyze",
    "tts.speak": os.getenv("KOKORO_URL", "http://athena-kokoro:8091") + "/tts",
    
    # Frontend tools (NEW)
    "frontend.xcode_build": "http://host.docker.internal:8413/tool/xcode_build",
    "frontend.app_launch": "http://host.docker.internal:8413/tool/app_launch",
    "frontend.ui_typing_probe": "http://host.docker.internal:8413/tool/ui_typing_probe",
    "frontend.swift_frontend_reflex": "http://host.docker.internal:8413/tool/swift_frontend_reflex",
    
    # Git tools (NEW)
    "git.commit_push_pr": os.getenv("MCP_URL", "http://athena-mcp-ecosystem:8412") + "/tool/git_commit_push_pr",
}
```

## Verify Tool Registry

```bash
# Check if tools are accessible
curl -fsS http://localhost:8413/tool/xcode_build -X POST \
  -H 'Content-Type: application/json' \
  -d '{"project": "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp/NeuroForgeApp.xcodeproj"}' | jq .

# Restart AGI Core
docker compose restart agi-core

# Test tool resolution
curl -s http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{"objective": "List available tools", "tools": [], "context": {}}' | jq '.result.tools_available'
```

## Quick Test

Once tools are registered:

```bash
# Simple test: Ask AGI to read a file
curl -s -X POST http://localhost:8000/api/execute \
  -H 'Content-Type: application/json' \
  -d '{
    "objective": "Read the main ContentView.swift file",
    "context": {"repo": "/Users/christianmerrill/Documents/GitHub/NeuroForgeApp"},
    "tools": ["mcp.fs.read"],
    "max_steps": 2
  }' | jq .

# If that works, you're ready for the full fix
make agi-fix-frontend
```

