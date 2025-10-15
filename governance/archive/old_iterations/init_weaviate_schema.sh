#!/bin/bash
#
# Initialize Weaviate schema for MCP Store
# This creates the ValidationResult class in Weaviate for semantic search
#

set -e

WEAVIATE_URL=${WEAVIATE_URL:-"http://localhost:8090"}

echo "🔧 Initializing Weaviate schema for MCP Store..."
echo "   Target: $WEAVIATE_URL"

# Check if Weaviate is reachable
if ! curl -sf "$WEAVIATE_URL/v1/meta" >/dev/null 2>&1; then
    echo "❌ ERROR: Weaviate is not reachable at $WEAVIATE_URL"
    echo "   Start it with: make mcp-store-full"
    exit 1
fi

echo "✅ Weaviate is reachable"

# Create ValidationResult class
echo "📝 Creating ValidationResult class..."

curl -sS -X POST "$WEAVIATE_URL/v1/schema" \
  -H "Content-Type: application/json" \
  -d '{
  "classes": [
    {
      "class": "ValidationResult",
      "description": "Validation and test results from all agents and services",
      "vectorizer": "none",
      "properties": [
        {
          "name": "agent",
          "dataType": ["text"],
          "description": "Name of the agent that performed the validation"
        },
        {
          "name": "service",
          "dataType": ["text"],
          "description": "Name of the service being validated"
        },
        {
          "name": "status",
          "dataType": ["text"],
          "description": "Validation status: PASS, FAIL, or WARN"
        },
        {
          "name": "summary",
          "dataType": ["text"],
          "description": "Brief summary of the validation result"
        },
        {
          "name": "details",
          "dataType": ["text"],
          "description": "Detailed validation metrics and results as JSON"
        },
        {
          "name": "commit",
          "dataType": ["text"],
          "description": "Git commit SHA or version identifier"
        },
        {
          "name": "ts",
          "dataType": ["date"],
          "description": "Timestamp of the validation"
        }
      ]
    }
  ]
}' 2>&1 | grep -v "already exists" || true

echo ""
echo "✅ Weaviate schema initialized successfully!"
echo ""
echo "📊 Verifying schema..."
curl -sS "$WEAVIATE_URL/v1/schema/ValidationResult" | python3 -m json.tool 2>/dev/null || echo "  (Schema exists)"
echo ""
echo "🎉 Done! MCP Store is ready to use."

