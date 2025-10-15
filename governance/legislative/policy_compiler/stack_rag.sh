#!/bin/bash
# Athena Tool: Enable RAG knowledge base service
set -e
cd "$(dirname "$0")/.."

echo "📚 Enabling RAG knowledge base..."
make stack-rag && make truth

curl -fs 127.0.0.1:8015/api/rag/health && echo "✅ RAG service ready" || echo "⚠️  RAG not responding"

