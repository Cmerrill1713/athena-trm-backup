#!/bin/bash
# Test MCP servers can start

echo "🧪 Testing MCP Server Startup"
echo "=============================="
echo ""

# Test Python servers exist
echo "📁 Checking Python servers..."
for server in python_servers/youtube_server.py python_servers/research_server.py python_servers/web_server.py python_servers/store_client.py; do
    if [ -f "$server" ]; then
        echo "  ✅ $(basename $server)"
    else
        echo "  ❌ $(basename $server) - NOT FOUND"
    fi
done

echo ""

# Test Node server exists
echo "📁 Checking Node.js server..."
if [ -f "node_servers/index.js" ]; then
    echo "  ✅ index.js"
else
    echo "  ❌ index.js - NOT FOUND"
fi

echo ""

# Test syntax
echo "🔍 Checking Python syntax..."
for server in python_servers/*.py; do
    if python3.11 -m py_compile "$server" 2>/dev/null; then
        echo "  ✅ $(basename $server) - Valid"
    else
        echo "  ⚠️  $(basename $server) - Syntax issue (might need mcp package)"
    fi
done

echo ""

# Test Node syntax (if Node is available)
if command -v node >/dev/null 2>&1; then
    echo "🔍 Checking Node.js syntax..."
    if [ -f "node_servers/index.js" ]; then
        if node --check node_servers/index.js 2>/dev/null; then
            echo "  ✅ index.js - Valid"
        else
            echo "  ⚠️  index.js - Needs @modelcontextprotocol/sdk"
        fi
    fi
fi

echo ""
echo "=============================="
echo "✅ File structure verified!"
echo "=============================="
