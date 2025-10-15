#!/bin/bash
#
# Cursor MCP Setup Script
# =======================
#
# Sets up Athena MCP server for Cursor IDE integration
# Compatible with macOS, Linux, Windows (WSL)
#

set -e

echo "🎯 Setting up Cursor MCP Integration"
echo "==================================="

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is required but not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "❌ Docker Compose is required but not installed."
    exit 1
fi

# Function to check command success
check_command() {
    if [ $? -eq 0 ]; then
        echo "✅ $1"
    else
        echo "❌ $1 failed"
        exit 1
    fi
}

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "📁 Working directory: $SCRIPT_DIR"

# 1. Create .cursor directory if it doesn't exist
echo
echo "1️⃣ Setting up Cursor configuration..."
mkdir -p ~/.cursor
check_command "Created ~/.cursor directory"

# Copy MCP configuration
if [ -f "$SCRIPT_DIR/.cursor/mcp.json" ]; then
    cp "$SCRIPT_DIR/.cursor/mcp.json" ~/.cursor/
    check_command "HTTP MCP configuration"
else
    echo "⚠️ HTTP MCP config not found, creating basic config"
    cat > ~/.cursor/mcp.json << 'EOF'
{
  "mcpServers": {
    "athena-mcp": {
      "transport": "http",
      "url": "http://localhost:3333",
      "capabilities": ["tools", "resources", "prompts"]
    }
  }
}
EOF
fi

# 2. Install MCP server dependencies
echo
echo "2️⃣ Installing MCP server dependencies..."

# Create requirements file for MCP server
cat > requirements-mcp.txt << 'EOF'
mcp-server>=0.1.0
fastapi>=0.100.0
uvicorn>=0.20.0
pydantic>=2.0.0
EOF

if command -v pip3 &> /dev/null; then
    pip3 install -r requirements-mcp.txt
    check_command "MCP server dependencies"
elif command -v pip &> /dev/null; then
    pip install -r requirements-mcp.txt
    check_command "MCP server dependencies"
else
    echo "⚠️ pip not found, you'll need to install dependencies manually:"
    echo "   pip install mcp-server fastapi uvicorn pydantic"
fi

# 3. Test MCP server locally (optional)
echo
echo "3️⃣ Testing MCP server setup..."
if [ -f "$SCRIPT_DIR/mcp_server.py" ]; then
    python3 -c "
import sys
sys.path.insert(0, '$SCRIPT_DIR')
try:
    from mcp_server import AthenaMCPServer
    print('✅ MCP server imports successfully')
except ImportError as e:
    print('❌ Import error:', e)
    print('Make sure all dependencies are installed')
    exit(1)
"
    check_command "MCP server test"
else
    echo "⚠️ MCP server file not found at $SCRIPT_DIR/mcp_server.py"
fi

# 4. Create Docker wrapper scripts
echo
echo "4️⃣ Creating Docker management scripts..."

# Create start script
cat > start_mcp_server.sh << 'EOF'
#!/bin/bash
echo "🚀 Starting Athena MCP Server..."

# Check if already running
if docker ps | grep -q athena_mcp_server; then
    echo "✅ Server already running"
    exit 0
fi

# Start with docker-compose
if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.mcp.yml up -d
elif docker compose version &> /dev/null; then
    docker compose -f docker-compose.mcp.yml up -d
else
    echo "❌ Docker Compose not found"
    exit 1
fi

echo "⏳ Waiting for server to be ready..."
sleep 5

# Check health
if curl -f http://localhost:3333/health &> /dev/null; then
    echo "✅ MCP Server is healthy at http://localhost:3333"
else
    echo "⚠️ Server started but health check failed"
fi
EOF

# Create stop script
cat > stop_mcp_server.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Athena MCP Server..."

if command -v docker-compose &> /dev/null; then
    docker-compose -f docker-compose.mcp.yml down
elif docker compose version &> /dev/null; then
    docker compose -f docker-compose.mcp.yml down
else
    echo "❌ Docker Compose not found"
    exit 1
fi

echo "✅ Server stopped"
EOF

# Make scripts executable
chmod +x start_mcp_server.sh stop_mcp_server.sh
check_command "Docker management scripts"

# 5. Create Cursor integration documentation
echo
echo "5️⃣ Creating Cursor integration guide..."

cat > CURSOR_MCP_INTEGRATION.md << 'EOF'
# Cursor + Athena MCP Integration

This guide shows how to use Athena's AI capabilities directly in Cursor IDE.

## Quick Start

1. **Start the MCP Server:**
   ```bash
   ./start_mcp_server.sh
   ```

2. **Restart Cursor** to load the MCP configuration.

