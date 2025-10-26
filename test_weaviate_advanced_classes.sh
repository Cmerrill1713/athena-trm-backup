#!/bin/bash

echo "🧪 Testing Weaviate Advanced Classes"
echo "====================================="
echo ""

echo "1️⃣ Testing AIMemory (Conversation Memory)"
echo "------------------------------------------"

# Store new memory
echo "Storing test memory..."
curl -s -X POST http://localhost:8090/v1/objects \
  -H "Content-Type: application/json" \
  -d '{
    "class": "AIMemory",
    "properties": {
      "content": "User asked about autonomous AI features. System explained all 6 features A-F.",
      "memoryType": "conversation",
      "serviceId": "integration_test",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "metadata": "{\"test\": true}"
    }
  }' | jq '{id: .id[:20], class: .class}'

echo ""
echo "Retrieving memories:"
curl -s 'http://localhost:8090/v1/objects?class=AIMemory&limit=5' \
  | jq '.objects[] | {content: .properties.content[:80], type: .properties.memoryType, timestamp: .properties.timestamp}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "2️⃣ Testing AIContext (User Preferences)"
echo "----------------------------------------"

# Store new context
echo "Storing user preference..."
curl -s -X POST http://localhost:8090/v1/objects \
  -H "Content-Type: application/json" \
  -d '{
    "class": "AIContext",
    "properties": {
      "content": "User prefers detailed technical explanations with examples",
      "contextKey": "explanation_style"
    }
  }' | jq '{id: .id[:20], class: .class}'

echo ""
echo "All user contexts:"
curl -s 'http://localhost:8090/v1/objects?class=AIContext' \
  | jq '.objects[] | {key: .properties.contextKey, value: .properties.content}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "3️⃣ Testing AIAgentLog (Activity Logging)"
echo "-----------------------------------------"

# Store agent activity
curl -s -X POST http://localhost:8090/v1/objects \
  -H "Content-Type: application/json" \
  -d '{
    "class": "AIAgentLog",
    "properties": {
      "action": "comprehensive_test",
      "result": "success",
      "timestamp": "'$(date -u +%Y-%m-%dT%H:%M:%SZ)'",
      "metadata": "{\"tests_run\": 39, \"passed\": 38}"
    }
  }' | jq '{id: .id[:20], class: .class, stored: true}'

echo ""
echo "Recent agent activity:"
curl -s 'http://localhost:8090/v1/objects?class=AIAgentLog&limit=3' \
  | jq '.objects[] | {action: .properties.action, result: .properties.result, timestamp: .properties.timestamp}'

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "4️⃣ Testing LearnedPattern (Pattern Storage)"
echo "---------------------------------------------"

# Store learned pattern
curl -s -X POST http://localhost:8090/v1/objects \
  -H "Content-Type: application/json" \
  -d '{
    "class": "LearnedPattern",
    "properties": {
      "pattern": "weather_queries_prefer_tool_routing",
      "confidence": 0.92,
      "usageCount": 11,
      "successRate": 0.91
    }
  }' | jq '{id: .id[:20], class: .class, stored: true}'

echo ""
echo "All learned patterns:"
curl -s 'http://localhost:8090/v1/objects?class=LearnedPattern' \
  | jq '.objects[] | {pattern: .properties.pattern, confidence: .properties.confidence, usageCount: .properties.usageCount}'

echo ""
echo "====================================="
echo "✅ Weaviate Advanced Classes Tested"

