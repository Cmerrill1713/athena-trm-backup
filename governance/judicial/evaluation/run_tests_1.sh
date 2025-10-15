#!/bin/bash
#
# Test Complete MCP Ecosystem
# Verifies all SDKs and servers are working
#

set -e

echo "🧪 MCP Ecosystem Integration Tests"
echo "======================================"
echo ""

cd "$(dirname "$0")"

PASSED=0
FAILED=0

# Helper function
test_command() {
    local name=$1
    local command=$2
    
    echo -n "Testing $name... "
    if eval "$command" >/dev/null 2>&1; then
        echo "✅ PASS"
        ((PASSED++))
    else
        echo "❌ FAIL"
        ((FAILED++))
    fi
}

# Test Python servers
echo "🐍 Python MCP Servers"
echo "----------------------"
test_command "YouTube Server" "python3 python_servers/youtube_server.py --help"
test_command "Research Server" "python3 python_servers/research_server.py --help"
test_command "Web Server" "python3 python_servers/web_server.py --help"
test_command "Store Client" "python3 python_servers/store_client.py --help"
test_command "Pydantic Orchestrator" "python3 -c 'import pydantic_orchestrator'"

echo ""

# Test Node.js servers
echo "📘 Node.js MCP Servers"
echo "----------------------"
test_command "Node MCP Server" "node -c 'require(\"./node_servers/index.js\")'"
test_command "MCP SDK" "node -e 'require(\"@modelcontextprotocol/sdk\")'"

echo ""

# Test Python dependencies
echo "📦 Python Dependencies"
echo "----------------------"
test_command "yt-dlp-transcript" "python3 -c 'from yt_dlp_transcript import yt_dlp_transcript'"
test_command "arxiv" "python3 -c 'import arxiv'"
test_command "wikipedia" "python3 -c 'import wikipedia'"
test_command "duckduckgo-search" "python3 -c 'from duckduckgo_search import DDGS'"
test_command "FastMCP" "python3 -c 'from mcp.server.fastmcp import FastMCP'"
test_command "Pydantic AI" "python3 -c 'from pydantic_ai import Agent'"
test_command "beautifulsoup4" "python3 -c 'from bs4 import BeautifulSoup'"

echo ""

# Test Node dependencies  
echo "📦 Node.js Dependencies"
echo "-----------------------"
test_command "axios" "node -e 'require(\"axios\")'"
test_command "cheerio" "node -e 'require(\"cheerio\")'"

echo ""

# Test Go (optional)
if [ -f "go_mcp/mcp-go-server" ]; then
    echo "🟦 Go MCP Server"
    echo "----------------"
    test_command "Go MCP Binary" "go_mcp/mcp-go-server --version"
    echo ""
fi

# Test Rust (optional)
if [ -f "rust_mcp/target/release/rust-mcp-server" ]; then
    echo "🦀 Rust MCP Server"
    echo "------------------"
    test_command "Rust MCP Binary" "rust_mcp/target/release/rust-mcp-server --version"
    echo ""
fi

# Summary
echo "======================================"
echo "📊 Test Summary"
echo "======================================"
echo "Total Tests:  $((PASSED + FAILED))"
echo "Passed:       $PASSED ✅"
echo "Failed:       $FAILED ❌"
echo ""

if [ $FAILED -eq 0 ]; then
    echo "🎉 All tests passed!"
    echo ""
    echo "✅ MCP Ecosystem is ready to use!"
    echo ""
    echo "📝 Next steps:"
    echo "  • Build Docker: docker compose build"
    echo "  • Start: docker compose up -d"
    echo "  • Use: Update mcp-config.json"
    exit 0
else
    echo "❌ Some tests failed"
    echo ""
    echo "🔧 Fix issues and run again: ./run_tests.sh"
    exit 1
fi

