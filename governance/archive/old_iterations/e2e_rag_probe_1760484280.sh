#!/bin/bash
# End-to-end RAG quality probe
set -euo pipefail

API="${API_BASE:-http://localhost:8014}"

echo "🧪 RAG End-to-End Probe"
echo "API: $API"
echo "="
echo

probe() {
    q="$1"
    echo "Q: $q"
    echo "---"
    
    curl -s "$API/api/rag/query" \
        -H 'Content-Type: application/json' \
        -d "{\"query\":\"$q\",\"k\":5,\"alpha\":0.45}" \
        | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    hits = data.get('hits', [])
    for i, hit in enumerate(hits[:3], 1):
        print(f\"{i}. {hit['title']}\")
        print(f\"   Channel: {hit.get('channel', 'Unknown')}\")
        print(f\"   Score: {hit.get('score', 0):.2f}\")
        print()
    print(f\"Latency: {data.get('latency_ms', 0)}ms\")
except Exception as e:
    print(f'Error: {e}')
"
    echo
    echo
}

probe "How does Cursor compare to Claude Code for repo-wide refactors?"
probe "What is the Scout-Plan-Build pattern?"
probe "Agentic coding with MCP servers"
probe "Best practices for prompt engineering with AI agents"

echo "✅ Probe complete"

