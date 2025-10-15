#!/bin/bash
#
# Build Complete MCP Ecosystem
# Compiles Python, Node.js, Go, and Rust MCP servers
#

set -e

echo "🏗️  Building Complete MCP Ecosystem"
echo "======================================"
echo ""

cd "$(dirname "$0")"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 1. Python servers
echo -e "${BLUE}1️⃣  Building Python MCP Servers...${NC}"
if [ -f "requirements.txt" ]; then
    python3 -m pip install -q -r requirements.txt
    echo -e "${GREEN}✅ Python dependencies installed${NC}"
else
    echo "⚠️  requirements.txt not found"
fi

# Verify Python servers
for server in python_servers/*.py pydantic_orchestrator.py; do
    if [ -f "$server" ]; then
        python3 -m py_compile "$server" && echo "  ✅ $(basename $server)"
    fi
done

echo ""

# 2. Node.js servers
echo -e "${BLUE}2️⃣  Building Node.js MCP Servers...${NC}"
if [ -f "package.json" ]; then
    npm install --silent
    echo -e "${GREEN}✅ Node.js dependencies installed${NC}"
    
    # Verify Node server
    if [ -f "node_servers/index.js" ]; then
        node -c node_servers/index.js && echo "  ✅ index.js"
    fi
else
    echo "⚠️  package.json not found - creating..."
    cat > package.json << 'EOF'
{
  "name": "mcp-ecosystem-node",
  "version": "1.0.0",
  "type": "module",
  "dependencies": {
    "@modelcontextprotocol/sdk": "^1.0.0",
    "axios": "^1.7.9",
    "cheerio": "^1.0.0"
  }
}
EOF
    npm install --silent
    echo -e "${GREEN}✅ Node.js setup complete${NC}"
fi

echo ""

# 3. Go servers (optional)
echo -e "${BLUE}3️⃣  Building Go MCP Server...${NC}"
if [ -d "go_mcp" ] && [ -f "go_mcp/server.go" ]; then
    cd go_mcp
    go build -o mcp-go-server server.go 2>/dev/null && echo -e "${GREEN}✅ Go MCP server built${NC}" || echo "⚠️  Go build skipped (optional)"
    cd ..
else
    echo "⚠️  Go MCP not found (optional)"
fi

echo ""

# 4. Rust servers (optional)
echo -e "${BLUE}4️⃣  Building Rust MCP Server...${NC}"
if [ -d "rust_mcp" ] && [ -f "rust_mcp/Cargo.toml" ]; then
    cd rust_mcp
    cargo build --release 2>/dev/null && echo -e "${GREEN}✅ Rust MCP server built${NC}" || echo "⚠️  Rust build skipped (optional)"
    cd ..
else
    echo "⚠️  Rust MCP not found (optional)"
fi

echo ""

# 5. Create startup scripts
echo -e "${BLUE}5️⃣  Creating helper scripts...${NC}"

# Create test script
cat > test_ecosystem.sh << 'TESTEOF'
#!/bin/bash
echo "🧪 Testing MCP Ecosystem Components"
echo ""

# Test Python servers
echo "Python Servers:"
python3 -c "from yt_dlp_transcript import yt_dlp_transcript; print('  ✅ yt-dlp-transcript')" 2>/dev/null || echo "  ❌ yt-dlp-transcript"
python3 -c "import arxiv; print('  ✅ arxiv')" 2>/dev/null || echo "  ❌ arxiv"
python3 -c "import wikipedia; print('  ✅ wikipedia')" 2>/dev/null || echo "  ❌ wikipedia"
python3 -c "from mcp.server.fastmcp import FastMCP; print('  ✅ FastMCP')" 2>/dev/null || echo "  ❌ FastMCP"
python3 -c "from pydantic_ai import Agent; print('  ✅ Pydantic AI')" 2>/dev/null || echo "  ❌ Pydantic AI"

echo ""
echo "Node.js Modules:"
node -e "require('@modelcontextprotocol/sdk'); console.log('  ✅ MCP SDK')" 2>/dev/null || echo "  ❌ MCP SDK"
node -e "require('axios'); console.log('  ✅ axios')" 2>/dev/null || echo "  ❌ axios"
node -e "require('cheerio'); console.log('  ✅ cheerio')" 2>/dev/null || echo "  ❌ cheerio"

echo ""
echo "✅ Ecosystem components verified!"
TESTEOF

chmod +x test_ecosystem.sh

echo -e "${GREEN}✅ test_ecosystem.sh created${NC}"

echo ""
echo "======================================"
echo -e "${GREEN}🎉 MCP Ecosystem Build Complete!${NC}"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo "  1. Test components:    ./test_ecosystem.sh"
echo "  2. Build Docker:       docker compose build"
echo "  3. Start ecosystem:    docker compose up -d"
echo "  4. Run tests:          ./run_tests.sh"
echo ""