3. **Use Athena Tools** in Cursor:
   - Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
   - Type "MCP" or look for server tools
   - Available tools will appear

## Available Tools

### SwiftUI Development
- **Generate NavigationStack** - Create modern SwiftUI navigation
- **Create ViewModel (Async)** - Generate ViewModels with async/await
- **Refactor to Async** - Convert completion handlers to async/await
- **Analyze Performance** - Check SwiftUI code for performance issues
- **Generate Component** - Create complete SwiftUI components

### Athena System
- **System Status** - Check Athena component health

## Example Usage

### Generate NavigationStack
```
Select code or use command palette → "Generate NavigationStack"
Input: view_name="MainView", destinations=["ProfileView", "SettingsView"]
Output: Complete NavigationStack implementation
```

### Refactor to Async/Await
```
Select code with completion handlers → "Refactor to Async"
Tool automatically converts completion handler patterns
```

## Troubleshooting

### Server Not Connecting
```bash
# Check if server is running
curl http://localhost:3333/health

# Restart server
./stop_mcp_server.sh
./start_mcp_server.sh
```

### Tools Not Appearing in Cursor
1. Restart Cursor completely
2. Check `~/.cursor/mcp.json` exists and is valid JSON
3. Verify server is healthy

### Permission Issues
```bash
# On macOS, allow Cursor to run unsigned binaries if needed
# System Settings → Privacy & Security → Developer Tools
```

## Configuration

### Switch to Stdio Transport (Alternative)
If HTTP transport doesn't work, use stdio:

1. Copy `.cursor/mcp_stdio.json` to `~/.cursor/mcp.json`
2. Start server with stdio profile:
   ```bash
   docker-compose -f docker-compose.mcp.yml --profile stdio up -d athena-mcp-stdio
   ```

### Custom Server Configuration
Edit `~/.cursor/mcp.json`:
```json
{
  "mcpServers": {
    "athena-mcp": {
      "transport": "http",
      "url": "http://localhost:3333",
      "capabilities": ["tools", "resources", "prompts"]
    }
  }
}
```

## Development

### Local MCP Server Development
```bash
# Run server locally (no Docker)
pip install -r requirements-mcp.txt
python mcp_server.py --transport http --port 3333

# Test tools
curl -X POST http://localhost:3333/mcp \
  -H "Content-Type: application/json" \
  -d '{"tool": "athena_system_status"}'
```

### Adding New Tools
1. Add tool definition in `mcp_server.py`
2. Implement handler method
3. Restart MCP server
4. Restart Cursor

## Support

If tools aren't appearing:
1. Check Cursor version (MCP support requires recent versions)
2. Verify server logs: `docker logs athena_mcp_server`
3. Check Cursor logs for MCP connection errors

---
**Athena MCP Server**: Bringing AI-powered development tools directly into your IDE.
EOF

check_command "Cursor integration guide"

# 6. Final instructions
echo
echo "🎉 Cursor MCP Integration Setup Complete!"
echo
echo "🚀 Next Steps:"
echo "   1. Start MCP server: ./start_mcp_server.sh"
echo "   2. Restart Cursor IDE completely"
echo "   3. Open Command Palette (Cmd+Shift+P) and look for MCP tools"
echo
echo "📚 Documentation: CURSOR_MCP_INTEGRATION.md"
echo
echo "🔧 Management:"
echo "   Start server:  ./start_mcp_server.sh"
echo "   Stop server:   ./stop_mcp_server.sh"
echo "   Check status:  curl http://localhost:3333/health"
echo
echo "🎯 Available Tools:"
echo "   • Generate NavigationStack - Modern SwiftUI routing"
echo "   • Create ViewModel (Async) - Async/await patterns"
echo "   • Refactor to Async - Convert completion handlers"
echo "   • Analyze Performance - SwiftUI optimization"
echo "   • System Status - Athena component health"
echo "   • Generate Component - Complete SwiftUI components"
echo
echo "✅ Ready for AI-powered development in Cursor!"

# Final verification
echo
echo "🔍 Final verification..."
if [ -f ~/.cursor/mcp.json ]; then
    echo "✅ Cursor MCP config: ~/.cursor/mcp.json"
else
    echo "❌ Cursor MCP config missing"
fi

if [ -f start_mcp_server.sh ] && [ -f stop_mcp_server.sh ]; then
    echo "✅ Docker management scripts ready"
else
    echo "❌ Docker scripts missing"
fi

if [ -f CURSOR_MCP_INTEGRATION.md ]; then
    echo "✅ Documentation created"
else
    echo "❌ Documentation missing"
fi

echo
echo "🎯 Setup verification complete!"
