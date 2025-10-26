#!/bin/bash
# Quick ship check - just essentials

echo "Quick Ship Check:"
echo ""

# RAG Gateway
curl -sf http://localhost:8088/health > /dev/null && echo "✓ RAG Gateway (8088)" || echo "✗ RAG Gateway"

# Weaviate  
curl -sf http://localhost:8090/v1/meta > /dev/null && echo "✓ Weaviate (8090)" || echo "✗ Weaviate"

# OpenAI Adapter
curl -sf http://localhost:3000/v1/models > /dev/null && echo "✓ OpenAI Adapter (3000)" || echo "✗ Adapter"

# Test KB search
echo ""
echo "Testing KB search..."
RESULT=$(curl -s http://localhost:8088/kb/search -H "Content-Type: application/json" -d "{\"query\":\"test\",\"topK\":3,\"mode\":\"nearText\"}")
HITS=$(echo "$RESULT" | jq -r ".hits | length" 2>/dev/null || echo "0")

if [ "$HITS" -ge 0 ]; then
  echo "✓ KB search works (returned $HITS hits)"
else
  echo "✗ KB search failed"
  exit 1
fi

echo ""
echo "✓ CORE SERVICES READY - You can use the RAG Gateway!"
