#!/bin/bash
# Athena Tool: Query RAG knowledge base directly
cd "$(dirname "$0")/.."

QUERY="${1:-neuroforge}"

echo "🔍 Querying RAG: '$QUERY'"
echo ""

curl -s -X POST 127.0.0.1:8015/api/rag/query \
  -H 'content-type: application/json' \
  -d "{\"query\":\"$QUERY\",\"k\":5}" \
  | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    hits = data.get('hits', [])
    print(f'✅ Found {len(hits)} results\\n')
    for i, hit in enumerate(hits[:3], 1):
        print(f'{i}. {hit.get(\"title\", \"Untitled\")}')
        print(f'   {hit.get(\"text\", \"\")[:150]}...\\n')
except:
    print('⚠️  RAG service not responding or returned invalid JSON')
    sys.exit(1)
"

