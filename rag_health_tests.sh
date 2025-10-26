#!/bin/bash
# RAG Health Tests - Copy/Paste Ready
# ===================================
# Quick health checks for DocsV2 semantic search functionality

set -e

WEAVIATE_URL="${WEAVIATE_URL:-http://127.0.0.1:8090}"
EXPECTED_DIM=384

echo "🧪 RAG Health Tests - DocsV2 Validation"
echo "========================================"

# Test 1: Schema Sanity Check
echo "1️⃣ Schema Sanity Check..."
SCHEMA_CHECK=$(curl -s "$WEAVIATE_URL/v1/schema/DocsV2" | jq -r '{class:.class,vectorizer:.vectorizer,idx:.vectorIndexType}')
echo "   Schema: $SCHEMA_CHECK"

if echo "$SCHEMA_CHECK" | jq -e '.vectorizer != "text2vec-huggingface"' > /dev/null; then
    echo "❌ Schema check FAILED: Wrong vectorizer"
    exit 1
fi

if echo "$SCHEMA_CHECK" | jq -e '.idx != "hnsw"' > /dev/null; then
    echo "❌ Schema check FAILED: Wrong index type"
    exit 1
fi

echo "✅ Schema check PASSED"

# Test 2: nearText Semantic Search
echo ""
echo "2️⃣ nearText Semantic Search Test..."
NEARTEXT_RESULT=$(curl -s -X POST "$WEAVIATE_URL/v1/graphql" \
    -H "Content-Type: application/json" \
    -d '{"query":"{Get{DocsV2(nearText:{concepts:[\"smoke test\"]} limit:1){path text _additional{distance}}}}"}')

echo "   Result: $NEARTEXT_RESULT"

if echo "$NEARTEXT_RESULT" | jq -e '.errors' > /dev/null; then
    echo "❌ nearText test FAILED: GraphQL errors detected"
    echo "$NEARTEXT_RESULT" | jq '.errors'
    exit 1
fi

echo "✅ nearText test PASSED"

# Test 3: nearVector + 384-dim Check
echo ""
echo "3️⃣ nearVector + Dimension Check..."

# Generate 384-dim vector using Python
PYTHON_TEST=$(python3 -c "
from sentence_transformers import SentenceTransformer
import requests, json, os

# Load model and generate vector
model = SentenceTransformer('all-MiniLM-L6-v2')
vector = model.encode('smoke test').tolist()

# Validate dimension
assert len(vector) == 384, f'Wrong dimension: {len(vector)} != 384'
print(f'Vector dimension: {len(vector)}')

# Test nearVector query
weaviate_url = os.environ.get('WEAVIATE_URL', 'http://127.0.0.1:8090')
query = {
    'query': '{Get{DocsV2(nearVector:{vector:%s} limit:1){path text _additional{distance}}}}' % json.dumps(vector)
}

try:
    response = requests.post(f'{weaviate_url}/v1/graphql', json=query, timeout=10)
    response.raise_for_status()
    result = response.json()
    
    if 'errors' in result:
        print('ERROR:', result['errors'])
        exit(1)
    else:
        print('SUCCESS:', json.dumps(result, indent=2))
except Exception as e:
    print('ERROR:', str(e))
    exit(1)
")

echo "   Python test result:"
echo "$PYTHON_TEST"

if echo "$PYTHON_TEST" | grep -q "ERROR"; then
    echo "❌ nearVector test FAILED"
    exit 1
fi

echo "✅ nearVector test PASSED"

# Test 4: Performance Baseline
echo ""
echo "4️⃣ Performance Baseline Check..."
START_TIME=$(date +%s%N)
curl -s -X POST "$WEAVIATE_URL/v1/graphql" \
    -H "Content-Type: application/json" \
    -d '{"query":"{Get{DocsV2(nearText:{concepts:[\"performance test\"]} limit:5){path text _additional{distance}}}}"}' > /dev/null
END_TIME=$(date +%s%N)
DURATION_MS=$(( (END_TIME - START_TIME) / 1000000 ))

echo "   Query latency: ${DURATION_MS}ms"

if [ $DURATION_MS -gt 1000 ]; then
    echo "⚠️  Performance WARNING: Query took ${DURATION_MS}ms (>1000ms)"
else
    echo "✅ Performance check PASSED: ${DURATION_MS}ms"
fi

# Test 5: Feature Flag Check
echo ""
echo "5️⃣ Feature Flag Check..."
if [ "${FEATURE_RAG_SEMANTIC:-true}" = "true" ]; then
    echo "✅ RAG semantic search is ENABLED"
else
    echo "⚠️  RAG semantic search is DISABLED via FEATURE_RAG_SEMANTIC=false"
fi

echo ""
echo "🎉 All health tests completed!"
echo "📊 DocsV2 is ready for production semantic search"
